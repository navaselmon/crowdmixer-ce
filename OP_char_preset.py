# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import json
import os
import bpy
from copy import deepcopy
from .system_var import *
from .OP_common import cmx_set_progress_task
from .OP_preview import cmx_shader_selector, cmx_char_preview_item
from .OP_update_prop import *

CMX_BUILD_STATE_NEVER = "never"
CMX_BUILD_STATE_BUILT = "built"
CMX_BUILD_STATE_DIRTY = "dirty"
CMX_BUILD_STATES = {CMX_BUILD_STATE_NEVER, CMX_BUILD_STATE_BUILT, CMX_BUILD_STATE_DIRTY}
CMX_BUILD_VERSION_4 = "blender_4"
CMX_BUILD_VERSION_5 = "blender_5"
CMX_BUILD_VERSION_KEYS = (CMX_BUILD_VERSION_4, CMX_BUILD_VERSION_5)

def _cmx_request_ui_redraw():
    """Best-effort UI refresh for preset panels."""
    try:
        for area in bpy.context.screen.areas:
            area.tag_redraw()
    except Exception:
        pass

def cmx_get_current_build_version_key():
    """Return the build-state key for the current Blender major version."""
    try:
        major_version = int(bpy.app.version[0])
    except Exception:
        major_version = 0
    return CMX_BUILD_VERSION_5 if major_version >= 5 else CMX_BUILD_VERSION_4

def cmx_get_default_build_states(default_state=CMX_BUILD_STATE_NEVER):
    """Return the default per-version build-state map."""
    state = default_state if default_state in CMX_BUILD_STATES else CMX_BUILD_STATE_NEVER
    return {
        CMX_BUILD_VERSION_4: state,
        CMX_BUILD_VERSION_5: state,
    }

def _cmx_cache_build_states(collection_name, build_states):
    """Update in-memory build-state cache for every Blender version bucket."""
    for version_key in CMX_BUILD_VERSION_KEYS:
        PRESET_BUILD_STATUS[(collection_name, version_key)] = build_states.get(version_key, CMX_BUILD_STATE_NEVER)

def _cmx_normalize_build_states(meta):
    """Normalize per-version build states from legacy and current metadata."""
    legacy_state = meta.get("build_state")
    if legacy_state not in CMX_BUILD_STATES:
        legacy_state = CMX_BUILD_STATE_BUILT if bool(meta.get("build", False)) else CMX_BUILD_STATE_NEVER

    raw_states = meta.get("build_states")
    if not isinstance(raw_states, dict):
        raw_states = {}

    build_states = {}
    for version_key in CMX_BUILD_VERSION_KEYS:
        version_state = raw_states.get(version_key, legacy_state)
        if version_state not in CMX_BUILD_STATES:
            version_state = legacy_state
        build_states[version_key] = version_state
    return build_states

def _cmx_store_collection_build_states(collection_name, build_states):
    """Persist normalized build states and refresh cache/UI."""
    if not collection_name:
        return

    normalized_states = {}
    for version_key in CMX_BUILD_VERSION_KEYS:
        state = build_states.get(version_key, CMX_BUILD_STATE_NEVER)
        if state not in CMX_BUILD_STATES:
            state = CMX_BUILD_STATE_NEVER
        normalized_states[version_key] = state

    current_version_key = cmx_get_current_build_version_key()
    data = _cmx_load_char_preset_raw()
    record = _cmx_normalize_collection_record(data.get(collection_name))
    record["__meta"]["build_states"] = normalized_states
    record["__meta"]["build_state"] = normalized_states[current_version_key]
    record["__meta"]["build"] = (record["__meta"]["build_state"] == CMX_BUILD_STATE_BUILT)
    data[collection_name] = record
    _cmx_cache_build_states(collection_name, normalized_states)
    try:
        _cmx_save_char_preset_raw(data)
        _cmx_request_ui_redraw()
    except Exception:
        pass

# ----------------------- helper: file IO and normalization -----------------------
def _cmx_load_char_preset_raw():
    file_path = os.path.join(CURRENT_DIRECTORY, "CMX_Data", "char_preset.json")
    if not os.path.exists(file_path):
        return {}
    with open(file_path, "r") as f:
        try:
            return json.load(f)
        except Exception:
            return {}

def _cmx_save_char_preset_raw(data):
    file_path = os.path.join(CURRENT_DIRECTORY, "CMX_Data", "char_preset.json")
    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)

def cmx_load_char_preset_raw():
    """Public wrapper to load raw char preset json data."""
    return _cmx_load_char_preset_raw()

def cmx_save_char_preset_raw(data):
    """Public wrapper to save raw char preset json data."""
    return _cmx_save_char_preset_raw(data)

