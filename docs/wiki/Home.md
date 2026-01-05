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

### Personal Monitor
- Activity: Total Spots, Unique Stations, Spots/min
- Propagation: Most Active Band/Mode, Max Distance, Avg SNR
- Health: Connection Status, Feed Health, Message Rate

### Global Monitor
- Activity: Global Spots, Global Unique Stations
- Propagation: Most Active Band/Mode (Global)
- Per-Band: 160m through 6m activity counts
- Health: Same as personal

## Support

- [GitHub Issues](https://github.com/pentafive/pskr-ha-bridge/issues)
- [PSKReporter.info](https://pskreporter.info/)
