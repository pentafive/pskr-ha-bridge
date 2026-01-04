<p align="center">
  <img src="https://raw.githubusercontent.com/pentafive/pskr-ha-bridge/main/images/logo.png" alt="PSKReporter HA Bridge" width="400">
</p>

<p align="center">
  <a href="https://github.com/hacs/integration"><img src="https://img.shields.io/badge/HACS-Custom-41BDF5.svg" alt="HACS Custom"></a>
  <a href="https://github.com/pentafive/pskr-ha-bridge/releases"><img src="https://img.shields.io/github/v/release/pentafive/pskr-ha-bridge" alt="GitHub Release"></a>
  <a href="https://github.com/pentafive/pskr-ha-bridge/blob/main/LICENSE"><img src="https://img.shields.io/github/license/pentafive/pskr-ha-bridge" alt="License"></a>
  <a href="https://github.com/pentafive/pskr-ha-bridge/actions/workflows/hacs-validation.yml"><img src="https://github.com/pentafive/pskr-ha-bridge/actions/workflows/hacs-validation.yml/badge.svg" alt="HACS Validation"></a>
</p>

Monitor amateur radio digital mode propagation from [PSKReporter.info](https://pskreporter.info/) in Home Assistant. Track FT8, FT4, WSPR, and other digital modes with real-time statistics, band activity, and feed health monitoring.

## Features

- **Personal Callsign Monitoring** - Track spots for your specific callsign (RX, TX, or both)
- **Global Propagation Monitor** - PSKReporter-wide statistics without a callsign
- **Per-Band Activity** - Monitor propagation on 160m through 6m
- **Feed Health Monitoring** - Real-time MQTT connection and data flow status
- **Low-Resource Mode** - Count-only option for memory-constrained devices
- **Rate Limiting** - Configurable message sampling for global monitoring
- **Two Deployment Options** - Native HACS integration or Docker/MQTT bridge

## Monitor Modes

### Personal Monitor (Callsign Required)

Track spots where you are the sender or receiver:
- See who's hearing your signal and from where
- Monitor band conditions for your location
- Track DX achievements and propagation patterns

### Global Monitor (No Callsign)

Monitor PSKReporter-wide network activity:
- View overall band conditions across the network
- Track which bands are open globally
- Monitor PSKReporter feed health
- Ideal for non-hams or general propagation awareness

## Installation

### Option 1: HACS (Recommended)

1. Open HACS in Home Assistant
2. Click the three dots menu > **Custom repositories**
3. Add `https://github.com/pentafive/pskr-ha-bridge` as an **Integration**
4. Search for "PSKReporter Monitor" and install
5. Restart Home Assistant
6. Go to **Settings > Devices & Services > Add Integration**
7. Search for "PSKReporter Monitor" and configure

### Option 2: Docker/MQTT Bridge

For container deployment or MQTT-based integration:

1. **Clone the repository:**
    ```bash
    git clone https://github.com/pentafive/pskr-ha-bridge.git
    cd pskr-ha-bridge
    ```

2. **Configure:** Copy `.env.example` to `.env` and edit:
    ```bash
    cp .env.example .env
    nano .env
    ```

3. **Run with Docker Compose:**
    ```bash
    docker compose up -d
    ```

## Sensors

### Personal Monitor Sensors

| Category | Sensor | Description | Unit |
|----------|--------|-------------|------|
| **Activity** | Total Spots | Spots in last 15 minutes | spots |
| **Activity** | Unique Stations | Distinct callsigns | stations |
| **Activity** | Spots per Minute | Current activity rate | spots/min |
| **Activity** | Last Spot Time | When last spot received | timestamp |
| **Propagation** | Most Active Band | Band with most spots | band |
| **Propagation** | Most Active Mode | Mode with most spots | mode |
| **Propagation** | Maximum Distance | Furthest spot | km |
| **Propagation** | Average SNR | Mean signal-to-noise | dB |
| **Connection** | Connection Status | MQTT connected | Connected/Disconnected |
| **Health** | Feed Status | Data flowing | Healthy/Unhealthy |
| **Health** | Message Rate | MQTT messages/min | msg/min |
| **Health** | Feed Latency | Time since last message | seconds |
| **Health** | Connection Uptime | Time connected | seconds |
| **Health** | Reconnect Count | Connection restarts | count |
| **Health** | Sequence Gaps | Missed messages detected | count |
| **Health** | Parse Errors | Malformed messages | count |

### Global Monitor Sensors

| Category | Sensor | Description | Unit |
|----------|--------|-------------|------|
| **Activity** | Global Spots | Total MQTT messages | spots |
| **Activity** | Global Unique Stations | Stations seen | stations |
| **Propagation** | Most Active Band (Global) | Top band | band |
| **Propagation** | Most Active Mode (Global) | Top mode | mode |
| **Per-Band** | 160m Activity | 160m spot count | spots |
| **Per-Band** | 80m Activity | 80m spot count | spots |
| **Per-Band** | 40m Activity | 40m spot count | spots |
| **Per-Band** | 30m Activity | 30m spot count | spots |
| **Per-Band** | 20m Activity | 20m spot count | spots |
| **Per-Band** | 17m Activity | 17m spot count | spots |
| **Per-Band** | 15m Activity | 15m spot count | spots |
| **Per-Band** | 12m Activity | 12m spot count | spots |
| **Per-Band** | 10m Activity | 10m spot count | spots |
| **Per-Band** | 6m Activity | 6m spot count | spots |
| **Health** | *(same as personal)* | | |

### Binary Sensors

| Sensor | Description |
|--------|-------------|
| Feed Health | ON when data flowing, OFF when stale (>60s) |

## Understanding the Data

### What is PSKReporter?

[PSKReporter.info](https://pskreporter.info/) is a real-time database of amateur radio digital mode reception reports. When software like WSJT-X decodes a digital signal, it automatically reports the reception to PSKReporter, creating a global picture of radio propagation.

### Spots vs Messages

- **Spot**: A reception report (Station A heard Station B on frequency X with SNR Y)
- **Message**: Raw MQTT message from the PSKReporter feed

### Feed Health

The `feed_health` binary sensor indicates whether PSKReporter data is flowing:
- **ON (Healthy)**: Messages received within the last 60 seconds
- **OFF (Unhealthy)**: No messages for 60+ seconds

Unhealthy can mean:
- PSKReporter MQTT feed is down (rare)
- Your callsign has no activity (common during off-hours)
- Network connectivity issue

### Sample Rate (Global Mode)

Global mode processes 1 in N messages to reduce CPU/memory load. Default: 1:10.

At ~1500 messages/minute globally, sampling 1:10 means processing ~150/min - statistically representative while being resource-friendly.

### Band Activity

Per-band sensors show relative propagation conditions:
- **High counts** = Band is open, propagation is good
- **Low/zero counts** = Band closed or inactive

## Configuration

### HACS Integration

Configure via the UI:

| Option | Description | Personal Mode | Global Mode |
|--------|-------------|---------------|-------------|
| Callsign | Your amateur radio callsign | Required | Leave empty |
| Direction | RX, TX, or Both | Yes | N/A |

#### Options (After Setup)

| Option | Description | Default |
|--------|-------------|---------|
| Count-Only Mode | Don't store individual spots (reduces memory) | Off |
| Sample Rate | Process 1 in N messages (1-100) | 10 |
| Minimum Distance | Filter spots closer than X km | 0 (disabled) |
| Maximum Distance | Filter spots farther than X km | 0 (disabled) |
| Mode Filter | Only show specific digital modes | All |

### Docker Bridge

All configuration via environment variables. See `.env.example` for the full list.

| Variable | Description | Default |
|----------|-------------|---------|
| `MY_CALLSIGN` | Your callsign | *required* |
| `HA_MQTT_BROKER` | MQTT broker host | `homeassistant.local` |
| `HA_MQTT_PASS` | MQTT password | `""` |
| `SCRIPT_DIRECTION` | `rx`, `tx`, or `dual` | `rx` |

## Requirements

- **Home Assistant** 2024.1.0+ (for HACS integration)
- **Internet connection** for PSKReporter MQTT feed
- **Optional**: Amateur radio callsign (for personal monitoring)

### For Docker Bridge Only
- **MQTT Broker** - Mosquitto or compatible
- **MQTT Integration** - Home Assistant MQTT with discovery enabled

## Technical Details

### Data Source

This integration connects to the public PSKReporter MQTT feed at `mqtt.pskreporter.info`. The feed provides real-time spot data as JSON messages over MQTT WebSocket (port 1886, TLS).

### Topic Structure

Personal monitor subscribes to callsign-specific topics:
```
pskr/filter/v2/+/+/{callsign}/+/#  (RX - spots received by callsign)
pskr/filter/v2/+/+/+/{callsign}/#  (TX - spots sent by callsign)
```

Global monitor subscribes to FT8/FT4 (90%+ of traffic):
```
pskr/filter/v2/+/FT8/+/+/#
pskr/filter/v2/+/FT4/+/+/#
```

### Resource Usage

| Mode | MQTT Messages/min | Memory | CPU Impact |
|------|-------------------|--------|------------|
| Personal | 10-100 | ~50KB | Minimal |
| Global (1:10) | ~150 processed | ~1KB | Minimal |
| Global (1:1) | ~1500 | ~5KB | Low |

## Documentation

- [Dashboard Examples](https://github.com/pentafive/pskr-ha-bridge/wiki/Dashboard-Examples) - Lovelace configurations
- [Troubleshooting](https://github.com/pentafive/pskr-ha-bridge/wiki/Troubleshooting) - Common issues
- [PSKReporter Data](https://github.com/pentafive/pskr-ha-bridge/wiki/PSKReporter-Data) - Understanding the feed

## Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Security

Report security vulnerabilities privately. See [SECURITY.md](SECURITY.md).

## License

MIT License - see [LICENSE](LICENSE) for details.

## Acknowledgements

- **Philip Gladstone, N1DQ** - [PSKReporter.info](https://pskreporter.info/) creator and maintainer
- **Tom, M0LTE** - Public MQTT feed at mqtt.pskreporter.info
- **[Home Assistant](https://www.home-assistant.io/)** - Home automation platform

## Resources

- [PSKReporter.info](https://pskreporter.info/) - Official PSKReporter website
- [PSKReporter MQTT Documentation](https://mqtt.pskreporter.info/) - MQTT feed details
- [WSJT-X](https://wsjt.sourceforge.io/) - FT8/FT4 software
- [Home Assistant MQTT Integration](https://www.home-assistant.io/integrations/mqtt/)
