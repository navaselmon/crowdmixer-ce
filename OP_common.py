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

import bpy
import json
import os
import webbrowser
from copy import deepcopy
from .system_var import *

def cmx_request_ui_redraw(delay=0.0, swap=False):
    """Request a full UI redraw, optionally on the next UI tick."""
    def _redraw():
        wm = getattr(bpy.context, "window_manager", None)
        if wm:
            for window in wm.windows:
                screen = getattr(window, "screen", None)
                if not screen:
                    continue
                for area in screen.areas:
                    area.tag_redraw()
        if swap:
            try:
                bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)
            except Exception:
                pass
        return None

    if delay and delay > 0.0:
        bpy.app.timers.register(_redraw, first_interval=float(delay))
        return
    _redraw()

def cmx_show_message_box(message="", title="Message Box", icon='INFO'):
    """Show a message popup in Blender."""
    def draw(self, context):
        self.layout.label(text=message)
    bpy.context.window_manager.popup_menu(draw, title=title, icon=icon)
    cmx_request_ui_redraw(swap=True)
    cmx_request_ui_redraw(delay=0.05, swap=True)

def cmx_show_message_box_deferred(message="", title="Message Box", icon='INFO', delay=0.01):
    """Show a popup on the next UI tick to avoid blocking property update callbacks."""
    def _show_popup():
        try:
            cmx_show_message_box(message=message, title=title, icon=icon)
        except Exception:
            return None
        return None
    bpy.app.timers.register(_show_popup, first_interval=max(0.0, float(delay)))

def cmx_get_dir_asset_path():
    """Get asset directory path from add-on preferences."""
    addon_prefs = cmx_get_addon_preferences()
    return addon_prefs.folder_path if addon_prefs else ""


def cmx_get_addon_preferences(context=None):
    """Return addon preferences when available."""
    context = context or bpy.context
    try:
        addon_name = __package__ or "CrowdMixer"
        return context.preferences.addons[addon_name].preferences
    except Exception:
        return None


def cmx_get_popup_preview_size(context=None):
    """Return the configured popup preview size from addon preferences."""
    addon_prefs = cmx_get_addon_preferences(context)
    if addon_prefs is not None:
        try:
            return int(getattr(addon_prefs, "popup_preview_size", 5))
        except Exception:
            pass
    return 5

def cmx_get_blender_source_bucket():
    """Return the source-library bucket for the current Blender major version."""
    try:
        major_version = int(bpy.app.version[0])
    except Exception:
        major_version = 0
    return "Blender-5" if major_version >= 5 else "Blender-4"

def cmx_get_source_dir(create_if_missing=True):
    """
    Get absolute path to the version-specific CMX-Source folder under the asset root.
    Returns None if asset path is not set. Creates the folder if requested.
    """
    base_dir = cmx_get_dir_asset_path()
    if not base_dir:
        return None
    source_dir = os.path.join(base_dir, "CMX-Source", cmx_get_blender_source_bucket())
    if create_if_missing and not os.path.isdir(source_dir):
        try:
            os.makedirs(source_dir, exist_ok=True)
        except Exception:
            return None
    return source_dir

def cmx_get_asset_dir_by_mode():
    """
    Get the asset directory for the Lite character library.
    """
    base_dir = cmx_get_dir_asset_path()
    if not base_dir:
        return None
    return os.path.join(base_dir, "CMX-Single-Mesh")

def cmx_get_single_mesh_filter_dirs(base_dir):
    """Return top-level subfolder names under CMX-Single-Mesh."""
    if not base_dir or not os.path.isdir(base_dir):
        return []
    dirs = []
    for name in sorted(os.listdir(base_dir)):
        full = os.path.join(base_dir, name)
        if os.path.isdir(full):
            dirs.append(name)
    return dirs

