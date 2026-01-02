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

**Symptoms:** `binary_sensor.feed_health` is OFF, sensors show stale data.

**Possible Causes:**

| Cause | Solution |
|-------|----------|
| No station activity | Normal if you're not transmitting/receiving |
| Network issue | Check internet connectivity |
| PSKReporter down | Check [status.pskreporter.info](https://pskreporter.info/) |
| Firewall blocking | Allow outbound WSS to port 1886 |

**Diagnostic Steps:**
1. Check `sensor.*_message_rate` - should be > 0 msg/min when active
2. Check `sensor.*_connection_status` - should show "Connected"
3. Check `sensor.*_feed_latency` - time since last message

### Connection Status Shows Disconnected

**Symptoms:** MQTT connection failing to PSKReporter.

**Solutions:**

1. **Check network connectivity**
   ```bash
   # Test from HA host
   curl -v https://mqtt.pskreporter.info:1886
   ```

2. **Verify firewall rules** - Allow outbound TCP 1886 (WebSocket TLS)

3. **Check for IP blocks** - PSKReporter may rate-limit aggressive connections

4. **Review reconnect count** - If high, check for network instability

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
| brands | Brand not in HA brands repo | Wait for PR merge or use without |
| topics | Missing repo topics | Already fixed in v2.0.0 |

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
- **MQTT Feed**: [mqtt.pskreporter.info](https://mqtt.pskreporter.info/)
- **Status Page**: Check for any announced outages
