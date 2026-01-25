#!/usr/bin/env python3
"""
PSKReporter Dashboard Generator for Home Assistant

Generates a customized Lovelace dashboard YAML for your callsign(s).
Uses template files from ./templates/ directory.

Usage:
    python generate_dashboard.py KD5QLM                    # Single callsign
    python generate_dashboard.py KD5QLM KJ5IUY             # Two callsigns (comparison)
    python generate_dashboard.py KD5QLM --no-global        # Without global monitor
    python generate_dashboard.py KD5QLM -o dashboard.yaml  # Save to file

Requirements:
    - PSKReporter HACS integration v2.3.0+
    - HACS Frontend cards: mushroom, mini-graph-card, apexcharts-card (optional)
"""

import argparse
import sys
from pathlib import Path

# Color scheme for consistent styling
COLORS = ["#1E88E5", "#FFA726", "#43A047", "#E53935"]

# Template directory (relative to this script)
TEMPLATE_DIR = Path(__file__).parent / "templates"


def load_template(name: str) -> str:
    """Load a template file from the templates directory."""
    template_path = TEMPLATE_DIR / f"{name}.yaml"
    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")
    return template_path.read_text()


def substitute(template: str, **kwargs) -> str:
    """Substitute ${VAR} placeholders in template."""
    result = template
    for key, value in kwargs.items():
        result = result.replace(f"${{{key}}}", str(value))
    return result


def generate_callsign_section(callsign: str, color: str) -> str:
    """Generate a complete section for one callsign using template."""
    template = load_template("callsign-section")
    return substitute(
        template,
        CALLSIGN=callsign.upper(),
        CALL_LOWER=callsign.lower(),
        COLOR=color,
    )


def generate_band_breakdown(callsign: str) -> str:
    """Generate per-band breakdown section using template."""
    template = load_template("band-breakdown")
    return substitute(
        template,
        CALLSIGN=callsign.upper(),
        CALL_LOWER=callsign.lower(),
    )


def generate_global_section() -> str:
    """Generate the global propagation monitor section using template."""
    return load_template("global-section")


def generate_series_entry(callsign: str, sensor_suffix: str, color: str) -> str:
    """Generate a single ApexCharts series entry."""
    return f"""          - entity: sensor.pskreporter_{callsign.lower()}_{sensor_suffix}
            name: {callsign.upper()}
            color: "{color}"
            stroke_width: 2"""


def generate_comparison_section(callsigns: list[str]) -> str:
    """Generate comparison charts for multiple callsigns using template."""
    template = load_template("comparison-section")

    series_spots = "\n".join(
        generate_series_entry(c, "total_spots", COLORS[i % len(COLORS)])
        for i, c in enumerate(callsigns)
    )
    series_snr = "\n".join(
        generate_series_entry(c, "average_snr", COLORS[i % len(COLORS)])
        for i, c in enumerate(callsigns)
    )
    series_propagation = "\n".join(
        generate_series_entry(c, "propagation_score", COLORS[i % len(COLORS)])
        for i, c in enumerate(callsigns)
    )

    return substitute(
        template,
        SERIES_SPOTS=series_spots,
        SERIES_SNR=series_snr,
        SERIES_PROPAGATION=series_propagation,
    )


def generate_badges(callsigns: list[str], include_global: bool) -> str:
    """Generate badge definitions."""
    badges = []
    for c in callsigns:
        call_lower = c.lower()
        badges.append(f"  - entity: sensor.pskreporter_{call_lower}_total_spots")
        badges.append(f"    name: {c.upper()}")
        badges.append(f"  - entity: binary_sensor.pskreporter_{call_lower}_feed_health")

    if include_global:
        badges.append("  - entity: sensor.pskreporter_global_monitor_global_spots")
        badges.append("    name: Global")
        badges.append("  - entity: binary_sensor.pskreporter_global_monitor_feed_health")

    return "\n".join(badges)


def generate_dashboard(
    callsigns: list[str],
    include_global: bool = True,
    include_bands: bool = True,
) -> str:
    """Generate complete dashboard YAML using templates."""

    # Normalize callsigns
    callsigns = [c.upper() for c in callsigns]

    # Determine column layout
    num_cols = len(callsigns) + (1 if include_global else 0)
    num_cols = min(num_cols, 3)  # Max 3 columns

    # Build header
    header_template = load_template("header")
    header = substitute(
        header_template,
        CALLSIGNS=", ".join(callsigns),
        MAX_COLUMNS=num_cols,
    )

    sections = []

    # Add callsign sections
    for i, callsign in enumerate(callsigns):
        color = COLORS[i % len(COLORS)]
        sections.append(generate_callsign_section(callsign, color))

    # Add global section
    if include_global:
        sections.append(generate_global_section())

    # Add band breakdowns
    if include_bands:
        for callsign in callsigns:
            sections.append(generate_band_breakdown(callsign))

    # Add comparison section if multiple callsigns
    if len(callsigns) > 1:
        sections.append(generate_comparison_section(callsigns))

    # Combine all parts
    sections_yaml = "\n".join(sections)
    badges_yaml = generate_badges(callsigns, include_global)

    return f"{header}{sections_yaml}\nbadges:\n{badges_yaml}\ncards: []\n"


def main():
    parser = argparse.ArgumentParser(
        description="Generate a PSKReporter dashboard for Home Assistant",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s W1ABC                     Single callsign dashboard
  %(prog)s W1ABC K2DEF               Two callsign comparison
  %(prog)s W1ABC --no-global         Without global monitor
  %(prog)s W1ABC -o my-dashboard.yaml  Save to file

Requirements:
  - PSKReporter HACS integration v2.3.0+
  - HACS Frontend: mushroom, mini-graph-card, apexcharts-card
        """,
    )
    parser.add_argument(
        "callsigns",
        nargs="+",
        help="Your callsign(s) - up to 2 for comparison view",
    )
    parser.add_argument(
        "--no-global",
        action="store_true",
        help="Exclude global propagation monitor",
    )
    parser.add_argument(
        "--no-bands",
        action="store_true",
        help="Exclude per-band breakdown sections",
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        help="Output file (default: stdout)",
    )

    args = parser.parse_args()

    if len(args.callsigns) > 2:
        print("Warning: Only first 2 callsigns will be used for optimal layout", file=sys.stderr)
        args.callsigns = args.callsigns[:2]

    try:
        dashboard = generate_dashboard(
            callsigns=args.callsigns,
            include_global=not args.no_global,
            include_bands=not args.no_bands,
        )
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        print("Make sure you're running from the dashboards directory or templates exist.", file=sys.stderr)
        sys.exit(1)

    if args.output:
        with open(args.output, "w") as f:
            f.write(dashboard)
        print(f"Dashboard saved to: {args.output}", file=sys.stderr)
    else:
        print(dashboard)


if __name__ == "__main__":
    main()