def cmx_build_character_maps(base_dir):
    """
    Scan character files and build maps for blend/json/png paths.
    Supports nested folders for Single-Mesh assets.
    """
    blend_paths = {}
    json_paths = {}
    png_paths = {}
    category_map = {}
    if not base_dir or not os.path.isdir(base_dir):
        return blend_paths, json_paths, png_paths, category_map

    for root, _, files in os.walk(base_dir):
        rel = os.path.relpath(root, base_dir)
        top_folder = "" if rel in {".", ""} else rel.split(os.sep)[0]
        for fn in files:
            lower = fn.lower()
            name, ext = os.path.splitext(fn)
            full = os.path.join(root, fn)
            if lower.endswith(".blend"):
                blend_paths[name] = full
                category_map[name] = top_folder
            elif lower.endswith(".json"):
                # prefer json in same folder as blend if available later
                if name not in json_paths or top_folder:
                    json_paths[name] = full
            elif lower.endswith(".png"):
                if name not in png_paths or top_folder:
                    png_paths[name] = full

    # Fallback json/png next to blend or at base root
    for char_name, blend_path in blend_paths.items():
        blend_dir = os.path.dirname(blend_path)
        base_json = os.path.join(base_dir, f"{char_name}.json")
        near_json = os.path.join(blend_dir, f"{char_name}.json")
        if os.path.exists(near_json):
            json_paths[char_name] = near_json
        elif os.path.exists(base_json) and char_name not in json_paths:
            json_paths[char_name] = base_json

        base_png = os.path.join(base_dir, f"{char_name}.png")
        near_png = os.path.join(blend_dir, f"{char_name}.png")
        if os.path.exists(near_png):
            png_paths[char_name] = near_png
        elif os.path.exists(base_png) and char_name not in png_paths:
            png_paths[char_name] = base_png

    return blend_paths, json_paths, png_paths, category_map

def cmx_refresh_character_maps_and_list(context):
    """
    Refresh CHAR_LIST and character file maps from the Single-Mesh library.
    """
    wm = context.window_manager
    base_dir = cmx_get_asset_dir_by_mode()

    CHAR_LIST.clear()
    CHAR_BLEND_PATHS.clear()
    CHAR_JSON_PATHS.clear()
    CHAR_PNG_PATHS.clear()
    CHAR_CATEGORY.clear()

    if not base_dir or not os.path.isdir(base_dir):
        return []

    blend_paths, json_paths, png_paths, category_map = cmx_build_character_maps(base_dir)
    CHAR_BLEND_PATHS.update(blend_paths)
    CHAR_JSON_PATHS.update(json_paths)
    CHAR_PNG_PATHS.update(png_paths)
    CHAR_CATEGORY.update(category_map)

    selected = []
    available_filters = cmx_get_single_mesh_filter_dirs(base_dir)
    current_filter = getattr(wm, "single_char_filter", "All")
    if current_filter != "All" and current_filter not in available_filters:
        current_filter = "All"
        try:
            wm.single_char_filter = "All"
        except Exception:
            pass
    for name in sorted(CHAR_BLEND_PATHS.keys()):
        if current_filter == "All" or CHAR_CATEGORY.get(name, "") == current_filter:
            selected.append(name)
    if not selected and current_filter != "All":
        try:
            wm.single_char_filter = "All"
        except Exception:
            pass
        selected = sorted(CHAR_BLEND_PATHS.keys())

    active_name = ACTIVE_CHAR.get("Char_name")
    for char_name in selected:
        if char_name == active_name:
            CHAR_LIST.insert(0, char_name)
        else:
            CHAR_LIST.append(char_name)
        CMX_PUB_VAR["Default_Pose"][char_name] = None

    return CHAR_LIST

def cmx_get_character_blend_path(char_name):
    """Get absolute .blend path for a character name in current mode."""
    if not char_name:
        return None
    path = CHAR_BLEND_PATHS.get(char_name)
    if path and os.path.exists(path):
        return path
    base_dir = cmx_get_asset_dir_by_mode()
    if not base_dir:
        return None
    fallback = os.path.join(base_dir, f"{char_name}.blend")
    if os.path.exists(fallback):
        return fallback
    for root, _, files in os.walk(base_dir):
        target = f"{char_name}.blend"
        if target in files:
            return os.path.join(root, target)
    return None

def cmx_get_character_json_path(char_name):
    """Get absolute .json path for a character name in current mode."""
    if not char_name:
        return None
    path = CHAR_JSON_PATHS.get(char_name)
    if path and os.path.exists(path):
        return path
    base_dir = cmx_get_asset_dir_by_mode()
    if not base_dir:
        return None
    fallback = os.path.join(base_dir, f"{char_name}.json")
    if os.path.exists(fallback):
        return fallback
    for root, _, files in os.walk(base_dir):
        target = f"{char_name}.json"
        if target in files:
            return os.path.join(root, target)
    return None

