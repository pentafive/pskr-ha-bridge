# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 2.0.x   | :white_check_mark: |
| 1.x.x   | :x:                |

## Reporting a Vulnerability

If you discover a security vulnerability in PSKReporter HA Bridge, please report it responsibly:

1. **Do NOT open a public issue**
2. **Email**: pentafive@gmail.com with subject "pskr-ha-bridge Security Issue"
3. **Include**:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Any suggested fixes (optional)

## Response Timeline

- **Acknowledgment**: Within 48 hours
- **Initial assessment**: Within 1 week
- **Fix timeline**: Depends on severity, typically 1-4 weeks

## Security Considerations

### Credentials

- MQTT credentials are stored in environment variables (Docker) or HA config (HACS)
- **Never commit `.env` files** - only `.env.example` with placeholders
- Consider using Docker secrets or a secrets manager in production

### Network Security

- The bridge connects to PSKReporter MQTT (mqtt.pskreporter.info)
- The bridge connects to your local MQTT broker (Docker mode only)
- PSKReporter supports TLS (MQTT_TLS, MQTT_WS_TLS modes)
- Restrict network access to the bridge container if using Docker

### Data Privacy

- Amateur radio callsigns are inherently public information
- No personal data beyond callsigns is transmitted or stored
- Spot data originates from the public PSKReporter feed
- Consider filtering callsigns if you want to limit exposure

### Logging

- Debug mode may log callsigns and spot data
- Keep `DEBUG_MODE=False` in production
- Review logs before sharing in issue reports

## Scope

This security policy covers:
- The `pskr-ha-bridge.py` script
- The `custom_components/pskr/` HACS integration
- Docker configuration files
- Example configurations

It does NOT cover:
- PSKReporter.info service security
- Home Assistant security
- MQTT broker security
