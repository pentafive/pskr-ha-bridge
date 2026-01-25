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
| **Activity** | Spots (1h) | Spots in last hour | spots |
| **Activity** | Last Spot Time | When last spot received | timestamp |
| **Propagation** | Most Active Band | Band with most spots | band |
| **Propagation** | Most Active Mode | Mode with most spots | mode |
| **Propagation** | Maximum Distance | Furthest spot | km |
| **Propagation** | Min Distance | Closest spot | km |
| **Propagation** | Avg Distance | Mean distance | km |
| **Propagation** | Average SNR | Mean signal-to-noise | dB |
| **Propagation** | Min SNR | Weakest signal | dB |
| **Propagation** | Max SNR | Strongest signal | dB |
| **Geographic** | Unique Countries | DXCC countries worked | countries |
| **Geographic** | Farthest Station | Callsign of farthest contact | callsign |
| **Derived** | DX Ratio | % of spots > 5000 km | % |
| **Derived** | Propagation Score | Composite quality metric | score |
| **Per-Band** | {band} Spots | Spot count on each HF band (160m-6m) | spots |
| **Per-Band** | {band} Avg SNR | Average SNR per band | dB |
| **Per-Band** | {band} Max Distance | Farthest spot per band | km |
| **Per-Band** | {band} Stations | Unique stations per band | stations |
| **Per-Band** | {band} Countries | Unique countries per band | countries |
| **Connection** | Connection Status | MQTT connected | Connected/Disconnected |
| **Health** | Feed Status | Data flowing | Healthy/Unhealthy |
| **Health** | Message Rate | MQTT messages/min | msg/min |
| **Health** | Feed Latency | Time since last message | seconds |
| **Health** | Connection Uptime | Time connected | seconds |
| **Health** | Reconnect Count | Connection restarts | count |
| **Health** | Sequence Gaps | Missed messages detected | count |
| **Health** | Parse Errors | Malformed messages | count |

**v2.3.0:** Personal mode now includes 75 sensors total (9 activity + 9 extended + 7 health + 50 per-band).

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
| Feed Health | ON when data flowing, OFF when stale (personal: >300s, global: >60s) |

## Understanding the Data

### What is PSKReporter?

[PSKReporter.info](https://pskreporter.info/) is a real-time database of amateur radio digital mode reception reports. When software like WSJT-X decodes a digital signal, it automatically reports the reception to PSKReporter, creating a global picture of radio propagation.

### Spots vs Messages

- **Spot**: A reception report (Station A heard Station B on frequency X with SNR Y)
- **Message**: Raw MQTT message from the PSKReporter feed

### Feed Health

The `feed_health` binary sensor and `feed_status` sensor indicate data flow status.

**v2.2.0+:** Activity-aware thresholds reduce false alarms for personal monitors:
- **Personal Monitor:** 300-second threshold (amateur radio spots are naturally sparse)
- **Global Monitor:** 60-second threshold (high message volume)

**Feed Status States:**
| State | Meaning |
|-------|---------|
| Healthy | Messages received within threshold |
| Low Activity | 180-300 seconds since last message (personal only) |
| Stale | No messages beyond threshold |
| Disconnected | MQTT connection lost |

**Common reasons for Stale/Disconnected:**
- Your callsign has no activity (common during off-hours or poor propagation)
- PSKReporter MQTT feed is down (rare)
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

The setup wizard guides you through configuration:

**Step 1: Choose Monitor Type**
| Option | Description |
|--------|-------------|
| Personal Monitor | Track spots for your callsign (requires valid amateur radio callsign) |
| Global Monitor | Network-wide propagation statistics (no callsign needed) |

**Step 2: Personal Monitor Only**
| Option | Description |
|--------|-------------|
| Callsign | Your amateur radio callsign (e.g., W1AW, KD5QLM/P) |
| Direction | RX (being heard), TX (hearing others), or Both |

**Callsign Format:** 1-3 letters/numbers, followed by a digit, then 0-4 characters ending in a letter. Optional `/` suffix allowed (e.g., W1ABC/P for portable).

#### Options (After Setup)

Configure filtering via **Settings > Devices & Services > PSKReporter > Configure**.

**Both Modes:**
| Option | Description | Default |
|--------|-------------|---------|
| Connection Transport | MQTT transport method (see Transport Options below) | WebSocket+TLS |
| Count-Only Mode | Don't store individual spots (reduces memory) | Off |
| Sample Rate | Process 1 in N messages (range: 1-100, where 1 = all) | 10 |

**Personal Mode Only:**
| Option | Description | Default |
|--------|-------------|---------|
| Minimum Distance | Filter spots closer than X km | 0 (disabled) |
| Maximum Distance | Filter spots farther than X km | 0 (disabled) |
| Mode Filter | Only show specific digital modes (FT8, FT4, etc.) | All |
| Callsign Allow List | Only include spots involving these callsigns (comma-separated) | Empty |
| Callsign Block List | Exclude spots involving these callsigns (comma-separated) | Empty |
| Country Allow List | Only include spots from these DXCC codes (comma-separated) | Empty |
| Country Block List | Exclude spots from these DXCC codes (comma-separated) | Empty |

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

This integration connects to the public PSKReporter MQTT feed at `mqtt.pskreporter.info`.

### Transport Options

**v2.2.0+:** Configurable transport modes for different network environments.

| Transport | Port | Protocol | Recommended |
|-----------|------|----------|-------------|
| WebSocket + TLS | 1886 | WSS | ✅ Default, most firewall-friendly |
| TCP + TLS | 1884 | MQTTS | Good alternative |
| WebSocket | 1885 | WS | If TLS issues |
| TCP plain | 1883 | MQTT | Not recommended (unencrypted) |

The `connection_status` sensor shows the active transport mode and port in its attributes.

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

- **[Dashboard Generator](https://pentafive.github.io/pskr-ha-bridge/dashboard-generator.html)** - Generate a customized dashboard for your callsign
- [Dashboard Examples](https://github.com/pentafive/pskr-ha-bridge/wiki/Dashboard-Examples) - Lovelace configurations
- [Troubleshooting](https://github.com/pentafive/pskr-ha-bridge/wiki/Troubleshooting) - Common issues
- [PSKReporter Data](https://github.com/pentafive/pskr-ha-bridge/wiki/PSKReporter-Data) - Understanding the feed
- [Roadmap](docs/ROADMAP.md) - Planned features

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
- [PSKReporter MQTT Documentation](http://mqtt.pskreporter.info/) - MQTT feed details
- [WSJT-X](https://wsjt.sourceforge.io/) - FT8/FT4 software
- [Home Assistant MQTT Integration](https://www.home-assistant.io/integrations/mqtt/)
