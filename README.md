# PSKReporter HA Bridge

[![HACS Validation](https://github.com/pentafive/pskr-ha-bridge/actions/workflows/hacs-validation.yml/badge.svg)](https://github.com/pentafive/pskr-ha-bridge/actions/workflows/hacs-validation.yml)
[![Ruff](https://github.com/pentafive/pskr-ha-bridge/actions/workflows/ruff.yml/badge.svg)](https://github.com/pentafive/pskr-ha-bridge/actions/workflows/ruff.yml)

Monitor amateur radio spot data from [PSKReporter.info](https://pskreporter.info/) in Home Assistant.

Track FT8, FT4, WSPR, and other digital mode activity for your callsign with real-time statistics and dashboard integration.

## Installation Options

Choose the installation method that best fits your setup:

| Method | Best For | MQTT Broker Required |
|--------|----------|---------------------|
| **HACS Integration** (Recommended) | Most Home Assistant users | No |
| **Docker Container** | Kubernetes, Synology, Proxmox, non-HA setups | Yes |

---

## Option A: HACS Integration (Recommended)

Native Home Assistant custom component with UI-based configuration.

### Prerequisites

- Home Assistant 2024.1.0 or newer
- [HACS](https://hacs.xyz/) installed

### Installation

1. Open HACS in Home Assistant
2. Click **Integrations** > **+ Explore & Download Repositories**
3. Search for "PSKReporter Monitor"
4. Click **Download**
5. Restart Home Assistant
6. Go to **Settings** > **Devices & Services** > **+ Add Integration**
7. Search for "PSKReporter Monitor"
8. Enter your callsign and select monitoring direction (RX/TX/Both)

### Configuration

| Option | Description | Default |
|--------|-------------|---------|
| Callsign | Your amateur radio callsign | Required |
| Direction | RX (received), TX (transmitted), or Both | RX |
| Min Distance | Minimum spot distance in km (0 = no filter) | 0 |
| Max Distance | Maximum spot distance in km (0 = no limit) | 0 |
| Mode Filter | Filter by specific digital modes | All |

### Sensors Created

- **Total Spots** - Number of spots in the 15-minute window
- **Unique Stations** - Count of unique callsigns heard/hearing you
- **Most Active Band** - Band with most activity
- **Most Active Mode** - Digital mode with most activity
- **Maximum Distance** - Furthest spot distance (km)
- **Average SNR** - Mean signal-to-noise ratio (dB)
- **Spots per Minute** - Activity rate
- **Last Spot Time** - Timestamp of most recent spot
- **Connection Status** - PSKReporter MQTT connection state

---

## Option B: Docker Container

Standalone Python container for users who prefer Docker deployment or don't use Home Assistant.

### Prerequisites

- Docker and Docker Compose
- MQTT broker (e.g., Mosquitto)
- Home Assistant with MQTT integration (optional)

### Quick Start

```bash
# Clone the repository
git clone https://github.com/pentafive/pskr-ha-bridge.git
cd pskr-ha-bridge

# Create configuration
cp .env.example .env
nano .env  # Edit with your settings

# Start the container
docker compose up -d
```

### Configuration (.env)

```ini
# Required
MY_CALLSIGN=W1ABC
HA_MQTT_BROKER=192.168.1.100

# Optional (with defaults shown)
DEBUG_MODE=False
PSK_TRANSPORT_MODE=MQTT_WS_TLS
SCRIPT_DIRECTION=rx
HA_MQTT_PORT=1883
HA_MQTT_USER=
HA_MQTT_PASS=
```

See `.env.example` for all configuration options.

### Docker Compose

```yaml
services:
  pskr-ha-bridge:
    image: pentafive/pskr-ha-bridge:latest
    container_name: pskr-ha-bridge
    restart: unless-stopped
    env_file: .env
```

### Home Assistant Integration (Docker Mode)

1. Ensure MQTT integration is configured in Home Assistant
2. Enable MQTT discovery in **Settings** > **Devices & Services** > **MQTT** > **Configure**
3. After starting the container, devices will auto-discover:
   - `PSKr Spots ({CALLSIGN})`
   - `PSKr Stats RX ({CALLSIGN})`
   - `PSKr Stats TX ({CALLSIGN})` (if using dual mode)

---

## Dashboard Examples

### Lovelace Card (Minimal)

```yaml
type: entities
title: PSKReporter - W1ABC
entities:
  - entity: sensor.pskreporter_w1abc_rx_total_spots
  - entity: sensor.pskreporter_w1abc_rx_unique_stations
  - entity: sensor.pskreporter_w1abc_rx_most_active_band
  - entity: sensor.pskreporter_w1abc_rx_max_distance
```

See `examples/` directory for more dashboard configurations.

---

## Troubleshooting

### HACS Integration

| Issue | Solution |
|-------|----------|
| Integration not found | Restart HA after HACS download |
| No sensors appearing | Check callsign format, wait for spots |
| Connection failed | Check network/firewall, PSKReporter status |

### Docker Container

| Issue | Solution |
|-------|----------|
| Container exits | Check `docker logs pskr-ha-bridge` |
| No MQTT connection | Verify broker address, credentials |
| Missing sensors | Enable MQTT discovery in HA |

---

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Security

Report security vulnerabilities privately via email. See [SECURITY.md](SECURITY.md).

## License

MIT License - see [LICENSE](LICENSE) for details.

## Acknowledgements

- **Philip Gladstone, N1DQ** - [PSKReporter.info](https://pskreporter.info/)
- **Tom, M0LTE** - Public MQTT feed at mqtt.pskreporter.info
- **Home Assistant** - Home automation platform
- **PyHamtools** - Amateur radio utilities library
