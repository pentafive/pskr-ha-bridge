# Dashboard Examples

This directory provides tools and templates for creating Home Assistant dashboards for the PSKReporter integration.

## Dashboard Generator (Recommended)

The easiest way to create a dashboard is to use the generator:

### Web Generator (No Install Required)

Visit: **[Dashboard Generator](https://pentafive.github.io/pskr-ha-bridge/dashboard-generator.html)**

Just enter your callsign and copy the generated YAML.

### Command Line

```bash
# Single callsign
python3 generate_dashboard.py W1ABC

# Two callsigns (comparison view)
python3 generate_dashboard.py W1ABC K2DEF

# Save to file
python3 generate_dashboard.py W1ABC -o my-dashboard.yaml

# Options
python3 generate_dashboard.py W1ABC --no-global   # Without global monitor
python3 generate_dashboard.py W1ABC --no-bands    # Without per-band breakdown
```

### One-liner (curl)

```bash
curl -sL https://raw.githubusercontent.com/pentafive/pskr-ha-bridge/main/examples/dashboards/generate_dashboard.py | python3 - W1ABC
```

## Installing the Generated Dashboard

1. Copy the generated YAML
2. In Home Assistant: **Settings → Dashboards → Add Dashboard**
3. Create a new dashboard
4. Click ⋮ → **Edit Dashboard** → ⋮ → **Raw configuration editor**
5. Paste the YAML and save

## Directory Contents

```
dashboards/
├── generate_dashboard.py    # CLI dashboard generator
├── templates/               # YAML templates (used by generator)
│   ├── header.yaml
│   ├── callsign-section.yaml
│   ├── band-breakdown.yaml
│   ├── global-section.yaml
│   └── comparison-section.yaml
├── personal-monitor.yaml    # Basic HACS integration example
├── docker-personal-monitor.yaml  # Docker bridge example
├── global-monitor.yaml      # Global monitor example
└── antenna-comparison.yaml  # Multi-antenna comparison
```

## Entity Naming Patterns

| Mode | Entity Pattern | Example |
|------|----------------|---------|
| HACS Integration | `sensor.pskreporter_{call}_*` | `sensor.pskreporter_w1abc_total_spots` |
| Docker Bridge | `sensor.pskr_stats_rx_{call}_*` | `sensor.pskr_stats_rx_w1abc_total_spots` |
| Global Monitor | `sensor.pskreporter_global_monitor_*` | `sensor.pskreporter_global_monitor_20m_activity` |

Replace `{call}` with your callsign in lowercase.

## Required HACS Frontend Cards

Install from HACS → Frontend:

- **[Mushroom](https://github.com/piitaya/lovelace-mushroom)** - Modern entity cards
- **[Mini Graph Card](https://github.com/kalkih/mini-graph-card)** - Trend charts
- **[ApexCharts Card](https://github.com/RomRider/apexcharts-card)** - Comparison charts

Basic entity cards work without any custom cards.

## Template Placeholders

The templates use these placeholders:

| Placeholder | Description | Example |
|-------------|-------------|---------|
| `${CALLSIGN}` | Uppercase callsign | W1ABC |
| `${CALL_LOWER}` | Lowercase callsign | w1abc |
| `${COLOR}` | Theme color for callsign | #1E88E5 |

## Modifying Templates

To customize the dashboard layout:

1. Edit files in `templates/`
2. Run the generator to test changes
3. Both CLI and web generators will pick up template changes

The web generator fetches templates from GitHub, so changes are reflected after push.
