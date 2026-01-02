#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import paho.mqtt.client as mqtt
import json
import time
import datetime
import os
import statistics
import threading
from collections import deque, defaultdict
import sys
import traceback
import re # For callsign cleaning regex

# --- Dependency Handling & Notes ---
try:
    from pyhamtools import LookupLib, Callinfo
    from pyhamtools.locator import calculate_distance, calculate_heading, locator_to_latlong
    # Note: pyhamtools lookuplib may need to download data files on first run if not cached.
except ImportError as e:
    print(f"ERROR: Missing essential pyhamtools library or component: {e}")
    print("Please ensure pyhamtools is installed correctly in your environment:")
    print("  (Activate venv) pip install pyhamtools")
    sys.exit(1)

# ==============================================================================
# --- Configuration (loaded from environment variables) ---
# ==============================================================================
# Configuration is loaded from config.py which reads environment variables.
# For Docker: Set variables in .env file or docker-compose.yaml
# For standalone: Export environment variables before running
#
# Required variables:
#   MY_CALLSIGN - Your amateur radio callsign
#   HA_MQTT_BROKER - Home Assistant MQTT broker address
#
# See .env.example for full configuration options
# ==============================================================================

from config import (
    MY_CALLSIGN,
    DEBUG_MODE,
    PSK_BROKER,
    PSK_TRANSPORT_MODE,
    PSK_TLS_INSECURE,
    HA_MQTT_BROKER,
    HA_MQTT_PORT,
    HA_MQTT_USER,
    HA_MQTT_PASS,
    SCRIPT_DIRECTION,
    MODES_FILTER,
    STATS_INTERVAL_WINDOW_SECONDS,
    STATS_UPDATE_INTERVAL_SECONDS,
    ENABLE_SPOT_SENSORS,
    SPOT_FILTER_MIN_DISTANCE_KM,
    SPOT_ALLOW_CALLSIGNS,
    SPOT_FILTERED_CALLSIGNS,
    SPOT_ALLOW_COUNTRIES,
    SPOT_FILTERED_COUNTRIES,
    HA_DISCOVERY_PREFIX,
    HA_ENTITY_BASE,
)

# ==============================================================================
# --- Other Global Variables & Constants ---
# ==============================================================================
SCRIPT_VERSION = "2.0.0"  # Docker + HACS modernization
MAX_SPOT_HISTORY = 5000

# --- State Variables ---
spot_session_stats = {}
all_spots_history = deque(maxlen=MAX_SPOT_HISTORY)

# --- Initialization for PyHamtools Lookups ---
# (Initialization code remains the same)
lookuplib = None; callinfo = None; pyhamtools_lookups_ok = False
try:
    print("INFO: Initializing pyhamtools LookupLib..."); lookuplib = LookupLib(lookuptype="countryfile")
    print("INFO: Initializing pyhamtools Callinfo..."); callinfo = Callinfo(lookuplib)
    print("INFO: PyHamtools lookups initialized."); pyhamtools_lookups_ok = True
except Exception as e: print(f"WARNING: Failed lookup init: {e}. Enrichment disabled.")


# --- Helper Functions --- (Unchanged from v1.4.7)
def sanitize_for_mqtt(input_string):
    if not isinstance(input_string, str): return ""
    safe_str = input_string.replace('.', '-').replace('/', '-').replace('#', '-').replace('+', '-')
    safe_str = ''.join(c for c in safe_str if c.isalnum() or c in ['-', '_'])
    return safe_str.lower()

SAFE_MY_CALLSIGN = sanitize_for_mqtt(MY_CALLSIGN) if MY_CALLSIGN else ""
ALLOW_CALLS_UPPER = {c.upper() for c in SPOT_ALLOW_CALLSIGNS}; FILTERED_CALLS_UPPER = {c.upper() for c in SPOT_FILTERED_CALLSIGNS}
ALLOW_COUNTRIES_SET = set(SPOT_ALLOW_COUNTRIES); FILTERED_COUNTRIES_SET = set(SPOT_FILTERED_COUNTRIES)

def get_base_callsign(full_callsign):
    if not full_callsign or not isinstance(full_callsign, str): return None
    call = full_callsign.replace('.', '/'); parts = call.split('/')
    if len(parts) == 1: return call
    if re.search(r'\d', parts[-1]) and len(parts[-1]) > 2:
         if len(parts) == 2 and re.fullmatch(r'[A-Z0-9]+', parts[0]): return parts[-1]
    return parts[0]

DEVICE_NAME_SPOTS = f"PSKr Spots ({MY_CALLSIGN})" if MY_CALLSIGN else "PSKr Spots"
DEVICE_UNIQUE_ID_SPOTS = f"{HA_ENTITY_BASE}_spots_{SAFE_MY_CALLSIGN}" if SAFE_MY_CALLSIGN else f"{HA_ENTITY_BASE}_spots"
DEVICE_NAME_STATS_RX = f"PSKr Stats RX ({MY_CALLSIGN})" if MY_CALLSIGN else "PSKr Stats RX"
DEVICE_UNIQUE_ID_STATS_RX = f"{HA_ENTITY_BASE}_stats_rx_{SAFE_MY_CALLSIGN}" if SAFE_MY_CALLSIGN else f"{HA_ENTITY_BASE}_stats_rx"
DEVICE_NAME_STATS_TX = f"PSKr Stats TX ({MY_CALLSIGN})" if MY_CALLSIGN else "PSKr Stats TX"
DEVICE_UNIQUE_ID_STATS_TX = f"{HA_ENTITY_BASE}_stats_tx_{SAFE_MY_CALLSIGN}" if SAFE_MY_CALLSIGN else f"{HA_ENTITY_BASE}_stats_tx"

def get_spot_device_config():
    return { "identifiers": [DEVICE_UNIQUE_ID_SPOTS], "name": DEVICE_NAME_SPOTS, "manufacturer": "PSKReporter.info / Python Script", "model": "MQTT Spot Listener", "sw_version": SCRIPT_VERSION }