def cmx_get_character_png_path(char_name):
    """Get absolute .png path for a character name in current mode."""
    if not char_name:
        return None
    path = CHAR_PNG_PATHS.get(char_name)
    if path and os.path.exists(path):
        return path
    base_dir = cmx_get_asset_dir_by_mode()
    if not base_dir:
        return None
    fallback = os.path.join(base_dir, f"{char_name}.png")
    if os.path.exists(fallback):
        return fallback
    for root, _, files in os.walk(base_dir):
        target = f"{char_name}.png"
        if target in files:
            return os.path.join(root, target)
    return None

def cmx_get_setting_file_path():
    """Return the customize settings JSON path, creating CMX_Data if needed."""
    data_dir = os.path.join(CURRENT_DIRECTORY, "CMX_Data")
    os.makedirs(data_dir, exist_ok=True)
    return os.path.join(data_dir, "cf_setting.json")

def _cmx_normalize_mesh_mode(mesh_mode):
    return "SINGLE"

def _cmx_get_modular_snapshot_keys():
    keys = {"Char_name", "cloth_filter"}
    for body_part in BODY_PART:
        keys.add(body_part)
        keys.add(f"{body_part}_Color")
        keys.add(f"{body_part}_Shader")
    return keys

def _cmx_get_single_snapshot_keys():
    return {"Char_name", "Action", "Action_Filter", "single_char_filter"}

def _cmx_default_active_char_state():
    state = {
        "Action": None,
        "Action_Filter": None,
        "Char_name": None,
    }
    for prev in PREVIEW_LIST:
        state[prev] = None
    return state

def _cmx_default_animation_state():
    return {
        "enabled": False,
        "anim_filter": "",
        "anim_preview": "",
        "action": None,
        "action_filter": None,
        "set_frame_range": True,
    }

def _cmx_normalize_mode_snapshot(mode, raw_snapshot=None):
    normalized_mode = _cmx_normalize_mesh_mode(mode)
    snapshot = {"mesh_mode": normalized_mode}
    if normalized_mode == "SINGLE":
        snapshot["single_char_filter"] = "All"

    if isinstance(raw_snapshot, dict):
        allowed_keys = (
            _cmx_get_single_snapshot_keys()
            if normalized_mode == "SINGLE"
            else _cmx_get_modular_snapshot_keys()
        )
        for key, value in deepcopy(raw_snapshot).items():
            if key in allowed_keys:
                snapshot[key] = value

    if normalized_mode == "SINGLE":
        snapshot["single_char_filter"] = snapshot.get("single_char_filter") or "All"
    return snapshot

def _cmx_normalize_animation_state(raw_state=None):
    state = _cmx_default_animation_state()
    if isinstance(raw_state, dict):
        for key in state.keys():
            if key in raw_state:
                state[key] = deepcopy(raw_state[key])
    state["enabled"] = bool(state.get("enabled"))
    state["anim_filter"] = str(state.get("anim_filter") or "")
    state["anim_preview"] = str(state.get("anim_preview") or "")
    state["action_filter"] = state.get("action_filter") or None
    state["action"] = state.get("action") or None
    state["set_frame_range"] = bool(state.get("set_frame_range", True))
    return state

def _cmx_default_setting_data():
    return {
        "version": 2,
        "last_mesh_mode": "SINGLE",
        "animation": _cmx_default_animation_state(),
        "modes": {
            "SINGLE": _cmx_normalize_mode_snapshot("SINGLE", {"mesh_mode": "SINGLE", "single_char_filter": "All"}),
        },
    }