def _cmx_normalize_collection_record(raw):
    """
    Ensure collection record has structure:
    {"__meta": {"build": bool, "build_state": str, "build_states": {...}}, "presets": {...}}
    Accepts legacy dict without __meta/presets and wraps it.
    """
    def _normalize_meta(meta):
        normalized_meta = dict(meta or {})
        build_states = _cmx_normalize_build_states(normalized_meta)
        current_state = build_states[cmx_get_current_build_version_key()]
        normalized_meta["build_states"] = build_states
        normalized_meta["build_state"] = current_state
        normalized_meta["build"] = (current_state == CMX_BUILD_STATE_BUILT)
        return normalized_meta

    if isinstance(raw, dict) and "__meta" in raw and "presets" in raw:
        raw["__meta"] = _normalize_meta(raw.get("__meta"))
        raw["presets"] = raw.get("presets") or {}
        return raw
    if isinstance(raw, dict):
        return {"__meta": _normalize_meta({}), "presets": raw}
    return {"__meta": _normalize_meta({}), "presets": {}}

def cmx_normalize_collection_record(raw):
    """Public wrapper for normalization helper."""
    return _cmx_normalize_collection_record(raw)

def cmx_get_collection_build_status(collection_name, version_key=None):
    """Return build status for a preset collection in the requested Blender version bucket."""
    if not collection_name:
        return CMX_BUILD_STATE_NEVER

    version_key = version_key or cmx_get_current_build_version_key()
    cache_key = (collection_name, version_key)
    cached = PRESET_BUILD_STATUS.get(cache_key)
    if cached in CMX_BUILD_STATES:
        return cached

    data = _cmx_load_char_preset_raw()
    record = _cmx_normalize_collection_record(data.get(collection_name))
    build_states = record.get("__meta", {}).get("build_states", cmx_get_default_build_states())
    _cmx_cache_build_states(collection_name, build_states)
    state = build_states.get(version_key, CMX_BUILD_STATE_NEVER)
    return state

def _cmx_set_collection_build_status(collection_name, state, version_key=None):
    """Update build status for one Blender version bucket and persist it."""
    if not collection_name:
        return
    version_key = version_key or cmx_get_current_build_version_key()

    data = _cmx_load_char_preset_raw()
    record = _cmx_normalize_collection_record(data.get(collection_name))
    build_states = dict(record.get("__meta", {}).get("build_states", cmx_get_default_build_states()))
    build_states[version_key] = state if state in CMX_BUILD_STATES else CMX_BUILD_STATE_NEVER
    _cmx_store_collection_build_states(collection_name, build_states)

def cmx_mark_collection_built(collection_name):
    """Mark a preset collection as built for the current Blender version bucket."""
    _cmx_set_collection_build_status(collection_name, CMX_BUILD_STATE_BUILT, cmx_get_current_build_version_key())

def cmx_mark_collection_dirty(collection_name):
    """Mark a preset collection as needing rebuild in every Blender version bucket.

    Transition rule:
    - built -> dirty
    - dirty -> dirty
    - never -> never
    """
    if not collection_name:
        return

    data = _cmx_load_char_preset_raw()
    record = _cmx_normalize_collection_record(data.get(collection_name))
    current_states = dict(record.get("__meta", {}).get("build_states", cmx_get_default_build_states()))
    next_states = {}
    for version_key in CMX_BUILD_VERSION_KEYS:
        current_state = current_states.get(version_key, CMX_BUILD_STATE_NEVER)
        if current_state == CMX_BUILD_STATE_BUILT:
            next_states[version_key] = CMX_BUILD_STATE_DIRTY
        elif current_state == CMX_BUILD_STATE_DIRTY:
            next_states[version_key] = CMX_BUILD_STATE_DIRTY
        else:
            next_states[version_key] = CMX_BUILD_STATE_NEVER
    _cmx_store_collection_build_states(collection_name, next_states)

def cmx_remove_collection_status(collection_name):
    """Remove status entry for a deleted collection."""
    if not collection_name:
        return
    for version_key in CMX_BUILD_VERSION_KEYS:
        PRESET_BUILD_STATUS.pop((collection_name, version_key), None)
    data = _cmx_load_char_preset_raw()
    if collection_name in data:
        record = _cmx_normalize_collection_record(data[collection_name])
        record["__meta"]["build_states"] = cmx_get_default_build_states()
        record["__meta"]["build_state"] = CMX_BUILD_STATE_NEVER
        record["__meta"]["build"] = False
        data[collection_name] = record
    try:
        _cmx_save_char_preset_raw(data)
    except Exception:
        pass

def cmx_get_collections(self, context):
    """Return a list of all collection names in char_preset.json for EnumProperty."""
    data = _cmx_load_char_preset_raw()
    return [(col, col, "") for col in data.keys()]