def get_stats_device_config(direction):
    direction_clean = direction.lower()
    if direction_clean == "rx": return { "identifiers": [DEVICE_UNIQUE_ID_STATS_RX], "name": DEVICE_NAME_STATS_RX, "manufacturer": "PSKReporter.info / Python Script", "model": "MQTT Statistics Aggregator", "sw_version": SCRIPT_VERSION }
    elif direction_clean == "tx": return { "identifiers": [DEVICE_UNIQUE_ID_STATS_TX], "name": DEVICE_NAME_STATS_TX, "manufacturer": "PSKReporter.info / Python Script", "model": "MQTT Statistics Aggregator", "sw_version": SCRIPT_VERSION }
    else: print(f"WARNING: Invalid direction '{direction}'. Defaulting to RX stats device."); return get_stats_device_config("rx")

def km_to_miles(km): km_val = km if isinstance(km, (int, float)) else 0; return km_val * 0.621371
def safe_mean(data): numeric_data = [x for x in data if isinstance(x, (int, float))]; return statistics.mean(numeric_data) if numeric_data else 0.0
def safe_min(data): numeric_data = [x for x in data if isinstance(x, (int, float))]; return min(numeric_data) if numeric_data else None
def safe_max(data): numeric_data = [x for x in data if isinstance(x, (int, float))]; return max(numeric_data) if numeric_data else None

def publish_mqtt(client, topic, payload, retain=False, qos=0):
    if not client or not client.is_connected():
        if DEBUG_MODE: print(f"DEBUG: MQTT client not connected. Skip publish to {topic}")
        return False
    try:
        payload_to_send = "" if payload is None else str(payload)
        if DEBUG_MODE:
             print(f"DEBUG: MQTT Publish -> Topic: {topic}")
             payload_info = f"Type: {type(payload_to_send)}, Length: {len(payload_to_send)}" if payload_to_send else "EMPTY Payload"
             print(f"DEBUG: MQTT Publish -> {payload_info}, QoS: {qos}, Retain: {retain}")
        result, mid = client.publish(topic, payload=payload_to_send, qos=qos, retain=retain)
        if result == mqtt.MQTT_ERR_SUCCESS: return True
        else: print(f"ERROR: Failed to publish to {topic}. Result code: {result}"); return False
    except Exception as e: print(f"ERROR: Unexpected error publishing to {topic}: {e}"); return False

# --- Discovery Publishing Functions --- (Unchanged from v1.4.7)
def publish_spot_discovery(client, sender_call, receiver_call):
    safe_sender = sanitize_for_mqtt(sender_call); safe_receiver = sanitize_for_mqtt(receiver_call)
    if not safe_sender or not safe_receiver: return
    unique_id = f"{HA_ENTITY_BASE}_spots_{safe_sender}_{safe_receiver}"
    base_topic = f"{HA_ENTITY_BASE}/spots/{safe_sender}/{safe_receiver}"
    config_topic = f"{HA_DISCOVERY_PREFIX}/sensor/{unique_id}/config"
    name = f"{sender_call} -> {receiver_call}"
    payload = { "name": name, "state_topic": f"{base_topic}/state", "json_attributes_topic": f"{base_topic}/attributes",
                "unique_id": unique_id, "icon": "mdi:radio-tower", "unit_of_measurement": "dB",
                "device_class": "signal_strength", "value_template": "{{ value }}", "device": get_spot_device_config() }
    if DEBUG_MODE: print(f"DEBUG: Publishing Spot Discovery for {name} (ID: {unique_id})")
    publish_mqtt(client, config_topic, json.dumps(payload), retain=True, qos=0)

def publish_stat_discovery(client, direction, metric, unit="", icon="", state_class=None, device_class=None, band=None, signal_mode=None, extra_attrs=None):
    if not isinstance(metric, str): print(f"ERROR: Invalid metric type '{type(metric)}' for discovery. Skipping."); return
    if not SAFE_MY_CALLSIGN: print("ERROR: Cannot publish stat discovery, MY_CALLSIGN not set."); return
    safe_band = sanitize_for_mqtt(band) if band else None
    safe_mode = sanitize_for_mqtt(signal_mode) if signal_mode else None
    safe_metric = sanitize_for_mqtt(metric)
    period_minutes = STATS_INTERVAL_WINDOW_SECONDS // 60

    name_parts = []; topic_parts = [HA_ENTITY_BASE, "stats", direction, SAFE_MY_CALLSIGN]; id_parts = list(topic_parts)
    if band: name_parts.append(band); topic_parts.append(safe_band); id_parts.append(safe_band)
    if signal_mode: name_parts.append(signal_mode); topic_parts.append(safe_mode); id_parts.append(safe_mode)

    metric_name_pretty = metric.replace('_', ' ').title()
    if metric == "unique_senders": metric_name_pretty = "Unique Senders"
    elif metric == "unique_receivers": metric_name_pretty = "Unique Receivers"
    elif metric == "unique_countries": metric_name_pretty = "Unique Countries"
    elif metric == "total_unique_countries": metric_name_pretty = "Total Unique Countries"
    elif metric == "total_spots": metric_name_pretty = "Total Spots"
    elif metric == "total_unique_stations": metric_name_pretty = f"Total Unique {'Senders' if direction == 'rx' else 'Receivers'}"
    elif metric == "avg_dist": metric_name_pretty = "Avg Dist"
    elif metric == "min_dist": metric_name_pretty = "Min Dist"
    elif metric == "max_dist": metric_name_pretty = "Max Dist"

    name_parts.append(f"{metric_name_pretty}")
    id_parts.append(safe_metric)
    topic_parts.append(safe_metric)

    unique_id = "_".join(id_parts)
    base_topic = "/".join(topic_parts)
    name = " ".join(name_parts)
    config_topic = f"{HA_DISCOVERY_PREFIX}/sensor/{unique_id}/config"

    payload = { "name": name, "state_topic": f"{base_topic}/state", "unique_id": unique_id, "device": get_stats_device_config(direction) }
    if unit: payload["unit_of_measurement"] = unit
    if icon: payload["icon"] = icon
    if state_class: payload["state_class"] = state_class
    if device_class: payload["device_class"] = device_class
    payload["attributes"] = { "direction": direction.upper(), "metric": metric, "measurement_period_minutes": period_minutes }
    if band: payload["attributes"]["band"] = band
    if signal_mode: payload["attributes"]["signal_mode"] = signal_mode
    if extra_attrs: payload["attributes"].update(extra_attrs)

    if DEBUG_MODE: print(f"DEBUG: Publishing Stat Discovery for {name} (ID: {unique_id})")
    publish_mqtt(client, config_topic, json.dumps(payload), retain=True, qos=0)

