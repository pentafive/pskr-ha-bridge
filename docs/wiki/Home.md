# PSKReporter HA Bridge

Welcome to the PSKReporter HA Bridge wiki!

## Quick Links

- [Dashboard Examples](Dashboard-Examples) - Lovelace card configurations
- [Troubleshooting](Troubleshooting) - Common issues and solutions
- [PSKReporter Data](PSKReporter-Data) - Understanding the MQTT feed

## Getting Started

### Installation

1. **HACS (Recommended)**
   - Add `https://github.com/pentafive/pskr-ha-bridge` as a custom repository
   - Install "PSKReporter Monitor"
   - Restart Home Assistant
   - Add via Settings > Devices & Services

2. **Docker**
   ```bash
   git clone https://github.com/pentafive/pskr-ha-bridge.git
   cp .env.example .env
   docker compose up -d
   ```

### Monitor Modes

The setup wizard asks you to choose a monitor type first:

| Mode | Callsign | Use Case |
|------|----------|----------|
| Personal | Required | Track your spots (RX, TX, or both) |
| Global | Not needed | Monitor PSKReporter-wide activity |

**Personal Mode** then asks for your callsign and direction (RX/TX/Both).
**Global Mode** skips straight to completion - no callsign needed.

## Sensors Overview

### Personal Monitor (75 sensors in v2.3.0)
- **Activity:** Total Spots, Unique Stations, Spots/min, Spots (1h), Last Spot
- **Propagation:** Most Active Band/Mode, Min/Avg/Max Distance, Min/Avg/Max SNR
- **Geographic:** Unique Countries, Farthest Station
- **Derived:** DX Ratio (% > 5000km), Propagation Score
- **Per-Band (50 sensors):** For each HF band (160m-6m): Spots, Avg SNR, Max Distance, Stations, Countries
- **Health:** Connection Status, Feed Status, Message Rate, Latency, Uptime

### Global Monitor (22 sensors)
- Activity: Global Spots, Global Unique Stations
- Propagation: Most Active Band/Mode (Global)
- Per-Band: 160m through 6m activity counts
- Health: Same as personal

## What's New

### v2.3.0 Features

- **Rich Per-Band Statistics** - 50 new sensors for HF bands (10 bands × 5 metrics each)
- **Extended Aggregate Sensors** - Min/avg distance, min/max SNR, unique countries, farthest station
- **Derived Metrics** - DX ratio and propagation score for at-a-glance conditions
- **Geographic Tracking** - Track DXCC countries worked with detailed lists in attributes

### v2.2.0 Features

- **Activity-Aware Health Thresholds** - Personal monitors use 5-minute threshold (vs 1-minute for global) to reduce false alarms during normal low-activity periods
- **Granular Feed Status** - States: Healthy, Low Activity, Stale, Disconnected
- **Configurable Transport** - Choose between WebSocket+TLS (default), TCP+TLS, WebSocket, or TCP via integration options

## Support

- [GitHub Issues](https://github.com/pentafive/pskr-ha-bridge/issues)
- [PSKReporter.info](https://pskreporter.info/)