def cmx_get_preset_collection_order(context):
    """Return current collection order from the UI list."""
    wm = context.window_manager
    return [item.collection for item in wm.preset_items if not item.is_preset]

def cmx_reorder_preset_collection_data(data, ordered_collections=None):
    """Return a dict reordered to match ordered_collections, keeping unknown keys at the end."""
    if not ordered_collections:
        return data

    reordered = {}
    for collection_name in ordered_collections:
        if collection_name in data:
            reordered[collection_name] = data[collection_name]
    for collection_name, value in data.items():
        if collection_name not in reordered:
            reordered[collection_name] = value
    return reordered

def cmx_sort_presets_in_collection_record(record):
    """Return a normalized collection record with presets sorted alphabetically."""
    normalized = _cmx_normalize_collection_record(deepcopy(record))
    presets = normalized.get("presets", {})
    normalized["presets"] = {
        preset_name: presets[preset_name]
        for preset_name in sorted(presets.keys(), key=str.casefold)
    }
    return normalized

def cmx_load_preset_List_data(context, ordered_collections=None, expanded_states_override=None):
    """Load all preset collections and their presets to WindowManager.preset_items."""
    wm = context.window_manager

    if isinstance(expanded_states_override, dict):
        expanded_states = dict(expanded_states_override)
    else:
        expanded_states = {item.collection: item.expanded for item in wm.preset_items if not item.is_preset}
    current_order = [item.collection for item in wm.preset_items if not item.is_preset]
    wm.preset_items.clear()

    data = _cmx_load_char_preset_raw()
    data = cmx_reorder_preset_collection_data(data, ordered_collections or current_order)
    changed = False
    for collection, raw_record in data.items():
        record = _cmx_normalize_collection_record(raw_record)
        if record != raw_record:
            changed = True
        _cmx_cache_build_states(collection, record.get("__meta", {}).get("build_states", cmx_get_default_build_states()))

        collection_item = wm.preset_items.add()
        collection_item.collection = collection
        collection_item.is_preset = False
        collection_item.expanded = expanded_states.get(collection, False)

        if collection_item.expanded:
            presets = record.get("presets", {})
            for preset, values in presets.items():
                vcopy = deepcopy(values)
                if "mesh_mode" not in vcopy:
                    vcopy["mesh_mode"] = "SINGLE"
                preset_item = wm.preset_items.add()
                preset_item.collection = collection
                preset_item.preset = preset
                preset_item.is_preset = True
                preset_item.data = f"{vcopy}"
        data[collection] = record
    if changed:
        try:
            _cmx_save_char_preset_raw(data)
        except Exception:
            pass
    return {'FINISHED'}

def cmx_get_preset_data(coll_name, preset_name):
    """Return preset data (dict) for a given collection and preset name."""
    preset_data = None
    if coll_name and preset_name:
        data = _cmx_load_char_preset_raw()
        record = _cmx_normalize_collection_record(data.get(coll_name))
        presets = record.get("presets", {})
        if preset_name in presets:
            preset_data = deepcopy(presets[preset_name])
            if "mesh_mode" not in preset_data:
                preset_data["mesh_mode"] = "SINGLE"
    return preset_data

def cmx_get_preset_collection_data(coll_name):
    """Return all preset data for a given collection."""
    preset_data = None
    if coll_name:
        data = _cmx_load_char_preset_raw()
        record = _cmx_normalize_collection_record(data.get(coll_name))
        preset_data = record.get("presets", {})
    return preset_data

def cmx_unload_preset_list_data(context):
    """Clear all WindowManager.preset_items."""
    wm = context.window_manager
    wm.preset_items.clear()
    return {'FINISHED'}

def cmx_set_char_to_preset(context, preset_data):
    """Apply a preset dict to WindowManager and all relevant runtime structures."""
    wm = context.window_manager   
    cmx_set_progress_task("Load Preset")
    
    mesh_mode = "SINGLE"
    if wm.cf_mesh_mode != "SINGLE":
        wm.cf_mesh_mode = "SINGLE"

    char_name = preset_data["Char_name"]
    items = cmx_char_preview_item(None, context)
    if items:
        ids = [it[0] for it in items]
        if char_name not in ids:
            char_name = ids[0]
    wm.char_previews = char_name

    action = preset_data.get("Action")
    action_filter = preset_data.get("Action_Filter")
    if action and action_filter:
        if not wm.anim_use_toggle:
            wm.anim_use_toggle = True
        context.window_manager.anim_filter = action_filter
        anim_val = f"{action_filter}.{action}"
        enum_items = [item[0] for item in cmx_anim_preview_item(None, context)]
        if anim_val in enum_items:
            context.window_manager.anim_previews = anim_val
    else:
        wm.anim_use_toggle = False
    return {'FINISHED'}