def publish_most_active_discovery(client, direction, metric_type):
    if not SAFE_MY_CALLSIGN: return
    metric = f"most_active_{metric_type}"
    safe_metric = sanitize_for_mqtt(metric)
    unique_id = f"{HA_ENTITY_BASE}_stats_{direction}_{SAFE_MY_CALLSIGN}_{safe_metric}"
    base_topic = f"{HA_ENTITY_BASE}/stats/{direction}/{SAFE_MY_CALLSIGN}/{safe_metric}"
    config_topic = f"{HA_DISCOVERY_PREFIX}/sensor/{unique_id}/config"
    attributes_topic = f"{base_topic}/attributes"
    period_minutes = STATS_INTERVAL_WINDOW_SECONDS // 60
    name = f"Most Active {metric_type.capitalize()}"
    icon = "mdi:chart-bar" if metric_type == "band" else "mdi:waveform"

    payload = { "name": name, "state_topic": f"{base_topic}/state", "unique_id": unique_id, "icon": icon,
                "json_attributes_topic": attributes_topic, "device": get_stats_device_config(direction),
                "attributes": { "direction": direction.upper(), "metric": metric, "measurement_period_minutes": period_minutes } }
    if DEBUG_MODE: print(f"DEBUG: Publishing Most Active Discovery for {name} (ID: {unique_id})")
    publish_mqtt(client, config_topic, json.dumps(payload), retain=True, qos=0)

def publish_global_country_discovery(client, direction):
    publish_stat_discovery(client=client, direction=direction, metric="total_unique_countries",
                           unit="countries", icon="mdi:map-marker-multiple", state_class="measurement")

# --- State Update Publishing Functions ---
def publish_spot_update(client, sender_call, receiver_call, current_snr, attributes_payload):
    safe_sender = sanitize_for_mqtt(sender_call); safe_receiver = sanitize_for_mqtt(receiver_call)
    if not safe_sender or not safe_receiver: return
    base_topic = f"{HA_ENTITY_BASE}/spots/{safe_sender}/{safe_receiver}"
    state_topic = f"{base_topic}/state"; attributes_topic = f"{base_topic}/attributes"
    if DEBUG_MODE: print(f"DEBUG: Updating spot state for {sender_call}->{receiver_call}: {current_snr}")
    publish_mqtt(client, state_topic, current_snr, qos=1)
    try:
        attributes_payload_clean = {k: v for k, v in attributes_payload.items() if v is not None}
        json_attributes = json.dumps(attributes_payload_clean)
        if DEBUG_MODE: print(f"DEBUG: Updating spot attributes for {sender_call}->{receiver_call}")
        publish_mqtt(client, attributes_topic, json_attributes, qos=0)
    except Exception as e: print(f"ERROR: publishing spot attributes for {sender_call}->{receiver_call}: {e}")

def publish_stat_update(client, direction, metric, value, band=None, signal_mode=None):
    """Publishes state update for various statistics sensors. Uses keywords for safety."""
    safe_band = sanitize_for_mqtt(band) if band else None
    safe_mode = sanitize_for_mqtt(signal_mode) if signal_mode else None
    safe_metric = sanitize_for_mqtt(metric)
    if not SAFE_MY_CALLSIGN: return # Need callsign for topic
    topic_parts = [HA_ENTITY_BASE, "stats", direction, SAFE_MY_CALLSIGN]
    if band: topic_parts.append(safe_band)
    if signal_mode: topic_parts.append(safe_mode)
    topic_parts.append(safe_metric)
    state_topic = "/".join(topic_parts) + "/state"
    if DEBUG_MODE: print(f"DEBUG: Updating stat state: {state_topic} = {value}")
    publish_mqtt(client, state_topic, value if value is not None else 0, qos=0)

def publish_most_active_sensor(client, direction, metric_type, state_value, count_value):
    if not SAFE_MY_CALLSIGN: return
    metric = f"most_active_{metric_type}"
    safe_metric = sanitize_for_mqtt(metric)
    base_topic = f"{HA_ENTITY_BASE}/stats/{direction}/{SAFE_MY_CALLSIGN}/{safe_metric}"
    state_topic = f"{base_topic}/state"; attributes_topic = f"{base_topic}/attributes"
    state_to_publish = state_value if state_value else "None"
    attributes_payload = {"spot_count": count_value if count_value is not None else 0}
    if DEBUG_MODE:
         print(f"DEBUG: Updating Most Active {metric_type.capitalize()} state: {state_topic} = {state_to_publish}")
         print(f"DEBUG: Updating Most Active {metric_type.capitalize()} attributes: {attributes_topic} = {attributes_payload}")
    publish_mqtt(client, state_topic, state_to_publish, qos=0)
    publish_mqtt(client, attributes_topic, json.dumps(attributes_payload), qos=0)

# --- Periodic Stats Calculation Task ---
state_lock = threading.Lock()
stats_timer = None
stop_event = threading.Event()

