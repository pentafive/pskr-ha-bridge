# Dashboard Examples

This directory contains ready-to-use Home Assistant dashboard YAML files for PSKReporter integration.

## HACS Integration Dashboards

These dashboards use entity names from the **HACS custom component** (`sensor.pskreporter_*`):

| File | Purpose | Required Cards |
|------|---------|----------------|
| [`personal-monitor.yaml`](personal-monitor.yaml) | Single station monitoring | mushroom, mini-graph-card |
| [`global-monitor.yaml`](global-monitor.yaml) | Network-wide propagation | mushroom, apexcharts-card, mini-graph-card |
| [`antenna-comparison.yaml`](antenna-comparison.yaml) | Compare two stations | mushroom, apexcharts-card |

### Installation

1. Install required HACS frontend cards (see table above)
2. Copy the YAML content
3. Replace `{callsign}` placeholders with your callsign in lowercase
4. Paste into a new dashboard view

## Docker Bridge Dashboards

These dashboards use entity names from the **Docker/MQTT bridge** (`sensor.pskr_stats_rx_*`):

| File | Purpose | Required Cards |
|------|---------|----------------|
| [`docker-personal-monitor.yaml`](docker-personal-monitor.yaml) | Single station (Docker mode) | mushroom, mini-graph-card |

### Entity Naming Differences

| Mode | Entity Pattern | Example |
|------|----------------|---------|
| HACS Integration | `sensor.pskreporter_{call}_*` | `sensor.pskreporter_kd5qlm_total_spots` |
| Docker Bridge | `sensor.pskr_stats_rx_{call}_*` | `sensor.pskr_stats_rx_kd5qlm_total_spots` |

## Required HACS Cards

Install from HACS -> Frontend:

- **[Mushroom](https://github.com/piitaya/lovelace-mushroom)** - Modern entity cards and chips
- **[Mini Graph Card](https://github.com/kalkih/mini-graph-card)** - Simple trend charts
- **[ApexCharts Card](https://github.com/RomRider/apexcharts-card)** - Advanced charts and comparisons

## Documentation

See the [Dashboard Examples Wiki](../../docs/wiki/Dashboard-Examples.md) for:
- Individual card snippets
- Entity mapping (Docker -> HACS)
- Automation examples
- SNR threshold configuration
