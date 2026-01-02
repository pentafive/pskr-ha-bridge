# PSKReporter Data

## What is PSKReporter?

[PSKReporter.info](https://pskreporter.info/) is a real-time database of amateur radio digital mode reception reports. Created and maintained by Philip Gladstone (N1DQ), it aggregates reception reports from thousands of amateur radio operators worldwide.

## How It Works

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│   WSJT-X    │────▶│  PSKReporter │────▶│   MQTT Feed     │
│   JS8Call   │     │   Server     │     │ mqtt.pskreporter│
│   etc.      │     └──────────────┘     └────────┬────────┘
└─────────────┘                                   │
                                                  ▼
                                         ┌────────────────┐
                                         │ Home Assistant │
                                         │  (This Bridge) │
                                         └────────────────┘
```

1. **Decoding Software** (WSJT-X, JS8Call, etc.) decodes digital signals
2. **Automatic Reporting** - Software sends reception reports to PSKReporter
3. **MQTT Feed** - PSKReporter publishes spots in real-time via MQTT
4. **This Integration** - Subscribes to MQTT and creates HA sensors

## MQTT Feed Details

### Connection

| Parameter | Value |
|-----------|-------|
| Host | mqtt.pskreporter.info |
| Port | 1886 (WebSocket TLS) |
| Protocol | MQTT over WebSocket with TLS |
| Authentication | None required |
| QoS | 0 (at most once) |

### Topic Structure

```
pskr/filter/v2/{band}/{mode}/{sender}/{receiver}/{flow}/{sequence}
```

| Component | Description | Example |
|-----------|-------------|---------|
| band | Frequency band | 20m, 40m, etc. |
| mode | Digital mode | FT8, FT4, WSPR |
| sender | Transmitting callsign | W1ABC |
| receiver | Receiving callsign | VK2XYZ |
| flow | Message flow | rx, tx |
| sequence | Sequence number | 12345 |

### Message Payload (JSON)

```json
{
  "sq": 12345,           // Sequence number
  "f": 14074000,         // Frequency in Hz
  "md": "FT8",           // Mode
  "rp": -12,             // Signal report (dB)
  "t": 1704067200,       // Unix timestamp
  "sc": "W1ABC",         // Sender callsign
  "rc": "VK2XYZ",        // Receiver callsign
  "sl": "FM18",          // Sender grid square
  "rl": "QF56",          // Receiver grid square
  "sa": "US",            // Sender country code
  "ra": "AU",            // Receiver country code
  "b": "20m"             // Band
}
```

## Data Fields Explained

### Core Fields

| Field | Name | Description |
|-------|------|-------------|
| `sc` | Sender Callsign | Station that transmitted the signal |
| `rc` | Receiver Callsign | Station that received/decoded the signal |
| `f` | Frequency | Frequency in Hz (e.g., 14074000 = 14.074 MHz) |
| `md` | Mode | Digital mode (FT8, FT4, WSPR, JS8, etc.) |
| `rp` | Report | Signal-to-noise ratio in dB |
| `t` | Timestamp | Unix epoch time of reception |

### Location Fields

| Field | Name | Description |
|-------|------|-------------|
| `sl` | Sender Locator | Maidenhead grid square (4 or 6 char) |
| `rl` | Receiver Locator | Maidenhead grid square (4 or 6 char) |
| `sa` | Sender Country | ISO country code |
| `ra` | Receiver Country | ISO country code |

### Metadata

| Field | Name | Description |
|-------|------|-------------|
| `sq` | Sequence | Message sequence number (for gap detection) |
| `b` | Band | Amateur band designation (20m, 40m, etc.) |

## Understanding the Statistics

### Spots vs Messages

- **Spot**: A complete reception report (sender heard by receiver)
- **Message**: Raw MQTT message from the feed

In personal mode, each message = one spot for your callsign.
In global mode, you receive ALL spots (sampled at 1:N rate).

### Band Activity

Per-band sensors show how many spots occurred on each band. Higher counts indicate:
- Better propagation on that band
- More operators active on that band
- Time of day effects (different bands open at different times)

### Typical Patterns

| Time (UTC) | Active Bands |
|------------|--------------|
| 00:00-06:00 | 40m, 80m, 160m (night) |
| 06:00-12:00 | 20m, 17m, 15m (sunrise) |
| 12:00-18:00 | 20m, 15m, 12m, 10m (day) |
| 18:00-24:00 | 20m, 40m (sunset) |

### Rate Limiting (Global Mode)

Global mode processes 1 in N messages (default: 1:10) because:
- PSKReporter sees ~1500+ spots/minute globally
- Processing all would be resource-intensive
- Sampling still provides statistically valid data

At 1:10 sampling:
- 1500 spots/min → 150 processed
- Still representative of band activity
- Minimal CPU/memory impact

## Message Volume Expectations

### Personal Monitor

| Activity Level | Messages/min |
|----------------|--------------|
| Inactive | 0 |
| Light activity | 1-10 |
| Active contest | 50-200 |
| Rare DX | 100+ |

### Global Monitor

| Time Period | Messages/min |
|-------------|--------------|
| Quiet (night) | 500-1000 |
| Normal | 1000-1500 |
| Contest weekend | 2000-3000 |

## Data Accuracy

### Limitations

1. **Propagation only** - Shows who decoded you, not who heard you
2. **Software dependent** - Only stations running reporting software
3. **Internet dependent** - Requires uploading to PSKReporter
4. **Timing variation** - Reports batched by some software

### Reliability

- **High accuracy** - Data comes directly from decoding software
- **Real-time** - Typically < 30 second delay from decode to MQTT
- **Comprehensive** - Thousands of stations reporting globally

## Related Resources

- [PSKReporter.info](https://pskreporter.info/) - Official website
- [PSKReporter MQTT](https://mqtt.pskreporter.info/) - MQTT feed documentation
- [Maidenhead Locator](https://en.wikipedia.org/wiki/Maidenhead_Locator_System) - Grid square system
- [WSJT-X](https://wsjt.sourceforge.io/) - FT8/FT4 software
- [JS8Call](http://js8call.com/) - JS8 software