def cmx_load_setting_data():
    """Load and normalize customize settings for both mesh modes."""
    file_path = cmx_get_setting_file_path()
    default_data = _cmx_default_setting_data()

    if not os.path.exists(file_path):
        return default_data

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            raw_data = json.load(file)
    except Exception:
        return default_data

    if not isinstance(raw_data, dict):
        return default_data

    # Legacy format: a single ACTIVE_CHAR-like dict saved at the root.
    if "modes" not in raw_data:
        legacy_mode = _cmx_normalize_mesh_mode(raw_data.get("mesh_mode", "SINGLE"))
        default_data["last_mesh_mode"] = legacy_mode
        default_data["modes"][legacy_mode] = _cmx_normalize_mode_snapshot(legacy_mode, raw_data)
        if legacy_mode == "SINGLE" and "single_char_filter" in raw_data:
            default_data["modes"]["SINGLE"]["single_char_filter"] = raw_data.get("single_char_filter") or "All"
        default_data["animation"] = _cmx_normalize_animation_state({
            "enabled": bool(raw_data.get("Action")),
            "anim_filter": raw_data.get("Action_Filter") or "",
            "anim_preview": f'{raw_data.get("Action_Filter")}.{raw_data.get("Action")}'
                            if raw_data.get("Action") and raw_data.get("Action_Filter") else "",
            "action": raw_data.get("Action"),
            "action_filter": raw_data.get("Action_Filter"),
            "set_frame_range": True,
        })
        return default_data

    normalized_data = _cmx_default_setting_data()
    normalized_data["version"] = raw_data.get("version", 2)
    normalized_data["last_mesh_mode"] = _cmx_normalize_mesh_mode(raw_data.get("last_mesh_mode", "SINGLE"))
    normalized_data["animation"] = _cmx_normalize_animation_state(raw_data.get("animation"))

    raw_modes = raw_data.get("modes", {})
    if not isinstance(raw_modes, dict):
        raw_modes = {}

    single_filter = raw_data.get("single_char_filter")
    single_mode_raw = raw_modes.get("SINGLE")
    if not isinstance(single_mode_raw, dict):
        single_mode_raw = raw_modes.get("MODULAR")
    if not isinstance(single_mode_raw, dict):
        single_mode_raw = {}
    normalized_data["modes"]["SINGLE"] = _cmx_normalize_mode_snapshot("SINGLE", single_mode_raw)
    if single_filter and not single_mode_raw.get("single_char_filter"):
        normalized_data["modes"]["SINGLE"]["single_char_filter"] = single_filter

    return normalized_data

def cmx_write_setting_data(setting_data):
    """Write normalized customize settings to disk."""
    normalized = _cmx_default_setting_data()
    if isinstance(setting_data, dict):
        normalized["version"] = setting_data.get("version", 2)
        normalized["last_mesh_mode"] = _cmx_normalize_mesh_mode(setting_data.get("last_mesh_mode", "SINGLE"))
        normalized["animation"] = _cmx_normalize_animation_state(setting_data.get("animation"))
        modes = setting_data.get("modes", {})
        if isinstance(modes, dict):
            single_mode = modes.get("SINGLE")
            if not isinstance(single_mode, dict):
                single_mode = modes.get("MODULAR")
            normalized["modes"]["SINGLE"] = _cmx_normalize_mode_snapshot("SINGLE", single_mode)

    file_path = cmx_get_setting_file_path()
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(normalized, file, indent=2, sort_keys=False)
    return normalized

def cmx_get_saved_mode_settings(mode, setting_data=None):
    """Return the saved customize snapshot for a mesh mode."""
    setting_data = setting_data or cmx_load_setting_data()
    modes = setting_data.get("modes", {})
    snapshot = modes.get("SINGLE", {})
    return _cmx_normalize_mode_snapshot(mode, snapshot)

def cmx_restore_active_char_state(snapshot, mode=None):
    """Replace ACTIVE_CHAR with a normalized saved snapshot."""
    normalized_mode = _cmx_normalize_mesh_mode(mode or (snapshot or {}).get("mesh_mode", "SINGLE"))
    runtime_state = _cmx_default_active_char_state()
    normalized_snapshot = _cmx_normalize_mode_snapshot(normalized_mode, snapshot)
    ACTIVE_CHAR.clear()
    ACTIVE_CHAR.update(runtime_state)
    ACTIVE_CHAR.update(normalized_snapshot)
    return ACTIVE_CHAR

