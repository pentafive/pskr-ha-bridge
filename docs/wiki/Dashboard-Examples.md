# Dashboard Examples

This page provides Home Assistant dashboard examples for the PSKReporter integration.

**Quick Links:**
- [Personal Monitor Cards](#personal-monitor-cards)
- [Global Monitor Cards](#global-monitor-cards)
- [Antenna Comparison Dashboard](#antenna-comparison-dashboard)
- [Health Monitoring Cards](#health-monitoring-cards)
- [Automations](#automations)
- [Entity Mapping (Docker → HACS)](#entity-mapping-docker--hacs)

## Required HACS Frontend Cards

For the full dashboard experience, install these cards from HACS:

| Card | Purpose | Install |
|------|---------|---------|
| [mushroom](https://github.com/piitaya/lovelace-mushroom) | Modern entity cards, chips, titles | HACS → Frontend |
| [mini-graph-card](https://github.com/kalkih/mini-graph-card) | Simple trend charts with thresholds | HACS → Frontend |
| [apexcharts-card](https://github.com/RomRider/apexcharts-card) | Advanced charts, comparisons, bar charts | HACS → Frontend |

**Minimum requirement:** The basic entities card works without custom cards.

---

## Complete Dashboard Files

Ready-to-use dashboard YAML files are available in [`examples/dashboards/`](../../examples/dashboards/):

| Dashboard | File | Purpose |
|-----------|------|---------|
| Personal Monitor | [`personal-monitor.yaml`](../../examples/dashboards/personal-monitor.yaml) | Single station monitoring |
| Global Monitor | [`global-monitor.yaml`](../../examples/dashboards/global-monitor.yaml) | Network-wide propagation |
| Antenna Comparison | [`antenna-comparison.yaml`](../../examples/dashboards/antenna-comparison.yaml) | Compare two stations |

Replace `{callsign}` with your callsign in lowercase (e.g., `w1abc`, `kd5qlm`).

---

## Personal Monitor Cards

### Basic Entities Card

```yaml
type: entities
title: PSKReporter - W1ABC
entities:
  - entity: sensor.pskreporter_w1abc_total_spots
  - entity: sensor.pskreporter_w1abc_unique_stations
  - entity: sensor.pskreporter_w1abc_most_active_band
  - entity: sensor.pskreporter_w1abc_maximum_distance
  - entity: sensor.pskreporter_w1abc_average_snr
  - entity: sensor.pskreporter_w1abc_spots_per_minute
  - entity: sensor.pskreporter_w1abc_last_spot_time
```

### Glance Card

```yaml
type: glance
title: Ham Radio Activity
entities:
  - entity: sensor.pskreporter_w1abc_total_spots
    name: Spots
  - entity: sensor.pskreporter_w1abc_unique_stations
    name: Stations
  - entity: sensor.pskreporter_w1abc_most_active_band
    name: Band
  - entity: binary_sensor.pskreporter_w1abc_feed_health
    name: Feed
```

### Mushroom Cards (Personal)

```yaml
type: vertical-stack
cards:
  - type: custom:mushroom-title-card
    title: PSKReporter - W1ABC
    subtitle: Amateur Radio Spot Monitoring

  - type: horizontal-stack
    cards:
      - type: custom:mushroom-entity-card
        entity: sensor.pskreporter_w1abc_total_spots
        name: Spots
        icon_color: blue
      - type: custom:mushroom-entity-card
        entity: sensor.pskreporter_w1abc_unique_stations
        name: Stations
        icon_color: green

  - type: horizontal-stack
    cards:
      - type: custom:mushroom-entity-card
        entity: sensor.pskreporter_w1abc_most_active_band
        name: Band
        icon_color: orange
      - type: custom:mushroom-entity-card
        entity: sensor.pskreporter_w1abc_maximum_distance
        name: Max DX
        icon_color: purple

  - type: custom:mushroom-entity-card
    entity: binary_sensor.pskreporter_w1abc_feed_health
    name: Feed Health
    icon_color: "{{ 'green' if is_state(entity, 'on') else 'red' }}"
```

### Activity Trend with SNR Thresholds

```yaml
type: vertical-stack
cards:
  # Spot activity trend
  - type: custom:mini-graph-card
    name: Spot Activity (24h)
    entities:
      - entity: sensor.pskreporter_w1abc_total_spots
        name: Spots
    hours_to_show: 24
    points_per_hour: 4
    line_width: 2
    show:
      labels: true
      points: false
      legend: false

  # SNR with color thresholds
  - type: custom:mini-graph-card
    name: SNR Quality (24h)
    entities:
      - entity: sensor.pskreporter_w1abc_average_snr
        name: SNR
    hours_to_show: 24
    line_width: 2
    color_thresholds:
      - value: -15
        color: "#F44336"
      - value: -10
        color: "#FFC107"
      - value: -5
        color: "#4CAF50"
    show:
      labels: true
      points: false
```

---

## Global Monitor Cards

### Band Activity Overview

```yaml
type: entities
title: Global Band Activity
entities:
  - entity: sensor.pskreporter_global_monitor_160m_activity
    name: 160m
  - entity: sensor.pskreporter_global_monitor_80m_activity
    name: 80m
  - entity: sensor.pskreporter_global_monitor_40m_activity
    name: 40m
  - entity: sensor.pskreporter_global_monitor_30m_activity
    name: 30m
  - entity: sensor.pskreporter_global_monitor_20m_activity
    name: 20m
  - entity: sensor.pskreporter_global_monitor_17m_activity
    name: 17m
  - entity: sensor.pskreporter_global_monitor_15m_activity
    name: 15m
  - entity: sensor.pskreporter_global_monitor_12m_activity
    name: 12m
  - entity: sensor.pskreporter_global_monitor_10m_activity
    name: 10m
  - entity: sensor.pskreporter_global_monitor_6m_activity
    name: 6m
```

### Global Stats Glance

```yaml
type: glance
title: PSKReporter Global
entities:
  - entity: sensor.pskreporter_global_monitor_global_spots
    name: Messages
  - entity: sensor.pskreporter_global_monitor_global_unique_stations
    name: Stations
  - entity: sensor.pskreporter_global_monitor_most_active_band_global
    name: Top Band
  - entity: binary_sensor.pskreporter_global_monitor_feed_health
    name: Feed
```

### Band Activity Bar Chart (ApexCharts)

Requires [apexcharts-card](https://github.com/RomRider/apexcharts-card):

```yaml
type: custom:apexcharts-card
header:
  title: HF Band Activity
  show: true
chart_type: bar
series:
  - entity: sensor.pskreporter_global_monitor_20m_activity
    name: 20m
    color: "#1E88E5"
  - entity: sensor.pskreporter_global_monitor_40m_activity
    name: 40m
    color: "#43A047"
  - entity: sensor.pskreporter_global_monitor_15m_activity
    name: 15m
    color: "#FFA726"
  - entity: sensor.pskreporter_global_monitor_10m_activity
    name: 10m
    color: "#E53935"
  - entity: sensor.pskreporter_global_monitor_17m_activity
    name: 17m
    color: "#8E24AA"
  - entity: sensor.pskreporter_global_monitor_30m_activity
    name: 30m
    color: "#00ACC1"
```

### Band Activity Chips

```yaml
type: custom:mushroom-chips-card
chips:
  - type: entity
    entity: sensor.pskreporter_global_monitor_20m_activity
    name: "20m"
    icon_color: blue
  - type: entity
    entity: sensor.pskreporter_global_monitor_40m_activity
    name: "40m"
    icon_color: green
  - type: entity
    entity: sensor.pskreporter_global_monitor_15m_activity
    name: "15m"
    icon_color: orange
  - type: entity
    entity: sensor.pskreporter_global_monitor_10m_activity
    name: "10m"
    icon_color: red
```

---

## Antenna Comparison Dashboard

Compare two stations/antennas side-by-side. See [`examples/dashboards/antenna-comparison.yaml`](../../examples/dashboards/antenna-comparison.yaml) for the complete dashboard.

### Dual-Line Comparison Chart

```yaml
type: custom:apexcharts-card
header:
  title: Spot Count Comparison (24h)
  show: true
graph_span: 24h
series:
  - entity: sensor.pskreporter_kd5qlm_total_spots
    name: "KD5QLM"
    color: "#1E88E5"
    stroke_width: 2
  - entity: sensor.pskreporter_kj5iuy_total_spots
    name: "KJ5IUY"
    color: "#FFA726"
    stroke_width: 2
```

### SNR Quality Comparison

```yaml
type: custom:apexcharts-card
header:
  title: SNR Quality Comparison (24h)
  show: true
graph_span: 24h
yaxis:
  - min: -20
    max: 0
series:
  - entity: sensor.pskreporter_kd5qlm_average_snr
    name: "KD5QLM"
    color: "#1E88E5"
    stroke_width: 2
  - entity: sensor.pskreporter_kj5iuy_average_snr
    name: "KJ5IUY"
    color: "#FFA726"
    stroke_width: 2
```

### Side-by-Side Stats

```yaml
type: horizontal-stack
cards:
  - type: entities
    title: "KD5QLM"
    entities:
      - entity: sensor.pskreporter_kd5qlm_total_spots
        name: Total Spots
      - entity: sensor.pskreporter_kd5qlm_average_snr
        name: Avg SNR
      - entity: sensor.pskreporter_kd5qlm_maximum_distance
        name: Max Distance
  - type: entities
    title: "KJ5IUY"
    entities:
      - entity: sensor.pskreporter_kj5iuy_total_spots
        name: Total Spots
      - entity: sensor.pskreporter_kj5iuy_average_snr
        name: Avg SNR
      - entity: sensor.pskreporter_kj5iuy_maximum_distance
        name: Max Distance
```

---

## Health Monitoring Cards

### Diagnostic Panel

```yaml
type: entities
title: PSKReporter Health
show_header_toggle: false
entities:
  - entity: sensor.pskreporter_w1abc_connection_status
  - entity: sensor.pskreporter_w1abc_feed_status
  - entity: sensor.pskreporter_w1abc_message_rate
  - entity: sensor.pskreporter_w1abc_feed_latency
  - entity: sensor.pskreporter_w1abc_connection_uptime
  - entity: sensor.pskreporter_w1abc_reconnect_count
```

### Conditional Alert Card

```yaml
type: conditional
conditions:
  - entity: binary_sensor.pskreporter_w1abc_feed_health
    state: "off"
card:
  type: markdown
  content: |
    ## ⚠️ PSKReporter Feed Unhealthy
    No data received beyond threshold (personal: 5min, global: 1min).
    Check `sensor.pskreporter_w1abc_feed_status` for details:
    - **Low Activity**: Normal during poor propagation
    - **Stale**: Check network connectivity
    - **Disconnected**: Check firewall/transport settings
```

---

## Automations

### Alert on Feed Failure

```yaml
automation:
  - alias: "PSKReporter Feed Alert"
    trigger:
      - platform: state
        entity_id: binary_sensor.pskreporter_w1abc_feed_health
        to: "off"
        for:
          minutes: 5
    action:
      - service: notify.mobile_app
        data:
          title: "PSKReporter Alert"
          message: "Feed has been unhealthy for 5 minutes"
```

### Log DX Achievement

```yaml
automation:
  - alias: "Log DX Over 10000km"
    trigger:
      - platform: numeric_state
        entity_id: sensor.pskreporter_w1abc_maximum_distance
        above: 10000
    action:
      - service: logbook.log
        data:
          name: "DX Achievement"
          message: "New DX record: {{ states('sensor.pskreporter_w1abc_maximum_distance') }} km"
```

---

## Entity Mapping (Docker → HACS)

If you're migrating from the Docker/MQTT bridge to the HACS integration, use this mapping:

### Personal Monitor Entities

| Docker Bridge Entity | HACS Integration Entity | Status |
|---------------------|------------------------|--------|
| `sensor.pskr_stats_rx_{call}_total_spots` | `sensor.pskreporter_{call}_total_spots` | ✅ Direct |
| `sensor.pskr_stats_rx_{call}_total_unique_senders` | `sensor.pskreporter_{call}_unique_stations` | ✅ Renamed |
| `sensor.pskr_stats_rx_{call}_most_active_band` | `sensor.pskreporter_{call}_most_active_band` | ✅ Direct |
| `sensor.pskr_stats_rx_{call}_most_active_mode` | `sensor.pskreporter_{call}_most_active_mode` | ✅ Direct |
| `sensor.pskr_stats_rx_{call}_total_max_dist` | `sensor.pskreporter_{call}_maximum_distance` | ✅ Renamed |
| `sensor.pskr_stats_rx_{call}_total_avg_snr` | `sensor.pskreporter_{call}_average_snr` | ✅ Renamed |
| `sensor.pskr_stats_rx_{call}_total_unique_countries` | N/A | ❌ Not available |
| `sensor.pskr_stats_rx_{call}_active_bands` | `sensor.pskreporter_{call}_most_active_band` (attr: band_counts) | ⚠️ Attribute only |
| `sensor.pskr_stats_rx_{call}_total_avg_dist` | N/A | ❌ Not available |
| `sensor.pskr_stats_rx_{call}_total_min_dist` | N/A | ❌ Not available |
| `sensor.pskr_stats_rx_{call}_total_max_snr` | N/A | ❌ Not available |
| `sensor.pskr_stats_rx_{call}_total_min_snr` | N/A | ❌ Not available |

### New in HACS (No Docker Equivalent)

| Entity | Purpose |
|--------|---------|
| `sensor.pskreporter_{call}_spots_per_minute` | Activity rate |
| `sensor.pskreporter_{call}_last_spot_time` | Timestamp of last spot |
| `sensor.pskreporter_{call}_connection_status` | MQTT connection state |
| `sensor.pskreporter_{call}_feed_status` | Granular health (healthy/stale/disconnected) |
| `sensor.pskreporter_{call}_message_rate` | Messages per minute |
| `sensor.pskreporter_{call}_feed_latency` | Seconds since last message |
| `binary_sensor.pskreporter_{call}_feed_health` | Simple ON/OFF health |
| `sensor.pskreporter_{call}_connection_uptime` | Connection duration |
| `sensor.pskreporter_{call}_reconnect_count` | Reconnection counter |

### Missing Features (Consider for Future)

These Docker bridge features are not yet in the HACS integration:

- `unique_countries` - Count of DXCC entities (requires DXCC lookup)
- `avg_distance` / `min_distance` - Distance statistics beyond max
- `best_snr` / `worst_snr` - SNR range tracking
- `active_bands` count - Currently only most_active_band available

---

## Entity ID Naming Pattern

Entity IDs follow this pattern:
- **Personal:** `sensor.pskreporter_{callsign}_{sensor_name}`
- **Global:** `sensor.pskreporter_global_monitor_{sensor_name}`

Examples:
- `sensor.pskreporter_kd5qlm_total_spots`
- `sensor.pskreporter_global_monitor_20m_activity`
- `binary_sensor.pskreporter_kd5qlm_feed_health`