def update_band_stats_task():
    """Calculates and publishes interval-based stats. Runs periodically."""
    global stats_timer
    if stop_event.is_set(): return
    if not SAFE_MY_CALLSIGN: print("ERROR: Cannot run stats update without MY_CALLSIGN set."); return

    current_time = time.time()
    interval_cutoff_time = current_time - STATS_INTERVAL_WINDOW_SECONDS

    with state_lock: history_snapshot = list(all_spots_history)

    spots_in_interval = [spot for spot in history_snapshot if spot[0] >= interval_cutoff_time]
    if DEBUG_MODE: print(f"DEBUG: Found {len(spots_in_interval)} spots in the {STATS_INTERVAL_WINDOW_SECONDS}s interval for stats calculation.")

    directions_to_process = []
    if SCRIPT_DIRECTION.lower() in ["rx", "dual"]: directions_to_process.append("rx")
    if SCRIPT_DIRECTION.lower() in ["tx", "dual"]: directions_to_process.append("tx")

    if not directions_to_process: print("ERROR: Invalid SCRIPT_DIRECTION."); return

    for direction in directions_to_process:
        if direction == "rx": dir_spots_interval = [s for s in spots_in_interval if s[5] == MY_CALLSIGN]; adif_idx, station_idx = 7, 4; unique_station_metric = "unique_senders"
        else: dir_spots_interval = [s for s in spots_in_interval if s[4] == MY_CALLSIGN]; adif_idx, station_idx = 8, 5; unique_station_metric = "unique_receivers"
        if DEBUG_MODE: print(f"DEBUG: [{direction.upper()}] Processing {len(dir_spots_interval)} spots for this direction.")

        # Aggregators
        agg_band_mode = defaultdict(lambda: defaultdict(lambda: {'distances': [], 'snrs': [], 'stations': set()}))
        agg_band_mode_counts = defaultdict(lambda: defaultdict(int)); band_adif_codes = defaultdict(set); global_stations_per_mode = defaultdict(set)
        global_counts_per_mode = defaultdict(int); global_adif_codes = set(); global_stations = set(); global_distances = []; global_snrs = []

        # Aggregate data
        for ts, band, dist, snr, sender, receiver, mode, s_adif, r_adif in dir_spots_interval:
            if not band or not mode: continue
            stats_band_mode = agg_band_mode[band][mode]; agg_band_mode_counts[band][mode] += 1
            if dist is not None and dist > 0: stats_band_mode['distances'].append(dist); global_distances.append(dist)
            if snr is not None: stats_band_mode['snrs'].append(snr); global_snrs.append(snr)
            station = sender if direction == 'rx' else receiver
            stats_band_mode['stations'].add(station); global_stations_per_mode[mode].add(station); global_stations.add(station)
            adif_code = s_adif if direction == 'rx' else r_adif
            if adif_code: global_adif_codes.add(adif_code); band_adif_codes[band].add(adif_code)

        # Calculate Final Statistics
        global_total_spots = len(dir_spots_interval); global_total_unique_stations = len(global_stations); global_total_unique_countries = len(global_adif_codes)
        global_min_dist = safe_min(global_distances); global_avg_dist = safe_mean(global_distances); global_max_dist = safe_max(global_distances)
        global_min_snr = safe_min(global_snrs); global_avg_snr = safe_mean(global_snrs); global_max_snr = safe_max(global_snrs)
        counts_per_band = {band: sum(m_counts.values()) for band, m_counts in agg_band_mode_counts.items()}
        most_active_band = max(counts_per_band, key=counts_per_band.get) if counts_per_band else None; most_active_band_count = counts_per_band.get(most_active_band, 0)
        global_counts_per_mode = defaultdict(int);
        for band_data in agg_band_mode_counts.values():
             for mode, count in band_data.items(): global_counts_per_mode[mode] += count
        most_active_mode = max(global_counts_per_mode, key=global_counts_per_mode.get) if global_counts_per_mode else None; most_active_mode_count = global_counts_per_mode.get(most_active_mode, 0)

        # --- Publish Global Stats ---
        if ha_client.is_connected():
            # Publish discovery first (includes small delay within functions now)
            publish_global_country_discovery(ha_client, direction)
            publish_stat_discovery(ha_client, direction=direction, metric="total_spots", unit="spots", icon="mdi:counter", state_class="measurement"); time.sleep(0.05)
            publish_stat_discovery(ha_client, direction=direction, metric=f"total_{unique_station_metric}", unit="stations", icon="mdi:account-multiple", state_class="measurement"); time.sleep(0.05)
            publish_stat_discovery(ha_client, direction=direction, metric="total_min_dist", unit="km", icon="mdi:arrow-collapse-right", state_class="measurement", device_class="distance"); time.sleep(0.05)
            publish_stat_discovery(ha_client, direction=direction, metric="total_avg_dist", unit="km", icon="mdi:map-marker-distance", state_class="measurement", device_class="distance"); time.sleep(0.05)
            publish_stat_discovery(ha_client, direction=direction, metric="total_max_dist", unit="km", icon="mdi:arrow-expand-left", state_class="measurement", device_class="distance"); time.sleep(0.05)
            publish_stat_discovery(ha_client, direction=direction, metric="total_min_snr", unit="dB", icon="mdi:signal-cellular-1", state_class="measurement", device_class="signal_strength"); time.sleep(0.05)
            publish_stat_discovery(ha_client, direction=direction, metric="total_avg_snr", unit="dB", icon="mdi:signal", state_class="measurement", device_class="signal_strength"); time.sleep(0.05)
            publish_stat_discovery(ha_client, direction=direction, metric="total_max_snr", unit="dB", icon="mdi:signal-cellular-3", state_class="measurement", device_class="signal_strength"); time.sleep(0.05)
            publish_stat_discovery(ha_client, direction=direction, metric="active_bands", unit="bands", icon="mdi:chart-bell-curve", state_class="measurement"); time.sleep(0.05)
            publish_most_active_discovery(ha_client, direction, "band"); time.sleep(0.05)
            publish_most_active_discovery(ha_client, direction, "mode"); time.sleep(0.05)
            active_modes_global = set(global_counts_per_mode.keys()) | set(global_stations_per_mode.keys())
            for mode in active_modes_global:
                publish_stat_discovery(ha_client, direction=direction, metric="count", unit="spots", icon="mdi:counter", state_class="measurement", signal_mode=mode); time.sleep(0.05)
                publish_stat_discovery(ha_client, direction=direction, metric=unique_station_metric, unit="stations", icon="mdi:account-multiple", state_class="measurement", signal_mode=mode); time.sleep(0.05)

            # Publish updates for globals
            publish_stat_update(ha_client, direction=direction, metric="total_unique_countries", value=global_total_unique_countries)
            publish_stat_update(ha_client, direction=direction, metric="total_spots", value=global_total_spots)
            publish_stat_update(ha_client, direction=direction, metric=f"total_{unique_station_metric}", value=global_total_unique_stations)
            publish_stat_update(ha_client, direction=direction, metric="total_min_dist", value=round(global_min_dist,1) if global_min_dist is not None else None)
            publish_stat_update(ha_client, direction=direction, metric="total_avg_dist", value=round(global_avg_dist, 1))
            publish_stat_update(ha_client, direction=direction, metric="total_max_dist", value=round(global_max_dist, 1) if global_max_dist is not None else None)
            publish_stat_update(ha_client, direction=direction, metric="total_min_snr", value=global_min_snr)
            publish_stat_update(ha_client, direction=direction, metric="total_avg_snr", value=round(global_avg_snr, 1))
            publish_stat_update(ha_client, direction=direction, metric="total_max_snr", value=global_max_snr)
            publish_stat_update(ha_client, direction=direction, metric="active_bands", value=len(counts_per_band))
            publish_most_active_sensor(ha_client, direction, "band", most_active_band, most_active_band_count)
            publish_most_active_sensor(ha_client, direction, "mode", most_active_mode, most_active_mode_count)
            for mode in active_modes_global:
                publish_stat_update(ha_client, direction=direction, metric="count", value=global_counts_per_mode.get(mode, 0), signal_mode=mode)
                publish_stat_update(ha_client, direction=direction, metric=unique_station_metric, value=len(global_stations_per_mode.get(mode, set())), signal_mode=mode)

        if not ha_client.is_connected(): continue

        # Process and Publish Per-Band Stats
        active_bands_this_direction = set(agg_band_mode.keys()) | set(agg_band_mode_counts.keys()) | set(band_adif_codes.keys())
        for band in active_bands_this_direction:
             band_unique_country_count = len(band_adif_codes[band])
             publish_stat_discovery(ha_client, direction=direction, metric="unique_countries", unit="countries", icon="mdi:map-marker", state_class="measurement", band=band); time.sleep(0.05)
             publish_stat_update(ha_client, direction=direction, metric="unique_countries", value=band_unique_country_count, band=band)

             active_modes_this_band = set(agg_band_mode[band].keys()) | set(agg_band_mode_counts[band].keys())
             for mode in active_modes_this_band:
                 mode_stats = agg_band_mode[band][mode]
                 spot_count = agg_band_mode_counts[band][mode]
                 avg_dist = safe_mean(mode_stats['distances']) # Use avg_dist metric name
                 avg_snr = safe_mean(mode_stats['snrs'])
                 unique_stations = len(mode_stats['stations'])
                 unit_stations = "stations"

                 # Publish Discovery
                 publish_stat_discovery(ha_client, direction=direction, metric="count", unit="spots", icon="mdi:counter", state_class="measurement", band=band, signal_mode=mode); time.sleep(0.05)
                 publish_stat_discovery(ha_client, direction=direction, metric="avg_dist", unit="km", icon="mdi:map-marker-distance", state_class="measurement", device_class="distance", band=band, signal_mode=mode); time.sleep(0.05)
                 publish_stat_discovery(ha_client, direction=direction, metric="avg_snr", unit="dB", icon="mdi:signal", state_class="measurement", device_class="signal_strength", band=band, signal_mode=mode); time.sleep(0.05)
                 publish_stat_discovery(ha_client, direction=direction, metric=unique_station_metric, unit=unit_stations, icon="mdi:account-multiple", state_class="measurement", band=band, signal_mode=mode); time.sleep(0.05)

                 # Publish Updates
                 publish_stat_update(ha_client, direction=direction, metric="count", value=spot_count, band=band, signal_mode=mode)
                 publish_stat_update(ha_client, direction=direction, metric="avg_dist", value=round(avg_dist, 1), band=band, signal_mode=mode) # Use avg_dist metric
                 publish_stat_update(ha_client, direction=direction, metric="avg_snr", value=round(avg_snr, 1), band=band, signal_mode=mode)
                 publish_stat_update(ha_client, direction=direction, metric=unique_station_metric, value=unique_stations, band=band, signal_mode=mode)

    # Schedule the next update
    if not stop_event.is_set():
        stats_timer = threading.Timer(STATS_UPDATE_INTERVAL_SECONDS, update_band_stats_task)
        stats_timer.daemon = True; stats_timer.start()