def cmx_capture_mode_settings(context, mode=None):
    """Capture current ACTIVE_CHAR into a persistable snapshot for one mesh mode."""
    wm = context.window_manager
    normalized_mode = _cmx_normalize_mesh_mode(mode or getattr(wm, "cf_mesh_mode", "SINGLE"))
    snapshot = deepcopy(ACTIVE_CHAR) if isinstance(ACTIVE_CHAR, dict) else {}
    snapshot["mesh_mode"] = normalized_mode
    if normalized_mode == "SINGLE":
        snapshot["single_char_filter"] = getattr(wm, "single_char_filter", "All") or "All"
    return _cmx_normalize_mode_snapshot(normalized_mode, snapshot)

def cmx_has_saved_mode_settings(snapshot):
    """Return True when a saved snapshot contains enough data to reapply."""
    return bool(isinstance(snapshot, dict) and snapshot.get("Char_name"))

def cmx_capture_animation_settings(context):
    """Capture current animation UI/runtime state."""
    wm = context.window_manager
    anim_filter = str(getattr(wm, "anim_filter", "") or "")
    anim_preview = str(getattr(wm, "anim_previews", "") or "")
    action = ACTIVE_CHAR.get("Action")
    action_filter = ACTIVE_CHAR.get("Action_Filter") or anim_filter or None
    if not action and anim_preview and "." in anim_preview:
        _, action = anim_preview.split(".", 1)
    return _cmx_normalize_animation_state({
        "enabled": bool(getattr(wm, "anim_use_toggle", False)),
        "anim_filter": anim_filter,
        "anim_preview": anim_preview,
        "action": action,
        "action_filter": action_filter,
        "set_frame_range": bool(getattr(wm, "set_frame_range_toggle", True)),
    })

def cmx_get_saved_animation_settings(setting_data=None):
    """Return saved animation state."""
    setting_data = setting_data or cmx_load_setting_data()
    return _cmx_normalize_animation_state(setting_data.get("animation"))

def cmx_store_animation_settings(context, setting_data=None):
    """Save current animation state into the customize settings file."""
    setting_data = deepcopy(setting_data) if isinstance(setting_data, dict) else cmx_load_setting_data()
    setting_data["animation"] = cmx_capture_animation_settings(context)
    return cmx_write_setting_data(setting_data)

def cmx_restore_animation_settings(context, animation_state=None):
    """Restore animation UI/runtime state after character loading."""
    from .OP_preview import cmx_anim_preview_item

    wm = context.window_manager
    saved = _cmx_normalize_animation_state(animation_state)
    target_enabled = bool(saved.get("enabled"))

    if bool(getattr(wm, "anim_use_toggle", False)) and not target_enabled:
        wm.anim_use_toggle = False

    wm.set_frame_range_toggle = bool(saved.get("set_frame_range", True))

    target_filter = saved.get("anim_filter") or saved.get("action_filter") or ""
    if target_filter and target_filter in ANIMATION_FILTER:
        wm.anim_filter = target_filter
    elif ANIMATION_FILTER:
        wm.anim_filter = ANIMATION_FILTER[0]

    desired_preview = saved.get("anim_preview") or ""
    action = saved.get("action")
    action_filter = saved.get("action_filter") or getattr(wm, "anim_filter", "")
    if not desired_preview and action and action_filter:
        desired_preview = f"{action_filter}.{action}"

    enum_items = [item[0] for item in cmx_anim_preview_item(None, context)]
    if desired_preview in enum_items:
        wm.anim_previews = desired_preview
    elif enum_items:
        wm.anim_previews = enum_items[0]

    if target_enabled and getattr(wm, "anim_previews", ""):
        if not wm.anim_use_toggle:
            wm.anim_use_toggle = True
    elif wm.anim_use_toggle:
        wm.anim_use_toggle = False

def cmx_store_mode_settings(context, mode=None, last_mesh_mode=None):
    """Merge the current mode snapshot into the customize settings file."""
    normalized_mode = _cmx_normalize_mesh_mode(mode or context.window_manager.cf_mesh_mode)
    setting_data = cmx_load_setting_data()
    setting_data["modes"][normalized_mode] = cmx_capture_mode_settings(context, normalized_mode)
    setting_data["last_mesh_mode"] = _cmx_normalize_mesh_mode(last_mesh_mode or context.window_manager.cf_mesh_mode)
    setting_data["animation"] = cmx_capture_animation_settings(context)
    return cmx_write_setting_data(setting_data)

