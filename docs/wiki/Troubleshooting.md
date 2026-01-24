# Troubleshooting

## Common Issues

### No Sensors Appearing

**Symptoms:** Integration added but no sensors show up in Home Assistant.

**Solutions:**
1. **Check callsign format** - Must be valid amateur radio callsign (e.g., W1ABC, VK2XYZ/P)
2. **Wait for activity** - If your station isn't currently active, no spots will appear
3. **Restart Home Assistant** - Required after initial installation
4. **Check logs** - Look for errors in Home Assistant logs

```yaml
# Check logs for PSKReporter errors
logger:
  default: info
  logs:
    custom_components.pskr: debug
```

### Feed Health Shows Unhealthy

**Symptoms:** `binary_sensor.pskreporter_{callsign}_feed_health` is OFF, sensors show stale data.

**v2.2.0 Update:** Activity-aware thresholds significantly reduce false alarms:
- **Personal monitors:** 300-second threshold (5 minutes) - appropriate for sparse amateur radio activity
- **Global monitors:** 60-second threshold - high message volume expected

**Feed Status States (check `sensor.pskreporter_{callsign}_feed_status`):**
| State | Meaning | Action |
|-------|---------|--------|
| Healthy | Data flowing normally | None needed |
| Low Activity | 180-300s since last message | Normal during low propagation |
| Stale | No data beyond threshold | Check connection/activity |
| Disconnected | MQTT connection lost | Check network/firewall |

**Possible Causes:**

| Cause | Solution |
|-------|----------|
| No station activity | Normal if you're not transmitting/receiving |
| Poor propagation | Low Activity status is expected - not an error |
| Network issue | Check internet connectivity |
| PSKReporter down | Check [pskreporter.info](https://pskreporter.info/) |
| Firewall blocking | Allow outbound to port 1886 (or configured port) |

**Diagnostic Steps:**
1. Check `sensor.pskreporter_{callsign}_feed_status` - shows granular status with reason
2. Check `sensor.pskreporter_{callsign}_message_rate` - should be > 0 msg/min when active
3. Check `sensor.pskreporter_{callsign}_connection_status` - should show "Connected"
4. Check connection_status attributes for `transport_mode` and `transport_port`

**Entity ID Pattern:**
- Personal: `sensor.pskreporter_{callsign}_{sensor_name}` (e.g., `sensor.pskreporter_w1abc_feed_status`)
- Global: `sensor.pskreporter_global_monitor_{sensor_name}` (e.g., `sensor.pskreporter_global_monitor_feed_status`)

### Connection Status Shows Disconnected

**Symptoms:** MQTT connection failing to PSKReporter.

**Solutions:**

1. **Try a different transport mode** (v2.2.0+)
   - Go to Settings > Devices & Services > PSKReporter > Configure
   - Change "Connection Transport" to a different option
   - Options: WebSocket+TLS (1886), TCP+TLS (1884), WebSocket (1885), TCP (1883)

2. **Check network connectivity**
   ```bash
   # Test WebSocket+TLS (default)
   curl -v https://mqtt.pskreporter.info:1886

   # Test TCP+TLS
   openssl s_client -connect mqtt.pskreporter.info:1884
   ```

3. **Verify firewall rules**
   | Transport | Port | Protocol |
   |-----------|------|----------|
   | WebSocket+TLS | 1886 | TCP outbound |
   | TCP+TLS | 1884 | TCP outbound |
   | WebSocket | 1885 | TCP outbound |
   | TCP plain | 1883 | TCP outbound |

4. **Check for IP blocks** - PSKReporter may rate-limit aggressive connections

5. **Review reconnect count** - If high, check for network instability

### Global Monitor Not Receiving Data

**Symptoms:** Global monitor shows 0 spots, but personal monitors work.

**Solutions:**
1. **Check sample rate** - Default 1:10 means only every 10th message processed
2. **Wait for accumulation** - Global stats reset every 15 minutes
3. **Verify topic subscription** - Check logs for `pskr/filter/v2/+/FT8/+/+/#`

### High Memory Usage

**Symptoms:** Home Assistant memory increasing over time.

**Solutions:**
1. **Enable Count-Only Mode** - Options > Count-Only Mode = ON
2. **Increase Sample Rate** - Higher sample rate = less processing
3. **Reduce stats window** - Fewer spots stored (default: 15 min)

## HACS Specific Issues

### Integration Not Found After Install

1. Fully restart Home Assistant (not just reload)
2. Clear browser cache
3. Check HACS download completed successfully

### "Custom Repository" Error

1. Verify URL: `https://github.com/pentafive/pskr-ha-bridge`
2. Select "Integration" as category
3. Check GitHub is accessible from your network

### Validation Errors

| Error | Cause | Solution |
|-------|-------|----------|
| brands | Brand not in HA brands repo | Fixed - PR #8971 merged |
| topics | Missing repo topics | Fixed in v2.0.0 |

## Docker Specific Issues

### Container Exits Immediately

```bash
# Check logs
docker logs pskr-ha-bridge

# Common causes:
# - Missing MY_CALLSIGN
# - Invalid MQTT broker address
# - Network connectivity issues
```

### No MQTT Discovery in Home Assistant

1. **Enable discovery** - Settings > Devices & Services > MQTT > Configure
2. **Check broker** - Container must reach HA's MQTT broker
3. **Verify topics** - Check broker for `homeassistant/sensor/pskr_*`

### MQTT Connection Refused

```bash
# Test MQTT from container
docker exec pskr-ha-bridge mosquitto_pub -h $HA_MQTT_BROKER -t test -m test

# Common fixes:
# - Verify HA_MQTT_BROKER address
# - Check credentials in HA_MQTT_USER/HA_MQTT_PASS
# - Ensure broker allows external connections
```

## Debug Logging

### Enable Debug Mode

**HACS Integration:**
```yaml
# configuration.yaml
logger:
  default: info
  logs:
    custom_components.pskr: debug
    custom_components.pskr.coordinator: debug
```

**Docker:**
```bash
# .env
DEBUG_MODE=True
```

### Key Log Messages

| Message | Meaning |
|---------|---------|
| `Connected to mqtt.pskreporter.info` | MQTT connection successful |
| `Subscribed to topic: pskr/filter/...` | Topic subscription active |
| `Received spot from ...` | Spot data being processed |
| `Feed health: healthy` | Data flowing normally |
| `Connection lost` | MQTT disconnected (will auto-reconnect) |

## Getting Help

1. **Check existing issues**: [GitHub Issues](https://github.com/pentafive/pskr-ha-bridge/issues)
2. **Enable debug logging** and capture relevant logs
3. **Open new issue** with:
   - Home Assistant version
   - Integration version
   - Debug logs
   - Steps to reproduce

## PSKReporter Status

- **Website**: [pskreporter.info](https://pskreporter.info/)
- **MQTT Feed**: [mqtt.pskreporter.info](http://mqtt.pskreporter.info/)
- **Status Page**: Check for any announced outages
