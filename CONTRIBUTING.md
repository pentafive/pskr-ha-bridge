# Contributing to PSKReporter HA Bridge

Thank you for your interest in contributing to PSKReporter HA Bridge!

## Ways to Contribute

### Reporting Issues

- **Bug reports**: Include your environment (Python version, Docker version, HA version), deployment method (HACS/Docker), steps to reproduce, and any relevant logs
- **Feature requests**: Describe the use case and expected behavior
- **Documentation improvements**: Typos, unclear instructions, missing information

### Code Contributions

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/your-feature-name`
3. **Make your changes**
4. **Test thoroughly**: Ensure the bridge connects and publishes data correctly
5. **Commit with clear messages**: Use conventional commits (e.g., `fix:`, `feat:`, `docs:`)
6. **Push and create a Pull Request**

### Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/pskr-ha-bridge.git
cd pskr-ha-bridge

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements_dev.txt

# Copy and configure environment
cp .env.example .env
# Edit .env with your test environment settings

# Run in debug mode
DEBUG_MODE=True python3 pskr-ha-bridge.py
```

### Code Style

- We use [Ruff](https://github.com/astral-sh/ruff) for linting
- Run `ruff check .` before submitting
- Follow PEP 8 guidelines
- Add docstrings for new functions
- Keep functions focused and modular

### Testing

- Test with both Docker and direct Python execution
- Test with HACS installation (if modifying custom_components)
- Verify MQTT discovery messages in MQTT Explorer
- Confirm sensors appear correctly in Home Assistant
- Test error handling (disconnect from PSKReporter, stop MQTT broker)

## Pull Request Guidelines

- Keep PRs focused on a single change
- Update documentation if adding features
- Update CHANGELOG.md for user-facing changes
- Ensure no sensitive data (IPs, passwords, callsigns) in commits

## Dual Architecture

This project supports two deployment methods:

1. **HACS Integration** (`custom_components/pskr/`): Native Home Assistant component
2. **Docker/MQTT Bridge** (`pskr-ha-bridge.py`): Standalone container

Please test both if your change affects shared functionality.

## Questions?

- Open an issue for discussion
- Check existing issues and documentation first

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