def cmx_save_setting_data(context=None):
    """Save the current customize state, preserving the other mesh mode snapshot."""
    context = context or bpy.context
    if not context or not getattr(context, "window_manager", None):
        return None
    if not ACTIVE_CHAR:
        return None
    return cmx_store_mode_settings(context)

def cmx_set_progress_info(information):
    """Legacy no-op: progress tab was removed from the UI."""
    return None

def cmx_trim_progress_text(text, max_length=28):
    """Trim progress text to fit the single-line progress tab."""
    text = str(text or "").strip()
    if max_length <= 0:
        return ""
    if len(text) <= max_length:
        return text
    if max_length <= 3:
        return text[:max_length]
    return text[:max_length - 3] + "..."

def cmx_format_progress_text(action, name="", max_length=28):
    """Build a short progress label for the compact progress tab."""
    action = cmx_trim_progress_text(action, max_length=max_length).strip()
    name = str(name or "").strip()
    if not name:
        return action
    prefix = f"{action}: "
    remain = max_length - len(prefix)
    if remain <= 0:
        return action
    return prefix + cmx_trim_progress_text(name, max_length=remain)

def cmx_set_progress_task(action, name="", max_length=28):
    """Legacy no-op: progress tab was removed from the UI."""
    return None

def cmx_set_progress_success(name=""):
    """Legacy no-op: progress tab was removed from the UI."""
    return None

def cmx_set_progress_success_deferred(delay=0.01):
    """Legacy no-op: progress tab was removed from the UI."""
    return None

def cmx_set_progress_error(name="", detail=""):
    """Legacy no-op: progress tab was removed from the UI."""
    return None

def cmx_sanitize_identifier(text):
    """Sanitize a string for Blender EnumProperty identifier."""
    if not isinstance(text, str):
        return ""
    s = text.replace(" ", "_")
    s = ''.join(c for c in s if c.isalnum() or c == '_')
    s = s.lower()
    return s

def cmx_check_asset_path(folder_path):
    if not folder_path or not os.path.isdir(folder_path):
        # print(f"Invalid or missing folder: {folder_path}")
        return False
            
    # 1. List .blend files recursively (supports Single-Mesh category subfolders)
    blend_files = []
    for root, _, files in os.walk(folder_path):
        for fn in files:
            if fn.lower().endswith(".blend"):
                blend_files.append((root, fn))
    if not blend_files:
        print("No .blend files found in folder.")
        return False
    errors = []

    for root, blend_file in blend_files:
        base = os.path.splitext(blend_file)[0]
        json_file = base + ".json"
        json_path_same_dir = os.path.join(root, json_file)
        json_path_root = os.path.join(folder_path, json_file)
        json_path = json_path_same_dir if os.path.exists(json_path_same_dir) else json_path_root

        # 2. Check if json file exists
        if not os.path.exists(json_path):
            errors.append(f"JSON file missing for {blend_file}")
            continue

        # 3. Check JSON structure
        try:
            with open(json_path, "r", encoding="utf-8-sig") as f:
                data = json.load(f)
        except Exception as e:
            errors.append(f"Error loading JSON for {blend_file}: {e}")
            continue

        # 4. Check top-level keys
        missing_keys = [key for key in REQUIRED_KEYS if key not in data]
        if missing_keys:
            errors.append(f"Missing keys in {json_file}: {missing_keys}")

    if errors:
        print("Errors found:")
        for err in errors:
            print("-", err)
        return False
    else:
        print("All .blend files have matching .json with required structure.")
        return True

class CMXOpenHelpURLOperator(bpy.types.Operator):
    """Open the manual/help page in the browser."""
    bl_idname = "cmx.open_help_url"
    bl_label = "Open Help"
    bl_description = "Open the manual in the browser"

    url: bpy.props.StringProperty(default="")  # type: ignore

    def execute(self, context):
        webbrowser.open(self.url)
        self.report({'INFO'}, f"Opened URL: {self.url}")
        return {'FINISHED'}

classes = [
    CMXOpenHelpURLOperator
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
