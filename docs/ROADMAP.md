# Roadmap

Future enhancements for pskr-ha-bridge.

## v2.4.0 - Band Filter & DXCC Wanted List

*DXCC/band wanted list requested by VK3GA — requirements confirmed 2026-02-02*

- [ ] **Band filter activation** - Wire existing `CONF_BAND_FILTER` into filtering logic (HACS + Docker)
- [ ] **Band filter UI** - Multi-select in HACS options flow, `SPOT_BAND_FILTER` env var for Docker
- [ ] **Wanted list matching** - Direction-aware DXCC+band combo detection (RX, TX, or both)
- [ ] **Wanted list config** - Inline configuration: comma-separated `DXCC:BAND` env var (Docker), text input in HACS options flow
- [ ] **Wanted match sensors** - Binary sensor (on/off), match count, list size diagnostic
- [ ] **HA event** - `pskr_wanted_spot` event for automations (push notifications, alerts)
- [ ] **Tests** - Unit tests for wanted list parsing and matching
- [ ] **Documentation** - Wiki page, example automations, .env.example updates

## v2.5.0 - Wanted List Import & Enrichment

- [ ] **Wanted list file import** - Load from text file (`DXCC:BAND` per line), file path in HACS options, Docker file mount
- [ ] **ClubLog API integration** - Auto-build wanted list from QSO history via ClubLog API (suggested by VK3GA)
- [ ] **ADIF file import** - Parse LoTW/Club Log exports to derive needed DXCC/band combos
- [ ] **DXCC name mapping** - Human-readable country names alongside ADIF numeric codes in sensors/events

## v2.6.x - Dashboard Generator Improvements

- [ ] **Global-only dashboard** - Generate dashboard without callsign for global monitor only
- [ ] **Preset tiers** - Minimal | Standard | Full complexity options
- [ ] **Minimal preset** - Fewer cards, simpler layout for basic monitoring

## v2.7.x - Advanced Features

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

*Last updated: 2026-02-02*
