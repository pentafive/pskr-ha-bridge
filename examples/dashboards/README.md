# Dashboard Examples

This directory provides guidance for creating Home Assistant dashboards for the PSKReporter integration.

## Getting Dashboard YAML

Complete dashboard examples with copy-paste YAML are available in the **[Dashboard Examples Wiki](../../docs/wiki/Dashboard-Examples.md)**.

The wiki includes:
- Personal monitor cards (basic, glance, mushroom, graphs)
- Global monitor cards (band activity, charts)
- Antenna comparison dashboards
- Health monitoring cards
- Automation examples
- v2.3.0 per-band sensor cards

## Entity Naming Patterns

| Mode | Entity Pattern | Example |
|------|----------------|---------|
| HACS Integration | `sensor.pskreporter_{call}_*` | `sensor.pskreporter_kd5qlm_total_spots` |
| Docker Bridge | `sensor.pskr_stats_rx_{call}_*` | `sensor.pskr_stats_rx_kd5qlm_total_spots` |
| Global Monitor | `sensor.pskreporter_global_monitor_*` | `sensor.pskreporter_global_monitor_20m_activity` |

Replace `{call}` with your callsign in lowercase.

## Required HACS Frontend Cards

Install from HACS -> Frontend:

- **[Mushroom](https://github.com/piitaya/lovelace-mushroom)** - Modern entity cards and chips
- **[Mini Graph Card](https://github.com/kalkih/mini-graph-card)** - Simple trend charts
- **[ApexCharts Card](https://github.com/RomRider/apexcharts-card)** - Advanced charts and comparisons

**Note:** Basic entity cards work without any custom cards.

## Quick Start Example

Minimal personal monitor card (no custom cards required):

```yaml
type: entities
title: PSKReporter - W1ABC
entities:
  - entity: sensor.pskreporter_w1abc_total_spots
  - entity: sensor.pskreporter_w1abc_unique_stations
  - entity: sensor.pskreporter_w1abc_most_active_band
  - entity: sensor.pskreporter_w1abc_maximum_distance
  - entity: sensor.pskreporter_w1abc_average_snr
  - entity: binary_sensor.pskreporter_w1abc_feed_health
```

Replace `w1abc` with your callsign in lowercase.
