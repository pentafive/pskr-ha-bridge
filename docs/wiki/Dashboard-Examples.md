# Dashboard Examples

This page provides Home Assistant dashboard examples for the PSKReporter integration.

## Dashboard Generator (Recommended)

The easiest way to create a dashboard is with the generator:

**[📡 Dashboard Generator](https://pentafive.github.io/pskr-ha-bridge/dashboard-generator.html)** - Enter your callsign and get a complete dashboard YAML

Or use the command line:
```bash
python3 examples/dashboards/generate_dashboard.py W1ABC
```

See [`examples/dashboards/README.md`](../../examples/dashboards/README.md) for full generator documentation.

---

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

### v2.3.0 Extended Stats Card

```yaml
type: entities
title: Extended Propagation Stats
entities:
  - entity: sensor.pskreporter_w1abc_farthest_station
    name: Farthest Station
  - entity: sensor.pskreporter_w1abc_unique_countries
    name: Countries Worked
  - entity: sensor.pskreporter_w1abc_dx_ratio
    name: DX Ratio (>5000km)
  - entity: sensor.pskreporter_w1abc_propagation_score
    name: Propagation Score
  - entity: sensor.pskreporter_w1abc_spots_last_hour
    name: Spots (1h)
  - type: section
    label: Distance Range
  - entity: sensor.pskreporter_w1abc_min_distance
  - entity: sensor.pskreporter_w1abc_avg_distance
  - entity: sensor.pskreporter_w1abc_maximum_distance
  - type: section
    label: SNR Range
  - entity: sensor.pskreporter_w1abc_min_snr
  - entity: sensor.pskreporter_w1abc_average_snr
  - entity: sensor.pskreporter_w1abc_max_snr
```

### Per-Band Overview (v2.3.0)

```yaml
type: entities
title: Per-Band Statistics
entities:
  - entity: sensor.pskreporter_w1abc_20m_spots
    name: 20m Spots
  - entity: sensor.pskreporter_w1abc_20m_avg_snr
    name: 20m Avg SNR
  - entity: sensor.pskreporter_w1abc_20m_max_distance
    name: 20m Max Distance
  - entity: sensor.pskreporter_w1abc_20m_unique_countries
    name: 20m Countries
  - type: section
    label: 40m
  - entity: sensor.pskreporter_w1abc_40m_spots
  - entity: sensor.pskreporter_w1abc_40m_avg_snr
  - entity: sensor.pskreporter_w1abc_40m_max_distance
  - entity: sensor.pskreporter_w1abc_40m_unique_countries
```

### Band Activity Bar Chart (Personal - v2.3.0)

Requires [apexcharts-card](https://github.com/RomRider/apexcharts-card):

```yaml
type: custom:apexcharts-card
header:
  title: My Band Activity
  show: true
chart_type: bar
series:
  - entity: sensor.pskreporter_w1abc_20m_spots
    name: 20m
    color: "#1E88E5"
  - entity: sensor.pskreporter_w1abc_40m_spots
    name: 40m
    color: "#43A047"
  - entity: sensor.pskreporter_w1abc_15m_spots
    name: 15m
    color: "#FFA726"
  - entity: sensor.pskreporter_w1abc_10m_spots
    name: 10m
    color: "#E53935"
  - entity: sensor.pskreporter_w1abc_17m_spots
    name: 17m
    color: "#8E24AA"
```

### DX Ratio & Propagation Score Gauge

```yaml
type: horizontal-stack
cards:
  - type: gauge
    entity: sensor.pskreporter_w1abc_dx_ratio
    name: DX Ratio
    unit: "%"
    min: 0
    max: 100
    severity:
      green: 50
      yellow: 25
      red: 0
  - type: gauge
    entity: sensor.pskreporter_w1abc_propagation_score
    name: Propagation
    min: 0
    max: 1000
    severity:
      green: 500
      yellow: 200
      red: 0
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
# Replace {callsign_a} and {callsign_b} with your callsigns (lowercase)
type: custom:apexcharts-card
header:
  title: Spot Count Comparison (24h)
  show: true
graph_span: 24h
series:
  - entity: sensor.pskreporter_{callsign_a}_total_spots
    name: "{CALLSIGN_A}"
    color: "#1E88E5"
    stroke_width: 2
  - entity: sensor.pskreporter_{callsign_b}_total_spots
    name: "{CALLSIGN_B}"
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
  - entity: sensor.pskreporter_{callsign_a}_average_snr
    name: "{CALLSIGN_A}"
    color: "#1E88E5"
    stroke_width: 2
  - entity: sensor.pskreporter_{callsign_b}_average_snr
    name: "{CALLSIGN_B}"
    color: "#FFA726"
    stroke_width: 2
```

### Side-by-Side Stats

```yaml
type: horizontal-stack
cards:
  - type: entities
    title: "{CALLSIGN_A}"
    entities:
      - entity: sensor.pskreporter_{callsign_a}_total_spots
        name: Total Spots
      - entity: sensor.pskreporter_{callsign_a}_average_snr
        name: Avg SNR
      - entity: sensor.pskreporter_{callsign_a}_maximum_distance
        name: Max Distance
  - type: entities
    title: "{CALLSIGN_B}"
    entities:
      - entity: sensor.pskreporter_{callsign_b}_total_spots
        name: Total Spots
      - entity: sensor.pskreporter_{callsign_b}_average_snr
        name: Avg SNR
      - entity: sensor.pskreporter_{callsign_b}_maximum_distance
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

### Wanted DXCC/Band Alert (v2.4.0)

Get notified when a wanted DXCC/band combination is spotted. Requires the DXCC/Band Wanted List to be configured in integration options (e.g., `339:20m,150:40m`).

**Option A: Event-based (instant, HACS only)**

```yaml
automation:
  - alias: "Wanted DXCC Spot Alert"
    trigger:
      - platform: event
        event_type: pskr_wanted_spot
    action:
      - service: notify.mobile_app
        data:
          title: "Wanted DXCC Spotted!"
          message: >
            {{ trigger.event.data.sender_callsign }} → {{ trigger.event.data.receiver_callsign }}
            on {{ trigger.event.data.band }} ({{ trigger.event.data.mode }})
            DXCC {{ trigger.event.data.matched_dxcc }} | SNR {{ trigger.event.data.snr }} dB
            Distance: {{ trigger.event.data.distance_km | round(0) }} km
```

**Option B: Binary sensor-based (works with both HACS and Docker)**

```yaml
automation:
  - alias: "Wanted Match Alert"
    trigger:
      - platform: state
        entity_id: binary_sensor.pskreporter_w1abc_wanted_match
        to: "on"
    action:
      - service: notify.mobile_app
        data:
          title: "Wanted DXCC Match!"
          message: >
            {{ state_attr('binary_sensor.pskreporter_w1abc_wanted_match', 'match_count') }} match(es)
            from wanted list of {{ state_attr('binary_sensor.pskreporter_w1abc_wanted_match', 'wanted_list_size') }} entries
```

### Wanted Match Dashboard Card (v2.4.0)

```yaml
type: entities
title: DXCC Wanted List
entities:
  - entity: binary_sensor.pskreporter_w1abc_wanted_match
    name: Wanted Match Active
  - entity: sensor.pskreporter_w1abc_wanted_matches
    name: Matches (this window)
  - entity: sensor.pskreporter_w1abc_wanted_list_size
    name: Wanted List Entries
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
| `sensor.pskr_stats_rx_{call}_total_unique_countries` | `sensor.pskreporter_{call}_unique_countries` | ✅ v2.3.0 |
| `sensor.pskr_stats_rx_{call}_active_bands` | `sensor.pskreporter_{call}_most_active_band` (attr: band_counts) | ⚠️ Attribute only |
| `sensor.pskr_stats_rx_{call}_total_avg_dist` | `sensor.pskreporter_{call}_avg_distance` | ✅ v2.3.0 |
| `sensor.pskr_stats_rx_{call}_total_min_dist` | `sensor.pskreporter_{call}_min_distance` | ✅ v2.3.0 |
| `sensor.pskr_stats_rx_{call}_total_max_snr` | `sensor.pskreporter_{call}_max_snr` | ✅ v2.3.0 |
| `sensor.pskr_stats_rx_{call}_total_min_snr` | `sensor.pskreporter_{call}_min_snr` | ✅ v2.3.0 |

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

### v2.4.0 New Sensors

| Entity | Purpose |
|--------|---------|
| `sensor.pskreporter_{call}_wanted_matches` | Wanted DXCC/band match count in stats window |
| `sensor.pskreporter_{call}_wanted_list_size` | Number of entries in wanted list config |
| `binary_sensor.pskreporter_{call}_wanted_match` | ON when a wanted match occurred in stats window |

### v2.3.0 New Sensors

These sensors were added in v2.3.0 and now have parity with Docker bridge:

| Entity | Purpose |
|--------|---------|
| `sensor.pskreporter_{call}_unique_countries` | DXCC country count (list in attributes) |
| `sensor.pskreporter_{call}_min_distance` | Minimum distance in window |
| `sensor.pskreporter_{call}_avg_distance` | Average distance in window |
| `sensor.pskreporter_{call}_min_snr` | Weakest signal in window |
| `sensor.pskreporter_{call}_max_snr` | Strongest signal in window |
| `sensor.pskreporter_{call}_farthest_station` | Callsign of farthest contact |
| `sensor.pskreporter_{call}_spots_last_hour` | Hourly spot count |
| `sensor.pskreporter_{call}_dx_ratio` | Percentage of spots > 5000 km |
| `sensor.pskreporter_{call}_propagation_score` | Composite quality metric |
| `sensor.pskreporter_{call}_{band}_spots` | Per-band spot counts (160m-6m) |
| `sensor.pskreporter_{call}_{band}_avg_snr` | Per-band average SNR |
| `sensor.pskreporter_{call}_{band}_max_distance` | Per-band maximum distance |
| `sensor.pskreporter_{call}_{band}_unique_stations` | Per-band unique stations |
| `sensor.pskreporter_{call}_{band}_unique_countries` | Per-band unique countries |

---

## Entity ID Naming Pattern

Entity IDs follow this pattern:
- **Personal:** `sensor.pskreporter_{callsign}_{sensor_name}`
- **Global:** `sensor.pskreporter_global_monitor_{sensor_name}`

Examples:
- `sensor.pskreporter_kd5qlm_total_spots`
- `sensor.pskreporter_global_monitor_20m_activity`
- `binary_sensor.pskreporter_kd5qlm_feed_health`
