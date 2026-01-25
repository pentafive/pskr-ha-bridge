# Roadmap

Future enhancements for pskr-ha-bridge.

## v2.4.x - Dashboard Generator Improvements

- [ ] **Global-only dashboard** - Generate dashboard without callsign for global monitor only
- [ ] **Preset tiers** - Minimal | Standard | Full complexity options
- [ ] **Minimal preset** - Fewer cards, simpler layout for basic monitoring

## v2.5.x - Advanced Features

- [ ] **Bearing/direction sensors** - Calculate bearing from Maidenhead locators (requires pyhamtools enhancement)
- [ ] **Activity heatmap data** - Hour × Band matrix as sensor attribute
- [ ] **Contest mode** - Track unique multipliers for contest logging

## Future Considerations

- [ ] **DX cluster integration** - Cross-reference spots with DX cluster data
- [ ] **QRZ.com lookup** - Enrich spot data with operator info
- [ ] **Multi-rig support** - Track spots from multiple stations/antennas with unified dashboard

## Completed

### v2.3.1
- [x] Web-based dashboard generator
- [x] CLI dashboard generator
- [x] Template system for maintainable generation

### v2.3.0
- [x] Per-band statistics (50 sensors)
- [x] Extended aggregate sensors (unique countries, DX ratio, propagation score)
- [x] Farthest station tracking

### v2.2.0
- [x] Activity-aware health thresholds
- [x] Configurable transport modes
- [x] Granular feed status

---

*Last updated: 2026-01-24*