# --- MQTT Callbacks ---
def on_connect_psk(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print(f"INFO: Connected successfully to PSK Reporter Broker ({PSK_BROKER}). Mode: {SCRIPT_DIRECTION.upper()}")
        topics_to_subscribe = []
        topic_base = "pskr/filter/v2/+/{mode}/{sender}/{receiver}/#"
        if SCRIPT_DIRECTION.lower() in ["rx", "dual"]:
            rx_topic = topic_base.format(mode=MODES_FILTER, sender='+', receiver=MY_CALLSIGN)
            topics_to_subscribe.append((rx_topic, 0)); print(f"INFO: Will subscribe to RX topic: {rx_topic}")
        if SCRIPT_DIRECTION.lower() in ["tx", "dual"]:
            tx_topic = topic_base.format(mode=MODES_FILTER, sender=MY_CALLSIGN, receiver='+')
            topics_to_subscribe.append((tx_topic, 0)); print(f"INFO: Will subscribe to TX topic: {tx_topic}")
        if topics_to_subscribe:
            try:
                result, mid = client.subscribe(topics_to_subscribe)
                if result == mqtt.MQTT_ERR_SUCCESS: print(f"INFO: Subscribe command issued successfully (Mid: {mid})")
                else: print(f"ERROR: Failed to issue subscribe command. Result code: {result}")
            except Exception as e: print(f"ERROR: Exception during subscribe command: {e}")
        else: print("ERROR: Invalid SCRIPT_DIRECTION set.")
    else: print(f"ERROR: Connection to PSK Reporter failed with code {rc}.")

def on_connect_ha(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print(f"INFO: Connected successfully to Home Assistant Broker ({HA_MQTT_BROKER}).")
        print("INFO: Re-publishing discovery for known Spot sensors...")
        with state_lock: spot_keys_snapshot = list(spot_session_stats.keys())
        for key in spot_keys_snapshot:
            try:
                 parts = key.split('->'); sender, receiver = (parts[0], parts[1]) if len(parts) == 2 else (None, None)
                 if sender and receiver: publish_spot_discovery(client, sender, receiver); time.sleep(0.02)
            except Exception as e: print(f"ERROR: Failed during spot rediscovery for key {key}: {e}")
        print("INFO: Finished re-publishing Spot discovery. (Stats discovery republished periodically)")
    else: print(f"ERROR: Connection to Home Assistant Broker failed with code {rc}.")

def on_disconnect(client, userdata, flags, rc, properties=None):
     broker_name = "Unknown"; client_id = "?"
     if hasattr(client, '_client_id'): client_id = client._client_id.decode()
     if client == psk_client: broker_name = "PSK Reporter"
     elif client == ha_client: broker_name = "Home Assistant"
     if rc != 0: print(f"WARNING: Unexpected disconnection from {broker_name} Broker ({client_id})! Result code: {rc}. Will attempt to reconnect.")
     else: print(f"INFO: Disconnected from {broker_name} Broker ({client_id}) normally.")

# --- on_message_psk ---
def on_message_psk(client, userdata, msg):
    try:
        payload_str = msg.payload.decode("utf-8")
        data = json.loads(payload_str)
        sender_call_orig = data.get("sc"); receiver_call_orig = data.get("rc")
        raw_sender_loc = data.get("sl"); raw_receiver_loc = data.get("rl")
        snr = data.get("rp"); timestamp_unix = data.get("t"); frequency = data.get("f")
        band = data.get("b"); signal_mode = data.get("md")
        sender_adif = data.get("sa"); receiver_adif = data.get("ra")
        if not all([sender_call_orig, receiver_call_orig, raw_sender_loc, isinstance(snr, (int, float)), timestamp_unix, band, signal_mode]): return
        is_rx_spot = (receiver_call_orig == MY_CALLSIGN); is_tx_spot = (sender_call_orig == MY_CALLSIGN)
        if SCRIPT_DIRECTION.lower() == "rx" and not is_rx_spot: return
        if SCRIPT_DIRECTION.lower() == "tx" and not is_tx_spot: return
        if SCRIPT_DIRECTION.lower() != "dual" and not is_rx_spot and not is_tx_spot: return

        # Geo Calcs & Lookups
        dist_km, bearing = None, None
        sender_loc_for_calc = raw_sender_loc[:6] if raw_sender_loc else None; receiver_loc_for_calc = raw_receiver_loc[:6] if raw_receiver_loc else None
        my_loc_in_message = receiver_loc_for_calc if is_rx_spot else sender_loc_for_calc; other_loc_in_message = sender_loc_for_calc if is_rx_spot else receiver_loc_for_calc
        if my_loc_in_message and other_loc_in_message and len(my_loc_in_message) >= 4 and len(other_loc_in_message) >= 4:
            try:
                dist_km = calculate_distance(my_loc_in_message, other_loc_in_message); bearing = calculate_heading(my_loc_in_message, other_loc_in_message)
            except Exception: pass
        sender_lat, sender_lon, receiver_lat, receiver_lon = None, None, None, None
        sender_loc_for_latlon = raw_sender_loc[:8] if raw_sender_loc else None; receiver_loc_for_latlon = raw_receiver_loc[:8] if raw_receiver_loc else None
        try:
            if sender_loc_for_latlon: sender_lat, sender_lon = locator_to_latlong(sender_loc_for_latlon)
        except Exception: pass
        try:
            if receiver_loc_for_latlon: receiver_lat, receiver_lon = locator_to_latlong(receiver_loc_for_latlon)
        except Exception: pass
        sender_country, sender_continent, receiver_country, receiver_continent = None, None, None, None
        base_sender_call = get_base_callsign(sender_call_orig); base_receiver_call = get_base_callsign(receiver_call_orig)
        callinfo_local = userdata.get('callinfo') if userdata else callinfo
        if pyhamtools_lookups_ok and callinfo_local:
            if base_sender_call:
                 try:
                     sender_info = callinfo_local.get_all(base_sender_call)
                     if sender_info: sender_country, sender_continent = sender_info.get('country'), sender_info.get('continent')
                 except Exception: pass
            if base_receiver_call:
                 try:
                     receiver_info = callinfo_local.get_all(base_receiver_call)
                     if receiver_info: receiver_country, receiver_continent = receiver_info.get('country'), receiver_info.get('continent')
                 except Exception: pass

        # Update History (Always)
        with state_lock:
            all_spots_history.append(( timestamp_unix, band, dist_km, snr, sender_call_orig, receiver_call_orig, signal_mode, sender_adif, receiver_adif ))

        # Apply Spot Sensor Filtering
        allow_spot_sensor = True
        if not ENABLE_SPOT_SENSORS: allow_spot_sensor = False
        else:
            if SPOT_FILTER_MIN_DISTANCE_KM > 0:
                if dist_km is None or dist_km <= SPOT_FILTER_MIN_DISTANCE_KM: allow_spot_sensor = False
            if allow_spot_sensor and SPOT_FILTERED_CALLSIGNS:
                if sender_call_orig.upper() in FILTERED_CALLS_UPPER or receiver_call_orig.upper() in FILTERED_CALLS_UPPER: allow_spot_sensor = False
            if allow_spot_sensor and SPOT_FILTERED_COUNTRIES:
                if sender_adif in FILTERED_COUNTRIES_SET or receiver_adif in FILTERED_COUNTRIES_SET: allow_spot_sensor = False
            if allow_spot_sensor and SPOT_ALLOW_CALLSIGNS:
                if not (sender_call_orig.upper() in ALLOW_CALLS_UPPER or receiver_call_orig.upper() in ALLOW_CALLS_UPPER): allow_spot_sensor = False
            if allow_spot_sensor and SPOT_ALLOW_COUNTRIES:
                 if not (sender_adif in ALLOW_COUNTRIES_SET or receiver_adif in ALLOW_COUNTRIES_SET): allow_spot_sensor = False
        if DEBUG_MODE: print(f"DEBUG: Spot {sender_call_orig}->{receiver_call_orig}: Filter decision = {allow_spot_sensor}")

        # Update/Publish Spot Sensor (Only if Allowed)
        if allow_spot_sensor:
            needs_discovery = False; session_data_for_publish = {}
            with state_lock:
                spot_key = f"{sender_call_orig}->{receiver_call_orig}"
                if spot_key not in spot_session_stats:
                    spot_session_stats[spot_key] = { 'sender': sender_call_orig, 'receiver': receiver_call_orig, 'snrs': [], 'timestamps': [], 'first_seen': timestamp_unix, 'last_seen': timestamp_unix, 'count': 0, 'config_published': False }; needs_discovery = True
                session = spot_session_stats[spot_key]; session['snrs'].append(snr); session['timestamps'].append(timestamp_unix); session['last_seen'] = timestamp_unix; session['count'] += 1; session['sender_loc'] = raw_sender_loc; session['receiver_loc'] = raw_receiver_loc
                session_data_for_publish = { 'snrs': list(session['snrs']), 'count': session.get('count', 0), 'first_seen': session.get('first_seen'), 'last_seen': session.get('last_seen') }
            if ha_client.is_connected():
                if needs_discovery: publish_spot_discovery(ha_client, sender_call_orig, receiver_call_orig); time.sleep(0.5)
                avg_snr = round(safe_mean(session_data_for_publish['snrs']), 1); min_snr = safe_min(session_data_for_publish['snrs']); max_snr = safe_max(session_data_for_publish['snrs']); dist_miles = round(km_to_miles(dist_km), 1) if dist_km is not None else None
                attributes_payload = {
                    "sender_callsign": sender_call_orig, "receiver_callsign": receiver_call_orig, "sender_locator": raw_sender_loc, "receiver_locator": raw_receiver_loc,
                    "sender_latitude": sender_lat, "sender_longitude": sender_lon, "receiver_latitude": receiver_lat, "receiver_longitude": receiver_lon,
                    "sender_country": sender_country, "sender_continent": sender_continent, "receiver_country": receiver_country, "receiver_continent": receiver_continent,
                    "frequency": frequency, "band": band, "mode": signal_mode, "distance_km": round(dist_km, 1) if dist_km is not None else None, "distance_miles": dist_miles,
                    "bearing": round(bearing, 1) if bearing is not None else None, "session_spot_count": session_data_for_publish.get('count', 0),
                    "session_snr_avg": avg_snr, "session_snr_min": min_snr, "session_snr_max": max_snr,
                    "session_first_heard_utc": datetime.datetime.fromtimestamp(session_data_for_publish.get('first_seen', 0), tz=datetime.timezone.utc).isoformat() if session_data_for_publish.get('first_seen') else None,
                    "session_last_heard_utc": datetime.datetime.fromtimestamp(session_data_for_publish.get('last_seen', 0), tz=datetime.timezone.utc).isoformat() if session_data_for_publish.get('last_seen') else None,
                    "script_last_updated": datetime.datetime.now(tz=datetime.timezone.utc).isoformat() }
                attributes_payload_clean = {k: v for k, v in attributes_payload.items() if v is not None}
                publish_spot_update(ha_client, sender_call_orig, receiver_call_orig, snr, attributes_payload_clean)
    except json.JSONDecodeError: print(f"ERROR: Could not decode JSON: {msg.payload.decode('utf-8', errors='ignore')}")
    except Exception as e: print(f"ERROR: An unexpected error occurred processing message: {e}"); traceback.print_exc()

# --- Main Execution ---
if __name__ == "__main__":
    print("--- PSKReporter to Home Assistant MQTT Bridge ---")
    print(f"INFO: Script Version {SCRIPT_VERSION}")
    print(f"INFO: Monitoring for callsign: {MY_CALLSIGN}")
    print(f"INFO: Script Direction Mode: {SCRIPT_DIRECTION.upper()}")
    print(f"INFO: HA MQTT Broker: {HA_MQTT_BROKER}:{HA_MQTT_PORT}")
    print(f"INFO: Statistics Interval: {STATS_INTERVAL_WINDOW_SECONDS}s ({STATS_INTERVAL_WINDOW_SECONDS//60}min)")
    print(f"INFO: Statistics Update Frequency: {STATS_UPDATE_INTERVAL_SECONDS}s ({STATS_UPDATE_INTERVAL_SECONDS//60}min)")
    print(f"INFO: Spot Sensors Enabled: {ENABLE_SPOT_SENSORS}")
    if ENABLE_SPOT_SENSORS:
        print(f"INFO: Spot Filter Allow Calls: {'Any' if not SPOT_ALLOW_CALLSIGNS else SPOT_ALLOW_CALLSIGNS}")
        print(f"INFO: Spot Filter Filtered Calls: {'None' if not SPOT_FILTERED_CALLSIGNS else SPOT_FILTERED_CALLSIGNS}")
        print(f"INFO: Spot Filter Allow Countries (ADIF): {'Any' if not SPOT_ALLOW_COUNTRIES else SPOT_ALLOW_COUNTRIES}")
        print(f"INFO: Spot Filter Filtered Countries (ADIF): {'None' if not SPOT_FILTERED_COUNTRIES else SPOT_FILTERED_COUNTRIES}")
        print(f"INFO: Spot Filter Min Distance (Km): {'Disabled' if SPOT_FILTER_MIN_DISTANCE_KM <= 0 else SPOT_FILTER_MIN_DISTANCE_KM}")
    print(f"INFO: Debug Mode Enabled: {DEBUG_MODE}")

    psk_transport_protocol = "tcp"; psk_port = 1883; use_tls = False # Default to standard MQTT TCP
    mode = PSK_TRANSPORT_MODE.upper()
    if mode == "MQTT": psk_port, psk_transport_protocol, use_tls = 1883, "tcp", False
    elif mode == "MQTT_TLS": psk_port, psk_transport_protocol, use_tls = 1884, "tcp", True
    elif mode == "MQTT_WS": psk_port, psk_transport_protocol, use_tls = 1885, "websockets", False
    elif mode == "MQTT_WS_TLS": psk_port, psk_transport_protocol, use_tls = 1886, "websockets", True
    else: print(f"FATAL: Invalid PSK_TRANSPORT_MODE '{PSK_TRANSPORT_MODE}'. Exiting."); sys.exit(1)
    print(f"INFO: PSK Reporter Connection: Mode={mode}, Port={psk_port}, Transport={psk_transport_protocol}, TLS={use_tls}")
    if psk_transport_protocol == "websockets": print("INFO: Ensure 'websockets' library is installed (`pip install websockets`)")

    client_userdata = {'lookuplib': lookuplib, 'callinfo': callinfo} if pyhamtools_lookups_ok else None
    psk_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f"ha_psk_listener_{MY_CALLSIGN}_{os.getpid()}", userdata=client_userdata, transport=psk_transport_protocol)
    psk_client.on_connect = on_connect_psk; psk_client.on_message = on_message_psk; psk_client.on_disconnect = on_disconnect
    psk_client.reconnect_delay_set(min_delay=5, max_delay=120)
    if use_tls:
        print("INFO: Configuring TLS for PSK Reporter connection.")
        try:
            psk_client.tls_set()
            if PSK_TLS_INSECURE: print("\n*** WARNING: TLS certificate verification is DISABLED! Connection is insecure! ***\n"); psk_client.tls_insecure_set(True)
        except Exception as tls_e: print(f"FATAL: Failed to configure TLS: {tls_e}"); sys.exit(1)

    ha_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f"ha_psk_bridge_{MY_CALLSIGN}_{os.getpid()}")
    ha_client.on_connect = on_connect_ha; ha_client.on_disconnect = on_disconnect
    if HA_MQTT_USER and HA_MQTT_PASS: ha_client.username_pw_set(HA_MQTT_USER, HA_MQTT_PASS); print("INFO: Using username/password for HA MQTT connection.")
    ha_client.reconnect_delay_set(min_delay=5, max_delay=120)

    try:
        print(f"INFO: Attempting to connect to PSK Reporter Broker ({PSK_BROKER}:{psk_port})...")
        psk_client.connect(PSK_BROKER, psk_port, 60)
        print(f"INFO: Attempting to connect to Home Assistant Broker ({HA_MQTT_BROKER}:{HA_MQTT_PORT})...")
        ha_client.connect(HA_MQTT_BROKER, HA_MQTT_PORT, 60)
    except Exception as e: print(f"FATAL: Could not initiate connection to MQTT broker(s): {e}"); traceback.print_exc(); sys.exit(1)

    psk_client.loop_start(); ha_client.loop_start()

    print("INFO: Waiting for initial MQTT connections...")
    initial_connect_timeout = 30; start_wait = time.time()
    while time.time() - start_wait < initial_connect_timeout:
         if psk_client.is_connected() and ha_client.is_connected(): print("INFO: Both clients connected."); break
         if stop_event.is_set(): print("INFO: Shutdown requested during initial connection wait."); sys.exit(1)
         time.sleep(0.5)
    else: # Timeout
         print("FATAL: Timed out waiting for initial MQTT connection(s).")
         if not psk_client.is_connected(): print(f"FATAL: PSK Reporter client failed to connect.")
         if not ha_client.is_connected(): print(f"FATAL: Home Assistant client failed to connect.")
         stop_event.set(); sys.exit(1)

    print(f"INFO: Scheduling first stats update in {STATS_UPDATE_INTERVAL_SECONDS} seconds.")
    stats_timer = threading.Timer(STATS_UPDATE_INTERVAL_SECONDS, update_band_stats_task)
    stats_timer.daemon = True; stats_timer.start()

    try:
        while not stop_event.is_set(): time.sleep(5)
    except KeyboardInterrupt: print("\nINFO: KeyboardInterrupt received. Shutting down gracefully...")
    except Exception as e: print(f"ERROR: An unexpected error occurred in main loop: {e}"); traceback.print_exc()
    finally:
        print("INFO: Setting stop event for threads..."); stop_event.set()
        print("INFO: Stopping periodic timer...");
        if stats_timer and stats_timer.is_alive(): stats_timer.cancel()
        print("INFO: Stopping MQTT loops (this may take a moment)...")
        psk_client.loop_stop(); ha_client.loop_stop()
        print("INFO: Disconnecting MQTT clients...")
        try:
            if psk_client.is_connected(): psk_client.disconnect()
        except Exception as de: print(f"Error disconnecting PSK client: {de}")
        try:
            if ha_client.is_connected(): ha_client.disconnect()
        except Exception as de: print(f"Error disconnecting HA client: {de}")
        print("INFO: Script finished.")

# --- End of Script ---
