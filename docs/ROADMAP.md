# Roadmap

Future enhancements for pskr-ha-bridge.

## v2.7.x - Advanced Features

- [ ] **Contest mode** - Track unique multipliers for contest logging

## Future Considerations

- [ ] **Wanted list file import** - Load from text file (`DXCC:BAND` per line), file path in HACS options, Docker file mount
- [ ] **ADIF file import** - Parse LoTW/Club Log exports to derive needed DXCC/band combos
- [ ] **DX cluster integration** - Cross-reference spots with DX cluster data
- [ ] **QRZ.com lookup** - Enrich spot data with operator info
- [ ] **Multi-rig support** - Track spots from multiple stations/antennas with unified dashboard

## Completed

### v2.6.0
- [x] Dashboard preset tiers — `--preset minimal|standard|full`
- [x] Minimal preset — native HA cards only, no HACS frontend dependencies
- [x] Activity heatmap — hour × band matrix as sensor attribute (24h rolling)
- [x] Disconnect log rate-limiting v2 — timestamp-based, max 1 WARNING per 300s

### v2.5.0
- [x] DXCC name mapping — human-readable country names in sensor attributes
- [x] Bearing/direction sensor — dominant direction with compass heading
- [x] Dashboard `views:` wrapper — paste directly into HA Raw Configuration Editor
- [x] Global-only dashboard — generate dashboard without callsign
- [x] MQTT disconnect log rate-limiting — fix log spam bug

### v2.4.0
- [x] Band filter activation — wire `CONF_BAND_FILTER` into filtering logic
- [x] Band filter UI — multi-select in HACS, `SPOT_BAND_FILTER` env var for Docker
- [x] Wanted list matching — direction-aware DXCC+band combo detection
- [x] Wanted list config — inline `DXCC:BAND` pairs
- [x] Wanted match sensors — binary sensor, match count, list size
- [x] HA event — `pskr_wanted_spot` event for automations
- [x] Tests — unit tests for wanted list parsing and matching
- [x] Documentation — wiki page, example automations

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

*Last updated: 2026-02-07*
