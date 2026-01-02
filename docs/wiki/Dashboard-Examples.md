# Dashboard Examples

## Personal Monitor Cards

### Basic Entities Card

```yaml
type: entities
title: PSKReporter - W1ABC
entities:
  - entity: sensor.pskreporter_w1abc_rx_total_spots
  - entity: sensor.pskreporter_w1abc_rx_unique_stations
  - entity: sensor.pskreporter_w1abc_rx_most_active_band
  - entity: sensor.pskreporter_w1abc_rx_max_distance
  - entity: sensor.pskreporter_w1abc_rx_avg_snr
  - entity: sensor.pskreporter_w1abc_rx_spots_per_minute
```

### Glance Card

```yaml
type: glance
title: Ham Radio Activity
entities:
  - entity: sensor.pskreporter_w1abc_rx_total_spots
    name: Spots
  - entity: sensor.pskreporter_w1abc_rx_unique_stations
    name: Stations
  - entity: sensor.pskreporter_w1abc_rx_most_active_band
    name: Band
  - entity: binary_sensor.pskreporter_w1abc_rx_feed_health
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
        entity: sensor.pskreporter_w1abc_rx_total_spots
        name: Spots
        icon_color: blue
      - type: custom:mushroom-entity-card
        entity: sensor.pskreporter_w1abc_rx_unique_stations
        name: Stations
        icon_color: green

  - type: horizontal-stack
    cards:
      - type: custom:mushroom-entity-card
        entity: sensor.pskreporter_w1abc_rx_most_active_band
        name: Band
        icon_color: orange
      - type: custom:mushroom-entity-card
        entity: sensor.pskreporter_w1abc_rx_max_distance
        name: Max DX
        icon_color: purple

  - type: custom:mushroom-entity-card
    entity: binary_sensor.pskreporter_w1abc_rx_feed_health
    name: Feed Health
    icon_color: "{{ 'green' if is_state(entity, 'on') else 'red' }}"
```

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
  - entity: sensor.pskreporter_global_monitor_global_spots_sampled
    name: Messages
  - entity: sensor.pskreporter_global_monitor_global_unique_stations
    name: Stations
  - entity: sensor.pskreporter_global_monitor_global_most_active_band
    name: Top Band
  - entity: binary_sensor.pskreporter_global_monitor_feed_health
    name: Feed
```

### Band Activity Bar Chart (ApexCharts)

Requires [apexcharts-card](https://github.com/RomRider/apexcharts-card):

```yaml
type: custom:apexcharts-card
header:
  title: Band Activity
  show: true
chart_type: bar
series:
  - entity: sensor.pskreporter_global_monitor_20m_activity
    name: 20m
  - entity: sensor.pskreporter_global_monitor_40m_activity
    name: 40m
  - entity: sensor.pskreporter_global_monitor_15m_activity
    name: 15m
  - entity: sensor.pskreporter_global_monitor_10m_activity
    name: 10m
  - entity: sensor.pskreporter_global_monitor_17m_activity
    name: 17m
  - entity: sensor.pskreporter_global_monitor_30m_activity
    name: 30m
```

## Health Monitoring Cards

### Diagnostic Panel

```yaml
type: entities
title: PSKReporter Health
show_header_toggle: false
entities:
  - entity: sensor.pskreporter_w1abc_rx_connection_status
  - entity: sensor.pskreporter_w1abc_rx_feed_status
  - entity: sensor.pskreporter_w1abc_rx_message_rate
  - entity: sensor.pskreporter_w1abc_rx_feed_latency
  - entity: sensor.pskreporter_w1abc_rx_connection_uptime
  - entity: sensor.pskreporter_w1abc_rx_reconnect_count
```

### Conditional Alert Card

```yaml
type: conditional
conditions:
  - entity: binary_sensor.pskreporter_w1abc_rx_feed_health
    state: "off"
card:
  type: markdown
  content: |
    ## ⚠️ PSKReporter Feed Unhealthy
    No data received for 60+ seconds.
    - Check network connectivity
    - Verify PSKReporter status
    - Review logs for errors
```

## Automations

### Alert on Feed Failure

```yaml
automation:
  - alias: "PSKReporter Feed Alert"
    trigger:
      - platform: state
        entity_id: binary_sensor.pskreporter_w1abc_rx_feed_health
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
        entity_id: sensor.pskreporter_w1abc_rx_max_distance
        above: 10000
    action:
      - service: logbook.log
        data:
          name: "DX Achievement"
          message: "New DX record: {{ states('sensor.pskreporter_w1abc_rx_max_distance') }} km"
```
