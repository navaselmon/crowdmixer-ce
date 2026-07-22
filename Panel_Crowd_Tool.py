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
import os, json, random, time
from bpy.app.handlers import persistent
from .system_icon import *
from .system_var import *
from .OP_common import *
from .OP_crowd import *
from .OP_link_asset import *
from .enum_item_gen import *
from .OP_animation import *

CMX_ID_NAME_LIMIT = 63
CMX_SOURCE_SUFFIX_LIMIT = len("_PROXY")
CMX_DENSITY_MASK_NONE_LABEL = "none"
CMX_DENSITY_MASK_NONE_VALUE = ""
CMX_DENSITY_MASK_SOCKET_NAMES = {"density_mask", "Density Mask"}
CMX_DENSITY_SOCKET_NAMES = {"density", "Density"}
CMX_EMITTER_OBJECT_SOCKET_NAMES = {"emiter", "emitter", "emiter_object", "emitter_object", "Emitter Object"}
CMX_EMITTER_TYPE_SOCKET_NAMES = {"emiter_type", "emitter_type", "Emitter Type"}
CMX_EMITTER_PANEL_NAMES = {"EMITER", "EMITTER"}
CMX_GRID_SETTINGS_PANEL_NAMES = {"GRID_SETTINGS", "GRID_SETTING", "Grid Setting", "Grid Settings"}
CMX_INS_COUNT_OUTPUT_SOCKET_NAMES = {"cmx_ins_count", "CMX_INS_COUNT"}
CMX_EMITTER_TYPE_ITEMS = (("Grid", 0), ("Object", 1))
CMX_ON_POINT_SOCKET_NAMES = {"on_point", "On Point"}
CMX_STANDING_OBJECT_EMITTER_HIDDEN_SOCKET_NAMES = {
    "align_to_point", "Align To Point", "align_point", "Align Point"
}
CMX_GRID_EMITTER_HIDDEN_SOCKET_NAMES = (
    CMX_EMITTER_OBJECT_SOCKET_NAMES |
    CMX_DENSITY_MASK_SOCKET_NAMES |
    CMX_STANDING_OBJECT_EMITTER_HIDDEN_SOCKET_NAMES
)
CMX_PRIMARY_SOURCE_SOCKET_NAMES = {"source", "source_main", "source_standing", "source_sitting"}
CMX_ALL_SOURCE_SOCKET_NAMES = CMX_PRIMARY_SOURCE_SOCKET_NAMES | SOURCE_SCIKET_NAME
CMX_CROWD_PANEL_GROUPS = (
    ("Source", "cmx_crowd_group_source_expanded", ("SOURCE",)),
    ("Emitter", "cmx_crowd_group_emitter_expanded", (CMX_EMITTER_PANEL_NAMES,)),
    ("Placement", "cmx_crowd_group_placement_expanded", (CMX_GRID_SETTINGS_PANEL_NAMES, "TRANSFORMS", "AIM", "DISTRIBUTION", "ROUTE", "ROUTE_VARIATION", "FLOW", "GROUND", "FADE")),
    ("Variation", "cmx_crowd_group_variation_expanded", ("RANDOM", "COLOR_THEME")),
    ("Assets", "cmx_crowd_group_assets_expanded", ("ATTACHED_PROP", "EXCLUDE", "PRESET_ASSET", "BASE", "SEAT", "SEAT_ZONE", "ELEMENT")),
)
CMX_CROWD_PANEL_BOTTOM_ORDER = ("COUNTER",)
CMX_STADIUM_CROWD_TYPE = "CMX_Stadium_Crowd"
CMX_STANDING_CROWD_TYPE = "CMX_Standing_Crowd"
CMX_EDIT_INSTANCE_SOCKET_NAMES = {"edit_instance", "Edit Instance"}
CMX_OVERRIDE_INFO_SOCKET_NAMES = {"cmx_override_info", "Override Info"}
CMX_SELECT_INDEX_SOCKET_NAMES = {"cmx_select_index", "Select Index"}
CMX_INS_VIS_ONLY_SELECT_SOCKET_NAMES = {"ins_vis_only_select", "Ins Vis Only Select", "Instance Visible Only Select"}
CMX_INSTANCE_OVERRIDE_PANEL_NAMES = {
    "INS_OVERRIDE",
    "INS OVERRIDE",
    "INSTANCE_OVERRIDE",
    "INSTANCE OVERRIDE",
    "Instance Override",
    "Instance Override Mode",
    "Override",
    "Overrides",
}
CMX_EDIT_INSTANCE_RUNTIME_SOCKET_NAMES = (
    CMX_EDIT_INSTANCE_SOCKET_NAMES |
    CMX_OVERRIDE_INFO_SOCKET_NAMES |
    CMX_SELECT_INDEX_SOCKET_NAMES |
    CMX_INS_VIS_ONLY_SELECT_SOCKET_NAMES
)
CMX_INDEX_ATTRIBUTE_NAMES = ("cmx_index",)
CMX_ORIGINAL_INSTANCE_ATTRIBUTE_NAMES = ("cmx_original_ins_index",)
CMX_ORIGINAL_VIS_ATTRIBUTE_NAMES = ("cmx_original_ins_vis",)
CMX_ORIGINAL_POS_ATTRIBUTE_NAMES = ("cmx_original_ins_pos",)
CMX_ORIGINAL_ROT_ATTRIBUTE_NAMES = ("cmx_original_ins_rot",)
CMX_ORIGINAL_SCALE_ATTRIBUTE_NAMES = ("cmx_original_ins_scale",)
CMX_ORIGINAL_SPEED_ATTRIBUTE_NAMES = ("cmx_original_ins_ispeed",)
CMX_OVERRIDE_INDEX_ATTRIBUTE_NAMES = ("cmx_override_index",)
CMX_OVERRIDE_ON_ATTRIBUTE_NAMES = ("cmx_override_ins_on",)
CMX_OVERRIDE_VIS_ATTRIBUTE_NAMES = ("cmx_override_vis",)
CMX_OVERRIDE_POS_ATTRIBUTE_NAMES = ("cmx_override_pos",)
CMX_OVERRIDE_ROT_ATTRIBUTE_NAMES = ("cmx_override_rot",)
CMX_OVERRIDE_SCALE_ATTRIBUTE_NAMES = ("cmx_override_scale",)
CMX_OVERRIDE_SPEED_ATTRIBUTE_NAMES = ("cmx_override_speed",)
CMX_FLOW_CURVE_CROWD_TYPE = "CMX_Flow_Curve_Crowd"
CMX_EDIT_INSTANCE_ROOT_COLLECTION_NAME = "CMX_Edit_Instance"
CMX_EDIT_INSTANCE_PROXY_FLAG = "cmx_is_edit_instance_proxy"
CMX_EDIT_INSTANCE_PROXY_INDEX_PROP = "cmx_index"
CMX_EDIT_INSTANCE_PROXY_SLOT_PROP = "cmx_slot_index"
CMX_EDIT_INSTANCE_PROXY_ORIGINAL_PROP = "cmx_original_ins_index"
CMX_EDIT_INSTANCE_PROXY_CROWD_PROP = "cmx_crowd_item_name"
CMX_EDIT_INSTANCE_PROXY_CROWD_TYPE_PROP = "cmx_crowd_obj_name"
CMX_EDIT_INSTANCE_PREV_HIDE_SELECT_PROP = "cmx_edit_instance_prev_hide_select"
CMX_EMPTY_DISPLAY_ITEMS = (
    ('PLAIN_AXES', "Plain Axes", ""),
    ('ARROWS', "Arrows", ""),
    ('SINGLE_ARROW', "Single Arrow", ""),
    ('CIRCLE', "Circle", ""),
    ('CUBE', "Cube", ""),
    ('SPHERE', "Sphere", ""),
    ('CONE', "Cone", ""),
    ('IMAGE', "Image", ""),
)
CMX_EDIT_INSTANCE_POLL_INTERVAL = 0.15
CMX_EDIT_INSTANCE_TIMER_RUNNING = False
CMX_EDIT_INSTANCE_UI_SYNCING = False
CMX_VECTOR_COMPARE_EPSILON = 0.00001
CMX_VECTOR_ZERO = (0.0, 0.0, 0.0)
CMX_VECTOR_ONE = (1.0, 1.0, 1.0)
CMX_EDIT_INSTANCE_UI_SYNC_GRACE_SECONDS = 0.2
CMX_EDIT_INSTANCE_STATE_CACHE = {}
CMX_EDIT_INSTANCE_LAST_SELECTION = {}


def cmx_get_crowd_type_items(_self, _context):
    return [
        (CMX_FLOW_CURVE_CROWD_TYPE, "CMX-FlowCurve", "", get_cf_icon("CMX_Flow_Curve_Crowd"), 0),
        ("CMX_Stadium_Crowd", "CMX-Stadium", "", get_cf_icon("CMX_Stadium_Crowd"), 1),
        ("CMX_Standing_Crowd", "CMX-Standing", "", get_cf_icon("CMX_Standing_Crowd"), 2),
    ]


def _cmx_normalize_socket_name(value):
    return str(value or "").strip().casefold().replace(" ", "_")


def _cmx_socket_matches(item, socket_names):
    normalized_socket_names = {_cmx_normalize_socket_name(name) for name in socket_names}
    item_names = {
        _cmx_normalize_socket_name(getattr(item, "name", "")),
        _cmx_normalize_socket_name(getattr(item, "description", "")),
    }
    return bool(normalized_socket_names & item_names)


def _cmx_name_matches(value, names):
    normalized_names = {_cmx_normalize_socket_name(name) for name in names}
    return _cmx_normalize_socket_name(value) in normalized_names


def _cmx_get_edit_instance_root_collection(context):
    root_collection = bpy.data.collections.get(CMX_EDIT_INSTANCE_ROOT_COLLECTION_NAME)
    if not root_collection:
        root_collection = bpy.data.collections.new(CMX_EDIT_INSTANCE_ROOT_COLLECTION_NAME)
        context.scene.collection.children.link(root_collection)
    elif root_collection.name not in [child.name for child in context.scene.collection.children]:
        context.scene.collection.children.link(root_collection)
    return root_collection


def _cmx_get_override_object_name(crowd_name):
    return f"{crowd_name}_CMX_OverrideInfo"


def _cmx_get_proxy_collection_name(crowd_name):
    return f"{crowd_name}_CMX_EditProxy"


def _cmx_collection_exists(name):
    return bool(name and bpy.data.collections.get(name))


def _cmx_get_source_reserved_collection_names(source_name):
    source_name = (source_name or "").strip()
    if not source_name:
        return set()
    return {
        source_name,
        f"{source_name}_Instance",
    }


def _cmx_get_crowd_reserved_collection_names(crowd_name):
    crowd_name = (crowd_name or "").strip()
    if not crowd_name:
        return set()
    return {
        crowd_name,
    }


def _cmx_set_collection_tree_visibility(collection, visible):
    if not collection:
        return
    try:
        collection.hide_viewport = not visible
        collection.hide_render = not visible
    except Exception:
        pass
    for obj in list(getattr(collection, "objects", [])):
        try:
            obj.hide_viewport = not visible
            obj.hide_render = not visible
        except Exception:
            pass
    for child_collection in list(getattr(collection, "children", [])):
        _cmx_set_collection_tree_visibility(child_collection, visible)


def _cmx_apply_source_instance_visibility(source_name, visible):
    source_name = (source_name or "").strip()
    if not source_name:
        return False
    inst_collection = bpy.data.collections.get(f"{source_name}_Instance")
    if not inst_collection:
        return False
    _cmx_set_collection_tree_visibility(inst_collection, visible)
    return True


def _cmx_validate_source_target_name(scene, source_name):
    source_name = (source_name or "").strip()
    if not source_name:
        return False, "Please enter a source name."
    if any(item.name == source_name for item in getattr(scene, "source_data_items", [])):
        return False, f"Source name '{source_name}' already exists in Source List."

    conflicting = next((name for name in _cmx_get_source_reserved_collection_names(source_name) if _cmx_collection_exists(name)), None)
    if conflicting:
        return False, f"Source name '{source_name}' conflicts with existing collection '{conflicting}'."
    return True, ""


def _cmx_validate_source_library_load(scene, source_library_name):
    source_library_name = (source_library_name or "").strip()
    if not source_library_name:
        return False, "Please select a source file."
    if any(getattr(item, "preset_collection", "") == source_library_name for item in getattr(scene, "source_data_items", [])):
        return False, f"Source '{source_library_name}' is already loaded."
    if _cmx_collection_exists(source_library_name):
        return False, f"Source '{source_library_name}' conflicts with existing collection '{source_library_name}'."
    return True, ""


def _cmx_get_preset_source_names(source_data):
    legacy_name = str((source_data or {}).get("name", "") or "").strip()
    source_base = str(
        (source_data or {}).get("preset_collection_enum") or
        (source_data or {}).get("source_name") or
        legacy_name
    ).strip()
    return source_base, (legacy_name or source_base)


def _cmx_build_scene_source_name_map(scene):
    source_name_map = {}
    for source_item in getattr(scene, "source_data_items", []):
        current_name = str(getattr(source_item, "name", "") or "").strip()
        canonical_name = str(getattr(source_item, "preset_collection", "") or current_name).strip()
        if not canonical_name:
            continue
        source_name_map[canonical_name] = canonical_name
        if current_name:
            source_name_map[current_name] = canonical_name
    return source_name_map


def _cmx_remap_internal_collection_value(saved_value_data, source_name_map):
    if not isinstance(saved_value_data, dict) or saved_value_data.get("type") != "INTERNAL_COLLECTION":
        return saved_value_data
    item_name = str(saved_value_data.get("name", "") or "").strip()
    remapped_name = source_name_map.get(item_name, item_name)
    if remapped_name == item_name:
        return saved_value_data
    remapped_value = dict(saved_value_data)
    remapped_value["name"] = remapped_name
    return remapped_value


def _cmx_resolve_saved_collection_name(saved_value_data, source_name_map=None):
    source_name_map = source_name_map or {}
    if isinstance(saved_value_data, dict):
        data_type = saved_value_data.get("type")
        if data_type == "INTERNAL_COLLECTION":
            item_name = str(saved_value_data.get("name", "") or "").strip()
        elif data_type == "EXTERNAL_FROM_ADDON_COLLECTION":
            item_name = str(
                saved_value_data.get("internal_name") or
                os.path.splitext(str(saved_value_data.get("library_name", "") or ""))[0]
            ).strip()
        else:
            return ""
    elif isinstance(saved_value_data, str):
        item_name = saved_value_data.strip()
    else:
        return ""
    return source_name_map.get(item_name, item_name)


def _cmx_get_modifier_input_socket_by_identifier(modifier, socket_identifier):
    if not modifier or not getattr(modifier, "node_group", None):
        return None
    interface = getattr(modifier.node_group, "interface", None)
    if not interface:
        return None
    for item in interface.items_tree:
        if (
            getattr(item, "item_type", None) == 'SOCKET' and
            getattr(item, "in_out", None) == 'INPUT' and
            getattr(item, "identifier", None) == socket_identifier
        ):
            return item
    return None


def _cmx_normalize_saved_source_socket_value(modifier, socket_identifier, saved_value_data, source_name_map):
    socket_item = _cmx_get_modifier_input_socket_by_identifier(modifier, socket_identifier)
    if not socket_item or not _cmx_is_any_source_socket(socket_item):
        return _cmx_remap_internal_collection_value(saved_value_data, source_name_map)

    source_names = {name for name in source_name_map.values() if name}
    source_name = _cmx_resolve_saved_collection_name(saved_value_data, source_name_map)
    if source_name in source_names:
        return {
            "type": "INTERNAL_COLLECTION",
            "name": source_name,
        }

    return _cmx_remap_internal_collection_value(saved_value_data, source_name_map)


def _cmx_validate_crowd_target_name(scene, crowd_name):
    crowd_name = (crowd_name or "").strip()
    if not crowd_name:
        return False, "Item name is required."
    if any(item.name == crowd_name for item in getattr(scene, "crowd_data_items", [])):
        return False, f"Crowd name '{crowd_name}' already exists in Crowd List."

    conflicting = next((name for name in _cmx_get_crowd_reserved_collection_names(crowd_name) if _cmx_collection_exists(name)), None)
    if conflicting:
        return False, f"Crowd name '{crowd_name}' conflicts with existing collection '{conflicting}'."
    return True, ""


def _cmx_show_validation_popup(message, title="Validation", icon='ERROR'):
    cmx_show_message_box(message=message, title=title, icon=icon)


def _cmx_to_float3(value, default=CMX_VECTOR_ZERO):
    if value is None:
        return tuple(float(component) for component in default)
    try:
        components = list(value)
    except Exception:
        components = []
    if len(components) < 3:
        components.extend(list(default)[len(components):3])
    try:
        return tuple(float(components[index]) for index in range(3))
    except Exception:
        return tuple(float(component) for component in default)


def _cmx_to_float(value, default=0.0):
    try:
        return float(value)
    except Exception:
        return float(default)


def _cmx_float_equal(value_a, value_b, epsilon=CMX_VECTOR_COMPARE_EPSILON):
    return abs(_cmx_to_float(value_a) - _cmx_to_float(value_b)) <= epsilon


def _cmx_float3_equal(value_a, value_b, epsilon=CMX_VECTOR_COMPARE_EPSILON):
    value_a = _cmx_to_float3(value_a)
    value_b = _cmx_to_float3(value_b)
    return all(abs(float(value_a[index]) - float(value_b[index])) <= epsilon for index in range(3))


def _cmx_add_float3(value_a, value_b):
    value_a = _cmx_to_float3(value_a)
    value_b = _cmx_to_float3(value_b)
    return tuple(float(value_a[index]) + float(value_b[index]) for index in range(3))


def _cmx_sub_float3(value_a, value_b):
    value_a = _cmx_to_float3(value_a)
    value_b = _cmx_to_float3(value_b)
    return tuple(float(value_a[index]) - float(value_b[index]) for index in range(3))


def _cmx_uniform_float3(value):
    scalar = float(value)
    return (scalar, scalar, scalar)


def _cmx_average_float3(value):
    value = _cmx_to_float3(value)
    return sum(float(component) for component in value) / 3.0


def _cmx_get_crowd_item_by_name(scene, crowd_name):
    if not scene or not crowd_name:
        return None
    return next((item for item in getattr(scene, "crowd_data_items", []) if item.name == crowd_name), None)


def _cmx_is_flow_curve_crowd_item(crowd_item):
    return bool(crowd_item and getattr(crowd_item, "crowd_obj_name", "") == CMX_FLOW_CURVE_CROWD_TYPE)


def _cmx_is_flow_curve_crowd_name(crowd_name, scene=None):
    crowd_item = _cmx_get_crowd_item_by_name(scene or getattr(bpy.context, "scene", None), crowd_name)
    return _cmx_is_flow_curve_crowd_item(crowd_item)


def _cmx_override_object_supports_speed(override_obj, crowd_name=""):
    if override_obj:
        crowd_type = str(override_obj.get(CMX_EDIT_INSTANCE_PROXY_CROWD_TYPE_PROP, "") or "")
        if crowd_type:
            return crowd_type == CMX_FLOW_CURVE_CROWD_TYPE
        crowd_name = crowd_name or str(override_obj.get(CMX_EDIT_INSTANCE_PROXY_CROWD_PROP, "") or "")
    return _cmx_is_flow_curve_crowd_name(crowd_name)


def _cmx_compute_override_on_state(
    original_index,
    override_index,
    original_vis,
    override_vis,
    original_pos,
    override_pos,
    original_rot,
    override_rot,
    original_scale,
    override_scale,
    original_speed=None,
    override_speed=None,
    force_disable=False,
):
    if force_disable:
        return False
    speed_overridden = (
        original_speed is not None or override_speed is not None
    ) and not _cmx_float_equal(override_speed, original_speed)
    return (
        int(override_index) != int(original_index) or
        bool(override_vis) != bool(original_vis) or
        not _cmx_float3_equal(override_pos, CMX_VECTOR_ZERO) or
        not _cmx_float3_equal(override_rot, original_rot) or
        not _cmx_float3_equal(override_scale, original_scale) or
        speed_overridden
    )


def _cmx_clear_edit_instance_ui_sync_lock():
    global CMX_EDIT_INSTANCE_UI_SYNCING
    CMX_EDIT_INSTANCE_UI_SYNCING = False
    scene = getattr(bpy.context, "scene", None)
    if scene and hasattr(scene, "cmx_edit_instance_ui_sync_lock"):
        try:
            scene.cmx_edit_instance_ui_sync_lock = False
        except Exception:
            pass
    return None


def _cmx_is_within_edit_instance_ui_sync_grace(scene):
    last_sync_time = float(getattr(scene, "cmx_edit_instance_last_sync_time", 0.0) or 0.0)
    if last_sync_time <= 0.0:
        return False
    return (time.monotonic() - last_sync_time) < CMX_EDIT_INSTANCE_UI_SYNC_GRACE_SECONDS


def _cmx_update_proxy_display_as(self, context):
    _cmx_apply_proxy_display_settings(context.scene)
    _cmx_tag_redraw_all()


def _cmx_update_proxy_show_names(self, context):
    _cmx_apply_proxy_display_settings(context.scene)
    _cmx_tag_redraw_all()


def _cmx_update_proxy_in_front(self, context):
    _cmx_apply_proxy_display_settings(context.scene)
    _cmx_tag_redraw_all()


def _cmx_sync_ins_vis_only_select_state(scene, crowd_name=None):
    scene = scene or getattr(bpy.context, "scene", None)
    if not scene:
        return
    target_crowd_name = crowd_name or getattr(scene, "cmx_edit_instance_crowd_name", "")
    if not target_crowd_name:
        return
    crowd_item = next((item for item in scene.crowd_data_items if item.name == target_crowd_name), None)
    modifier = cmx_get_crowd_modifier(crowd_item or target_crowd_name)
    if not modifier:
        return
    current_value = _cmx_get_modifier_input_by_names(modifier, CMX_INS_VIS_ONLY_SELECT_SOCKET_NAMES)
    scene.cmx_edit_instance_ins_vis_only_select = bool(current_value)


def _cmx_update_ins_vis_only_select(self, context):
    scene = context.scene
    crowd_name = getattr(scene, "cmx_edit_instance_crowd_name", "")
    if not crowd_name:
        return
    crowd_item = next((item for item in scene.crowd_data_items if item.name == crowd_name), None)
    modifier = cmx_get_crowd_modifier(crowd_item or crowd_name)
    if not modifier:
        return
    _cmx_set_modifier_input_by_names(
        modifier,
        CMX_INS_VIS_ONLY_SELECT_SOCKET_NAMES,
        bool(scene.cmx_edit_instance_ins_vis_only_select),
        socket_type='NodeSocketBool'
    )
    _cmx_request_modifier_evaluation(modifier, refresh_display=False)
    _cmx_tag_redraw_all()


def _cmx_sync_selected_override_ui_state(scene):
    global CMX_EDIT_INSTANCE_UI_SYNCING
    scene = scene or getattr(bpy.context, "scene", None)
    if not scene:
        return
    point_state = _cmx_get_selected_edit_instance_point_state(scene)
    CMX_EDIT_INSTANCE_UI_SYNCING = True
    if hasattr(scene, "cmx_edit_instance_ui_sync_lock"):
        scene.cmx_edit_instance_ui_sync_lock = True
    if hasattr(scene, "cmx_edit_instance_last_sync_time"):
        scene.cmx_edit_instance_last_sync_time = time.monotonic()
    try:
        scene.cmx_edit_instance_override_vis = bool(point_state["override_vis"]) if point_state else True
        scene.cmx_edit_instance_override_pos = _cmx_to_float3(point_state["override_pos"], CMX_VECTOR_ZERO) if point_state else CMX_VECTOR_ZERO
        scene.cmx_edit_instance_override_rot = _cmx_sub_float3(point_state["override_rot"], point_state["original_rot"]) if point_state else CMX_VECTOR_ZERO
        scene.cmx_edit_instance_override_scale = _cmx_average_float3(_cmx_sub_float3(point_state["override_scale"], point_state["original_scale"])) if point_state else 0.0
        scene.cmx_edit_instance_override_speed = _cmx_to_float(point_state.get("override_speed", point_state.get("original_speed", 1.0)), 1.0) if point_state else 1.0
    finally:
        bpy.app.timers.register(_cmx_clear_edit_instance_ui_sync_lock, first_interval=0.0)


def _cmx_sync_selected_override_vis_state(scene):
    _cmx_sync_selected_override_ui_state(scene)


def _cmx_apply_selected_override_scene_state(context, changed_field=None):
    scene = context.scene
    if (
        CMX_EDIT_INSTANCE_UI_SYNCING or
        getattr(scene, "cmx_edit_instance_ui_sync_lock", False) or
        _cmx_is_within_edit_instance_ui_sync_grace(scene)
    ):
        return
    crowd_name = getattr(scene, "cmx_edit_instance_crowd_name", "")
    point_index = getattr(scene, "cmx_edit_instance_selected_index", -1)
    slot_index = getattr(scene, "cmx_edit_instance_selected_slot", -1)
    original_index = getattr(scene, "cmx_edit_instance_selected_original_index", -1)
    if not crowd_name or point_index < 0 or slot_index < 0 or original_index < 0:
        return

    crowd_item = next((item for item in scene.crowd_data_items if item.name == crowd_name), None)
    modifier = cmx_get_crowd_modifier(crowd_item or crowd_name)
    override_obj = _cmx_get_override_object(crowd_name)
    if not modifier or not override_obj:
        return

    point_state = _cmx_get_override_runtime_state(override_obj, slot_index, point_index, original_index)
    if not point_state:
        return

    override_vis = point_state["override_vis"]
    override_pos = point_state["override_pos"]
    override_rot = point_state["override_rot"]
    override_scale = point_state["override_scale"]
    override_speed = point_state.get("override_speed", point_state.get("original_speed", 1.0))

    if changed_field in (None, "vis"):
        override_vis = bool(scene.cmx_edit_instance_override_vis)
    if changed_field in (None, "pos"):
        override_pos = _cmx_to_float3(getattr(scene, "cmx_edit_instance_override_pos", CMX_VECTOR_ZERO), CMX_VECTOR_ZERO)
    if changed_field in (None, "rot"):
        override_rot = _cmx_add_float3(point_state["original_rot"], getattr(scene, "cmx_edit_instance_override_rot", CMX_VECTOR_ZERO))
    if changed_field in (None, "scale"):
        override_scale = _cmx_add_float3(point_state["original_scale"], _cmx_uniform_float3(getattr(scene, "cmx_edit_instance_override_scale", 0.0)))
    if changed_field in (None, "speed") and _cmx_is_flow_curve_crowd_name(crowd_name, scene=scene):
        override_speed = _cmx_to_float(getattr(scene, "cmx_edit_instance_override_speed", 1.0), 1.0)

    _cmx_set_override_runtime_state(
        override_obj,
        point_state["slot_index"],
        point_state["original_index"],
        point_state["override_index"],
        override_vis=override_vis,
        override_pos=override_pos,
        override_rot=override_rot,
        override_scale=override_scale,
        override_speed=override_speed,
        debug_source=f"scene_update:{changed_field or 'all'}",
    )
    _cmx_set_modifier_input_by_names(modifier, CMX_SELECT_INDEX_SOCKET_NAMES, point_state["point_index"], socket_type='NodeSocketInt')
    _cmx_set_modifier_input_by_names(modifier, CMX_OVERRIDE_INFO_SOCKET_NAMES, override_obj, socket_type='NodeSocketObject')
    _cmx_request_modifier_evaluation(modifier, refresh_display=False)
    _cmx_update_override_visibility(override_obj)
    _cmx_tag_redraw_all()


def _cmx_update_selected_override_vis(self, context):
    if (
        CMX_EDIT_INSTANCE_UI_SYNCING or
        getattr(context.scene, "cmx_edit_instance_ui_sync_lock", False) or
        _cmx_is_within_edit_instance_ui_sync_grace(context.scene)
    ):
        return
    _cmx_apply_selected_override_scene_state(context, changed_field="vis")


def _cmx_update_selected_override_pos(self, context):
    if (
        CMX_EDIT_INSTANCE_UI_SYNCING or
        getattr(context.scene, "cmx_edit_instance_ui_sync_lock", False) or
        _cmx_is_within_edit_instance_ui_sync_grace(context.scene)
    ):
        return
    _cmx_apply_selected_override_scene_state(context, changed_field="pos")


def _cmx_update_selected_override_rot(self, context):
    if (
        CMX_EDIT_INSTANCE_UI_SYNCING or
        getattr(context.scene, "cmx_edit_instance_ui_sync_lock", False) or
        _cmx_is_within_edit_instance_ui_sync_grace(context.scene)
    ):
        return
    _cmx_apply_selected_override_scene_state(context, changed_field="rot")


def _cmx_update_selected_override_scale(self, context):
    if (
        CMX_EDIT_INSTANCE_UI_SYNCING or
        getattr(context.scene, "cmx_edit_instance_ui_sync_lock", False) or
        _cmx_is_within_edit_instance_ui_sync_grace(context.scene)
    ):
        return
    _cmx_apply_selected_override_scene_state(context, changed_field="scale")


def _cmx_update_selected_override_speed(self, context):
    if (
        CMX_EDIT_INSTANCE_UI_SYNCING or
        getattr(context.scene, "cmx_edit_instance_ui_sync_lock", False) or
        _cmx_is_within_edit_instance_ui_sync_grace(context.scene)
    ):
        return
    _cmx_apply_selected_override_scene_state(context, changed_field="speed")


def _cmx_tag_redraw_all():
    wm = getattr(bpy.context, "window_manager", None)
    if not wm:
        return
    for window in wm.windows:
        screen = getattr(window, "screen", None)
        if not screen:
            continue
        for area in screen.areas:
            area.tag_redraw()


def _cmx_flush_preset_load_viewport(context):
    """Force a light viewport refresh during long preset loads."""
    try:
        context.view_layer.update()
    except Exception:
        pass
    _cmx_tag_redraw_all()
    try:
        bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)
    except Exception:
        pass


def _cmx_get_view3d_override_context(scene=None):
    wm = getattr(bpy.context, "window_manager", None)
    if not wm:
        return None

    for window in wm.windows:
        screen = getattr(window, "screen", None)
        if not screen:
            continue
        for area in screen.areas:
            if area.type != 'VIEW_3D':
                continue
            region = next((item for item in area.regions if item.type == 'WINDOW'), None)
            if not region:
                continue
            override = {
                "window": window,
                "screen": screen,
                "area": area,
                "region": region,
            }
            if scene:
                override["scene"] = scene
            return override
    return None


def _cmx_get_modifier_input_socket_by_names(modifier, socket_names, socket_type=None):
    return _cmx_find_modifier_input_socket(modifier, socket_names, socket_type=socket_type)


def _cmx_set_modifier_input_by_names(modifier, socket_names, value, socket_type=None):
    socket_item = _cmx_get_modifier_input_socket_by_names(modifier, socket_names, socket_type=socket_type)
    if not socket_item:
        return False
    try:
        modifier[socket_item.identifier] = value
        return True
    except Exception:
        return False


def _cmx_request_modifier_evaluation(modifier, refresh_display=True):
    if not modifier:
        return
    modifier_owner = getattr(modifier, "id_data", None)
    try:
        if modifier_owner:
            modifier_owner.update_tag()
    except Exception:
        pass
    try:
        owner_data = getattr(modifier_owner, "data", None)
        if owner_data and hasattr(owner_data, "update"):
            owner_data.update()
    except Exception:
        pass
    try:
        bpy.context.view_layer.update()
    except Exception:
        pass
    if refresh_display:
        try:
            cmx_refresh_modifier_display(modifier)
        except Exception:
            pass
    _cmx_tag_redraw_all()


def _cmx_get_modifier_input_by_names(modifier, socket_names):
    socket_item = _cmx_get_modifier_input_socket_by_names(modifier, socket_names)
    if not socket_item:
        return None
    return modifier.get(socket_item.identifier)


def _cmx_get_attribute(geometry_data, attr_names):
    attributes = getattr(geometry_data, "attributes", None)
    if not attributes:
        return None
    for attr_name in attr_names:
        try:
            attribute = attributes.get(attr_name)
        except Exception:
            attribute = None
        if attribute:
            return attribute
    return None


def _cmx_ensure_attribute(geometry_data, attr_name, data_type, domain='POINT'):
    attributes = getattr(geometry_data, "attributes", None)
    if not attributes:
        return None
    try:
        attribute = attributes.get(attr_name)
    except Exception:
        attribute = None
    if attribute:
        return attribute
    try:
        return attributes.new(name=attr_name, type=data_type, domain=domain)
    except Exception:
        return None


def _cmx_get_attribute_value(attribute, index, default=None):
    if not attribute or index < 0 or index >= len(attribute.data):
        return default
    data_item = attribute.data[index]
    if hasattr(data_item, "value"):
        return data_item.value
    if hasattr(data_item, "vector"):
        return data_item.vector.copy()
    if hasattr(data_item, "color"):
        return tuple(data_item.color)
    return default


def _cmx_set_attribute_value(attribute, index, value):
    if not attribute or index < 0 or index >= len(attribute.data):
        return False
    data_item = attribute.data[index]
    try:
        if hasattr(data_item, "value"):
            data_item.value = value
            return True
        if hasattr(data_item, "vector"):
            data_item.vector = value
            return True
        if hasattr(data_item, "color"):
            data_item.color = value
            return True
    except Exception:
        return False
    return False


def _cmx_set_attribute_values(attribute, values):
    if not attribute:
        return False
    data = getattr(attribute, "data", None)
    if not data:
        return False
    if len(data) != len(values):
        return False

    try:
        sample = data[0] if len(data) else None
    except Exception:
        sample = None

    if sample and hasattr(sample, "value") and hasattr(data, "foreach_set"):
        try:
            data.foreach_set("value", list(values))
            return True
        except Exception:
            pass

    success = True
    for index, value in enumerate(values):
        success = _cmx_set_attribute_value(attribute, index, value) and success
    return success


def _cmx_collect_geometry_positions(geometry_data, count):
    if count <= 0:
        return []

    if hasattr(geometry_data, "vertices") and len(geometry_data.vertices) >= count:
        return [vertex.co.copy() for vertex in geometry_data.vertices[:count]]

    position_attr = _cmx_get_attribute(geometry_data, ("position", "Position"))
    if position_attr and len(position_attr.data) >= count:
        return [position_attr.data[index].vector.copy() for index in range(count)]

    if hasattr(geometry_data, "points") and len(geometry_data.points) >= count:
        return [point.co.copy() for point in geometry_data.points[:count]]

    return []


def _cmx_collect_crowd_point_data(crowd_item):
    crowd_obj = _cmx_get_crowd_node_object(crowd_item)
    if not crowd_obj:
        return []
    supports_speed = _cmx_is_flow_curve_crowd_item(crowd_item)

    depsgraph = None
    eval_obj = None
    try:
        depsgraph = bpy.context.evaluated_depsgraph_get()
        eval_obj = crowd_obj.evaluated_get(depsgraph)
    except Exception:
        eval_obj = None

    candidates = []
    seen_candidate_ids = set()

    def _add_candidate(geometry_data, label, is_temp=False):
        if not geometry_data:
            return
        candidate_id = id(geometry_data)
        if candidate_id in seen_candidate_ids:
            return
        seen_candidate_ids.add(candidate_id)
        candidates.append((geometry_data, label, is_temp))

    _add_candidate(getattr(crowd_obj, "data", None), "object_data")
    _add_candidate(getattr(eval_obj, "data", None), "evaluated_data")

    temp_mesh = None
    if eval_obj and depsgraph:
        try:
            temp_mesh = eval_obj.to_mesh(preserve_all_data_layers=True, depsgraph=depsgraph)
        except Exception:
            temp_mesh = None
    _add_candidate(temp_mesh, "evaluated_to_mesh", is_temp=True)

    points = []
    debug_states = []
    try:
        for geometry_data, candidate_label, _is_temp in candidates:
            index_attr = _cmx_get_attribute(geometry_data, CMX_INDEX_ATTRIBUTE_NAMES)
            original_attr = _cmx_get_attribute(geometry_data, CMX_ORIGINAL_INSTANCE_ATTRIBUTE_NAMES)
            original_vis_attr = _cmx_get_attribute(geometry_data, CMX_ORIGINAL_VIS_ATTRIBUTE_NAMES)
            original_pos_attr = _cmx_get_attribute(geometry_data, CMX_ORIGINAL_POS_ATTRIBUTE_NAMES)
            original_rot_attr = _cmx_get_attribute(geometry_data, CMX_ORIGINAL_ROT_ATTRIBUTE_NAMES)
            original_scale_attr = _cmx_get_attribute(geometry_data, CMX_ORIGINAL_SCALE_ATTRIBUTE_NAMES)
            original_speed_attr = _cmx_get_attribute(geometry_data, CMX_ORIGINAL_SPEED_ATTRIBUTE_NAMES) if supports_speed else None
            override_index_attr = _cmx_get_attribute(geometry_data, CMX_OVERRIDE_INDEX_ATTRIBUTE_NAMES)
            override_on_attr = _cmx_get_attribute(geometry_data, CMX_OVERRIDE_ON_ATTRIBUTE_NAMES)
            override_vis_attr = _cmx_get_attribute(geometry_data, CMX_OVERRIDE_VIS_ATTRIBUTE_NAMES)
            override_pos_attr = _cmx_get_attribute(geometry_data, CMX_OVERRIDE_POS_ATTRIBUTE_NAMES)
            override_rot_attr = _cmx_get_attribute(geometry_data, CMX_OVERRIDE_ROT_ATTRIBUTE_NAMES)
            override_scale_attr = _cmx_get_attribute(geometry_data, CMX_OVERRIDE_SCALE_ATTRIBUTE_NAMES)
            override_speed_attr = _cmx_get_attribute(geometry_data, CMX_OVERRIDE_SPEED_ATTRIBUTE_NAMES) if supports_speed else None
            vertex_count = len(getattr(geometry_data, "vertices", [])) if hasattr(geometry_data, "vertices") else -1
            debug_states.append({
                "label": candidate_label,
                "has_index": bool(index_attr),
                "has_original": bool(original_attr),
                "vertex_count": vertex_count,
            })
            if not index_attr or not original_attr:
                continue

            point_count = min(len(index_attr.data), len(original_attr.data))
            positions = _cmx_collect_geometry_positions(geometry_data, point_count)
            if point_count <= 0 or len(positions) < point_count:
                continue

            grouped_points = {}
            for slot_index in range(point_count):
                point_index = _cmx_get_attribute_value(index_attr, slot_index, slot_index)
                original_index = _cmx_get_attribute_value(original_attr, slot_index, 0)
                original_vis = bool(_cmx_get_attribute_value(original_vis_attr, slot_index, True))
                original_pos = _cmx_to_float3(_cmx_get_attribute_value(original_pos_attr, slot_index, CMX_VECTOR_ZERO), CMX_VECTOR_ZERO)
                original_rot = _cmx_to_float3(_cmx_get_attribute_value(original_rot_attr, slot_index, CMX_VECTOR_ZERO), CMX_VECTOR_ZERO)
                original_scale = _cmx_to_float3(_cmx_get_attribute_value(original_scale_attr, slot_index, CMX_VECTOR_ONE), CMX_VECTOR_ONE)
                original_speed = _cmx_to_float(_cmx_get_attribute_value(original_speed_attr, slot_index, 1.0), 1.0)
                override_index = _cmx_get_attribute_value(override_index_attr, slot_index, original_index)
                override_on = bool(_cmx_get_attribute_value(override_on_attr, slot_index, False))
                override_vis = bool(_cmx_get_attribute_value(override_vis_attr, slot_index, original_vis))
                override_pos = _cmx_to_float3(_cmx_get_attribute_value(override_pos_attr, slot_index, CMX_VECTOR_ZERO), CMX_VECTOR_ZERO)
                override_rot = _cmx_to_float3(_cmx_get_attribute_value(override_rot_attr, slot_index, original_rot), original_rot)
                override_scale = _cmx_to_float3(_cmx_get_attribute_value(override_scale_attr, slot_index, original_scale), original_scale)
                override_speed = _cmx_to_float(_cmx_get_attribute_value(override_speed_attr, slot_index, original_speed), original_speed)
                try:
                    point_index = int(point_index)
                except Exception:
                    point_index = slot_index
                try:
                    original_index = int(original_index)
                except Exception:
                    original_index = 0
                try:
                    override_index = int(override_index)
                except Exception:
                    override_index = original_index
                grouped_item = grouped_points.get(point_index)
                if not grouped_item:
                    grouped_points[point_index] = {
                        "point_index": point_index,
                        "original_index": original_index,
                        "has_original_vis": bool(original_vis_attr),
                        "has_original_pos": bool(original_pos_attr),
                        "has_original_rot": bool(original_rot_attr),
                        "has_original_scale": bool(original_scale_attr),
                        "has_original_speed": bool(original_speed_attr),
                        "has_override_index": bool(override_index_attr),
                        "has_override_on": bool(override_on_attr),
                        "has_override_vis": bool(override_vis_attr),
                        "has_override_pos": bool(override_pos_attr),
                        "has_override_rot": bool(override_rot_attr),
                        "has_override_scale": bool(override_scale_attr),
                        "has_override_speed": bool(override_speed_attr),
                        "original_vis": original_vis,
                        "original_pos": original_pos,
                        "original_rot": original_rot,
                        "original_scale": original_scale,
                        "original_speed": original_speed,
                        "override_index": override_index,
                        "override_on": override_on,
                        "override_vis": override_vis,
                        "override_pos": override_pos,
                        "override_rot": override_rot,
                        "override_scale": override_scale,
                        "override_speed": override_speed,
                        "local_position": positions[slot_index].copy(),
                        "sample_count": 1,
                    }
                else:
                    grouped_item["local_position"] += positions[slot_index]
                    grouped_item["sample_count"] += 1

            points = []
            for grouped_item in grouped_points.values():
                sample_count = max(1, int(grouped_item.pop("sample_count", 1)))
                grouped_item["local_position"] = grouped_item["local_position"] / sample_count
                points.append(grouped_item)
            if points:
                points.sort(key=lambda item: item["point_index"])
                break
    finally:
        if temp_mesh:
            try:
                eval_obj.to_mesh_clear()
            except Exception:
                pass

    return points


def _cmx_read_override_state(override_obj):
    geometry_data = getattr(override_obj, "data", None)
    if not geometry_data:
        return {}

    index_attr = _cmx_get_attribute(geometry_data, CMX_INDEX_ATTRIBUTE_NAMES)
    original_attr = _cmx_get_attribute(geometry_data, CMX_ORIGINAL_INSTANCE_ATTRIBUTE_NAMES)
    override_index_attr = _cmx_get_attribute(geometry_data, CMX_OVERRIDE_INDEX_ATTRIBUTE_NAMES)
    override_on_attr = _cmx_get_attribute(geometry_data, CMX_OVERRIDE_ON_ATTRIBUTE_NAMES)
    if not index_attr:
        return {}

    state = {}
    for slot_index in range(len(index_attr.data)):
        point_index = _cmx_get_attribute_value(index_attr, slot_index, slot_index)
        try:
            point_index = int(point_index)
        except Exception:
            point_index = slot_index
        original_index = _cmx_get_attribute_value(original_attr, slot_index, 0)
        override_index = _cmx_get_attribute_value(override_index_attr, slot_index, original_index)
        override_on = bool(_cmx_get_attribute_value(override_on_attr, slot_index, False))
        try:
            original_index = int(original_index)
        except Exception:
            original_index = 0
        try:
            override_index = int(override_index)
        except Exception:
            override_index = original_index
        state[point_index] = {
            "original_index": original_index,
            "override_index": override_index,
            "override_on": override_on,
        }
    return state


def _cmx_read_override_state_by_slot(override_obj):
    geometry_data = getattr(override_obj, "data", None)
    if not geometry_data:
        return []
    supports_speed = _cmx_override_object_supports_speed(override_obj)

    original_vis_attr = _cmx_get_attribute(geometry_data, CMX_ORIGINAL_VIS_ATTRIBUTE_NAMES)
    original_pos_attr = _cmx_get_attribute(geometry_data, CMX_ORIGINAL_POS_ATTRIBUTE_NAMES)
    original_rot_attr = _cmx_get_attribute(geometry_data, CMX_ORIGINAL_ROT_ATTRIBUTE_NAMES)
    original_scale_attr = _cmx_get_attribute(geometry_data, CMX_ORIGINAL_SCALE_ATTRIBUTE_NAMES)
    original_speed_attr = _cmx_get_attribute(geometry_data, CMX_ORIGINAL_SPEED_ATTRIBUTE_NAMES) if supports_speed else None
    override_index_attr = _cmx_get_attribute(geometry_data, CMX_OVERRIDE_INDEX_ATTRIBUTE_NAMES)
    override_on_attr = _cmx_get_attribute(geometry_data, CMX_OVERRIDE_ON_ATTRIBUTE_NAMES)
    override_vis_attr = _cmx_get_attribute(geometry_data, CMX_OVERRIDE_VIS_ATTRIBUTE_NAMES)
    override_pos_attr = _cmx_get_attribute(geometry_data, CMX_OVERRIDE_POS_ATTRIBUTE_NAMES)
    override_rot_attr = _cmx_get_attribute(geometry_data, CMX_OVERRIDE_ROT_ATTRIBUTE_NAMES)
    override_scale_attr = _cmx_get_attribute(geometry_data, CMX_OVERRIDE_SCALE_ATTRIBUTE_NAMES)
    override_speed_attr = _cmx_get_attribute(geometry_data, CMX_OVERRIDE_SPEED_ATTRIBUTE_NAMES) if supports_speed else None
    if not override_index_attr:
        return []

    state = []
    for slot_index in range(len(override_index_attr.data)):
        original_vis = bool(_cmx_get_attribute_value(original_vis_attr, slot_index, True))
        original_pos = _cmx_to_float3(_cmx_get_attribute_value(original_pos_attr, slot_index, CMX_VECTOR_ZERO), CMX_VECTOR_ZERO)
        original_rot = _cmx_to_float3(_cmx_get_attribute_value(original_rot_attr, slot_index, CMX_VECTOR_ZERO), CMX_VECTOR_ZERO)
        original_scale = _cmx_to_float3(_cmx_get_attribute_value(original_scale_attr, slot_index, CMX_VECTOR_ONE), CMX_VECTOR_ONE)
        original_speed = _cmx_to_float(_cmx_get_attribute_value(original_speed_attr, slot_index, 1.0), 1.0)
        override_index = _cmx_get_attribute_value(override_index_attr, slot_index, 0)
        override_on = bool(_cmx_get_attribute_value(override_on_attr, slot_index, False))
        override_vis = bool(_cmx_get_attribute_value(override_vis_attr, slot_index, True))
        override_pos = _cmx_to_float3(_cmx_get_attribute_value(override_pos_attr, slot_index, CMX_VECTOR_ZERO), CMX_VECTOR_ZERO)
        override_rot = _cmx_to_float3(_cmx_get_attribute_value(override_rot_attr, slot_index, CMX_VECTOR_ZERO), CMX_VECTOR_ZERO)
        override_scale = _cmx_to_float3(_cmx_get_attribute_value(override_scale_attr, slot_index, CMX_VECTOR_ONE), CMX_VECTOR_ONE)
        override_speed = _cmx_to_float(_cmx_get_attribute_value(override_speed_attr, slot_index, original_speed), original_speed)
        try:
            override_index = int(override_index)
        except Exception:
            override_index = 0
        state.append({
            "original_vis": original_vis,
            "original_pos": original_pos,
            "original_rot": original_rot,
            "original_scale": original_scale,
            "original_speed": original_speed,
            "override_index": override_index,
            "override_on": override_on,
            "override_vis": override_vis,
            "override_pos": override_pos,
            "override_rot": override_rot,
            "override_scale": override_scale,
            "override_speed": override_speed,
        })
    return state


def _cmx_snapshot_override_runtime_state(override_obj):
    geometry_data = getattr(override_obj, "data", None)
    if not geometry_data:
        return []
    index_attr = _cmx_get_attribute(geometry_data, CMX_INDEX_ATTRIBUTE_NAMES)
    if not index_attr:
        return []

    snapshot = []
    for slot_index in range(len(index_attr.data)):
        point_index = _cmx_get_attribute_value(index_attr, slot_index, slot_index)
        original_attr = _cmx_get_attribute(geometry_data, CMX_ORIGINAL_INSTANCE_ATTRIBUTE_NAMES)
        original_index = _cmx_get_attribute_value(original_attr, slot_index, 0)
        try:
            point_index = int(point_index)
        except Exception:
            point_index = slot_index
        try:
            original_index = int(original_index)
        except Exception:
            original_index = 0
        point_state = _cmx_get_override_runtime_state(override_obj, slot_index, point_index, original_index)
        if point_state:
            snapshot.append(dict(point_state))
    return snapshot


def _cmx_store_override_runtime_cache(crowd_name, state_list):
    if not crowd_name:
        return
    CMX_EDIT_INSTANCE_STATE_CACHE[crowd_name] = [dict(item) for item in (state_list or [])]


def _cmx_clear_override_runtime_cache(crowd_name):
    if crowd_name in CMX_EDIT_INSTANCE_STATE_CACHE:
        del CMX_EDIT_INSTANCE_STATE_CACHE[crowd_name]


def _cmx_store_last_edit_instance_selection(crowd_name, point_index, slot_index, original_index):
    if not crowd_name or slot_index < 0 or point_index < 0 or original_index < 0:
        return
    CMX_EDIT_INSTANCE_LAST_SELECTION[crowd_name] = {
        "point_index": int(point_index),
        "slot_index": int(slot_index),
        "original_index": int(original_index),
    }


def _cmx_get_last_edit_instance_selection(crowd_name):
    if not crowd_name:
        return None
    selection = CMX_EDIT_INSTANCE_LAST_SELECTION.get(crowd_name)
    return dict(selection) if selection else None


def _cmx_get_override_runtime_cache(crowd_name):
    return CMX_EDIT_INSTANCE_STATE_CACHE.get(crowd_name, [])


def _cmx_get_cached_override_state(crowd_name, slot_index, point_index=None):
    cache = _cmx_get_override_runtime_cache(crowd_name)
    if slot_index < 0 or slot_index >= len(cache):
        return None
    state = cache[slot_index]
    if point_index is not None and int(state.get("point_index", -1)) != int(point_index):
        return None
    return dict(state)


def _cmx_update_override_runtime_cache_slot(crowd_name, slot_index, state):
    cache = _cmx_get_override_runtime_cache(crowd_name)
    if slot_index < 0:
        return
    while len(cache) <= slot_index:
        cache.append({})
    cache[slot_index] = dict(state)
    CMX_EDIT_INSTANCE_STATE_CACHE[crowd_name] = cache


def _cmx_write_override_runtime_cache_to_object(override_obj, state_list):
    geometry_data = getattr(override_obj, "data", None)
    if not geometry_data or not state_list:
        return False
    supports_speed = _cmx_override_object_supports_speed(override_obj)

    point_index_attr = _cmx_get_attribute(geometry_data, CMX_INDEX_ATTRIBUTE_NAMES)
    original_index_attr = _cmx_get_attribute(geometry_data, CMX_ORIGINAL_INSTANCE_ATTRIBUTE_NAMES)
    original_vis_attr = _cmx_get_attribute(geometry_data, CMX_ORIGINAL_VIS_ATTRIBUTE_NAMES)
    original_pos_attr = _cmx_get_attribute(geometry_data, CMX_ORIGINAL_POS_ATTRIBUTE_NAMES)
    original_rot_attr = _cmx_get_attribute(geometry_data, CMX_ORIGINAL_ROT_ATTRIBUTE_NAMES)
    original_scale_attr = _cmx_get_attribute(geometry_data, CMX_ORIGINAL_SCALE_ATTRIBUTE_NAMES)
    original_speed_attr = _cmx_get_attribute(geometry_data, CMX_ORIGINAL_SPEED_ATTRIBUTE_NAMES) if supports_speed else None
    override_index_attr = _cmx_get_attribute(geometry_data, CMX_OVERRIDE_INDEX_ATTRIBUTE_NAMES)
    override_on_attrs = [_cmx_get_attribute(geometry_data, (attr_name,)) for attr_name in CMX_OVERRIDE_ON_ATTRIBUTE_NAMES]
    override_vis_attr = _cmx_get_attribute(geometry_data, CMX_OVERRIDE_VIS_ATTRIBUTE_NAMES)
    override_pos_attr = _cmx_get_attribute(geometry_data, CMX_OVERRIDE_POS_ATTRIBUTE_NAMES)
    override_rot_attr = _cmx_get_attribute(geometry_data, CMX_OVERRIDE_ROT_ATTRIBUTE_NAMES)
    override_scale_attr = _cmx_get_attribute(geometry_data, CMX_OVERRIDE_SCALE_ATTRIBUTE_NAMES)
    override_speed_attr = _cmx_get_attribute(geometry_data, CMX_OVERRIDE_SPEED_ATTRIBUTE_NAMES) if supports_speed else None

    for slot_index, state in enumerate(state_list):
        _cmx_set_attribute_value(point_index_attr, slot_index, int(state.get("point_index", slot_index)))
        _cmx_set_attribute_value(original_index_attr, slot_index, int(state.get("original_index", 0)))
        _cmx_set_attribute_value(original_vis_attr, slot_index, bool(state.get("original_vis", True)))
        _cmx_set_attribute_value(original_pos_attr, slot_index, _cmx_to_float3(state.get("original_pos", CMX_VECTOR_ZERO), CMX_VECTOR_ZERO))
        _cmx_set_attribute_value(original_rot_attr, slot_index, _cmx_to_float3(state.get("original_rot", CMX_VECTOR_ZERO), CMX_VECTOR_ZERO))
        _cmx_set_attribute_value(original_scale_attr, slot_index, _cmx_to_float3(state.get("original_scale", CMX_VECTOR_ONE), CMX_VECTOR_ONE))
        _cmx_set_attribute_value(original_speed_attr, slot_index, _cmx_to_float(state.get("original_speed", 1.0), 1.0))
        _cmx_set_attribute_value(override_index_attr, slot_index, int(state.get("override_index", state.get("original_index", 0))))
        for attr in override_on_attrs:
            _cmx_set_attribute_value(attr, slot_index, bool(state.get("override_on", False)))
        _cmx_set_attribute_value(override_vis_attr, slot_index, bool(state.get("override_vis", True)))
        _cmx_set_attribute_value(override_pos_attr, slot_index, _cmx_to_float3(state.get("override_pos", CMX_VECTOR_ZERO), CMX_VECTOR_ZERO))
        _cmx_set_attribute_value(override_rot_attr, slot_index, _cmx_to_float3(state.get("override_rot", CMX_VECTOR_ZERO), CMX_VECTOR_ZERO))
        _cmx_set_attribute_value(override_scale_attr, slot_index, _cmx_to_float3(state.get("override_scale", CMX_VECTOR_ONE), CMX_VECTOR_ONE))
        _cmx_set_attribute_value(override_speed_attr, slot_index, _cmx_to_float(state.get("override_speed", state.get("original_speed", 1.0)), 1.0))
    try:
        geometry_data.update()
    except Exception:
        pass
    return True


def _cmx_update_override_visibility(override_obj):
    if not override_obj:
        return
    override_obj.hide_viewport = True
    override_obj.hide_render = True
    override_obj.hide_select = True
    override_obj.display_type = 'WIRE'


def _cmx_ensure_override_object(context, crowd_item, point_data):
    crowd_obj = _cmx_get_crowd_node_object(crowd_item)
    if not crowd_obj:
        return None
    supports_speed = _cmx_is_flow_curve_crowd_item(crowd_item)

    root_collection = _cmx_get_edit_instance_root_collection(context)
    object_name = _cmx_get_override_object_name(crowd_item.name)
    existing_obj = bpy.data.objects.get(object_name)
    previous_state = _cmx_read_override_state_by_slot(existing_obj) if existing_obj else []

    if existing_obj:
        old_mesh = existing_obj.data
        if existing_obj.name in [obj.name for obj in root_collection.objects]:
            root_collection.objects.unlink(existing_obj)
        bpy.data.objects.remove(existing_obj, do_unlink=True)
        if old_mesh and old_mesh.users == 0:
            bpy.data.meshes.remove(old_mesh)

    mesh = bpy.data.meshes.new(f"{object_name}_Mesh")
    mesh.from_pydata([tuple(item["local_position"]) for item in point_data], [], [])
    mesh.update()

    override_obj = bpy.data.objects.new(object_name, mesh)
    root_collection.objects.link(override_obj)
    override_obj.matrix_world = crowd_obj.matrix_world.copy()
    override_obj[CMX_EDIT_INSTANCE_PROXY_CROWD_PROP] = crowd_item.name
    override_obj[CMX_EDIT_INSTANCE_PROXY_CROWD_TYPE_PROP] = getattr(crowd_item, "crowd_obj_name", "")
    _cmx_update_override_visibility(override_obj)

    point_index_attr = _cmx_ensure_attribute(mesh, "cmx_index", 'INT')
    original_index_attr = _cmx_ensure_attribute(mesh, "cmx_original_ins_index", 'INT')
    original_vis_attr = _cmx_ensure_attribute(mesh, "cmx_original_ins_vis", 'BOOLEAN')
    original_pos_attr = _cmx_ensure_attribute(mesh, "cmx_original_ins_pos", 'FLOAT_VECTOR')
    original_rot_attr = _cmx_ensure_attribute(mesh, "cmx_original_ins_rot", 'FLOAT_VECTOR')
    original_scale_attr = _cmx_ensure_attribute(mesh, "cmx_original_ins_scale", 'FLOAT_VECTOR')
    original_speed_attr = _cmx_ensure_attribute(mesh, "cmx_original_ins_ispeed", 'FLOAT') if supports_speed else None
    override_index_attr = _cmx_ensure_attribute(mesh, "cmx_override_index", 'INT')
    override_on_attrs = [
        _cmx_ensure_attribute(mesh, attr_name, 'BOOLEAN')
        for attr_name in CMX_OVERRIDE_ON_ATTRIBUTE_NAMES
    ]
    override_vis_attr = _cmx_ensure_attribute(mesh, "cmx_override_vis", 'BOOLEAN')
    override_pos_attr = _cmx_ensure_attribute(mesh, "cmx_override_pos", 'FLOAT_VECTOR')
    override_rot_attr = _cmx_ensure_attribute(mesh, "cmx_override_rot", 'FLOAT_VECTOR')
    override_scale_attr = _cmx_ensure_attribute(mesh, "cmx_override_scale", 'FLOAT_VECTOR')
    override_speed_attr = _cmx_ensure_attribute(mesh, "cmx_override_speed", 'FLOAT') if supports_speed else None
    runtime_state = []

    for slot_index, item in enumerate(point_data):
        point_index = int(item["point_index"])
        original_index = int(item["original_index"])
        previous_item = previous_state[slot_index] if slot_index < len(previous_state) else {}
        original_vis = bool(item["original_vis"]) if item.get("has_original_vis") else bool(previous_item.get("original_vis", True))
        original_pos = _cmx_to_float3(item["original_pos"], CMX_VECTOR_ZERO) if item.get("has_original_pos") else _cmx_to_float3(previous_item.get("original_pos", CMX_VECTOR_ZERO), CMX_VECTOR_ZERO)
        original_rot = _cmx_to_float3(item["original_rot"], CMX_VECTOR_ZERO) if item.get("has_original_rot") else _cmx_to_float3(previous_item.get("original_rot", CMX_VECTOR_ZERO), CMX_VECTOR_ZERO)
        original_scale = _cmx_to_float3(item["original_scale"], CMX_VECTOR_ONE) if item.get("has_original_scale") else _cmx_to_float3(previous_item.get("original_scale", CMX_VECTOR_ONE), CMX_VECTOR_ONE)
        original_speed = _cmx_to_float(item["original_speed"], 1.0) if item.get("has_original_speed") else _cmx_to_float(previous_item.get("original_speed", 1.0), 1.0)

        previous_override_on = bool(previous_item.get("override_on", False))
        if previous_override_on:
            override_index = int(previous_item.get("override_index", original_index))
            override_vis = bool(previous_item.get("override_vis", original_vis))
            override_pos = _cmx_to_float3(previous_item.get("override_pos", CMX_VECTOR_ZERO), CMX_VECTOR_ZERO)
            override_rot = _cmx_to_float3(previous_item.get("override_rot", original_rot), original_rot)
            override_scale = _cmx_to_float3(previous_item.get("override_scale", original_scale), original_scale)
            override_speed = _cmx_to_float(previous_item.get("override_speed", original_speed), original_speed)
            override_on = _cmx_compute_override_on_state(
                original_index,
                override_index,
                original_vis,
                override_vis,
                original_pos,
                override_pos,
                original_rot,
                override_rot,
                original_scale,
                override_scale,
                original_speed=original_speed,
                override_speed=override_speed,
            )
        else:
            override_index = int(item["override_index"]) if item.get("has_override_index") else int(previous_item.get("override_index", original_index))
            override_vis = bool(item["override_vis"]) if item.get("has_override_vis") else bool(previous_item.get("override_vis", original_vis))
            override_pos = _cmx_to_float3(item["override_pos"], CMX_VECTOR_ZERO) if item.get("has_override_pos") else _cmx_to_float3(previous_item.get("override_pos", CMX_VECTOR_ZERO), CMX_VECTOR_ZERO)
            override_rot = _cmx_to_float3(item["override_rot"], original_rot) if item.get("has_override_rot") else _cmx_to_float3(previous_item.get("override_rot", original_rot), original_rot)
            override_scale = _cmx_to_float3(item["override_scale"], original_scale) if item.get("has_override_scale") else _cmx_to_float3(previous_item.get("override_scale", original_scale), original_scale)
            override_speed = _cmx_to_float(item["override_speed"], original_speed) if item.get("has_override_speed") else _cmx_to_float(previous_item.get("override_speed", original_speed), original_speed)

            if item.get("has_override_on"):
                override_on = bool(item["override_on"])
            else:
                override_on = _cmx_compute_override_on_state(
                    original_index,
                    override_index,
                    original_vis,
                    override_vis,
                    original_pos,
                    override_pos,
                    original_rot,
                    override_rot,
                    original_scale,
                    override_scale,
                    original_speed=original_speed,
                    override_speed=override_speed,
                )

        if not override_on:
            override_index = original_index
            override_vis = original_vis
            override_pos = CMX_VECTOR_ZERO
            override_rot = original_rot
            override_scale = original_scale
            override_speed = original_speed

        _cmx_set_attribute_value(point_index_attr, slot_index, point_index)
        _cmx_set_attribute_value(original_index_attr, slot_index, original_index)
        _cmx_set_attribute_value(original_vis_attr, slot_index, original_vis)
        _cmx_set_attribute_value(original_pos_attr, slot_index, original_pos)
        _cmx_set_attribute_value(original_rot_attr, slot_index, original_rot)
        _cmx_set_attribute_value(original_scale_attr, slot_index, original_scale)
        _cmx_set_attribute_value(original_speed_attr, slot_index, original_speed)
        _cmx_set_attribute_value(override_index_attr, slot_index, override_index)
        for attr in override_on_attrs:
            _cmx_set_attribute_value(attr, slot_index, override_on)
        _cmx_set_attribute_value(override_vis_attr, slot_index, override_vis)
        _cmx_set_attribute_value(override_pos_attr, slot_index, override_pos)
        _cmx_set_attribute_value(override_rot_attr, slot_index, override_rot)
        _cmx_set_attribute_value(override_scale_attr, slot_index, override_scale)
        _cmx_set_attribute_value(override_speed_attr, slot_index, override_speed)
        runtime_state.append({
            "slot_index": slot_index,
            "point_index": point_index,
            "original_index": original_index,
            "original_vis": original_vis,
            "original_pos": original_pos,
            "original_rot": original_rot,
            "original_scale": original_scale,
            "original_speed": original_speed,
            "override_index": override_index,
            "override_on": override_on,
            "override_vis": override_vis,
            "override_pos": override_pos,
            "override_rot": override_rot,
            "override_scale": override_scale,
            "override_speed": override_speed,
        })
    mesh.update()
    _cmx_store_override_runtime_cache(crowd_item.name, runtime_state)

    return override_obj


def _cmx_clear_collection_objects(collection):
    if not collection:
        return
    for obj in list(collection.objects):
        mesh_data = obj.data if getattr(obj, "type", "") == 'MESH' else None
        bpy.data.objects.remove(obj, do_unlink=True)
        if mesh_data and mesh_data.users == 0:
            bpy.data.meshes.remove(mesh_data)


def _cmx_remove_proxy_collection(crowd_name):
    proxy_collection = bpy.data.collections.get(_cmx_get_proxy_collection_name(crowd_name))
    if not proxy_collection:
        return
    _cmx_clear_collection_objects(proxy_collection)
    for collection in bpy.data.collections:
        try:
            if proxy_collection.name in [child.name for child in collection.children]:
                collection.children.unlink(proxy_collection)
        except Exception:
            pass
    for scene in bpy.data.scenes:
        try:
            if proxy_collection.name in [child.name for child in scene.collection.children]:
                scene.collection.children.unlink(proxy_collection)
        except Exception:
            pass
    bpy.data.collections.remove(proxy_collection)


def _cmx_create_proxy_objects(context, crowd_item, point_data):
    _cmx_remove_proxy_collection(crowd_item.name)
    root_collection = _cmx_get_edit_instance_root_collection(context)
    proxy_collection = bpy.data.collections.new(_cmx_get_proxy_collection_name(crowd_item.name))
    root_collection.children.link(proxy_collection)

    crowd_obj = _cmx_get_crowd_node_object(crowd_item)
    if not crowd_obj:
        return proxy_collection

    for slot_index, item in enumerate(point_data):
        proxy_name = f"{crowd_item.name}_{item['point_index']}"
        existing_proxy = bpy.data.objects.get(proxy_name)
        if existing_proxy and (
            existing_proxy.get(CMX_EDIT_INSTANCE_PROXY_FLAG) or
            existing_proxy.get(CMX_EDIT_INSTANCE_PROXY_CROWD_PROP) == crowd_item.name
        ):
            bpy.data.objects.remove(existing_proxy, do_unlink=True)
        proxy_obj = bpy.data.objects.new(proxy_name, None)
        proxy_obj.empty_display_type = getattr(context.scene, "cmx_edit_instance_proxy_display_as", 'CUBE')
        proxy_obj.empty_display_size = 0.15
        proxy_obj.show_in_front = bool(getattr(context.scene, "cmx_edit_instance_proxy_in_front", True))
        proxy_obj.show_name = bool(getattr(context.scene, "cmx_edit_instance_proxy_show_names", False))
        proxy_obj.location = crowd_obj.matrix_world @ item["local_position"]
        proxy_obj[CMX_EDIT_INSTANCE_PROXY_FLAG] = True
        proxy_obj[CMX_EDIT_INSTANCE_PROXY_INDEX_PROP] = int(item["point_index"])
        proxy_obj[CMX_EDIT_INSTANCE_PROXY_SLOT_PROP] = int(slot_index)
        proxy_obj[CMX_EDIT_INSTANCE_PROXY_ORIGINAL_PROP] = int(item["original_index"])
        proxy_obj[CMX_EDIT_INSTANCE_PROXY_CROWD_PROP] = crowd_item.name
        proxy_collection.objects.link(proxy_obj)

    _cmx_apply_proxy_display_settings(context.scene, crowd_item.name)
    return proxy_collection


def _cmx_get_override_object(crowd_name):
    return bpy.data.objects.get(_cmx_get_override_object_name(crowd_name))


def _cmx_get_proxy_objects_for_crowd(crowd_name):
    proxy_collection = bpy.data.collections.get(_cmx_get_proxy_collection_name(crowd_name))
    if not proxy_collection:
        return []
    proxies = [obj for obj in proxy_collection.objects if _cmx_is_edit_instance_proxy_for_crowd(obj, crowd_name)]
    proxies.sort(key=lambda obj: int(obj.get(CMX_EDIT_INSTANCE_PROXY_SLOT_PROP, 0)))
    return proxies


def _cmx_get_proxy_object_by_slot(crowd_name, slot_index):
    for proxy_obj in _cmx_get_proxy_objects_for_crowd(crowd_name):
        try:
            current_slot = int(proxy_obj.get(CMX_EDIT_INSTANCE_PROXY_SLOT_PROP, -1))
        except Exception:
            current_slot = -1
        if current_slot == int(slot_index):
            return proxy_obj
    return None


def _cmx_get_proxy_object_by_point_index(crowd_name, point_index):
    for proxy_obj in _cmx_get_proxy_objects_for_crowd(crowd_name):
        try:
            current_point_index = int(proxy_obj.get(CMX_EDIT_INSTANCE_PROXY_INDEX_PROP, -1))
        except Exception:
            current_point_index = -1
        if current_point_index == int(point_index):
            return proxy_obj
    return None


def _cmx_apply_proxy_display_settings(scene, crowd_name=None):
    scene = scene or getattr(bpy.context, "scene", None)
    if not scene:
        return
    target_crowd_name = crowd_name or getattr(scene, "cmx_edit_instance_crowd_name", "")
    if not target_crowd_name:
        return
    display_type = getattr(scene, "cmx_edit_instance_proxy_display_as", 'CUBE')
    for proxy_obj in _cmx_get_proxy_objects_for_crowd(target_crowd_name):
        try:
            proxy_obj.empty_display_type = display_type
            proxy_obj.show_in_front = bool(getattr(scene, "cmx_edit_instance_proxy_in_front", True))
            proxy_obj.show_name = bool(getattr(scene, "cmx_edit_instance_proxy_show_names", False))
        except Exception:
            pass


def _cmx_set_crowd_node_selectable(crowd_item, selectable):
    crowd_obj = _cmx_get_crowd_node_object(crowd_item)
    if not crowd_obj:
        return

    if selectable:
        previous_hide_select = crowd_obj.get(CMX_EDIT_INSTANCE_PREV_HIDE_SELECT_PROP, None)
        try:
            crowd_obj.hide_select = bool(previous_hide_select) if previous_hide_select is not None else False
        except Exception:
            pass
        try:
            if CMX_EDIT_INSTANCE_PREV_HIDE_SELECT_PROP in crowd_obj:
                del crowd_obj[CMX_EDIT_INSTANCE_PREV_HIDE_SELECT_PROP]
        except Exception:
            pass
        return

    try:
        if CMX_EDIT_INSTANCE_PREV_HIDE_SELECT_PROP not in crowd_obj:
            crowd_obj[CMX_EDIT_INSTANCE_PREV_HIDE_SELECT_PROP] = bool(getattr(crowd_obj, "hide_select", False))
    except Exception:
        pass
    try:
        crowd_obj.hide_select = True
    except Exception:
        pass


def _cmx_get_selected_edit_instance_point_state(scene):
    crowd_name = getattr(scene, "cmx_edit_instance_crowd_name", "")
    point_index = getattr(scene, "cmx_edit_instance_selected_index", -1)
    slot_index = getattr(scene, "cmx_edit_instance_selected_slot", -1)
    original_index = getattr(scene, "cmx_edit_instance_selected_original_index", -1)
    if not crowd_name or point_index < 0 or slot_index < 0 or original_index < 0:
        return None

    cached_state = _cmx_get_cached_override_state(crowd_name, slot_index, point_index=point_index)
    if cached_state:
        return cached_state

    override_obj = _cmx_get_override_object(crowd_name)
    if not override_obj:
        return None
    return _cmx_get_override_runtime_state(override_obj, slot_index, point_index, original_index)


def _cmx_get_edit_instance_index_bounds(crowd_name):
    proxies = _cmx_get_proxy_objects_for_crowd(crowd_name)
    if not proxies:
        return None, None

    indices = []
    for proxy_obj in proxies:
        try:
            indices.append(int(proxy_obj.get(CMX_EDIT_INSTANCE_PROXY_ORIGINAL_PROP, -1)))
        except Exception:
            continue
    indices = [index for index in indices if index >= 0]
    if not indices:
        return None, None
    return min(indices), max(indices)


def _cmx_draw_edit_instance_inline_ui(layout, context, crowd_item):
    scene = context.scene
    crowd_name = getattr(scene, "cmx_edit_instance_crowd_name", "")
    if not crowd_item or crowd_name != crowd_item.name or not getattr(scene, "cmx_edit_instance_popup_visible", False):
        return

    wrapper = layout.box()
    display_row = wrapper.row(align=True)
    display_row.prop(scene, "cmx_edit_instance_proxy_display_as", text="Display As")
    display_row.prop(scene, "cmx_edit_instance_proxy_in_front", text="", toggle=True, icon='CUBE')
    display_row.prop(scene, "cmx_edit_instance_proxy_show_names", text="", toggle=True, icon='LONGDISPLAY')
    display_row.prop(scene, "cmx_edit_instance_ins_vis_only_select", text="", toggle=True, icon='MOD_MASK')

    point_state = _cmx_get_selected_edit_instance_point_state(scene)
    if not point_state:
        info = wrapper.box()
        info.label(text="Select a box to edit an instance index.", icon='INFO')
        return

    info = wrapper.box()
    info_col = info.column(align=True)
    row = info_col.row(align=True)
    status_icon = 'KEYTYPE_KEYFRAME_VEC' if point_state["override_on"] else 'HANDLETYPE_FREE_VEC'
    row.label(text="", icon=status_icon)
    row.label(text="|")
    row.label(text="", icon='STICKY_UVS_DISABLE')
    row.label(text=str(point_state["point_index"]))
    row.separator()
    instance_icon = 'USER'
    instance_value = point_state["override_index"] if point_state["override_on"] else point_state["original_index"]
    row.label(text="", icon=instance_icon)
    row.label(text=str(instance_value))
    row.separator()
    vis_icon = 'HIDE_OFF' if point_state["override_vis"] else 'HIDE_ON'
    row.label(text="", icon=vis_icon)

    transform_box = wrapper.box()
    transform_col = transform_box.column(align=True)
    pos_row = transform_col.row(align=True)
    pos_split = pos_row.split(factor=0.18, align=True)
    pos_split.label(text="Pos")
    pos_values = pos_split.row(align=True)
    pos_values.prop(scene, "cmx_edit_instance_override_pos", index=0, text="X")
    pos_values.prop(scene, "cmx_edit_instance_override_pos", index=1, text="Y")
    pos_values.prop(scene, "cmx_edit_instance_override_pos", index=2, text="Z")

    rot_row = transform_col.row(align=True)
    rot_split = rot_row.split(factor=0.18, align=True)
    rot_split.label(text="Rot")
    rot_split.prop(scene, "cmx_edit_instance_override_rot", index=2, text="Z")

    scale_row = transform_col.row(align=True)
    scale_split = scale_row.split(factor=0.18, align=True)
    scale_split.label(text="Scale")
    scale_split.prop(scene, "cmx_edit_instance_override_scale", text="")

    if _cmx_is_flow_curve_crowd_item(crowd_item):
        speed_row = transform_col.row(align=True)
        speed_split = speed_row.split(factor=0.18, align=True)
        speed_split.label(text="Speed")
        speed_split.prop(scene, "cmx_edit_instance_override_speed", text="")

    nav_row = transform_col.grid_flow(columns=4, even_columns=True, even_rows=True, align=True)
    vis_icon = 'HIDE_OFF' if getattr(scene, "cmx_edit_instance_override_vis", True) else 'HIDE_ON'
    nav_row.prop(scene, "cmx_edit_instance_override_vis", text="", toggle=True, icon=vis_icon)
    nav_row.operator("cmx.edit_instance_action", text="Previous", icon='TRIA_LEFT').action = 'PREVIOUS'
    nav_row.operator("cmx.edit_instance_action", text="Next", icon='TRIA_RIGHT').action = 'NEXT'
    nav_row.operator("cmx.edit_instance_action", text="Random", icon='FILE_REFRESH').action = 'RANDOM'

    reset_box = wrapper.box()
    reset_row = reset_box.grid_flow(columns=2, even_columns=True, even_rows=True, align=True)
    reset_row.operator("cmx.edit_instance_action", text="Reset Point", icon='LOOP_BACK').action = 'RESET'
    reset_row.operator("cmx.reset_all_edit_instance_overrides", text="Reset All")


def _cmx_find_override_slot(override_obj, point_index):
    geometry_data = getattr(override_obj, "data", None)
    if not geometry_data:
        return -1
    index_attr = _cmx_get_attribute(geometry_data, CMX_INDEX_ATTRIBUTE_NAMES)
    if not index_attr:
        return -1
    for slot_index in range(len(index_attr.data)):
        current_index = _cmx_get_attribute_value(index_attr, slot_index, slot_index)
        try:
            current_index = int(current_index)
        except Exception:
            current_index = slot_index
        if current_index == int(point_index):
            return slot_index
    return -1


def _cmx_get_override_point_state_by_slot(override_obj, slot_index):
    geometry_data = getattr(override_obj, "data", None)
    if not geometry_data:
        return None

    try:
        slot_index = int(slot_index)
    except Exception:
        return None

    index_attr = _cmx_get_attribute(geometry_data, CMX_INDEX_ATTRIBUTE_NAMES)
    if not index_attr or slot_index < 0 or slot_index >= len(index_attr.data):
        return None

    point_index = _cmx_get_attribute_value(index_attr, slot_index, slot_index)
    original_attr = _cmx_get_attribute(geometry_data, CMX_ORIGINAL_INSTANCE_ATTRIBUTE_NAMES)
    original_index = _cmx_get_attribute_value(original_attr, slot_index, 0)
    try:
        point_index = int(point_index)
    except Exception:
        point_index = slot_index
    try:
        original_index = int(original_index)
    except Exception:
        original_index = 0
    return _cmx_get_override_runtime_state(override_obj, slot_index, point_index, original_index)


def _cmx_get_override_point_state(override_obj, point_index):
    slot_index = _cmx_find_override_slot(override_obj, point_index)
    if slot_index < 0:
        return None
    return _cmx_get_override_point_state_by_slot(override_obj, slot_index)


def _cmx_get_override_runtime_state(override_obj, slot_index, point_index, original_index):
    geometry_data = getattr(override_obj, "data", None)
    if not geometry_data:
        return None

    try:
        slot_index = int(slot_index)
        point_index = int(point_index)
        original_index = int(original_index)
    except Exception:
        return None

    crowd_name = override_obj.get(CMX_EDIT_INSTANCE_PROXY_CROWD_PROP, "")
    supports_speed = _cmx_override_object_supports_speed(override_obj, crowd_name=crowd_name)
    cached_state = _cmx_get_cached_override_state(crowd_name, slot_index)
    if cached_state:
        return cached_state

    point_index_attr = _cmx_get_attribute(geometry_data, CMX_INDEX_ATTRIBUTE_NAMES)
    original_index_attr = _cmx_get_attribute(geometry_data, CMX_ORIGINAL_INSTANCE_ATTRIBUTE_NAMES)
    original_vis_attr = _cmx_get_attribute(geometry_data, CMX_ORIGINAL_VIS_ATTRIBUTE_NAMES)
    original_pos_attr = _cmx_get_attribute(geometry_data, CMX_ORIGINAL_POS_ATTRIBUTE_NAMES)
    original_rot_attr = _cmx_get_attribute(geometry_data, CMX_ORIGINAL_ROT_ATTRIBUTE_NAMES)
    original_scale_attr = _cmx_get_attribute(geometry_data, CMX_ORIGINAL_SCALE_ATTRIBUTE_NAMES)
    original_speed_attr = _cmx_get_attribute(geometry_data, CMX_ORIGINAL_SPEED_ATTRIBUTE_NAMES) if supports_speed else None
    override_index_attr = _cmx_get_attribute(geometry_data, CMX_OVERRIDE_INDEX_ATTRIBUTE_NAMES)
    override_on_attr = _cmx_get_attribute(geometry_data, CMX_OVERRIDE_ON_ATTRIBUTE_NAMES)
    override_vis_attr = _cmx_get_attribute(geometry_data, CMX_OVERRIDE_VIS_ATTRIBUTE_NAMES)
    override_pos_attr = _cmx_get_attribute(geometry_data, CMX_OVERRIDE_POS_ATTRIBUTE_NAMES)
    override_rot_attr = _cmx_get_attribute(geometry_data, CMX_OVERRIDE_ROT_ATTRIBUTE_NAMES)
    override_scale_attr = _cmx_get_attribute(geometry_data, CMX_OVERRIDE_SCALE_ATTRIBUTE_NAMES)
    override_speed_attr = _cmx_get_attribute(geometry_data, CMX_OVERRIDE_SPEED_ATTRIBUTE_NAMES) if supports_speed else None
    if not override_index_attr or slot_index < 0 or slot_index >= len(override_index_attr.data):
        return None

    point_index = _cmx_get_attribute_value(point_index_attr, slot_index, point_index)
    original_index = _cmx_get_attribute_value(original_index_attr, slot_index, original_index)
    original_vis = bool(_cmx_get_attribute_value(original_vis_attr, slot_index, True))
    original_pos = _cmx_to_float3(_cmx_get_attribute_value(original_pos_attr, slot_index, CMX_VECTOR_ZERO), CMX_VECTOR_ZERO)
    original_rot = _cmx_to_float3(_cmx_get_attribute_value(original_rot_attr, slot_index, CMX_VECTOR_ZERO), CMX_VECTOR_ZERO)
    original_scale = _cmx_to_float3(_cmx_get_attribute_value(original_scale_attr, slot_index, CMX_VECTOR_ONE), CMX_VECTOR_ONE)
    original_speed = _cmx_to_float(_cmx_get_attribute_value(original_speed_attr, slot_index, 1.0), 1.0)
    override_index = _cmx_get_attribute_value(override_index_attr, slot_index, original_index)
    override_on = bool(_cmx_get_attribute_value(override_on_attr, slot_index, False))
    override_vis = bool(_cmx_get_attribute_value(override_vis_attr, slot_index, original_vis))
    override_pos = _cmx_to_float3(_cmx_get_attribute_value(override_pos_attr, slot_index, CMX_VECTOR_ZERO), CMX_VECTOR_ZERO)
    override_rot = _cmx_to_float3(_cmx_get_attribute_value(override_rot_attr, slot_index, original_rot), original_rot)
    override_scale = _cmx_to_float3(_cmx_get_attribute_value(override_scale_attr, slot_index, original_scale), original_scale)
    override_speed = _cmx_to_float(_cmx_get_attribute_value(override_speed_attr, slot_index, original_speed), original_speed)
    try:
        point_index = int(point_index)
    except Exception:
        point_index = slot_index
    try:
        original_index = int(original_index)
    except Exception:
        original_index = 0
    try:
        override_index = int(override_index)
    except Exception:
        override_index = original_index

    return {
        "slot_index": slot_index,
        "point_index": point_index,
        "original_index": original_index,
        "original_vis": original_vis,
        "original_pos": original_pos,
        "original_rot": original_rot,
        "original_scale": original_scale,
        "original_speed": original_speed,
        "override_index": override_index,
        "override_on": override_on,
        "override_vis": override_vis,
        "override_pos": override_pos,
        "override_rot": override_rot,
        "override_scale": override_scale,
        "override_speed": override_speed,
    }


def _cmx_set_override_runtime_state(
    override_obj,
    slot_index,
    original_index,
    override_index,
    force_disable=False,
    override_vis=None,
    override_pos=None,
    override_rot=None,
    override_scale=None,
    override_speed=None,
    debug_source="",
):
    geometry_data = getattr(override_obj, "data", None)
    if not geometry_data:
        return False
    crowd_name = override_obj.get(CMX_EDIT_INSTANCE_PROXY_CROWD_PROP, "")

    state = _cmx_get_override_runtime_state(override_obj, slot_index, slot_index, original_index)
    if not state:
        return False

    override_index_attr = _cmx_get_attribute(geometry_data, CMX_OVERRIDE_INDEX_ATTRIBUTE_NAMES)
    override_on_attrs = [_cmx_get_attribute(geometry_data, (attr_name,)) for attr_name in CMX_OVERRIDE_ON_ATTRIBUTE_NAMES]
    override_vis_attr = _cmx_get_attribute(geometry_data, CMX_OVERRIDE_VIS_ATTRIBUTE_NAMES)
    override_pos_attr = _cmx_get_attribute(geometry_data, CMX_OVERRIDE_POS_ATTRIBUTE_NAMES)
    override_rot_attr = _cmx_get_attribute(geometry_data, CMX_OVERRIDE_ROT_ATTRIBUTE_NAMES)
    override_scale_attr = _cmx_get_attribute(geometry_data, CMX_OVERRIDE_SCALE_ATTRIBUTE_NAMES)
    original_speed_attr = _cmx_get_attribute(geometry_data, CMX_ORIGINAL_SPEED_ATTRIBUTE_NAMES)
    override_speed_attr = _cmx_get_attribute(geometry_data, CMX_OVERRIDE_SPEED_ATTRIBUTE_NAMES)
    original_vis = bool(state["original_vis"])
    original_pos = _cmx_to_float3(state["original_pos"], CMX_VECTOR_ZERO)
    original_rot = _cmx_to_float3(state["original_rot"], CMX_VECTOR_ZERO)
    original_scale = _cmx_to_float3(state["original_scale"], CMX_VECTOR_ONE)
    original_speed = _cmx_to_float(state.get("original_speed", _cmx_get_attribute_value(original_speed_attr, state["slot_index"], 1.0)), 1.0)
    if force_disable:
        override_index = int(original_index)
        override_vis = original_vis
        override_pos = CMX_VECTOR_ZERO
        override_rot = original_rot
        override_scale = original_scale
        override_speed = original_speed
    else:
        override_index = int(override_index)
        override_vis = state["override_vis"] if override_vis is None else bool(override_vis)
        override_pos = _cmx_to_float3(state["override_pos"] if override_pos is None else override_pos, CMX_VECTOR_ZERO)
        override_rot = _cmx_to_float3(state["override_rot"] if override_rot is None else override_rot, original_rot)
        override_scale = _cmx_to_float3(state["override_scale"] if override_scale is None else override_scale, original_scale)
        override_speed = _cmx_to_float(state.get("override_speed", original_speed) if override_speed is None else override_speed, original_speed)
    override_on = _cmx_compute_override_on_state(
        original_index,
        override_index,
        original_vis,
        override_vis,
        original_pos,
        override_pos,
        original_rot,
        override_rot,
        original_scale,
        override_scale,
        original_speed=original_speed,
        override_speed=override_speed,
        force_disable=force_disable,
    )

    _cmx_set_attribute_value(override_index_attr, state["slot_index"], override_index)
    for attr in override_on_attrs:
        _cmx_set_attribute_value(attr, state["slot_index"], override_on)
    _cmx_set_attribute_value(override_vis_attr, state["slot_index"], override_vis)
    _cmx_set_attribute_value(override_pos_attr, state["slot_index"], override_pos)
    _cmx_set_attribute_value(override_rot_attr, state["slot_index"], override_rot)
    _cmx_set_attribute_value(override_scale_attr, state["slot_index"], override_scale)
    _cmx_set_attribute_value(override_speed_attr, state["slot_index"], override_speed)
    try:
        geometry_data.update()
    except Exception:
        pass
    updated_state = dict(state)
    updated_state["override_index"] = int(override_index)
    updated_state["override_on"] = bool(override_on)
    updated_state["override_vis"] = bool(override_vis)
    updated_state["override_pos"] = _cmx_to_float3(override_pos, CMX_VECTOR_ZERO)
    updated_state["override_rot"] = _cmx_to_float3(override_rot, CMX_VECTOR_ZERO)
    updated_state["override_scale"] = _cmx_to_float3(override_scale, CMX_VECTOR_ONE)
    updated_state["original_speed"] = _cmx_to_float(original_speed, 1.0)
    updated_state["override_speed"] = _cmx_to_float(override_speed, 1.0)
    _cmx_update_override_runtime_cache_slot(crowd_name, state["slot_index"], updated_state)
    return True


def _cmx_set_override_point_state_by_slot(override_obj, slot_index, override_index, force_disable=False):
    point_state = _cmx_get_override_point_state_by_slot(override_obj, slot_index)
    if not point_state:
        return False
    return _cmx_set_override_runtime_state(
        override_obj,
        point_state["slot_index"],
        point_state["original_index"],
        override_index,
        force_disable=force_disable,
    )


def _cmx_set_override_point_state(override_obj, point_index, override_index, force_disable=False):
    point_state = _cmx_get_override_point_state(override_obj, point_index)
    if not point_state:
        return False
    return _cmx_set_override_point_state_by_slot(
        override_obj,
        point_state["slot_index"],
        override_index,
        force_disable=force_disable,
    )


def _cmx_override_object_has_active_overrides(override_obj):
    geometry_data = getattr(override_obj, "data", None)
    if not geometry_data:
        return False
    override_on_attr = _cmx_get_attribute(geometry_data, CMX_OVERRIDE_ON_ATTRIBUTE_NAMES)
    if not override_on_attr:
        return False
    return any(bool(_cmx_get_attribute_value(override_on_attr, index, False)) for index in range(len(override_on_attr.data)))


def _cmx_remove_override_object_if_unused(crowd_name, modifier=None):
    override_obj = _cmx_get_override_object(crowd_name)
    if not override_obj:
        return
    if _cmx_override_object_has_active_overrides(override_obj):
        _cmx_update_override_visibility(override_obj)
        if modifier:
            _cmx_set_modifier_input_by_names(modifier, CMX_OVERRIDE_INFO_SOCKET_NAMES, override_obj, socket_type='NodeSocketObject')
        return

    if modifier:
        _cmx_set_modifier_input_by_names(modifier, CMX_OVERRIDE_INFO_SOCKET_NAMES, None, socket_type='NodeSocketObject')

    mesh = override_obj.data
    bpy.data.objects.remove(override_obj, do_unlink=True)
    if mesh and mesh.users == 0:
        bpy.data.meshes.remove(mesh)


def _cmx_get_source_variant_count(crowd_item, modifier=None):
    modifier = modifier or cmx_get_crowd_modifier(crowd_item)
    source_collection = _cmx_get_modifier_input_by_names(modifier, CMX_PRIMARY_SOURCE_SOCKET_NAMES)
    if not isinstance(source_collection, bpy.types.Collection):
        source_collection = bpy.data.collections.get(getattr(crowd_item, "source_collection", ""))
    if not source_collection:
        return 0
    return len(source_collection.children)


def _cmx_is_edit_instance_proxy_for_crowd(obj, crowd_name):
    if not obj or not obj.get(CMX_EDIT_INSTANCE_PROXY_FLAG):
        return False
    return obj.get(CMX_EDIT_INSTANCE_PROXY_CROWD_PROP) == crowd_name


def _cmx_queue_edit_instance_popup():
    scene = getattr(bpy.context, "scene", None)
    if not scene:
        return None
    scene.cmx_edit_instance_popup_pending = False
    if (
        not scene.cmx_edit_instance_crowd_name or
        scene.cmx_edit_instance_selected_index < 0 or
        getattr(scene, "cmx_edit_instance_selected_slot", -1) < 0
    ):
        return None
    try:
        _cmx_show_edit_instance_popup(scene)
    except Exception:
        pass
    return None


def _cmx_show_edit_instance_popup(scene):
    crowd_name = getattr(scene, "cmx_edit_instance_popup_crowd_name", "") or getattr(scene, "cmx_edit_instance_crowd_name", "")
    if not crowd_name:
        return
    scene.show_modifier_settings = True
    scene.cmx_edit_instance_popup_visible = True
    _cmx_tag_redraw_all()


def _cmx_disable_edit_instance_mode(context, crowd_name=None, remove_override_if_unused=True):
    scene = context.scene
    target_crowd_name = crowd_name or getattr(scene, "cmx_edit_instance_crowd_name", "")
    if not target_crowd_name:
        scene.cmx_edit_instance_crowd_name = ""
        scene.cmx_edit_instance_selected_index = -1
        scene.cmx_edit_instance_selected_slot = -1
        scene.cmx_edit_instance_selected_original_index = -1
        scene.cmx_edit_instance_popup_pending = False
        scene.cmx_edit_instance_popup_visible = False
        scene.cmx_edit_instance_popup_last_index = -1
        scene.cmx_edit_instance_popup_crowd_name = ""
        scene.cmx_edit_instance_popup_target_index = -1
        scene.cmx_edit_instance_popup_target_slot = -1
        scene.cmx_edit_instance_popup_target_original_index = -1
        scene.cmx_edit_instance_ins_vis_only_select = False
        scene.cmx_edit_instance_ui_sync_lock = False
        scene.cmx_edit_instance_last_sync_time = 0.0
        scene.cmx_edit_instance_override_vis = True
        scene.cmx_edit_instance_override_pos = CMX_VECTOR_ZERO
        scene.cmx_edit_instance_override_rot = CMX_VECTOR_ZERO
        scene.cmx_edit_instance_override_scale = 0.0
        scene.cmx_edit_instance_override_speed = 1.0
        return

    crowd_item = next((item for item in scene.crowd_data_items if item.name == target_crowd_name), None)
    if crowd_item:
        _cmx_set_crowd_node_selectable(crowd_item, True)
    modifier = cmx_get_crowd_modifier(crowd_item or target_crowd_name)
    if modifier:
        _cmx_set_modifier_input_by_names(modifier, CMX_EDIT_INSTANCE_SOCKET_NAMES, False, socket_type='NodeSocketBool')
        _cmx_set_modifier_input_by_names(modifier, CMX_SELECT_INDEX_SOCKET_NAMES, -1, socket_type='NodeSocketInt')
        _cmx_set_modifier_input_by_names(modifier, CMX_INS_VIS_ONLY_SELECT_SOCKET_NAMES, False, socket_type='NodeSocketBool')
        if remove_override_if_unused:
            _cmx_remove_override_object_if_unused(target_crowd_name, modifier=modifier)
        cmx_refresh_modifier_display(modifier)
    elif remove_override_if_unused:
        _cmx_remove_override_object_if_unused(target_crowd_name, modifier=None)

    _cmx_remove_proxy_collection(target_crowd_name)
    _cmx_clear_override_runtime_cache(target_crowd_name)

    scene.cmx_edit_instance_crowd_name = ""
    scene.cmx_edit_instance_selected_index = -1
    scene.cmx_edit_instance_selected_slot = -1
    scene.cmx_edit_instance_selected_original_index = -1
    scene.cmx_edit_instance_popup_pending = False
    scene.cmx_edit_instance_popup_visible = False
    scene.cmx_edit_instance_popup_last_index = -1
    scene.cmx_edit_instance_popup_crowd_name = ""
    scene.cmx_edit_instance_popup_target_index = -1
    scene.cmx_edit_instance_popup_target_slot = -1
    scene.cmx_edit_instance_popup_target_original_index = -1
    scene.cmx_edit_instance_ins_vis_only_select = False
    scene.cmx_edit_instance_ui_sync_lock = False
    scene.cmx_edit_instance_last_sync_time = 0.0
    scene.cmx_edit_instance_override_vis = True
    scene.cmx_edit_instance_override_pos = CMX_VECTOR_ZERO
    scene.cmx_edit_instance_override_rot = CMX_VECTOR_ZERO
    scene.cmx_edit_instance_override_scale = 0.0
    scene.cmx_edit_instance_override_speed = 1.0
    _cmx_tag_redraw_all()


def _cmx_enable_edit_instance_mode(context, crowd_item):
    modifier = cmx_get_crowd_modifier(crowd_item)
    if not modifier:
        return False, "Crowd modifier not found."

    _cmx_set_crowd_node_selectable(crowd_item, False)
    _cmx_set_modifier_input_by_names(modifier, CMX_EDIT_INSTANCE_SOCKET_NAMES, True, socket_type='NodeSocketBool')
    _cmx_set_modifier_input_by_names(modifier, CMX_SELECT_INDEX_SOCKET_NAMES, -1, socket_type='NodeSocketInt')
    cmx_refresh_modifier_display(modifier)
    try:
        context.view_layer.update()
    except Exception:
        pass

    point_data = _cmx_collect_crowd_point_data(crowd_item)
    if not point_data:
        _cmx_set_crowd_node_selectable(crowd_item, True)
        _cmx_set_modifier_input_by_names(modifier, CMX_EDIT_INSTANCE_SOCKET_NAMES, False, socket_type='NodeSocketBool')
        _cmx_set_modifier_input_by_names(modifier, CMX_SELECT_INDEX_SOCKET_NAMES, -1, socket_type='NodeSocketInt')
        cmx_refresh_modifier_display(modifier)
        return False, "No crowd point data found. Check Blender console for CMX debug. The addon could not read cmx_index/cmx_original_ins_index from the crowd object's final mesh data."

    override_obj = _cmx_ensure_override_object(context, crowd_item, point_data)
    if not override_obj:
        _cmx_set_crowd_node_selectable(crowd_item, True)
        _cmx_set_modifier_input_by_names(modifier, CMX_EDIT_INSTANCE_SOCKET_NAMES, False, socket_type='NodeSocketBool')
        _cmx_set_modifier_input_by_names(modifier, CMX_SELECT_INDEX_SOCKET_NAMES, -1, socket_type='NodeSocketInt')
        cmx_refresh_modifier_display(modifier)
        return False, "Failed to create override data object."

    _cmx_create_proxy_objects(context, crowd_item, point_data)
    _cmx_set_modifier_input_by_names(modifier, CMX_OVERRIDE_INFO_SOCKET_NAMES, override_obj, socket_type='NodeSocketObject')
    _cmx_set_modifier_input_by_names(modifier, CMX_SELECT_INDEX_SOCKET_NAMES, -1, socket_type='NodeSocketInt')
    cmx_refresh_modifier_display(modifier)
    _cmx_write_override_runtime_cache_to_object(override_obj, _cmx_get_override_runtime_cache(crowd_item.name))

    scene = context.scene
    scene.cmx_edit_instance_crowd_name = crowd_item.name
    scene.cmx_edit_instance_selected_index = -1
    scene.cmx_edit_instance_selected_slot = -1
    scene.cmx_edit_instance_selected_original_index = -1
    scene.cmx_edit_instance_popup_pending = False
    scene.cmx_edit_instance_popup_visible = False
    scene.cmx_edit_instance_popup_last_index = -1
    scene.cmx_edit_instance_popup_crowd_name = crowd_item.name
    scene.cmx_edit_instance_popup_target_index = -1
    scene.cmx_edit_instance_popup_target_slot = -1
    scene.cmx_edit_instance_popup_target_original_index = -1
    scene.cmx_edit_instance_ui_sync_lock = False
    scene.cmx_edit_instance_last_sync_time = 0.0
    _cmx_sync_ins_vis_only_select_state(scene, crowd_item.name)
    scene.cmx_edit_instance_override_vis = True
    scene.cmx_edit_instance_override_pos = CMX_VECTOR_ZERO
    scene.cmx_edit_instance_override_rot = CMX_VECTOR_ZERO
    scene.cmx_edit_instance_override_scale = 0.0
    scene.cmx_edit_instance_override_speed = 1.0

    last_selection = _cmx_get_last_edit_instance_selection(crowd_item.name)
    if last_selection:
        selected_proxy = _cmx_get_proxy_object_by_point_index(crowd_item.name, last_selection["point_index"])
        if not selected_proxy:
            selected_proxy = _cmx_get_proxy_object_by_slot(crowd_item.name, last_selection["slot_index"])
        if selected_proxy:
            restored_point_index = int(selected_proxy.get(CMX_EDIT_INSTANCE_PROXY_INDEX_PROP, last_selection["point_index"]))
            restored_slot_index = int(selected_proxy.get(CMX_EDIT_INSTANCE_PROXY_SLOT_PROP, last_selection["slot_index"]))
            restored_original_index = int(selected_proxy.get(CMX_EDIT_INSTANCE_PROXY_ORIGINAL_PROP, last_selection["original_index"]))
            scene.cmx_edit_instance_selected_index = restored_point_index
            scene.cmx_edit_instance_selected_slot = restored_slot_index
            scene.cmx_edit_instance_selected_original_index = restored_original_index
            scene.cmx_edit_instance_popup_visible = True
            scene.cmx_edit_instance_popup_last_index = restored_point_index
            scene.cmx_edit_instance_popup_target_index = restored_point_index
            scene.cmx_edit_instance_popup_target_slot = restored_slot_index
            scene.cmx_edit_instance_popup_target_original_index = restored_original_index
            _cmx_set_modifier_input_by_names(modifier, CMX_SELECT_INDEX_SOCKET_NAMES, restored_point_index, socket_type='NodeSocketInt')
            _cmx_request_modifier_evaluation(modifier, refresh_display=False)
            _cmx_write_override_runtime_cache_to_object(override_obj, _cmx_get_override_runtime_cache(crowd_item.name))
            _cmx_sync_selected_override_ui_state(scene)
            _cmx_store_last_edit_instance_selection(crowd_item.name, restored_point_index, restored_slot_index, restored_original_index)
            try:
                view_layer = context.view_layer
                for selected_obj in getattr(context, "selected_objects", []):
                    if selected_obj != selected_proxy:
                        selected_obj.select_set(False)
                selected_proxy.select_set(True)
                if view_layer:
                    view_layer.objects.active = selected_proxy
            except Exception:
                pass
    _cmx_tag_redraw_all()
    return True, ""

def cmx_validate_source_name_for_preset_collection(source_name, preset_data):
    """
    Validate whether source_name can safely generate source child collection names.
    Returns (is_valid, suggested_name, offending_preset, safe_source_len).
    """
    if not source_name or not preset_data:
        return True, source_name, None, len(source_name or "")

    longest_preset_name = max(preset_data.keys(), key=len)
    safe_source_len = CMX_ID_NAME_LIMIT - 1 - len(longest_preset_name) - CMX_SOURCE_SUFFIX_LIMIT
    if len(source_name) <= safe_source_len:
        return True, source_name, None, safe_source_len

    suggested_name = source_name[:max(1, safe_source_len)].rstrip()
    if not suggested_name:
        suggested_name = source_name[:1]
    return False, suggested_name, longest_preset_name, safe_source_len


def _cmx_iter_collection_tree(root_collection):
    stack = [root_collection]
    visited = set()
    while stack:
        collection = stack.pop()
        if not collection:
            continue
        collection_key = collection.as_pointer()
        if collection_key in visited:
            continue
        visited.add(collection_key)
        yield collection
        stack.extend(list(collection.children))


def _cmx_unlink_collection_from_parent_collections(collection):
    """Unlink a collection from every scene/collection parent that references it."""
    if not collection:
        return

    for scene in list(bpy.data.scenes):
        try:
            if collection.name in [child.name for child in scene.collection.children]:
                scene.collection.children.unlink(collection)
        except Exception:
            pass

    for parent_collection in list(bpy.data.collections):
        if parent_collection == collection:
            continue
        try:
            if collection.name in [child.name for child in parent_collection.children]:
                parent_collection.children.unlink(collection)
        except Exception:
            pass


def _cmx_make_source_collections_local(root_collection):
    """
    Make only the collection tree local so CrowdMixer can rename and place the
    source collections without forcing the object hierarchy to detach first.
    """
    for collection in _cmx_iter_collection_tree(root_collection):
        try:
            if getattr(collection, "library", None) is not None:
                collection.make_local()
        except Exception:
            pass


def _cmx_override_source_hierarchy(root_collection):
    """
    Create editable overrides for linked objects and animation data so Source List
    controls can still modify NLA strips after importing via link.
    """
    for obj in list(root_collection.all_objects):
        try:
            if getattr(obj, "library", None) is not None and not obj.override_library:
                obj.override_create(remap_local_usages=True)
        except Exception:
            pass

        obj_data = getattr(obj, "data", None)
        try:
            if obj_data and getattr(obj_data, "library", None) is not None and not obj_data.override_library:
                obj_data.override_create(remap_local_usages=True)
        except Exception:
            pass

        for material_slot in getattr(obj, "material_slots", []):
            material = material_slot.material
            try:
                if material and getattr(material, "library", None) is not None and not material.override_library:
                    material.override_create(remap_local_usages=True)
            except Exception:
                pass

        animation_data = getattr(obj, "animation_data", None)
        if not animation_data:
            continue

        action_candidates = []
        action = getattr(animation_data, "action", None)
        if action:
            action_candidates.append(action)
        for track in getattr(animation_data, "nla_tracks", []):
            for strip in getattr(track, "strips", []):
                strip_action = getattr(strip, "action", None)
                if strip_action:
                    action_candidates.append(strip_action)

        seen_actions = set()
        for action_candidate in action_candidates:
            try:
                action_key = action_candidate.as_pointer()
            except Exception:
                action_key = id(action_candidate)
            if action_key in seen_actions:
                continue
            seen_actions.add(action_key)
            try:
                if getattr(action_candidate, "library", None) is not None and not action_candidate.override_library:
                    action_candidate.override_create(remap_local_usages=True)
            except Exception:
                pass


def _cmx_link_source_collection(blendfile, source_name):
    """
    Link the built source collection into the current file.

    Keep the source hierarchy linked while loading crowd presets. Creating
    overrides for the whole hierarchy can crash on some single-mesh sources,
    and appending everything as local data is heavier in the interactive UI.
    """
    with bpy.data.libraries.load(blendfile, link=True) as (data_from, data_to):
        if source_name not in data_from.collections:
            return None
        data_to.collections = [source_name]
    return bpy.data.collections.get(source_name)


def _cmx_ensure_source_item_for_collection(context, source_name, source_collection=None):
    """
    Register an already-loaded source collection in the Source List.

    Preset loading can leave source collections in the file even when the UI
    list item is missing, especially after a crash or a partial load. In that
    state, normal source validation rejects the name as a conflict, but the
    correct recovery is to rebuild the Source List entry around the existing
    collection.
    """
    source_name = (source_name or "").strip()
    if not source_name:
        return None

    scene = context.scene
    existing_item = next((it for it in scene.source_data_items if it.name == source_name), None)
    if existing_item:
        return existing_item

    source_collection = source_collection or bpy.data.collections.get(source_name)
    if not source_collection:
        return None

    item = scene.source_data_items.add()
    item.name = source_name
    if hasattr(item, "source_collection"):
        item.source_collection = source_name
    try:
        item.preset_collection = source_name
    except Exception:
        pass

    asset_scene = cmx_get_assets_scene()
    parent_sources = bpy.data.collections.get("CMX_Sources")
    if not parent_sources:
        parent_sources = bpy.data.collections.new("CMX_Sources")
        asset_scene.collection.children.link(parent_sources)
    if source_collection.name not in [c.name for c in parent_sources.children]:
        try:
            parent_sources.children.link(source_collection)
        except Exception:
            pass

    inst_root = bpy.data.collections.get("CMX_Sources_Instance")
    if not inst_root:
        inst_root = bpy.data.collections.new("CMX_Sources_Instance")
        context.scene.collection.children.link(inst_root)
    inst_coll_name = f"{source_name}_Instance"
    inst_coll = bpy.data.collections.get(inst_coll_name)
    if not inst_coll:
        inst_coll = bpy.data.collections.new(inst_coll_name)
    if inst_coll.name not in [c.name for c in inst_root.children]:
        inst_root.children.link(inst_coll)

    children = list(source_collection.children)
    total = len(children)
    for idx, child_coll in enumerate(children):
        inst_obj_name = f"{source_name}_{child_coll.name}"
        inst_obj = bpy.data.objects.get(inst_obj_name)
        if not inst_obj or inst_obj.type != 'EMPTY':
            inst_obj = bpy.data.objects.new(inst_obj_name, None)
            inst_obj.instance_type = 'COLLECTION'
            inst_obj.instance_collection = child_coll
            inst_obj.show_instancer_for_viewport = False
        if inst_obj.name not in [obj.name for obj in inst_coll.objects]:
            inst_coll.objects.link(inst_obj)
        cmx_calculate_instance_positions(inst_obj.name, idx, total, distance=1)

    return item


def _cmx_remove_action_if_unused(action):
    if not action:
        return
    try:
        if action.users > 0:
            return
        action.use_fake_user = False
    except Exception:
        pass
    try:
        if action.users == 0:
            bpy.data.actions.remove(action)
    except Exception:
        pass


def _cmx_remove_source_hierarchy(source_collection_name):
    """
    Remove a source collection tree together with its imported objects and
    actions so Blender 4.5 does not keep stale source data around.
    """
    root_collection = bpy.data.collections.get(source_collection_name)
    if not root_collection:
        return

    collection_tree = list(_cmx_iter_collection_tree(root_collection))
    object_list = []
    actions_to_cleanup = []
    seen_objects = set()
    seen_actions = set()

    for obj in list(root_collection.all_objects):
        try:
            obj_key = obj.as_pointer()
        except Exception:
            obj_key = id(obj)
        if obj_key in seen_objects:
            continue
        seen_objects.add(obj_key)
        object_list.append(obj)

        anim_data = getattr(obj, "animation_data", None)
        if not anim_data:
            continue

        action = getattr(anim_data, "action", None)
        if action:
            try:
                action_key = action.as_pointer()
            except Exception:
                action_key = id(action)
            if action_key not in seen_actions:
                seen_actions.add(action_key)
                actions_to_cleanup.append(action)

        for track in getattr(anim_data, "nla_tracks", []):
            for strip in getattr(track, "strips", []):
                strip_action = getattr(strip, "action", None)
                if not strip_action:
                    continue
                try:
                    action_key = strip_action.as_pointer()
                except Exception:
                    action_key = id(strip_action)
                if action_key in seen_actions:
                    continue
                seen_actions.add(action_key)
                actions_to_cleanup.append(strip_action)

    for obj in object_list:
        try:
            bpy.data.objects.remove(obj, do_unlink=True)
        except Exception:
            try:
                for parent_collection in list(getattr(obj, "users_collection", [])):
                    parent_collection.objects.unlink(obj)
                bpy.data.objects.remove(obj)
            except Exception:
                pass

    for collection in reversed(collection_tree):
        try:
            for child_collection in list(collection.children):
                collection.children.unlink(child_collection)
        except Exception:
            pass
        _cmx_unlink_collection_from_parent_collections(collection)
        try:
            bpy.data.collections.remove(collection)
        except Exception:
            pass

    for action in actions_to_cleanup:
        _cmx_remove_action_if_unused(action)


def cmx_add_source_data_item(context, source_name):
    """
    Core logic to append a source collection from CMX-Source and register it as a source item.
    Returns the created source item or None on failure.
    """
    scene = context.scene
    source_dir = cmx_get_source_dir(create_if_missing=False)
    if not source_dir or not source_name:
        return None

    desired_name = (source_name or "").strip()
    cmx_set_progress_task("Load Source", desired_name)

    is_valid_name, _message = _cmx_validate_source_target_name(scene, desired_name)
    if not is_valid_name:
        return None
    can_load_source, _load_message = _cmx_validate_source_library_load(scene, source_name)
    if not can_load_source:
        return None

    blendfile = os.path.join(source_dir, source_name + ".blend")
    if not os.path.exists(blendfile):
        return None
    try:
        item = scene.source_data_items.add()
        item.name = desired_name
        try:
            enum_items = cmx_get_preset_collections_item(None, context)
            if enum_items:
                item.preset_collection = enum_items[0][0]
        except Exception:
            pass

        # find existing base collection or append if missing
        new_coll = _cmx_link_source_collection(blendfile, source_name)
        if not new_coll:
            scene.source_data_items.remove(len(scene.source_data_items)-1)
            return None
        # unlink from any parent so it only lives where we place it
        _cmx_unlink_collection_from_parent_collections(new_coll)

        asset_scene = cmx_get_assets_scene()
        parent_sources = bpy.data.collections.get("CMX_Sources")
        if not parent_sources:
            parent_sources = bpy.data.collections.new("CMX_Sources")
            asset_scene.collection.children.link(parent_sources)
        if new_coll.name not in [c.name for c in parent_sources.children]:
            parent_sources.children.link(new_coll)

        if new_coll.name != desired_name and getattr(new_coll, "library", None) is None:
            new_coll.name = desired_name
       
        if hasattr(item, "source_collection"):
            item.source_collection = desired_name
        item.preset_collection = source_name
        item.name = desired_name

        # Create instance collection and instance objects for each child collection
        inst_root = bpy.data.collections.get("CMX_Sources_Instance")
        if not inst_root:
            inst_root = bpy.data.collections.new("CMX_Sources_Instance")
            context.scene.collection.children.link(inst_root)
        inst_coll_name = f"{new_coll.name}_Instance"
        inst_coll = bpy.data.collections.get(inst_coll_name)
        if not inst_coll:
            inst_coll = bpy.data.collections.new(inst_coll_name)
            inst_root.children.link(inst_coll)
        elif inst_coll.name not in [c.name for c in inst_root.children]:
            inst_root.children.link(inst_coll)

        children = list(new_coll.children)
        targets = children
        total = len(targets)
        for idx, child_coll in enumerate(targets):
            inst_obj_name = f"{new_coll.name}_{child_coll.name}"
            inst_obj = bpy.data.objects.get(inst_obj_name)
            if not inst_obj or inst_obj.type != 'EMPTY':
                inst_obj = bpy.data.objects.new(inst_obj_name, None)
                inst_obj.instance_type = 'COLLECTION'
                inst_obj.instance_collection = child_coll
                inst_obj.show_instancer_for_viewport = False
            if inst_obj.name not in [obj.name for obj in inst_coll.objects]:
                inst_coll.objects.link(inst_obj)
            cmx_calculate_instance_positions(inst_obj.name, idx, total, distance=1)

        try:
            cmx_active_nla(new_coll.name)
        except Exception:
            pass
        return item
    except Exception:
        try:
            scene.source_data_items.remove(len(scene.source_data_items)-1)
        except Exception:
            pass
        return None

def cmx_draw_panel_crowd(self, context, Main_panel_col):
    """
    Draw the main Crowd Mixer crowd panel UI. 
    Includes UI for crowd presets, source list, and crowd list, with controls for loading, saving, and modifying crowd items.
    """
    scene = context.scene
    wm = context.window_manager
    pop_size = cmx_get_popup_preview_size(context)

    main_layout = Main_panel_col.column(align=True)

    # Crowd Preset Section
    col = main_layout.column(align=True)

    row_L1 = col.row()
    col_L2 = row_L1.column(align=True)
    col_L3 = col_L2.column(align=True)
    col_L3.template_icon_view(wm, "crowd_preset", show_labels=False, scale=ICON_VIEW_SCALE + 2, scale_popup=pop_size)
    col_L3 = col_L2.column(align=True)
    col_L3.operator("cmx.load_preset_crowd", text="Load Preset Crowd", icon_value=get_cf_icon("main_panel_preset_apply"))
    col_L3.scale_y = 1.5

    col_L2 = row_L1.column(align=True)
    # col_L2.operator("cmx.save_preset_crowd", text="", icon_value=get_cf_icon("cf_new_preset"))
    # col_L2.operator("cmx.remove_preset_crowd", text="", icon_value=get_cf_icon("main_panel_crowd_remove"))

    main_layout.separator(factor=0.6)

    # Source List Section
    section_box = main_layout.box()
    col = section_box.column(align=True)
    row_L1 = col.row(align=True)
    row_L1.scale_y = 1.1
    icon_status = 'TRIA_DOWN' if scene.show_source_list else 'TRIA_RIGHT'
    row_L1.prop(scene, "show_source_list", text="", emboss=False, icon=icon_status)
    title_row = row_L1.row(align=True)
    title_row.alignment = 'LEFT'
    title_row.prop(scene, "show_source_list", text="Source List", emboss=False, icon_value=get_cf_icon("main_panel_crowd_list"))

    if scene.show_source_list:
        col.separator(factor=0.15)
        body_col = col.column(align=True)
        row_L1 = body_col.row()
        row_L1.template_list("CMX_UL_SourceData", "", scene, "source_data_items", scene, "source_data_index", rows=5)
        col_L2 = row_L1.column(align=True)
        col_L2.operator("cmx.source_data_add_item", text="", icon_value=get_cf_icon("main_panel_crowd_source_add"))
        col_L2.operator("cmx.source_data_remove_item", text="", icon_value=get_cf_icon("main_panel_crowd_remove"))
        body_col.separator(factor=0.05)

    main_layout.separator(factor=0.3)

    # Crowd List Section
    section_box = main_layout.box()
    col = section_box.column(align=True)
    icon_status = 'TRIA_DOWN' if scene.show_crowd_list else 'TRIA_RIGHT'
    split_header = col.split(factor=0.90, align=True)
    row_L1 = split_header.row(align=True)
    row_L1.scale_y = 1.1
    row_L1.prop(scene, "show_crowd_list", text="", emboss=False, icon=icon_status)
    title_row = row_L1.row(align=True)
    title_row.alignment = 'LEFT'
    title_row.prop(scene, "show_crowd_list", text="Crowd List", emboss=False, icon_value=get_cf_icon("main_panel_crowd_list"))
    sync_row = split_header.row(align=True)
    sync_row.scale_y = 1.1
    sync_row.prop(scene, "sync_crowd_selection", text="", toggle=True, icon='FILE_REFRESH')

    if scene.show_crowd_list:
        col.separator(factor=0.15)
        body_col = col.column(align=True)
        row_L1 = body_col.row()
        row_L1.template_list("CMX_UL_CrowdData", "", scene, "crowd_data_items", scene, "crowd_data_index", rows=5)
        col_L2 = row_L1.column(align=True)
        col_L2.operator("cmx.crowd_data_add_item", text="", icon_value=get_cf_icon("main_panel_crowd_add"))
        col_L2.operator("cmx.crowd_data_duplicate_item", text="", icon_value=get_cf_icon("main_panel_crowd_duplicate"))
        col_L2.operator("cmx.crowd_data_remove_item", text="", icon_value=get_cf_icon("main_panel_crowd_remove"))
        body_col.separator(factor=0.05)

    main_layout.separator(factor=0.3)

    # Crowd Setting Section
    section_box = main_layout.box()
    col = section_box.column(align=True)
    row_L1 = col.row(align=True)
    row_L1.scale_y = 1.1
    icon_status = 'TRIA_DOWN' if scene.show_modifier_settings else 'TRIA_RIGHT'
    row_L1.prop(scene, "show_modifier_settings", text="", emboss=False, icon=icon_status)
    row_L1.prop(scene, "show_modifier_settings", text="Crowd Setting", emboss=False, icon='MODIFIER')

    if scene.show_modifier_settings:
        col.separator(factor=0.15)
        if scene.sync_crowd_selection:
            modifier_item = _cmx_get_active_or_selected_crowd_item(scene, context)
        else:
            modifier_item = _cmx_get_selected_crowd_item(scene)
        modifier = cmx_get_crowd_modifier(modifier_item) if modifier_item else None
        if modifier_item and modifier and modifier.type == 'NODES' and modifier.node_group:
            box = col.box()
            row_L1 = box.row(align=True)
            row_L1.label(
                text=_cmx_format_crowd_modifier_header_text(modifier_item.name, modifier, modifier_item),
                icon_value=get_cf_icon(modifier_item.crowd_obj_name),
            )
            body_col = box.column(align=True)
            is_edit_mode_for_item = scene.cmx_edit_instance_crowd_name == modifier_item.name
            if is_edit_mode_for_item:
                info_box = body_col.box()
                info_box.label(text="Select a proxy box in the viewport.")
                _cmx_draw_edit_instance_inline_ui(body_col, context, modifier_item)
            else:
                cmx_draw_geometry_node_inputs(
                    body_col,
                    modifier,
                    modifier_item.source_collection,
                    wm=context.window_manager,
                    crowd_type=modifier_item.crowd_obj_name,
                    crowd_item_name=modifier_item.name
                )
        else:
            placeholder = col.box()
            placeholder.label(text="Select a Crowd Node to edit modifier settings.")


def _cmx_get_selected_crowd_item(scene):
    if not scene:
        return None
    index = getattr(scene, "crowd_data_index", -1)
    items = getattr(scene, "crowd_data_items", None)
    if items and 0 <= index < len(items):
        return items[index]
    return None


def _cmx_get_crowd_node_object(crowd_item_input):
    crowd_item = crowd_item_input if hasattr(crowd_item_input, "name") else None
    if not crowd_item:
        return None

    crowd_collection = bpy.data.collections.get(crowd_item.name)
    if not crowd_collection or not crowd_collection.objects:
        return None

    crowd_node_obj = None
    crowd_object_name_hint = getattr(crowd_item, "crowd_obj_name", "")
    if crowd_object_name_hint:
        crowd_node_obj = crowd_collection.objects.get(crowd_object_name_hint)

    if not crowd_node_obj:
        for obj in crowd_collection.objects:
            if obj.modifiers:
                for modifier in obj.modifiers:
                    if modifier.type == 'NODES' and modifier.node_group:
                        crowd_node_obj = obj
                        break
            if crowd_node_obj:
                break

    if not crowd_node_obj and crowd_collection.objects:
        crowd_node_obj = crowd_collection.objects[0]

    return crowd_node_obj


def _cmx_get_view_layer_crowd_node_object(context, crowd_item):
    if not context or not crowd_item:
        return None

    view_layer = getattr(context, "view_layer", None)
    crowd_node_obj = _cmx_get_crowd_node_object(crowd_item)
    if not view_layer or not crowd_node_obj:
        return None

    return view_layer.objects.get(crowd_node_obj.name)


def _cmx_get_crowd_item_from_object(scene, obj):
    if not scene or not obj:
        return None, -1

    selected_item = _cmx_get_selected_crowd_item(scene)
    if selected_item and _cmx_get_crowd_node_object(selected_item) == obj:
        return selected_item, scene.crowd_data_index

    for index, item in enumerate(scene.crowd_data_items):
        if _cmx_get_crowd_node_object(item) == obj:
            return item, index

    return None, -1


def _cmx_select_crowd_item_in_list(scene, crowd_item=None, crowd_index=None):
    if not scene:
        return False

    items = getattr(scene, "crowd_data_items", None)
    if not items:
        return False

    resolved_index = int(crowd_index) if crowd_index is not None else -1
    if resolved_index < 0 and crowd_item:
        for index, item in enumerate(items):
            if item == crowd_item or getattr(item, "name", "") == getattr(crowd_item, "name", ""):
                resolved_index = index
                break

    if resolved_index < 0 or resolved_index >= len(items):
        return False
    if getattr(scene, "crowd_data_index", -1) == resolved_index:
        return True

    scene.is_syncing_selection = True
    try:
        scene.crowd_data_index = resolved_index
    finally:
        scene.is_syncing_selection = False
    return True


def _cmx_select_crowd_item_in_viewport(scene, context, crowd_item):
    if not scene or not context or not crowd_item:
        return False

    view_layer_obj = _cmx_get_view_layer_crowd_node_object(context, crowd_item)
    view_layer = getattr(context, "view_layer", None)
    if not view_layer_obj or not view_layer:
        return False

    active_obj = getattr(view_layer.objects, "active", None)
    selected_objects = tuple(getattr(context, "selected_objects", ()) or ())
    if (
        active_obj == view_layer_obj and
        len(selected_objects) == 1 and
        selected_objects[0] == view_layer_obj and
        view_layer_obj.select_get()
    ):
        return True

    scene.is_syncing_selection = True
    try:
        for selected_obj in selected_objects:
            if selected_obj != view_layer_obj:
                selected_obj.select_set(False)
        if not view_layer_obj.select_get():
            view_layer_obj.select_set(True)
        if active_obj != view_layer_obj:
            view_layer.objects.active = view_layer_obj
    finally:
        scene.is_syncing_selection = False

    return True


def _cmx_get_active_or_selected_crowd_item(scene, context):
    active_item, _ = _cmx_get_crowd_item_from_object(scene, getattr(context, "object", None))
    if active_item:
        return active_item
    return _cmx_get_selected_crowd_item(scene)


def _cmx_update_crowd_selection_from_list(scene, context):
    if not scene or not context:
        return
    if not scene.sync_crowd_selection or scene.is_syncing_selection:
        return

    crowd_item = _cmx_get_selected_crowd_item(scene)
    _cmx_select_crowd_item_in_viewport(scene, context, crowd_item)


@persistent
def _cmx_sync_crowd_list_from_viewport(scene, depsgraph):
    if not scene or not getattr(scene, "sync_crowd_selection", False) or getattr(scene, "is_syncing_selection", False):
        return

    context = bpy.context
    if not context or context.scene != scene:
        return

    active_obj = context.object
    if not active_obj:
        return

    selected_item = _cmx_get_selected_crowd_item(scene)
    if selected_item and _cmx_get_crowd_node_object(selected_item) == active_obj:
        return

    crowd_item, crowd_index = _cmx_get_crowd_item_from_object(scene, active_obj)
    if not crowd_item or crowd_index < 0:
        return

    scene.is_syncing_selection = True
    try:
        scene.crowd_data_index = crowd_index
    finally:
        scene.is_syncing_selection = False


def _cmx_edit_instance_poll_timer():
    global CMX_EDIT_INSTANCE_TIMER_RUNNING

    if not CMX_EDIT_INSTANCE_TIMER_RUNNING:
        return None

    context = bpy.context
    scene = getattr(context, "scene", None)
    if not context or not scene:
        return CMX_EDIT_INSTANCE_POLL_INTERVAL

    active_crowd_name = getattr(scene, "cmx_edit_instance_crowd_name", "")
    if not active_crowd_name:
        return CMX_EDIT_INSTANCE_POLL_INTERVAL

    active_obj = getattr(context, "object", None)
    crowd_item = next((item for item in scene.crowd_data_items if item.name == active_crowd_name), None)
    crowd_node_obj = _cmx_get_crowd_node_object(crowd_item) if crowd_item else None

    if not active_obj:
        return CMX_EDIT_INSTANCE_POLL_INTERVAL

    if _cmx_is_edit_instance_proxy_for_crowd(active_obj, active_crowd_name):
        proxy_index = active_obj.get(CMX_EDIT_INSTANCE_PROXY_INDEX_PROP, -1)
        proxy_slot = active_obj.get(CMX_EDIT_INSTANCE_PROXY_SLOT_PROP, -1)
        proxy_original = active_obj.get(CMX_EDIT_INSTANCE_PROXY_ORIGINAL_PROP, -1)
        try:
            proxy_index = int(proxy_index)
        except Exception:
            proxy_index = -1
        try:
            proxy_slot = int(proxy_slot)
        except Exception:
            proxy_slot = -1
        try:
            proxy_original = int(proxy_original)
        except Exception:
            proxy_original = -1
        if proxy_index < 0 or proxy_slot < 0 or proxy_original < 0:
            return CMX_EDIT_INSTANCE_POLL_INTERVAL

        if crowd_item:
            _cmx_select_crowd_item_in_list(scene, crowd_item=crowd_item)

        selection_changed = (
            scene.cmx_edit_instance_selected_index != proxy_index or
            getattr(scene, "cmx_edit_instance_selected_slot", -1) != proxy_slot or
            getattr(scene, "cmx_edit_instance_selected_original_index", -1) != proxy_original
        )
        if selection_changed:
            scene.cmx_edit_instance_selected_index = proxy_index
            scene.cmx_edit_instance_selected_slot = proxy_slot
            scene.cmx_edit_instance_selected_original_index = proxy_original
            _cmx_store_last_edit_instance_selection(active_crowd_name, proxy_index, proxy_slot, proxy_original)
            scene.cmx_edit_instance_popup_crowd_name = active_crowd_name
            scene.cmx_edit_instance_popup_target_index = proxy_index
            scene.cmx_edit_instance_popup_target_slot = proxy_slot
            scene.cmx_edit_instance_popup_target_original_index = proxy_original

            modifier = cmx_get_crowd_modifier(crowd_item or active_crowd_name)
            override_obj = _cmx_get_override_object(active_crowd_name)
            if modifier:
                _cmx_set_modifier_input_by_names(modifier, CMX_SELECT_INDEX_SOCKET_NAMES, proxy_index, socket_type='NodeSocketInt')
                _cmx_request_modifier_evaluation(modifier, refresh_display=False)
                if override_obj:
                    _cmx_write_override_runtime_cache_to_object(override_obj, _cmx_get_override_runtime_cache(active_crowd_name))

            _cmx_sync_selected_override_vis_state(scene)
            scene.cmx_edit_instance_popup_last_index = proxy_index
            _cmx_tag_redraw_all()
        if (
            not getattr(scene, "cmx_edit_instance_popup_visible", False) and
            not getattr(scene, "cmx_edit_instance_popup_pending", False)
        ):
            scene.cmx_edit_instance_popup_crowd_name = active_crowd_name
            scene.cmx_edit_instance_popup_target_index = proxy_index
            scene.cmx_edit_instance_popup_target_slot = proxy_slot
            scene.cmx_edit_instance_popup_target_original_index = proxy_original
            scene.cmx_edit_instance_popup_pending = True
            bpy.app.timers.register(_cmx_queue_edit_instance_popup, first_interval=0.01)
        return CMX_EDIT_INSTANCE_POLL_INTERVAL

    if crowd_node_obj and active_obj == crowd_node_obj and scene.cmx_edit_instance_selected_index < 0:
        return CMX_EDIT_INSTANCE_POLL_INTERVAL

    return CMX_EDIT_INSTANCE_POLL_INTERVAL

def _cmx_get_panel_state(wm, name):
    """Fetch or create expand/collapse state for a modifier sub panel."""
    if not hasattr(wm, "crowd_modifier_panels"):
        return None
    for item in wm.crowd_modifier_panels:
        if item.name == name:
            return item
    new_item = wm.crowd_modifier_panels.add()
    new_item.name = name
    new_item.expanded = False
    return new_item


def _cmx_find_modifier_input_socket(modifier, socket_names, socket_type=None):
    if not modifier or not modifier.node_group or not modifier.node_group.interface:
        return None

    for item in modifier.node_group.interface.items_tree:
        if item.item_type != 'SOCKET' or item.in_out != 'INPUT':
            continue
        if socket_type and item.socket_type != socket_type:
            continue
        if _cmx_socket_matches(item, socket_names):
            return item
    return None


def _cmx_get_modifier_input_value_by_socket_name(modifier, socket_names):
    """Return a modifier input value by geometry-node socket name or display description."""
    socket_item = _cmx_find_modifier_input_socket(modifier, socket_names)
    if not socket_item:
        return None
    return modifier.get(socket_item.identifier)


def _cmx_find_modifier_output_socket(modifier, socket_names, socket_type=None):
    if not modifier or not modifier.node_group or not modifier.node_group.interface:
        return None

    for item in modifier.node_group.interface.items_tree:
        if item.item_type != 'SOCKET' or item.in_out != 'OUTPUT':
            continue
        if socket_type and item.socket_type != socket_type:
            continue
        if _cmx_socket_matches(item, socket_names):
            return item
    return None


def _cmx_get_modifier_output_value_by_socket_name(modifier, socket_names):
    socket_item = _cmx_find_modifier_output_socket(modifier, socket_names)
    if not socket_item:
        return None

    candidate_modifiers = [modifier]
    try:
        modifier_owner = getattr(modifier, "id_data", None)
        if modifier_owner and hasattr(modifier_owner, "evaluated_get"):
            depsgraph = bpy.context.evaluated_depsgraph_get()
            evaluated_owner = modifier_owner.evaluated_get(depsgraph)
            evaluated_modifier = evaluated_owner.modifiers.get(modifier.name) if evaluated_owner else None
            if evaluated_modifier and evaluated_modifier is not modifier:
                candidate_modifiers.append(evaluated_modifier)
    except Exception:
        pass

    candidate_keys = (
        getattr(socket_item, "identifier", ""),
        getattr(socket_item, "name", ""),
        getattr(socket_item, "description", ""),
    )

    for candidate_modifier in candidate_modifiers:
        for key in candidate_keys:
            if not key:
                continue
            value = candidate_modifier.get(key)
            if value is not None:
                return value

        for key in candidate_modifier.keys():
            if _cmx_name_matches(key, socket_names):
                value = candidate_modifier.get(key)
                if value is not None:
                    return value

    return None


def _cmx_get_crowd_instance_count_from_geometry(geometry_data):
    count_attr = _cmx_get_attribute(geometry_data, CMX_INS_COUNT_OUTPUT_SOCKET_NAMES)
    if not count_attr:
        return None

    values = []
    for index in range(len(getattr(count_attr, "data", []))):
        value = _cmx_get_attribute_value(count_attr, index, None)
        if value is None:
            continue
        try:
            numeric_value = int(value)
        except Exception:
            try:
                numeric_value = int(float(value))
            except Exception:
                continue
        values.append(numeric_value)

    if not values:
        return None
    instance_count = max(values)
    return instance_count if instance_count > 0 else None


def _cmx_get_crowd_instance_count(modifier, crowd_item=None):
    if not modifier:
        return None

    output_value = _cmx_get_modifier_output_value_by_socket_name(
        modifier,
        CMX_INS_COUNT_OUTPUT_SOCKET_NAMES,
    )
    if isinstance(output_value, (int, float)):
        output_value = int(output_value)
        if output_value > 0:
            return output_value

    modifier_owner = getattr(modifier, "id_data", None)
    if not modifier_owner:
        return None

    depsgraph = None
    evaluated_owner = None
    try:
        depsgraph = bpy.context.evaluated_depsgraph_get()
        evaluated_owner = modifier_owner.evaluated_get(depsgraph)
    except Exception:
        evaluated_owner = None

    candidates = []
    seen_candidate_ids = set()

    def _add_candidate(geometry_data):
        if not geometry_data:
            return
        candidate_id = id(geometry_data)
        if candidate_id in seen_candidate_ids:
            return
        seen_candidate_ids.add(candidate_id)
        candidates.append(geometry_data)

    _add_candidate(getattr(modifier_owner, "data", None))
    _add_candidate(getattr(evaluated_owner, "data", None))

    temp_mesh = None
    if evaluated_owner and depsgraph:
        try:
            temp_mesh = evaluated_owner.to_mesh(preserve_all_data_layers=True, depsgraph=depsgraph)
        except Exception:
            temp_mesh = None
    _add_candidate(temp_mesh)

    try:
        for geometry_data in candidates:
            instance_count = _cmx_get_crowd_instance_count_from_geometry(geometry_data)
            if instance_count is not None:
                return instance_count
    finally:
        if temp_mesh and evaluated_owner:
            try:
                evaluated_owner.to_mesh_clear()
            except Exception:
                pass

    if crowd_item:
        try:
            point_count = len(_cmx_collect_crowd_point_data(crowd_item))
            if point_count > 0:
                return point_count
        except Exception:
            pass

    return None


def _cmx_format_crowd_modifier_header_text(crowd_name, modifier, crowd_item=None):
    if not modifier:
        return crowd_name

    output_value = _cmx_get_crowd_instance_count(modifier, crowd_item=crowd_item)
    if output_value is None:
        return crowd_name

    return f"{crowd_name} ({output_value})"


def _cmx_get_modifier_interface_panel(modifier, panel_name):
    if not modifier or not modifier.node_group or not modifier.node_group.interface:
        return None

    panel_names = panel_name if isinstance(panel_name, (set, tuple, list)) else {panel_name}
    for item in modifier.node_group.interface.items_tree:
        if item.item_type == 'PANEL' and _cmx_name_matches(item.name, panel_names):
            return item
    return None


def _cmx_get_standing_emitter_object(modifier):
    emitter_object = _cmx_get_modifier_input_value_by_socket_name(
        modifier,
        CMX_EMITTER_OBJECT_SOCKET_NAMES,
    )
    if isinstance(emitter_object, bpy.types.Object):
        return emitter_object
    return None


def _cmx_is_density_mask_socket(if_item):
    return if_item.socket_type == 'NodeSocketString' and _cmx_socket_matches(if_item, CMX_DENSITY_MASK_SOCKET_NAMES)


def _cmx_is_density_socket(if_item):
    return (
        if_item.item_type == 'SOCKET' and
        if_item.in_out == 'INPUT' and
        _cmx_socket_matches(if_item, CMX_DENSITY_SOCKET_NAMES) and
        not _cmx_socket_matches(if_item, CMX_DENSITY_MASK_SOCKET_NAMES)
    )


def _cmx_ensure_density_mask_default(modifier, socket_identifier):
    current_value = modifier.get(socket_identifier)
    if current_value in {None, "", "None", CMX_DENSITY_MASK_NONE_LABEL}:
        modifier[socket_identifier] = CMX_DENSITY_MASK_NONE_VALUE
        return CMX_DENSITY_MASK_NONE_VALUE
    return current_value


def _cmx_get_density_mask_display_value(modifier, socket_identifier):
    current_value = modifier.get(socket_identifier)
    if current_value in {None, "", "None", CMX_DENSITY_MASK_NONE_LABEL}:
        return CMX_DENSITY_MASK_NONE_LABEL
    return current_value


def _cmx_ensure_standing_density_mask_default(modifier, crowd_type):
    if crowd_type != "CMX_Standing_Crowd":
        return
    socket_item = _cmx_find_modifier_input_socket(
        modifier,
        CMX_DENSITY_MASK_SOCKET_NAMES,
        socket_type='NodeSocketString',
    )
    if socket_item:
        _cmx_ensure_density_mask_default(modifier, socket_item.identifier)


def _cmx_draw_density_mask_dropdown(layout, modifier, socket_identifier, crowd_item_name):
    current_value = _cmx_get_density_mask_display_value(modifier, socket_identifier)
    label = current_value if current_value else CMX_DENSITY_MASK_NONE_LABEL
    CMX_MT_DensityMaskVertexGroup.crowd_item_name = crowd_item_name or ""
    CMX_MT_DensityMaskVertexGroup.socket_identifier = socket_identifier
    layout.menu("CMX_MT_density_mask_vertex_group", text=label)


def _cmx_is_primary_source_socket(if_item):
    return (
        if_item.item_type == 'SOCKET' and
        if_item.in_out == 'INPUT' and
        if_item.socket_type == 'NodeSocketCollection' and
        _cmx_socket_matches(if_item, CMX_PRIMARY_SOURCE_SOCKET_NAMES)
    )


def _cmx_is_any_source_socket(if_item):
    return (
        if_item.item_type == 'SOCKET' and
        if_item.in_out == 'INPUT' and
        if_item.socket_type == 'NodeSocketCollection' and
        _cmx_socket_matches(if_item, CMX_ALL_SOURCE_SOCKET_NAMES)
    )


def _cmx_modifier_has_primary_source_socket(modifier):
    if not modifier or not getattr(modifier, "node_group", None):
        return False
    for if_item in modifier.node_group.interface.items_tree:
        if _cmx_is_primary_source_socket(if_item):
            return True
    return False


def cmx_assign_source_collection_to_modifier(modifier, source_collection_name):
    source_collection = bpy.data.collections.get(source_collection_name)
    if not source_collection or not modifier or not modifier.node_group:
        return False

    for if_item in modifier.node_group.interface.items_tree:
        if _cmx_is_primary_source_socket(if_item):
            try:
                modifier[if_item.identifier] = source_collection
                return True
            except Exception:
                pass

    for if_item in modifier.node_group.interface.items_tree:
        if _cmx_is_any_source_socket(if_item):
            try:
                modifier[if_item.identifier] = source_collection
                return True
            except Exception:
                pass

    for if_item in modifier.node_group.interface.items_tree:
        if (
            if_item.item_type == 'SOCKET' and
            if_item.in_out == 'INPUT' and
            if_item.socket_type == 'NodeSocketCollection'
        ):
            try:
                if modifier.get(if_item.identifier) is None:
                    modifier[if_item.identifier] = source_collection
                    return True
            except Exception:
                pass
    return False


def _cmx_get_active_crowd_item_and_modifier(scene):
    if scene.crowd_data_index < 0 or scene.crowd_data_index >= len(scene.crowd_data_items):
        return None, None

    item = scene.crowd_data_items[scene.crowd_data_index]
    collection = bpy.data.collections.get(item.name)
    if not collection or not collection.objects:
        return item, None

    crowd_node_obj = collection.objects[0]
    if not crowd_node_obj.modifiers:
        return item, None

    modifier = crowd_node_obj.modifiers[0]
    if modifier.type != 'NODES' or not modifier.node_group:
        return item, None

    return item, modifier


def _cmx_is_standing_crowd(crowd_type):
    return crowd_type == CMX_STANDING_CROWD_TYPE


def _cmx_get_crowd_panel_groups(crowd_type):
    grouped_panels = []
    for label, prop_name, panel_names in CMX_CROWD_PANEL_GROUPS:
        reordered_panel_names = panel_names

        if crowd_type == CMX_STADIUM_CROWD_TYPE:
            if label == "Placement":
                reordered_panel_names = tuple(panel_names) + ("BASE", "SEAT")
            elif label == "Assets":
                reordered_panel_names = tuple(
                    panel_name for panel_name in panel_names
                    if panel_name not in {"BASE", "SEAT"}
                )

        if crowd_type == CMX_STADIUM_CROWD_TYPE and label == "Assets":
            reordered_panel_names = tuple(
                panel_name for panel_name in panel_names
                if panel_name not in {"BASE", "SEAT", "PRESET_ASSET"}
            ) + ("PRESET_ASSET",)

        if crowd_type == CMX_STANDING_CROWD_TYPE and label == "Placement":
            reordered_panel_names = tuple(
                panel_name for panel_name in panel_names
                if panel_name != "DISTRIBUTION"
            )
            transform_index = next(
                (index for index, panel_name in enumerate(reordered_panel_names) if panel_name == "TRANSFORMS"),
                -1,
            )
            insert_index = transform_index + 1 if transform_index >= 0 else len(reordered_panel_names)
            reordered_panel_names = (
                reordered_panel_names[:insert_index] +
                ("DISTRIBUTION",) +
                reordered_panel_names[insert_index:]
            )

        grouped_panels.append((label, prop_name, reordered_panel_names))
    return tuple(grouped_panels)


def _cmx_is_emitter_type_socket(if_item):
    return (
        if_item.item_type == 'SOCKET' and
        if_item.in_out == 'INPUT' and
        _cmx_socket_matches(if_item, CMX_EMITTER_TYPE_SOCKET_NAMES)
    )


def _cmx_is_object_emitter_type(modifier):
    emitter_type = _cmx_get_modifier_input_value_by_socket_name(
        modifier,
        CMX_EMITTER_TYPE_SOCKET_NAMES,
    )

    if isinstance(emitter_type, str):
        return emitter_type.casefold() == "object"
    if isinstance(emitter_type, (int, float)):
        return int(emitter_type) == 1
    return False


def _cmx_get_emitter_type_display_value(modifier, socket_identifier):
    emitter_type = modifier.get(socket_identifier)
    if isinstance(emitter_type, str):
        for label, _value in CMX_EMITTER_TYPE_ITEMS:
            if emitter_type.casefold() == label.casefold():
                return label
    if isinstance(emitter_type, (int, float)):
        for label, value in CMX_EMITTER_TYPE_ITEMS:
            if int(emitter_type) == value:
                return label
    return CMX_EMITTER_TYPE_ITEMS[0][0]


def _cmx_draw_emitter_type_dropdown(layout, modifier, socket_identifier, crowd_item_name):
    label = _cmx_get_emitter_type_display_value(modifier, socket_identifier)
    CMX_MT_EmitterType.crowd_item_name = crowd_item_name or ""
    CMX_MT_EmitterType.socket_identifier = socket_identifier
    layout.menu("CMX_MT_emitter_type", text=label)


def _cmx_should_show_standing_grid_settings(modifier):
    return not _cmx_is_object_emitter_type(modifier)


def _cmx_should_hide_standing_grid_emitter_socket(if_item, modifier):
    if _cmx_is_emitter_type_socket(if_item):
        return False
    if _cmx_is_density_socket(if_item):
        return _cmx_should_show_standing_grid_settings(modifier)
    if _cmx_socket_matches(if_item, CMX_ON_POINT_SOCKET_NAMES):
        return _cmx_should_show_standing_grid_settings(modifier)
    if _cmx_should_show_standing_grid_settings(modifier):
        return _cmx_socket_matches(if_item, CMX_GRID_EMITTER_HIDDEN_SOCKET_NAMES)
    return _cmx_socket_matches(if_item, CMX_STANDING_OBJECT_EMITTER_HIDDEN_SOCKET_NAMES)


def _cmx_should_hide_modifier_panel(interface_name, modifier, crowd_type):
    normalized_interface_name = _cmx_normalize_socket_name(interface_name)
    if _cmx_name_matches(interface_name, {"RANDOM"}):
        return True
    if (
        _cmx_name_matches(interface_name, CMX_INSTANCE_OVERRIDE_PANEL_NAMES) or
        "override" in normalized_interface_name
    ):
        return True
    if not _cmx_name_matches(interface_name, CMX_GRID_SETTINGS_PANEL_NAMES):
        return False

    emitter_type_socket = _cmx_find_modifier_input_socket(modifier, CMX_EMITTER_TYPE_SOCKET_NAMES)
    if emitter_type_socket:
        return not _cmx_should_show_standing_grid_settings(modifier)

    return False


def _cmx_panel_contains_socket(interface, socket_names):
    if not interface or getattr(interface, "item_type", "") != 'PANEL':
        return False
    for if_item in getattr(interface, "interface_items", []):
        if if_item.item_type == 'SOCKET' and if_item.in_out == 'INPUT' and _cmx_socket_matches(if_item, socket_names):
            return True
    return False


def _cmx_get_visible_modifier_panels(modifier, crowd_type):
    if not modifier or not modifier.node_group:
        return []

    visible_panels = []
    for interface in modifier.node_group.interface.items_tree:
        if interface.item_type != 'PANEL':
            continue
        if _cmx_should_hide_modifier_panel(interface.name, modifier, crowd_type):
            if (
                _cmx_is_standing_crowd(crowd_type) and
                _cmx_is_object_emitter_type(modifier) and
                _cmx_panel_contains_socket(interface, CMX_ON_POINT_SOCKET_NAMES)
            ):
                visible_panels.append(interface)
                continue
            continue
        visible_panels.append(interface)
    return visible_panels


def _cmx_get_modifier_panel_display_name(interface_name):
    display_name = str(interface_name)
    if "_" in display_name:
        return display_name.replace("_", " ").title()
    return display_name


def _cmx_draw_modifier_interface_panel_body(layout, interface, modifier, crowd_type=None, crowd_item_name=""):
    is_standing_emitter_panel = (
        _cmx_is_standing_crowd(crowd_type) and
        _cmx_name_matches(interface.name, CMX_EMITTER_PANEL_NAMES)
    )
    for if_item in interface.interface_items:
        if is_standing_emitter_panel and _cmx_should_hide_standing_grid_emitter_socket(if_item, modifier):
            continue

        _cmx_draw_modifier_socket_row(
            layout,
            modifier,
            if_item,
            crowd_type=crowd_type,
            crowd_item_name=crowd_item_name,
        )


def _cmx_draw_modifier_interface_panel(layout, interface, modifier, wm=None, crowd_type=None, crowd_item_name=""):
    box = layout.box()
    header_row = box.row(align=True)
    header_row.alignment = 'LEFT'
    panel_state = _cmx_get_panel_state(wm or bpy.context.window_manager, interface.name)
    icon = 'DOWNARROW_HLT' if panel_state and panel_state.expanded else 'RIGHTARROW'
    if panel_state:
        header_row.prop(panel_state, "expanded", text="", icon=icon, emboss=False, toggle=False)
        header_row.prop(panel_state, "expanded", text=_cmx_get_modifier_panel_display_name(interface.name), emboss=False)
    else:
        header_row.label(text=_cmx_get_modifier_panel_display_name(interface.name))

    if panel_state is None or panel_state.expanded:
        col = box.column(align=True)
        _cmx_draw_modifier_interface_panel_body(
            col,
            interface,
            modifier,
            crowd_type=crowd_type,
            crowd_item_name=crowd_item_name,
        )


def _cmx_interface_matches_panel_spec(interface, panel_spec):
    panel_names = (panel_spec,) if isinstance(panel_spec, str) else tuple(panel_spec)
    return any(_cmx_name_matches(interface.name, {panel_name}) for panel_name in panel_names)


def _cmx_should_inline_panel_in_group(group_label, interface, panel_specs, interfaces):
    return (
        len(interfaces) == 1 and
        any(_cmx_interface_matches_panel_spec(interface, panel_spec) for panel_spec in panel_specs)
    )


def _cmx_draw_modifier_panel_group(layout, wm, prop_name, label, panel_specs, interfaces, modifier, crowd_type=None, crowd_item_name=""):
    if not interfaces:
        return

    box = layout.box()
    header_row = box.row(align=True)
    expanded = getattr(wm, prop_name, True)
    icon = 'TRIA_DOWN' if expanded else 'TRIA_RIGHT'
    header_row.prop(wm, prop_name, text="", emboss=False, icon=icon)
    header_row.prop(wm, prop_name, text=label, emboss=False)

    if not expanded:
        return

    col = box.column(align=True)
    for interface in interfaces:
        if _cmx_should_inline_panel_in_group(label, interface, panel_specs, interfaces):
            _cmx_draw_modifier_interface_panel_body(
                col,
                interface,
                modifier,
                crowd_type=crowd_type,
                crowd_item_name=crowd_item_name,
            )
            continue
        _cmx_draw_modifier_interface_panel(
            col,
            interface,
            modifier,
            wm=wm,
            crowd_type=crowd_type,
            crowd_item_name=crowd_item_name,
        )


def _cmx_get_panel_from_map(panel_map, panel_spec, consumed_panel_names):
    panel_names = (panel_spec,) if isinstance(panel_spec, str) else tuple(panel_spec)
    for normalized_name, interface in panel_map.items():
        if normalized_name in consumed_panel_names:
            continue
        if any(_cmx_interface_matches_panel_spec(interface, panel_name) for panel_name in panel_names):
            return normalized_name, interface
    return None, None


def _cmx_draw_grouped_geometry_node_inputs(layout, modifier, wm=None, crowd_type=None, crowd_item_name=""):
    wm = wm or bpy.context.window_manager
    visible_panels = _cmx_get_visible_modifier_panels(modifier, crowd_type)
    panel_map = {_cmx_normalize_socket_name(interface.name): interface for interface in visible_panels}
    consumed_panel_names = set()

    for label, prop_name, panel_names in _cmx_get_crowd_panel_groups(crowd_type):
        group_interfaces = []
        for panel_spec in panel_names:
            normalized_name, interface = _cmx_get_panel_from_map(panel_map, panel_spec, consumed_panel_names)
            if not interface:
                continue
            group_interfaces.append(interface)
            consumed_panel_names.add(normalized_name)
        _cmx_draw_modifier_panel_group(
            layout,
            wm,
            prop_name,
            label,
            panel_names,
            group_interfaces,
            modifier,
            crowd_type=crowd_type,
            crowd_item_name=crowd_item_name,
        )

    for interface in visible_panels:
        normalized_name = _cmx_normalize_socket_name(interface.name)
        if normalized_name in consumed_panel_names:
            continue
        if normalized_name in {_cmx_normalize_socket_name(name) for name in CMX_CROWD_PANEL_BOTTOM_ORDER}:
            continue
        _cmx_draw_modifier_interface_panel(
            layout,
            interface,
            modifier,
            wm=wm,
            crowd_type=crowd_type,
            crowd_item_name=crowd_item_name,
        )
        consumed_panel_names.add(normalized_name)

    for panel_spec in CMX_CROWD_PANEL_BOTTOM_ORDER:
        normalized_name, interface = _cmx_get_panel_from_map(panel_map, panel_spec, consumed_panel_names)
        if not interface:
            continue
        _cmx_draw_modifier_interface_panel(
            layout,
            interface,
            modifier,
            wm=wm,
            crowd_type=crowd_type,
            crowd_item_name=crowd_item_name,
        )
        consumed_panel_names.add(normalized_name)


def _cmx_draw_modifier_socket_row(col, modifier, if_item, crowd_type=None, crowd_item_name=""):
    if if_item.item_type != 'SOCKET' or if_item.in_out != 'INPUT':
        return
    if _cmx_socket_matches(if_item, CMX_EDIT_INSTANCE_RUNTIME_SOCKET_NAMES):
        return

    socket_name = if_item.name
    socket_identifier = if_item.identifier
    socket_display_name = if_item.description or if_item.name
    split = col.split(factor=0.5)
    left_col = split.column(align=True)
    left_col.alignment = 'RIGHT'
    right_col = split.column(align=True)
    if if_item.socket_type == 'NodeSocketCollection':
        if _cmx_is_any_source_socket(if_item):
            left_col.label(text=socket_display_name)
            action_row = right_col.row(align=True)
            clear_source_op = action_row.operator("cmx.clear_source_collection", text="", icon='X')
            clear_source_op.socket_name = socket_name
            value_col = action_row.column(align=True)
            value_col.prop(modifier, f'["{socket_identifier}"]', text="")
            value_col.enabled = False
            set_source_op = action_row.operator("cmx.set_source_collection", text="", icon_value=get_cf_icon("main_panel_crowd_source"))
            set_source_op.socket_name = socket_name
        else:
            left_col.label(text=socket_display_name)
            right_col.prop_search(modifier, f'["{socket_identifier}"]', bpy.data, "collections", text="")
    else:
        left_col.label(text=socket_display_name)
        row_L1 = right_col.row(align=True)
        if crowd_type == "CMX_Standing_Crowd" and _cmx_is_emitter_type_socket(if_item):
            _cmx_draw_emitter_type_dropdown(row_L1, modifier, socket_identifier, crowd_item_name)
        elif crowd_type == "CMX_Standing_Crowd" and _cmx_is_density_mask_socket(if_item):
            _cmx_draw_density_mask_dropdown(row_L1, modifier, socket_identifier, crowd_item_name)
        elif if_item.socket_type == 'NodeSocketObject':
            row_L1.prop_search(modifier, f'["{socket_identifier}"]', bpy.data, "objects", text="")
        elif if_item.socket_type == 'NodeSocketBool':
            row_L1.alignment = 'CENTER'
            row_L1.prop(modifier, f'["{socket_identifier}"]', text="")
        elif if_item.socket_type == 'NodeSocketFloat' and getattr(if_item, "subtype", "") == 'ANGLE':
            row_L1.prop(modifier, f'["{socket_identifier}"]', text="", slider=True)
        else:
            row_L1.prop(modifier, f'["{socket_identifier}"]', text="")


def cmx_draw_geometry_node_inputs(layout, modifier, source_collection, wm=None, crowd_type=None, crowd_item_name=""):
    """
    Draw UI for geometry node modifier inputs, including special handling for collections and common socket types.
    """
    _cmx_draw_grouped_geometry_node_inputs(
        layout,
        modifier,
        wm=wm,
        crowd_type=crowd_type,
        crowd_item_name=crowd_item_name,
    )

def cmx_get_crowd_modifier(crowd_item_input):
    """
    Retrieve the geometry node modifier from the main object of a crowd setup.
    'crowd_item_input' can be a property group or string (collection name).
    Returns the first matching modifier, or None if not found.
    """
    crowd_collection_name = None
    crowd_object_name_hint = None
    if isinstance(crowd_item_input, str):
        crowd_collection_name = crowd_item_input
    elif hasattr(crowd_item_input, 'name') and hasattr(crowd_item_input, 'crowd_obj_name'):
        crowd_collection_name = crowd_item_input.name
        crowd_object_name_hint = crowd_item_input.crowd_obj_name
    else:
        return None

    if not crowd_collection_name:
        return None

    if hasattr(crowd_item_input, 'name') and hasattr(crowd_item_input, 'crowd_obj_name'):
        crowd_node_obj = _cmx_get_crowd_node_object(crowd_item_input)
    else:
        crowd_coll = bpy.data.collections.get(crowd_collection_name)
        if not crowd_coll or not crowd_coll.objects:
            return None
        crowd_node_obj = None
        if crowd_object_name_hint:
            crowd_node_obj = crowd_coll.objects.get(crowd_object_name_hint)
        if not crowd_node_obj:
            for obj in crowd_coll.objects:
                if obj.modifiers:
                    for mod in obj.modifiers:
                        if mod.type == 'NODES' and mod.node_group:
                            crowd_node_obj = obj
                            break
                if crowd_node_obj:
                    break
        if not crowd_node_obj and crowd_coll.objects:
            crowd_node_obj = crowd_coll.objects[0]

    if crowd_node_obj and crowd_node_obj.modifiers:
        for modifier in crowd_node_obj.modifiers:
            if modifier.type == 'NODES' and modifier.node_group:
                return modifier
        return None
    elif crowd_node_obj:
        return None
    else:
        return None

def cmx_get_modifier_inputs_from_crowd_item(crowd_item_instance):
    """
    Extract a dictionary of modifier input values from a crowd item,
    converting internal/external references to serializable data.
    """
    inputs = {}
    modifier = cmx_get_crowd_modifier(crowd_item_instance)
    if not modifier or not modifier.node_group:
        return inputs

    addon_prefs = cmx_get_addon_preferences(bpy.context)
    addon_asset_root_path = getattr(addon_prefs, 'folder_path', "") if addon_prefs else ""
    normalized_addon_asset_root_path = ""
    if addon_asset_root_path:
        normalized_addon_asset_root_path = os.path.normpath(addon_asset_root_path)
        if not normalized_addon_asset_root_path.endswith(os.sep):
             normalized_addon_asset_root_path += os.sep

    for item in modifier.node_group.interface.items_tree:
        if item.item_type == 'SOCKET' and item.in_out == 'INPUT':
            if _cmx_socket_matches(item, CMX_EDIT_INSTANCE_RUNTIME_SOCKET_NAMES):
                continue
            socket_identifier = item.identifier
            value = modifier.get(socket_identifier)
            saved_value = None
            if item.name == "emiter_type" :
                print(f"socket name:{item.name} socket_ident:{socket_identifier} value:{value}")

            if isinstance(value, bpy.types.Object) or isinstance(value, bpy.types.Collection):
                is_object_type = isinstance(value, bpy.types.Object)
                if value.library:
                    library_filepath_abs = bpy.path.abspath(value.library.filepath)
                    normalized_library_filepath_abs = os.path.normpath(library_filepath_abs)
                    library_filename = os.path.basename(library_filepath_abs)
                    relative_path_to_lib_dir = ""
                    if normalized_addon_asset_root_path and normalized_library_filepath_abs.startswith(normalized_addon_asset_root_path):
                        full_lib_dir = os.path.dirname(normalized_library_filepath_abs)
                        if full_lib_dir.startswith(normalized_addon_asset_root_path):
                            relative_path_to_lib_dir = full_lib_dir[len(normalized_addon_asset_root_path):].strip(os.sep)
                        saved_value = {
                            "type": "EXTERNAL_FROM_ADDON_OBJECT" if is_object_type else "EXTERNAL_FROM_ADDON_COLLECTION",
                            "library_name": library_filename,
                            "internal_name": value.name,
                            "relative_path_to_library_dir": relative_path_to_lib_dir
                        }
                    else:
                        saved_value = {
                            "type": "INTERNAL_OBJECT" if is_object_type else "INTERNAL_COLLECTION",
                            "name": value.name
                        }
                else:
                    saved_value = {
                        "type": "INTERNAL_OBJECT" if is_object_type else "INTERNAL_COLLECTION",
                        "name": value.name
                    }
            elif isinstance(value, (str, int, float, bool)):
                saved_value = value
            elif hasattr(value, "to_list"):
                saved_value = value.to_list()
            else:
                saved_value = str(value)
            inputs[socket_identifier] = saved_value
    return inputs

def cmx_set_modifier_input_value(modifier, socket_identifier_or_name, saved_value_data, context, source_name_map=None):
    """
    Set a specific modifier input value based on saved or imported preset data.
    Handles internal/external data types, simple types, and all major Geometry Node socket types.
    Returns True if successful, False otherwise.
    """
    if saved_value_data == "None" or saved_value_data is None:
        return 
    
    if not modifier or not hasattr(modifier, 'node_group') or not modifier.node_group:
        return False

    node_group_interface = modifier.node_group.interface
    socket_item = None

    # Try to find the socket by its identifier first
    for item_iter in node_group_interface.items_tree:
        if item_iter.item_type == 'SOCKET' and item_iter.in_out == 'INPUT' and \
           hasattr(item_iter, 'identifier') and item_iter.identifier == socket_identifier_or_name:
            socket_item = item_iter
            break
    # Fallback: if not found by identifier, try by name
    if not socket_item:
        for item_iter in node_group_interface.items_tree:
            if item_iter.item_type == 'SOCKET' and item_iter.in_out == 'INPUT' and \
               item_iter.name == socket_identifier_or_name:
                socket_item = item_iter
                break

    if not socket_item:
        return False

    actual_socket_identifier = socket_item.identifier
    socket_type = socket_item.socket_type

    try:
        assigned = False
        if isinstance(saved_value_data, dict) and "type" in saved_value_data:
            data_type = saved_value_data["type"]
            if data_type == "INTERNAL_OBJECT":
                item_name = saved_value_data.get("name")
                if socket_type == 'NodeSocketObject':
                    obj = bpy.data.objects.get(item_name)
                    if obj is not None:
                        modifier[actual_socket_identifier] = obj
                        assigned = True
                # Else: type mismatch; skip assignment
            elif data_type == "INTERNAL_COLLECTION":
                item_name = saved_value_data.get("name")
                if source_name_map:
                    item_name = source_name_map.get(item_name, item_name)
                if socket_type == 'NodeSocketCollection':
                    coll = bpy.data.collections.get(item_name)
                    if coll is not None:
                        modifier[actual_socket_identifier] = coll
                        assigned = True
            elif data_type in ["EXTERNAL_FROM_ADDON_OBJECT", "EXTERNAL_FROM_ADDON_COLLECTION"]:
                library_filename = saved_value_data.get("library_name")
                internal_item_name_in_lib = saved_value_data.get("internal_name")
                relative_path_to_lib_dir_from_preset = saved_value_data.get("relative_path_to_library_dir", "")
                if data_type == "EXTERNAL_FROM_ADDON_COLLECTION" and socket_type == 'NodeSocketCollection':
                    source_collection_name = _cmx_resolve_saved_collection_name(saved_value_data, source_name_map)
                    source_collection = bpy.data.collections.get(source_collection_name)
                    if source_collection is not None:
                        modifier[actual_socket_identifier] = source_collection
                        return True
                crowd_item_name_for_path = "DefaultCrowd"
                if modifier.id_data and modifier.id_data.users_collection:
                    crowd_item_name_for_path = modifier.id_data.users_collection[0].name
                try:
                    linked_item_to_assign = cmx_link_asset_For_Crowd_Prop(
                        context=context,
                        library_filename=library_filename,
                        internal_item_name=internal_item_name_in_lib,
                        crowd_item_name_for_path=crowd_item_name_for_path,
                        data_block_type=data_type,
                        relative_path_to_lib_dir=relative_path_to_lib_dir_from_preset
                    )
                except Exception:
                    pass
                    # linked_item_to_assign = None

                if linked_item_to_assign is not None:
                    if data_type == "EXTERNAL_FROM_ADDON_OBJECT" and socket_type == 'NodeSocketObject':
                        if isinstance(linked_item_to_assign, bpy.types.Object):
                            modifier[actual_socket_identifier] = linked_item_to_assign
                            assigned = True
                    elif data_type == "EXTERNAL_FROM_ADDON_COLLECTION":
                        if socket_type == 'NodeSocketObject':
                            if isinstance(linked_item_to_assign, bpy.types.Object) and linked_item_to_assign.instance_type == 'COLLECTION':
                                modifier[actual_socket_identifier] = linked_item_to_assign
                                assigned = True
                        elif socket_type == 'NodeSocketCollection':
                            if isinstance(linked_item_to_assign, bpy.types.Object) and linked_item_to_assign.instance_type == 'COLLECTION':
                                if linked_item_to_assign.instance_collection is not None:
                                    modifier[actual_socket_identifier] = linked_item_to_assign.instance_collection
                                    assigned = True
            return assigned

        elif isinstance(saved_value_data, list) and socket_type in {'NodeSocketVector', 'NodeSocketColor', 'NodeSocketRotation'}:
            if len(saved_value_data) >= 3:
                if socket_type == 'NodeSocketVector':
                    modifier[actual_socket_identifier] = tuple(saved_value_data[:3])
                elif socket_type == 'NodeSocketColor':
                    modifier[actual_socket_identifier] = tuple(saved_value_data[:4] if len(saved_value_data) >= 4 else saved_value_data[:3] + [1.0])
                elif socket_type == 'NodeSocketRotation':
                    modifier[actual_socket_identifier] = tuple(saved_value_data[:3])
            else:
                return False
        elif isinstance(saved_value_data, (str, int, float, bool)):
            if socket_type == 'NodeSocketCollection' and isinstance(saved_value_data, str) and source_name_map:
                item_name = source_name_map.get(saved_value_data, saved_value_data)
                coll = bpy.data.collections.get(item_name)
                if coll is not None:
                    modifier[actual_socket_identifier] = coll
                    assigned = True
            else:
                modifier[actual_socket_identifier] = saved_value_data
                assigned = True
        else:
            if socket_type == 'NodeSocketCollection' and isinstance(saved_value_data, str):
                item_name = source_name_map.get(saved_value_data, saved_value_data) if source_name_map else saved_value_data
                coll = bpy.data.collections.get(item_name)
                if coll is not None:
                    modifier[actual_socket_identifier] = coll
                    assigned = True
            elif socket_type == 'NodeSocketObject' and isinstance(saved_value_data, str):
                obj = bpy.data.objects.get(saved_value_data)
                if obj is not None:
                    modifier[actual_socket_identifier] = obj
                    assigned = True
            else:
                return False
        return assigned
    except KeyError:
        return False
    except Exception:
        return False

#------------------------------------------------SOURCE---------------------------------------------------

class CMXSourceDataPropertyGroup(bpy.types.PropertyGroup):
    """
    Property group for each source item in the Crowd Mixer source list.
    """
    name: bpy.props.StringProperty(name="Name") # type: ignore
    active: bpy.props.BoolProperty(name="Active", default=True)  # type: ignore  kept for compatibility with handlers
    expand_item: bpy.props.BoolProperty(name="Expand Item")# type: ignore
    visible: bpy.props.BoolProperty(name="Visible", default=True, update=cmx_set_source_visible)# type: ignore
    preview_type: bpy.props.EnumProperty(
        name="Preview Type",
        items=[('SOURCE_FULL', "Full", ""), ('SOURCE_PROXY', "Proxy", "")],
        update=cmx_set_source_preview_type
    )# type: ignore
    preset_collection: bpy.props.EnumProperty(name="Preset Collection", items=cmx_get_preset_collections_item)# type: ignore
    random_start: bpy.props.IntProperty(
        name="Random Start Offset",
        description="Maximum random frames to add to Start Frame",
        min=0,
        update=cmx_set_random_strat_frame_anim
    )# type: ignore
    random_speed: bpy.props.FloatProperty(
        name="Random Speed Variation",
        description="Maximum +/- variation from Animation Speed",
        min=0.0,
        precision=2,
        update=cmx_set_random_speed_anim_min
    )# type: ignore
    start_frame: bpy.props.IntProperty(
        name="Start Frame",
        default=0,
        update=cmx_update_source_start_frame
    )# type: ignore
    anim_speed: bpy.props.FloatProperty(
        name="Animation Speed",
        default=1.0,
        min=0.01,
        precision=2,
        update=cmx_update_source_anim_speed
    )# type: ignore


class CMXCrowdModifierPanelState(bpy.types.PropertyGroup):
    """Track expand/collapse state for each modifier subpanel."""
    name: bpy.props.StringProperty(name="Panel Name")  # type: ignore
    expanded: bpy.props.BoolProperty(name="Expanded", default=False)  # type: ignore

class CMX_UL_SourceData(bpy.types.UIList):
    """
    UIList for displaying source data items in the Crowd Mixer panel.
    """
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        main_col = layout.column()
        main_row = main_col.row()
        icon_expand = 'TRIA_DOWN' if item.expand_item else 'TRIA_RIGHT'
        main_row.prop(item, "expand_item", icon=icon_expand, text="", emboss=False)
        main_row.label(text=item.name, icon_value=get_cf_icon("main_panel_crowd_source"))
        col_L0 = main_row.column()
        vis_icon = "HIDE_OFF" if item.visible else "HIDE_ON"
        col_L0.prop(item, "visible", text="", toggle=True, emboss=False, icon=vis_icon)
        col_L0.enabled = True

        if item.expand_item:
            sub_box = main_col.box()
            sub_col = sub_box.column(align=True)

            sub_row_L1 = sub_col.row(align=True)
            sub_row_L1.label(text="Preview Type")
            sub_row_L1.prop(item, "preview_type", text="Preview Type", expand=True)

            sub_row_L1 = sub_col.row(align=True)
            split = sub_row_L1.split(factor=0.32)
            left_col = split.column(align=True)
            right_col = split.column(align=True)
            left_col.label(text="Preset Collection")
            right_col.prop(item, "preset_collection", text="")
            right_col.enabled = False

            sub_col.prop(item, "start_frame", text="Start Frame")
            sub_col.prop(item, "random_start", text="Random Start Frame")
            sub_col.separator()
            sub_col.prop(item, "anim_speed", text="Anim Speed")
            sub_col.prop(item, "random_speed", text="Random Anim Speed")

class CMXAddSourceDataOperator(bpy.types.Operator):
    """
    Operator to add a new source data item to the scene.
    """
    bl_idname = "cmx.source_data_add_item"
    bl_label = "Add Source"

    source_name: bpy.props.EnumProperty(
        name="Source",
        description="Select source .blend; collection with same name will be linked",
        items=cmx_source_blend_items
    ) # type: ignore

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "source_name")

    def execute(self, context):
        if not self.source_name:
            cmx_show_message_box(message="Please select a source file.", title="Missing Source", icon='ERROR')
            return {'CANCELLED'}
        can_load_source, load_message = _cmx_validate_source_library_load(context.scene, self.source_name)
        if not can_load_source:
            cmx_show_message_box(message=load_message, title="Source Conflict", icon='ERROR')
            return {'CANCELLED'}

        item = cmx_add_source_data_item(context, self.source_name)
        if item:
            cmx_set_progress_success()
            return {'FINISHED'}

        self.report({'ERROR'}, f"Failed to load source '{self.source_name}'.")
        return {'CANCELLED'}

    def invoke(self, context, event):
        source_dir = cmx_get_source_dir(create_if_missing=False)
        if not source_dir or not os.path.isdir(source_dir):
            cmx_show_message_box(message="CMX-Source folder not found. Please add sources first.",title="Message Box", icon='INFO')
            return {'CANCELLED'}
        return context.window_manager.invoke_props_dialog(self)

class CMXAddSourceFromPresetOperator(bpy.types.Operator):
    """
    Add a new source using preset collection name with auto name and load like previous active=True behavior.
    Shows a confirmation to start a new scene and auto-save the generated source blend.
    """
    bl_idname = "cmx.source_data_add_from_preset"
    bl_label = "Add Source From Preset"

    preset_collection: bpy.props.StringProperty(name="Preset Collection")  # type: ignore

    def draw(self, context):
        layout = self.layout
        layout.label(text="This will start a new scene and overwrite/save a source file.")
        layout.label(text="Please save your current work before continuing.")
        layout.separator()
        layout.label(text=f"Preset collection: {self.preset_collection}")
        source_dir = cmx_get_source_dir(create_if_missing=False)
        if source_dir:
            target_path = os.path.join(source_dir, f"{(self.preset_collection or 'NewSource')}.blend")
            layout.label(text=f"Target file: {target_path}")

    def invoke(self, context, event):
        directory = cmx_get_asset_dir_by_mode()
        if not directory or not cmx_check_asset_path(directory):
            cmx_show_message_box(message="The specified asset could not be found. Please ensure the asset path is correct.",title="Message Box", icon='INFO')
            return {'CANCELLED'}
        if context.window_manager.cf_on_off_toggle:
            cmx_show_message_box(message="To proceed, please turn off Character Customize.",title="Warning", icon='ERROR')
            return {'CANCELLED'}
        preset_data = cmx_get_preset_collection_data(self.preset_collection)
        is_valid, suggested_name, offending_preset, safe_source_len = cmx_validate_source_name_for_preset_collection(
            self.preset_collection,
            preset_data
        )
        if not is_valid:
            cmx_show_message_box(
                message=f"Source name too long. Suggested: ' {suggested_name} '",
                # message=f"Source name too long. Suggested: '{suggested_name}' (max {safe_source_len} chars). Longest preset: {offending_preset}",
                title="Source Name Too Long",
                icon='ERROR')
            return {'CANCELLED'}
        return context.window_manager.invoke_props_dialog(self, width=380)

    def execute(self, context):
        name = (self.preset_collection or "NewSource").strip() or "NewSource"
        source_dir = cmx_get_source_dir(create_if_missing=True)
        if not source_dir or not os.path.isdir(source_dir):
            _cmx_show_validation_popup("CMX-Source folder could not be found or created.", title="Source Error")
            self.report({'ERROR'}, "CMX-Source folder could not be found or created.")
            return {'CANCELLED'}
        can_load_source, load_message = _cmx_validate_source_library_load(context.scene, name)
        if not can_load_source:
            _cmx_show_validation_popup(load_message, title="Source Conflict")
            self.report({'ERROR'}, load_message)
            return {'CANCELLED'}
        preset_data = cmx_get_preset_collection_data(name)
        is_valid, suggested_name, offending_preset, safe_source_len = cmx_validate_source_name_for_preset_collection(
            name,
            preset_data
        )
        if not is_valid:
            _cmx_show_validation_popup(
                f"Source name too long. Suggested: '{suggested_name}' (max {safe_source_len} chars).",
                title="Source Name Too Long"
            )
            self.report({'ERROR'}, f"Source name too long. Suggested: '{suggested_name}' (max {safe_source_len} chars).")
            return {'CANCELLED'}
        save_path = os.path.join(source_dir, f"{name}.blend")

        # Start from a clean file (File > New), not just adding a scene inside the current file
        try:
            bpy.ops.wm.read_homefile(use_empty=True)
            context = bpy.context
            scene = context.scene
        except Exception as e:
            _cmx_show_validation_popup(f"Failed to start a new file: {e}", title="Source Error")
            self.report({'ERROR'}, f"Failed to start a new file: {e}")
            return {'CANCELLED'}

        is_valid_name, name_message = _cmx_validate_source_target_name(scene, name)
        if not is_valid_name:
            _cmx_show_validation_popup(name_message, title="Invalid Source Name")
            self.report({'ERROR'}, name_message)
            return {'CANCELLED'}

        item = scene.source_data_items.add()
        item.name = name
        # ensure the preset enum matches the chosen collection (avoid default "seminar")
        item.preset_collection = self.preset_collection or name
        item.expand_item = True

        try:
            # mimic old active=True: load crowd asset source from preset data
            preset_data = cmx_get_preset_collection_data(item.name)
            if preset_data:
                preset_dict = {item.name: preset_data}
                cmx_load_crowd_asset_source(item, context, preset_dict)
                item.visible = True
                cmx_schedule_source_save(save_path, collection_name=item.preset_collection)
        except Exception as e:
            _cmx_show_validation_popup(f"Failed to load source: {e}", title="Source Error")
            self.report({'ERROR'}, f"Failed to load source: {e}")
            return {'CANCELLED'}
        return {'FINISHED'}

class CMXRemoveSourceDataOperator(bpy.types.Operator):
    """
    Operator to remove the selected source data item from the scene.
    """
    bl_idname = "cmx.source_data_remove_item"
    bl_label = "Remove Source Item"

    def execute(self, context):
        scene = context.scene

        if not scene.source_data_items:
            self.report({'WARNING'}, "Source list is empty.")
            return {'CANCELLED'}

        if scene.source_data_index < 0 or scene.source_data_index >= len(scene.source_data_items):
            self.report({'WARNING'}, "No source item selected or index is out of bounds.")
            return {'CANCELLED'}

        idx_to_remove = scene.source_data_index
        item_to_remove = scene.source_data_items[idx_to_remove]
        # mimic old deactivate behavior: remove instances and assets if preset data exists
        try:
            preset_data = cmx_get_preset_collection_data(item_to_remove.preset_collection)
            cmx_remove_instance_preview(item_to_remove, item_to_remove.name)
            _cmx_remove_source_hierarchy(item_to_remove.name)
            if preset_data:
                preset_dict = {item_to_remove.preset_collection: preset_data}
                cmx_remove_crowd_asset(preset_dict, item_to_remove.name)
            if item_to_remove.name in STRIPS_LIST:
                del STRIPS_LIST[item_to_remove.name]
        except Exception:
            pass
        scene.source_data_items.remove(idx_to_remove)

        num_items = len(scene.source_data_items)
        if num_items == 0:
            scene.source_data_index = 0
        else:
            scene.source_data_index = min(idx_to_remove, num_items - 1)

        bpy.ops.outliner.orphans_purge(do_recursive=True)
        self.report({'INFO'}, f"Source item '{item_to_remove.name}' removed.")
        return {'FINISHED'}

    def invoke(self, context, event):
        if not context.scene.source_data_items:
            cmx_show_message_box(message="Source list is empty. Nothing to remove.", title="Info", icon='INFO')
            return {'CANCELLED'}
        return context.window_manager.invoke_props_dialog(self, width=250)

#------------------------------------------------CROWD---------------------------------------------------
class CMXCrowdDataPropertyGroup(bpy.types.PropertyGroup):
    """
    Property group for each crowd item in the Crowd Mixer crowd list.
    """
    name: bpy.props.StringProperty(name="Item Name") # type: ignore
    crowd_obj_name: bpy.props.StringProperty(name="Object Name")# type: ignore
    source_collection: bpy.props.StringProperty(name="Source Collection")# type: ignore
    visible: bpy.props.BoolProperty(name="Visible", default=True, update=cmx_set_crowd_visible)# type: ignore

class CMX_UL_CrowdData(bpy.types.UIList):
    """
    UIList for displaying crowd data items in the Crowd Mixer panel.
    """
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        col = layout.column()
        row = col.row(align=True)
        row.label(text=item.name, icon_value=get_cf_icon(item.crowd_obj_name))
        txt_label = ""
        crowd_mod = cmx_get_crowd_modifier(item)

        if crowd_mod and crowd_mod.node_group and crowd_mod.node_group.interface:
            first_source_found = False
            for inf_item in crowd_mod.node_group.interface.items_tree:
                if _cmx_is_primary_source_socket(inf_item):
                    source_input_value = crowd_mod.get(inf_item.identifier)
                    current_source_name = "N/A"
                    if isinstance(source_input_value, bpy.types.Collection):
                        current_source_name = source_input_value.name
                    elif isinstance(source_input_value, str) and source_input_value:
                        current_source_name = source_input_value
                    elif source_input_value is None:
                        current_source_name = "None"
                    if first_source_found:
                        txt_label += " | "
                    txt_label += current_source_name
                    first_source_found = True
            if not first_source_found:
                if item.source_collection:
                    txt_label = item.source_collection
                else:
                    txt_label = "N/A (No Source)"
        else:
            if item.source_collection:
                txt_label = item.source_collection
            else:
                txt_label = "N/A (No Modifier/Source)"
        row.label(text=txt_label, icon_value=get_cf_icon("main_panel_crowd_source"))
        vis_icon = "HIDE_OFF" if item.visible else 'HIDE_ON'
        row.prop(item, "visible", text="", emboss=False, icon=vis_icon)

class CMXAddCrowdDataOperator(bpy.types.Operator):
    """
    Operator to add a new crowd data item to the scene.
    """
    bl_label = "Add Crowd"
    bl_idname = "cmx.crowd_data_add_item"

    name: bpy.props.StringProperty(name="Item Name", default="New Item")# type: ignore
    crowd_obj_name: bpy.props.EnumProperty(
        name="Crowd Type",
        items=cmx_get_crowd_type_items,
        description="Select the object to add"
    )# type: ignore
    source_collection: bpy.props.EnumProperty(name="Source Collection", items=cmx_get_source_list_item)# type: ignore

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.prop(self, "name")
        col.prop(self, "crowd_obj_name")
        col.prop(self, "source_collection")

    def execute(self, context):
        scene = context.scene
        requested_name = (self.name or "").strip()
        is_valid_name, name_message = _cmx_validate_crowd_target_name(scene, requested_name)
        if not is_valid_name:
            _cmx_show_validation_popup(name_message, title="Invalid Crowd Name")
            self.report({'WARNING'}, name_message)
            return {'CANCELLED'}
        new_item = scene.crowd_data_items.add()
        new_item.name = requested_name
        new_item.crowd_obj_name = self.crowd_obj_name
        modifier = cmx_load_crowd_object(new_item)
        if modifier and modifier.type == 'NODES' and modifier.node_group:
            if cmx_assign_source_collection_to_modifier(modifier, self.source_collection):
                new_item.source_collection = self.source_collection
            else:
                new_item.source_collection = "N/A"
            _cmx_ensure_standing_density_mask_default(modifier, new_item.crowd_obj_name)
        scene.crowd_data_index = len(scene.crowd_data_items) - 1
        _cmx_select_crowd_item_in_viewport(scene, context, new_item)
        return {'FINISHED'}


class CMXToggleEditInstanceModeOperator(bpy.types.Operator):
    bl_idname = "cmx.toggle_edit_instance_mode"
    bl_label = "Toggle Instance Override"

    crowd_item_name: bpy.props.StringProperty(default="")  # type: ignore

    def execute(self, context):
        scene = context.scene
        crowd_item = None

        if self.crowd_item_name:
            crowd_item = next((item for item in scene.crowd_data_items if item.name == self.crowd_item_name), None)
        if not crowd_item:
            crowd_item = _cmx_get_active_or_selected_crowd_item(scene, context)
        if not crowd_item:
            self.report({'WARNING'}, "Select a Crowd Node first.")
            return {'CANCELLED'}

        active_crowd_name = getattr(scene, "cmx_edit_instance_crowd_name", "")
        if active_crowd_name and active_crowd_name != crowd_item.name:
            _cmx_disable_edit_instance_mode(context, crowd_name=active_crowd_name)

        if scene.cmx_edit_instance_crowd_name == crowd_item.name:
            _cmx_disable_edit_instance_mode(context, crowd_name=crowd_item.name)
            return {'FINISHED'}

        ok, message = _cmx_enable_edit_instance_mode(context, crowd_item)
        if not ok:
            self.report({'WARNING'}, message)
            return {'CANCELLED'}

        return {'FINISHED'}


class CMXEditInstanceActionOperator(bpy.types.Operator):
    bl_idname = "cmx.edit_instance_action"
    bl_label = "Edit Instance Action"

    action: bpy.props.EnumProperty(  # type: ignore
        name="Action",
        items=(
            ('PREVIOUS', "Previous", ""),
            ('NEXT', "Next", ""),
            ('RANDOM', "Random", ""),
            ('RESET', "Reset Override", ""),
        ),
    )

    def execute(self, context):
        scene = context.scene
        crowd_name = getattr(scene, "cmx_edit_instance_crowd_name", "")
        point_index = getattr(scene, "cmx_edit_instance_selected_index", -1)
        slot_index = getattr(scene, "cmx_edit_instance_selected_slot", -1)
        original_index = getattr(scene, "cmx_edit_instance_selected_original_index", -1)
        if not crowd_name or point_index < 0 or slot_index < 0 or original_index < 0:
            return {'CANCELLED'}

        crowd_item = next((item for item in scene.crowd_data_items if item.name == crowd_name), None)
        modifier = cmx_get_crowd_modifier(crowd_item or crowd_name)
        override_obj = _cmx_get_override_object(crowd_name)
        if not modifier or not override_obj:
            return {'CANCELLED'}

        point_state = _cmx_get_override_runtime_state(override_obj, slot_index, point_index, original_index)
        min_index, max_index = _cmx_get_edit_instance_index_bounds(crowd_name)
        if not point_state or min_index is None or max_index is None:
            return {'CANCELLED'}

        slot_index = point_state["slot_index"]
        point_index = point_state["point_index"]
        original_index = point_state["original_index"]
        current_index = point_state["override_index"]
        base_index = current_index if point_state["override_on"] else original_index

        if self.action == 'PREVIOUS':
            new_index = max_index if base_index <= min_index else base_index - 1
            _cmx_set_override_runtime_state(override_obj, slot_index, original_index, new_index, debug_source="action:previous")
        elif self.action == 'NEXT':
            new_index = min_index if base_index >= max_index else base_index + 1
            _cmx_set_override_runtime_state(override_obj, slot_index, original_index, new_index, debug_source="action:next")
        elif self.action == 'RANDOM':
            if min_index == max_index:
                new_index = min_index
            else:
                new_index = random.randint(min_index, max_index)
                while new_index == base_index:
                    new_index = random.randint(min_index, max_index)
            _cmx_set_override_runtime_state(override_obj, slot_index, original_index, new_index, debug_source="action:random")
        elif self.action == 'RESET':
            _cmx_set_override_runtime_state(override_obj, slot_index, original_index, original_index, force_disable=True, debug_source="action:reset")

        _cmx_set_modifier_input_by_names(modifier, CMX_SELECT_INDEX_SOCKET_NAMES, point_index, socket_type='NodeSocketInt')
        _cmx_set_modifier_input_by_names(modifier, CMX_OVERRIDE_INFO_SOCKET_NAMES, override_obj, socket_type='NodeSocketObject')
        _cmx_request_modifier_evaluation(modifier, refresh_display=False)
        _cmx_update_override_visibility(override_obj)
        _cmx_sync_selected_override_vis_state(scene)
        _cmx_tag_redraw_all()
        return {'FINISHED'}


class CMXCloseEditInstancePopupOperator(bpy.types.Operator):
    bl_idname = "cmx.close_edit_instance_popup"
    bl_label = "Close Edit Instance Popup"

    def execute(self, context):
        context.scene.cmx_edit_instance_popup_visible = False
        _cmx_tag_redraw_all()
        return {'FINISHED'}


class CMXResetAllEditInstanceOverridesOperator(bpy.types.Operator):
    bl_idname = "cmx.reset_all_edit_instance_overrides"
    bl_label = "Reset All Overrides"

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        scene = context.scene
        crowd_name = getattr(scene, "cmx_edit_instance_crowd_name", "")
        if not crowd_name:
            return {'CANCELLED'}

        crowd_item = next((item for item in scene.crowd_data_items if item.name == crowd_name), None)
        modifier = cmx_get_crowd_modifier(crowd_item or crowd_name)
        override_obj = _cmx_get_override_object(crowd_name)
        if not modifier or not override_obj:
            return {'CANCELLED'}

        proxies = _cmx_get_proxy_objects_for_crowd(crowd_name)
        if not proxies:
            return {'CANCELLED'}

        for proxy_obj in proxies:
            slot_index = int(proxy_obj.get(CMX_EDIT_INSTANCE_PROXY_SLOT_PROP, -1))
            original_index = int(proxy_obj.get(CMX_EDIT_INSTANCE_PROXY_ORIGINAL_PROP, -1))
            if slot_index < 0 or original_index < 0:
                continue
            _cmx_set_override_runtime_state(override_obj, slot_index, original_index, original_index, force_disable=True, debug_source="action:reset_all")

        selected_point_index = getattr(scene, "cmx_edit_instance_selected_index", -1)
        if selected_point_index >= 0:
            _cmx_set_modifier_input_by_names(modifier, CMX_SELECT_INDEX_SOCKET_NAMES, selected_point_index, socket_type='NodeSocketInt')
        _cmx_set_modifier_input_by_names(modifier, CMX_OVERRIDE_INFO_SOCKET_NAMES, override_obj, socket_type='NodeSocketObject')
        _cmx_request_modifier_evaluation(modifier, refresh_display=False)
        _cmx_update_override_visibility(override_obj)
        _cmx_sync_selected_override_vis_state(scene)
        _cmx_tag_redraw_all()
        return {'FINISHED'}


class CMX_PT_EditInstancePopup(bpy.types.Panel):
    bl_label = "Edit Instance"
    bl_idname = "CMX_PT_edit_instance_popup"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    bl_ui_units_x = 13

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = False
        layout.use_property_decorate = False
        scene = context.scene
        crowd_name = getattr(scene, "cmx_edit_instance_crowd_name", "")
        point_index = getattr(scene, "cmx_edit_instance_selected_index", -1)
        slot_index = getattr(scene, "cmx_edit_instance_selected_slot", -1)
        original_index = getattr(scene, "cmx_edit_instance_selected_original_index", -1)

        header = layout.row(align=True)
        header.label(text="Edit Instance", icon='OUTLINER_OB_POINTCLOUD')
        header.separator()
        header.operator("cmx.close_edit_instance_popup", text="", icon='X')

        if not crowd_name or point_index < 0 or slot_index < 0 or original_index < 0:
            info_box = layout.box()
            info_box.label(text="Select a box to edit an instance index.", icon='INFO')
            return

        override_obj = _cmx_get_override_object(crowd_name)
        point_state = _cmx_get_override_runtime_state(override_obj, slot_index, point_index, original_index) if override_obj else None
        if not point_state:
            info_box = layout.box()
            info_box.label(text="Override data is not available for this point.", icon='ERROR')
            return

        info_box = layout.box()
        info_col = info_box.column(align=True)
        info_row = info_col.row(align=True)
        info_row.label(text="", icon='EMPTY_AXIS')
        info_row.label(text=str(point_state["point_index"]))
        info_row.separator()
        info_row.label(text="", icon='KEYTYPE_KEYFRAME_VEC')
        info_row.label(text=str(point_state["original_index"]))

        info_row = info_col.row(align=True)
        info_row.label(text="", icon='TRACKING_REFINE_BACKWARDS')
        info_row.label(text=str(point_state["override_index"]))
        info_row.separator()
        status_icon = 'CHECKMARK' if point_state["override_on"] else 'RADIOBUT_OFF'
        info_row.label(text="", icon=status_icon)
        info_row.label(text="Override" if point_state["override_on"] else "Original")

        layout.separator()
        button_col = layout.column(align=True)
        row = button_col.grid_flow(columns=3, even_columns=True, even_rows=True, align=True)
        row.operator("cmx.edit_instance_action", text="Previous", icon='TRIA_LEFT').action = 'PREVIOUS'
        row.operator("cmx.edit_instance_action", text="Next", icon='TRIA_RIGHT').action = 'NEXT'
        row.operator("cmx.edit_instance_action", text="Random", icon='FILE_REFRESH').action = 'RANDOM'

        row = button_col.grid_flow(columns=2, even_columns=True, even_rows=True, align=True)
        row.operator("cmx.edit_instance_action", text="Reset Override", icon='LOOP_BACK').action = 'RESET'
        row.operator("cmx.reset_all_edit_instance_overrides", text="Reset All")


class CMXRemoveCrowdDataOperator(bpy.types.Operator):
    """
    Operator to remove the selected crowd data item from the scene.
    """
    bl_idname = "cmx.crowd_data_remove_item"
    bl_label = "Remove Crowd Node"

    def execute(self, context):
        scene = context.scene
        if not scene.crowd_data_items:
            self.report({'WARNING'}, "Crowd list is empty.")
            return {'CANCELLED'}
        if scene.crowd_data_index < 0 or scene.crowd_data_index >= len(scene.crowd_data_items):
            self.report({'WARNING'}, "No crowd item selected or index is out of bounds.")
            return {'CANCELLED'}
        idx_to_remove = scene.crowd_data_index
        item_to_remove = scene.crowd_data_items[idx_to_remove]
        if scene.cmx_edit_instance_crowd_name == item_to_remove.name:
            _cmx_disable_edit_instance_mode(context, crowd_name=item_to_remove.name, remove_override_if_unused=False)
        _cmx_remove_proxy_collection(item_to_remove.name)
        override_obj = _cmx_get_override_object(item_to_remove.name)
        if override_obj:
            mesh = override_obj.data
            bpy.data.objects.remove(override_obj, do_unlink=True)
            if mesh and mesh.users == 0:
                bpy.data.meshes.remove(mesh)
        collection = bpy.data.collections.get(item_to_remove.name)
        if collection:
            objects_in_coll = list(collection.objects)
            for obj in objects_in_coll:
                bpy.data.objects.remove(obj, do_unlink=True)
            bpy.data.collections.remove(collection)
        scene.crowd_data_items.remove(idx_to_remove)
        num_items = len(scene.crowd_data_items)
        if num_items == 0:
            scene.crowd_data_index = 0
        else:
            scene.crowd_data_index = min(idx_to_remove, num_items - 1)
        context.area.tag_redraw()
        bpy.ops.outliner.orphans_purge(do_recursive=True)
        self.report({'INFO'}, f"Crowd item '{item_to_remove.name}' removed.")
        return {'FINISHED'}

    def invoke(self, context, event):
        if not context.scene.crowd_data_items:
            cmx_show_message_box(message="Crowd list is empty. Nothing to remove.", title="Info", icon='INFO')
            return {'CANCELLED'}
        return context.window_manager.invoke_props_dialog(self, width=250)

class CMXSetSourceCollectionOperator(bpy.types.Operator):
    """
    Operator to set the source collection for a selected crowd item.
    """
    bl_label = "Set Source Collection"
    bl_idname = "cmx.set_source_collection"

    source_collection: bpy.props.EnumProperty(name="Source Collection", items=cmx_get_source_list_item)# type: ignore
    socket_name: bpy.props.StringProperty()# type: ignore

    def draw(self, context):
        layout = self.layout
        split = layout.split(factor=0.3)
        split.label(text="Source :")
        split.prop(self, "source_collection", text="")

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        scene = context.scene
        collection = bpy.data.collections.get(self.source_collection)
        if not collection:
            cmx_show_message_box(message="Please activate a source collection.", title="Message Box", icon='INFO')
            return {'CANCELLED'}
        item, modifier = _cmx_get_active_crowd_item_and_modifier(scene)
        if not item or not modifier:
            self.report({'WARNING'}, "Crowd modifier not found.")
            return {'CANCELLED'}

        for inf_panel in modifier.node_group.interface.items_tree:
            if inf_panel.item_type != 'PANEL':
                continue
            for inf_item in inf_panel.interface_items:
                if inf_item.name == self.socket_name:
                    source_coll = bpy.data.collections.get(self.source_collection)
                    modifier[inf_item.identifier] = source_coll
                    item.source_collection = self.source_collection
                    cmx_refresh_modifier_display(modifier)
                    source_coll.hide_viewport = True
                    self.report({'INFO'}, f"Source set to {self.source_collection} for {inf_item.identifier}")
                    break
        context.area.tag_redraw()
        return {'FINISHED'}


class CMXClearSourceCollectionOperator(bpy.types.Operator):
    """Clear the assigned source collection from a crowd source socket."""
    bl_label = "Clear Source Collection"
    bl_idname = "cmx.clear_source_collection"

    socket_name: bpy.props.StringProperty()# type: ignore

    def execute(self, context):
        item, modifier = _cmx_get_active_crowd_item_and_modifier(context.scene)
        if not item or not modifier:
            self.report({'WARNING'}, "Crowd modifier not found.")
            return {'CANCELLED'}

        cleared = False
        for inf_panel in modifier.node_group.interface.items_tree:
            if inf_panel.item_type != 'PANEL':
                continue
            for inf_item in inf_panel.interface_items:
                if inf_item.name != self.socket_name:
                    continue
                try:
                    modifier[inf_item.identifier] = None
                    cleared = True
                except Exception:
                    pass
                break

        if not cleared:
            self.report({'WARNING'}, "Source socket not found.")
            return {'CANCELLED'}

        item.source_collection = ""
        cmx_refresh_modifier_display(modifier)
        context.area.tag_redraw()
        self.report({'INFO'}, f"Source cleared for {self.socket_name}")
        return {'FINISHED'}


class CMXSetDensityMaskVertexGroupOperator(bpy.types.Operator):
    """Set Density Mask string from an emitter vertex group name."""
    bl_idname = "cmx.set_density_mask_vertex_group"
    bl_label = "Set Density Mask"
    bl_options = {'REGISTER', 'UNDO'}

    crowd_item_name: bpy.props.StringProperty() # type: ignore
    socket_identifier: bpy.props.StringProperty() # type: ignore
    value: bpy.props.StringProperty(default=CMX_DENSITY_MASK_NONE_VALUE) # type: ignore

    def execute(self, context):
        modifier = cmx_get_crowd_modifier(self.crowd_item_name)
        if not modifier:
            self.report({'WARNING'}, "Crowd modifier not found.")
            return {'CANCELLED'}

        socket_item = _cmx_find_modifier_input_socket(
            modifier,
            CMX_DENSITY_MASK_SOCKET_NAMES,
            socket_type='NodeSocketString',
        )
        if not socket_item or socket_item.identifier != self.socket_identifier:
            self.report({'WARNING'}, "Density Mask socket not found.")
            return {'CANCELLED'}

        modifier[self.socket_identifier] = self.value
        cmx_refresh_modifier_display(modifier)
        if context.area:
            context.area.tag_redraw()
        return {'FINISHED'}


class CMXSetEmitterTypeOperator(bpy.types.Operator):
    """Set the Standing crowd emitter type without exposing the internal socket name."""
    bl_idname = "cmx.set_emitter_type"
    bl_label = "Set Emitter Type"
    bl_options = {'REGISTER', 'UNDO'}

    crowd_item_name: bpy.props.StringProperty() # type: ignore
    socket_identifier: bpy.props.StringProperty() # type: ignore
    value: bpy.props.IntProperty(default=0) # type: ignore
    label_value: bpy.props.StringProperty(default="Grid") # type: ignore

    def execute(self, context):
        modifier = cmx_get_crowd_modifier(self.crowd_item_name)
        if not modifier:
            self.report({'WARNING'}, "Crowd modifier not found.")
            return {'CANCELLED'}

        socket_item = _cmx_find_modifier_input_socket(
            modifier,
            CMX_EMITTER_TYPE_SOCKET_NAMES,
        )
        if not socket_item or socket_item.identifier != self.socket_identifier:
            self.report({'WARNING'}, "Emitter Type socket not found.")
            return {'CANCELLED'}

        current_value = modifier.get(self.socket_identifier)
        modifier[self.socket_identifier] = self.label_value if isinstance(current_value, str) else int(self.value)
        cmx_refresh_modifier_display(modifier)
        if context.area:
            context.area.tag_redraw()
        return {'FINISHED'}


class CMX_MT_EmitterType(bpy.types.Menu):
    bl_label = "Emitter Type"
    bl_idname = "CMX_MT_emitter_type"
    crowd_item_name = ""
    socket_identifier = ""

    def draw(self, context):
        layout = self.layout
        crowd_item_name = self.__class__.crowd_item_name
        socket_identifier = self.__class__.socket_identifier

        for label, value in CMX_EMITTER_TYPE_ITEMS:
            op = layout.operator("cmx.set_emitter_type", text=label)
            op.crowd_item_name = crowd_item_name
            op.socket_identifier = socket_identifier
            op.value = value
            op.label_value = label


class CMX_MT_DensityMaskVertexGroup(bpy.types.Menu):
    bl_label = "Density Mask"
    bl_idname = "CMX_MT_density_mask_vertex_group"
    crowd_item_name = ""
    socket_identifier = ""

    def draw(self, context):
        layout = self.layout
        crowd_item_name = self.__class__.crowd_item_name
        socket_identifier = self.__class__.socket_identifier
        modifier = cmx_get_crowd_modifier(crowd_item_name)

        op = layout.operator("cmx.set_density_mask_vertex_group", text=CMX_DENSITY_MASK_NONE_LABEL)
        op.crowd_item_name = crowd_item_name
        op.socket_identifier = socket_identifier
        op.value = CMX_DENSITY_MASK_NONE_VALUE

        emitter_object = _cmx_get_standing_emitter_object(modifier)
        if not emitter_object:
            row = layout.row()
            row.enabled = False
            row.label(text="No Emitter Object")
            return

        if not emitter_object.vertex_groups:
            row = layout.row()
            row.enabled = False
            row.label(text="No Vertex Groups")
            return

        layout.separator()
        for vertex_group in emitter_object.vertex_groups:
            op = layout.operator("cmx.set_density_mask_vertex_group", text=vertex_group.name)
            op.crowd_item_name = crowd_item_name
            op.socket_identifier = socket_identifier
            op.value = vertex_group.name

class CMXDuplicateCrowdDataOperator(bpy.types.Operator):
    """Duplicate selected Crowd Data with user-defined name"""
    bl_idname = "cmx.crowd_data_duplicate_item"
    bl_label = "Duplicate Crowd Item"
    bl_options = {'REGISTER', 'UNDO'}

    new_name: bpy.props.StringProperty(name="New Name", default="CrowdItem_copy")  # type: ignore

    def invoke(self, context, event):
        scene = context.scene
        index = scene.crowd_data_index
        if index < 0 or index >= len(scene.crowd_data_items):
            self.report({'WARNING'}, "No crowd item selected.")
            return {'CANCELLED'}
        # Default name suggestion
        source_item = scene.crowd_data_items[index]
        self.new_name = source_item.name + "_copy"
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "new_name")

    def execute(self, context):
        scene = context.scene
        items = scene.crowd_data_items
        index = scene.crowd_data_index

        # Check for name conflict
        new_name = (self.new_name or "").strip()
        is_valid_name, name_message = _cmx_validate_crowd_target_name(scene, new_name)
        if not is_valid_name:
            _cmx_show_validation_popup(name_message, title="Duplicate Name")
            return {'CANCELLED'}

        source_item = items[index]

        # Add new item
        new_item = items.add()
        new_item.name = new_name
        new_item.crowd_obj_name = source_item.crowd_obj_name
        new_item.source_collection = source_item.source_collection
        new_item.visible = source_item.visible

        # Load node object
        modifier = cmx_load_crowd_object(new_item)

        # Copy modifier inputs
        source_modifier = cmx_get_crowd_modifier(source_item)
        if source_modifier and modifier:
            modifier_inputs = cmx_get_modifier_inputs_from_crowd_item(source_item)
            for socket_id, value in modifier_inputs.items():
                cmx_set_modifier_input_value(modifier, socket_id, value, context)

        # Re-assign source collection if needed
        if modifier and modifier.node_group:
            cmx_assign_source_collection_to_modifier(modifier, new_item.source_collection)
            _cmx_ensure_standing_density_mask_default(modifier, new_item.crowd_obj_name)

        scene.crowd_data_index = len(items) - 1
        _cmx_select_crowd_item_in_viewport(scene, context, new_item)
        self.report({'INFO'}, f"Duplicated as '{new_name}'")
        return {'FINISHED'}

#---------------------------------------------CROWD PRESET-------------------------------------------------
class CMXLoadPresetCrowdOperator(bpy.types.Operator):
    """
    Operator to load a full crowd preset (sources and crowd objects) from a JSON file.
    """
    bl_idname = "cmx.load_preset_crowd"
    bl_label = "Load Crowd Preset"
    bl_description = "Loads a crowd configuration from a saved preset"
    bl_options = {'UNDO'}

    duplicate_source_conflicts: bpy.props.StringProperty(  # type: ignore
        name="Duplicate Source Conflicts",
        default="",
        options={'HIDDEN'}
    )

    @classmethod
    def poll(cls, context):
        wm = context.window_manager
        return hasattr(wm, 'crowd_preset') and wm.crowd_preset and wm.crowd_preset != ""

    def _load_selected_preset(self, wm):
        selected_preset_name = wm.crowd_preset
        file_path = os.path.join(CURRENT_DIRECTORY, "CMX_Data", "crowd_data.json")

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Crowd preset file not found: {file_path}")

        with open(file_path, 'r') as f:
            all_crowd_presets = json.load(f)

        if selected_preset_name not in all_crowd_presets:
            raise KeyError(f"Preset '{selected_preset_name}' not found in crowd_data.json.")

        return selected_preset_name, all_crowd_presets[selected_preset_name]

    def _collect_duplicate_source_conflicts(self, scene, all_source_data_from_preset):
        conflicts = []
        for source_data in all_source_data_from_preset:
            source_base, saved_source_name = _cmx_get_preset_source_names(source_data)
            if not source_base:
                continue
            existing = next(
                (it for it in scene.source_data_items if getattr(it, "preset_collection", "") == source_base),
                None
            )
            if not existing:
                continue
            conflicts.append((source_base, saved_source_name, existing.name))
        return conflicts

    def invoke(self, context, event):
        wm = context.window_manager
        if wm.cf_on_off_toggle:
            cmx_show_message_box(message="To proceed, please turn off Character Customize.",title="Warning", icon='ERROR')
            return {'CANCELLED'}
        source_dir = cmx_get_source_dir(create_if_missing=False)
        if not source_dir or not os.path.isdir(source_dir):
            cmx_show_message_box(message="CMX-Source folder not found. Please ensure the source library exists.",title="Warning", icon='ERROR')
            return {'CANCELLED'}

        try:
            _selected_preset_name, preset_to_load = self._load_selected_preset(wm)
        except FileNotFoundError as e:
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}
        except json.JSONDecodeError:
            self.report({'ERROR'}, "Error decoding crowd_data.json.")
            return {'CANCELLED'}
        except KeyError as e:
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}
        except Exception as e:
            self.report({'ERROR'}, f"Error reading crowd_data.json: {e}")
            return {'CANCELLED'}

        all_source_data_from_preset = preset_to_load.get("all_source_data", [])
        conflicts = self._collect_duplicate_source_conflicts(context.scene, all_source_data_from_preset)
        if not conflicts:
            self.duplicate_source_conflicts = ""
            return self.execute(context)

        return self.execute(context)

    def draw(self, context):
        layout = self.layout
        layout.label(text="Some sources use a preset collection already loaded in the scene.")
        layout.label(text="Choose whether to reuse the existing sources.")
        layout.label(text="If disabled, those duplicate sources and dependent crowd items will be skipped.")
        layout.separator()
        for line in self.duplicate_source_conflicts.splitlines()[:8]:
            layout.label(text=line)
        extra_count = max(0, len(self.duplicate_source_conflicts.splitlines()) - 8)
        if extra_count:
            layout.label(text=f"...and {extra_count} more")

    def execute(self, context):
        """
        Load the selected crowd preset from the JSON file and populate source/crowd lists.
        """
        wm = context.window_manager
        if wm.cf_on_off_toggle:
            cmx_show_message_box(message="To proceed, please turn off Character Customize.",title="Warning", icon='ERROR')
            return {'CANCELLED'}
        source_dir = cmx_get_source_dir(create_if_missing=False)
        if not source_dir or not os.path.isdir(source_dir):
            cmx_show_message_box(message="CMX-Source folder not found. Please ensure the source library exists.",title="Warning", icon='ERROR')
            return {'CANCELLED'}
        
        scene = context.scene
        
        try:
            cmx_set_progress_task("Load Preset", wm.crowd_preset)
            selected_preset_name, preset_to_load = self._load_selected_preset(wm)
        except json.JSONDecodeError:
            self.report({'ERROR'}, "Error decoding crowd_data.json.")
            return {'CANCELLED'}
        except FileNotFoundError as e:
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}
        except KeyError as e:
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}
        except Exception as e:
            self.report({'ERROR'}, f"Error reading crowd_data.json: {e}")
            return {'CANCELLED'}
        all_source_data_from_preset = preset_to_load.get("all_source_data", [])
        all_crowd_data_from_preset = preset_to_load.get("all_crowd_data", [])
        duplicate_conflicts = self._collect_duplicate_source_conflicts(scene, all_source_data_from_preset)
        duplicate_source_base_names = {source_base for source_base, _target_name, _existing_name in duplicate_conflicts}
        preset_source_name_map = {}
        for source_data in all_source_data_from_preset:
            source_base, saved_source_name = _cmx_get_preset_source_names(source_data)
            if not source_base:
                continue
            preset_source_name_map[source_base] = source_base
            if saved_source_name:
                preset_source_name_map[saved_source_name] = source_base

        def get_source_load_issue(source_base_name):
            source_base_name = (source_base_name or "").strip()
            if not source_base_name:
                return "missing", "missing source name"

            build_status = cmx_get_collection_build_status(source_base_name)
            source_blend_path = os.path.join(source_dir, source_base_name + ".blend")

            if build_status == CMX_BUILD_STATE_NEVER:
                return "not_built", "source not built"
            if build_status == CMX_BUILD_STATE_DIRTY:
                return "not_built", "source needs rebuild"
            if not os.path.exists(source_blend_path):
                if build_status == CMX_BUILD_STATE_BUILT:
                    return "missing_file", "built source file missing"
                return "not_built", "source file not built"
            return None, ""

        def load_source_from_library(source_base_name):
            """Load source using the source-library name as the in-scene source name."""
            existing = next((it for it in scene.source_data_items if it.name == source_base_name), None)
            if existing:
                return existing, False, False
            existing_same_preset = next(
                (it for it in scene.source_data_items if getattr(it, "preset_collection", "") == source_base_name),
                None
            )
            if existing_same_preset:
                return existing_same_preset, True, False
            existing_collection = bpy.data.collections.get(source_base_name)
            if existing_collection:
                source_item = _cmx_ensure_source_item_for_collection(context, source_base_name, existing_collection)
                if source_item:
                    return source_item, False, False
            return cmx_add_source_data_item(context, source_base_name), False, False

        loaded_source_items_map = {}
        resolved_source_name_map = {}
        source_visibility_restore = []
        skipped_source_names = []
        skipped_source_not_built = []
        skipped_source_missing_files = []
        skipped_source_conflicts = []
        for source_data in all_source_data_from_preset:
            try:
                source_base, saved_source_name = _cmx_get_preset_source_names(source_data)
                if not source_base:
                    continue
                display_source_name = saved_source_name or source_base
                cmx_set_progress_task("Load Source", source_base)
                source_issue_type, source_issue_label = get_source_load_issue(source_base)
                if source_issue_type:
                    label = f"{display_source_name} ({source_base})"
                    skipped_source_names.append(label)
                    if source_issue_type == "not_built":
                        skipped_source_not_built.append(label)
                    elif source_issue_type == "missing_file":
                        skipped_source_missing_files.append(label)
                    loaded_source_items_map[source_base] = None
                    if saved_source_name:
                        loaded_source_items_map[saved_source_name] = None
                        resolved_source_name_map[saved_source_name] = ""
                    resolved_source_name_map[source_base] = ""
                    continue
                source_item_instance, reused_existing_source, duplicate_import_skipped = load_source_from_library(source_base)
                if not source_item_instance:
                    if duplicate_import_skipped:
                        label = f"{display_source_name} (duplicate source skipped)"
                        skipped_source_names.append(label)
                        skipped_source_conflicts.append(label)
                        loaded_source_items_map[source_base] = None
                        if saved_source_name:
                            loaded_source_items_map[saved_source_name] = None
                            resolved_source_name_map[saved_source_name] = ""
                        resolved_source_name_map[source_base] = ""
                    else:
                        label = f"{display_source_name} ({source_base})"
                        skipped_source_names.append(label)
                        skipped_source_conflicts.append(label)
                    continue
                should_apply_source_settings = (
                    not reused_existing_source and
                    source_base not in duplicate_source_base_names
                )
                final_source_visible = bool(source_data.get("visible", True))
                source_visibility_restore.append((source_item_instance.name, final_source_visible))
                if should_apply_source_settings:
                    source_item_instance.preview_type = source_data.get("preview_type", 'SOURCE_FULL')
                    source_item_instance.preset_collection = source_base
                    source_item_instance.start_frame = source_data.get("start_frame", 0)
                    source_item_instance.anim_speed = source_data.get("anim_speed", 1.0)
                    source_item_instance.random_start = source_data.get("random_start_offset", 0)
                    source_item_instance.random_speed = source_data.get("random_speed_variation", 0.0)
                    try:
                        cmx_update_source_start_frame(source_item_instance, context)
                        cmx_set_random_strat_frame_anim(source_item_instance, context)
                        cmx_update_source_anim_speed(source_item_instance, context)
                    except Exception:
                        pass
                loaded_source_items_map[source_item_instance.name] = source_item_instance
                loaded_source_items_map[source_base] = source_item_instance
                resolved_source_name_map[source_base] = source_item_instance.name
                if saved_source_name:
                    loaded_source_items_map[saved_source_name] = source_item_instance
                    resolved_source_name_map[saved_source_name] = source_item_instance.name
                resolved_source_name_map[source_item_instance.name] = source_item_instance.name
            finally:
                _cmx_flush_preset_load_viewport(context)

        skipped_crowd_names = []
        for crowd_data in all_crowd_data_from_preset:
            try:
                crowd_item_name = crowd_data.get("crowd_item_name")
                crowd_type = crowd_data.get("crowd_type")
                saved_source_coll_name = crowd_data.get("source_collection_name")

                if not crowd_item_name or not crowd_type:
                    continue

                crowd_item_instance = next((item for item in scene.crowd_data_items if item.name == crowd_item_name), None)
                if crowd_item_instance:
                    continue
                is_valid_name, _name_message = _cmx_validate_crowd_target_name(scene, crowd_item_name)
                if not is_valid_name:
                    skipped_crowd_names.append(crowd_item_name)
                    continue

                cmx_set_progress_task("Load Crowd", crowd_item_name)
                crowd_item_instance = scene.crowd_data_items.add()
                crowd_item_instance.name = crowd_item_name
                crowd_item_instance.crowd_obj_name = crowd_type
                resolved_source_name = resolved_source_name_map.get(saved_source_coll_name, "")
                crowd_item_instance.source_collection = resolved_source_name

                modifier = cmx_load_crowd_object(crowd_item_instance)
                if modifier:
                    if not resolved_source_name and saved_source_coll_name and _cmx_modifier_has_primary_source_socket(modifier):
                        skipped_crowd_names.append(f"{crowd_item_name} (source unavailable)")
                    modifier_inputs_data = crowd_data.get("modifier_inputs", {})
                    for socket_identifier, saved_value_data in modifier_inputs_data.items():
                        remapped_value = _cmx_remap_internal_collection_value(saved_value_data, preset_source_name_map)
                        cmx_set_modifier_input_value(
                            modifier,
                            socket_identifier,
                            remapped_value,
                            context,
                            source_name_map=resolved_source_name_map,
                        )
                    actual_source_blender_collection = bpy.data.collections.get(crowd_item_instance.source_collection)
                    if actual_source_blender_collection:
                        cmx_assign_source_collection_to_modifier(modifier, crowd_item_instance.source_collection)
                    _cmx_ensure_standing_density_mask_default(modifier, crowd_item_instance.crowd_obj_name)
            finally:
                _cmx_flush_preset_load_viewport(context)

        if source_visibility_restore:
            visibility_restore_data = list(source_visibility_restore)

            def _cmx_restore_loaded_source_visibility():
                scene_for_restore = getattr(bpy.context, "scene", None)
                if not scene_for_restore:
                    return None

                for source_item_name, final_source_visible in visibility_restore_data:
                    source_item = next(
                        (it for it in getattr(scene_for_restore, "source_data_items", []) if it.name == source_item_name),
                        None,
                    )
                    try:
                        if source_item is not None:
                            if bool(getattr(source_item, "visible", True)) != final_source_visible:
                                source_item.visible = final_source_visible
                            else:
                                _cmx_apply_source_instance_visibility(source_item_name, final_source_visible)
                        else:
                            _cmx_apply_source_instance_visibility(source_item_name, final_source_visible)
                    except Exception:
                        try:
                            _cmx_apply_source_instance_visibility(source_item_name, final_source_visible)
                        except Exception:
                            pass

                _cmx_tag_redraw_all()
                return None

            bpy.app.timers.register(_cmx_restore_loaded_source_visibility, first_interval=0.0)

        if scene.source_data_items:
            scene.source_data_index = len(scene.source_data_items) - 1
        if scene.crowd_data_items:
            scene.crowd_data_index = len(scene.crowd_data_items) - 1
            _cmx_select_crowd_item_in_viewport(scene, context, scene.crowd_data_items[scene.crowd_data_index])

        if skipped_source_names or skipped_crowd_names:
            skipped_parts = []
            popup_title = "Preset Load Warning"
            popup_message = "Some preset items were skipped."
            if skipped_source_not_built:
                popup_title = "Source Not Built"
                popup_message = "Some sources are not built yet or need rebuild."
                skipped_parts.append("Build Source First: " + ", ".join(skipped_source_not_built[:5]))
            if skipped_source_missing_files:
                skipped_parts.append("Missing Files: " + ", ".join(skipped_source_missing_files[:5]))
            if skipped_source_conflicts:
                skipped_parts.append("Conflicts: " + ", ".join(skipped_source_conflicts[:5]))
            if skipped_source_names and not (skipped_source_not_built or skipped_source_missing_files or skipped_source_conflicts):
                skipped_parts.append("Sources: " + ", ".join(skipped_source_names[:5]))
            if skipped_crowd_names:
                skipped_parts.append("Crowds: " + ", ".join(skipped_crowd_names[:5]))
            _cmx_show_validation_popup(
                popup_message + "\n" + "\n".join(skipped_parts),
                title=popup_title,
                icon='INFO'
            )

        self.report({'INFO'}, f"Crowd preset '{selected_preset_name}' loaded with all items.")
        cmx_set_progress_success()
        for area in context.screen.areas:
            area.tag_redraw()
        return {'FINISHED'}

class CMXSavePresetCrowdOperator(bpy.types.Operator):
    """
    Operator to save the current source/crowd data as a new crowd preset.
    """
    bl_idname = "cmx.save_preset_crowd"
    bl_label = "Save Crowd Preset"
    bl_description = "Saves the current source and crowd configurations as a new preset"
    bl_options = {'REGISTER', 'UNDO'}

    preset_name: StringProperty(
        name="Preset Name",
        description="Enter a name for this crowd preset"
    ) # type: ignore

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        """
        Gather all current source/crowd data, serialize, and save as a new preset in JSON file.
        """
        import os, json
        scene = context.scene
        scene_source_name_map = _cmx_build_scene_source_name_map(scene)
        if not self.preset_name.strip():
            self.report({'WARNING'}, "Preset name cannot be empty.")
            return {'CANCELLED'}

        all_source_data_to_save = []
        for src_item in scene.source_data_items:
            canonical_source_name = scene_source_name_map.get(
                getattr(src_item, "name", ""),
                getattr(src_item, "preset_collection", "") or getattr(src_item, "name", "")
            )
            source_data = {
                "name": canonical_source_name,
                "active": src_item.active,
                "visible": src_item.visible,
                "preview_type": src_item.preview_type,
                "preset_collection_enum": canonical_source_name,
                "start_frame": src_item.start_frame,
                "anim_speed": src_item.anim_speed,
                "random_start_offset": src_item.random_start,
                "random_speed_variation": src_item.random_speed,
            }
            all_source_data_to_save.append(source_data)

        all_crowd_data_to_save = []
        for crowd_item in scene.crowd_data_items:
            modifier = cmx_get_crowd_modifier(crowd_item)
            modifier_inputs = cmx_get_modifier_inputs_from_crowd_item(crowd_item)
            normalized_modifier_inputs = {
                socket_identifier: _cmx_normalize_saved_source_socket_value(
                    modifier,
                    socket_identifier,
                    saved_value_data,
                    scene_source_name_map,
                )
                for socket_identifier, saved_value_data in modifier_inputs.items()
            }
            crowd_data = {
                "crowd_item_name": crowd_item.name,
                "crowd_type": crowd_item.crowd_obj_name,
                "visible": crowd_item.visible,
                "source_collection_name": scene_source_name_map.get(crowd_item.source_collection, crowd_item.source_collection),
                "modifier_inputs": normalized_modifier_inputs,
            }
            all_crowd_data_to_save.append(crowd_data)

        preset_content = {
            "all_source_data": all_source_data_to_save,
            "all_crowd_data": all_crowd_data_to_save,
        }

        file_path = os.path.join(CURRENT_DIRECTORY, "CMX_Data", "crowd_data.json")
        all_presets = {}
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    all_presets = json.load(f)
            except json.JSONDecodeError:
                self.report({'WARNING'}, "crowd_data.json is corrupted. Saving as new file content.")
                all_presets = {}
            except Exception as e:
                self.report({'ERROR'}, f"Error reading crowd_data.json: {e}")
                return {'CANCELLED'}

        all_presets[self.preset_name.strip()] = preset_content

        try:
            with open(file_path, 'w') as f:
                json.dump(all_presets, f, indent=4)
            self.report({'INFO'}, f"Crowd preset '{self.preset_name.strip()}' saved successfully.")
        except Exception as e:
            self.report({'ERROR'}, f"Failed to save crowd_data.json: {e}")
            return {'CANCELLED'}

        for area in context.screen.areas:
            area.tag_redraw()
        return {'FINISHED'}

class CMXRemovePresetCrowdOperator(bpy.types.Operator):
    """
    Operator to remove the selected crowd preset from the JSON data file.
    """
    bl_idname = "cmx.remove_preset_crowd"
    bl_label = "Remove Crowd Preset"
    bl_description = "Removes the selected crowd preset from the JSON data file"
    bl_options = {'REGISTER', 'UNDO'}

    preset_name_to_remove: StringProperty() # type: ignore

    def draw(self, context):
        pass

    @classmethod
    def poll(cls, context):
        wm = context.window_manager
        return hasattr(wm, 'crowd_preset') and wm.crowd_preset != ""

    def execute(self, context):
        """
        Remove the specified crowd preset from the JSON file.
        """
        import os, json
        wm = context.window_manager
        preset_name = self.preset_name_to_remove

        if not preset_name:
            self.report({'WARNING'}, "No crowd preset name specified for removal.")
            return {'CANCELLED'}

        file_path = os.path.join(CURRENT_DIRECTORY, "CMX_Data", "crowd_data.json")
        all_crowd_presets = {}
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    all_crowd_presets = json.load(f)
            except json.JSONDecodeError:
                self.report({'WARNING'}, f"Could not decode crowd_data.json.")
                all_crowd_presets = {}
            except Exception as e:
                self.report({'ERROR'}, f"Error reading crowd_data.json: {e}")
                return {'CANCELLED'}
        else:
            self.report({'WARNING'}, f"crowd_data.json not found. Cannot remove preset '{preset_name}'.")
            return {'CANCELLED'}

        if preset_name in all_crowd_presets:
            del all_crowd_presets[preset_name]
            try:
                with open(file_path, 'w') as f:
                    json.dump(all_crowd_presets, f, indent=4)
                self.report({'INFO'}, f"Crowd preset '{preset_name}' removed successfully.")
            except Exception as e:
                self.report({'ERROR'}, f"Failed to save updated crowd_data.json: {e}")
                return {'CANCELLED'}
        else:
            self.report({'WARNING'}, f"Crowd preset '{preset_name}' not found in crowd_data.json.")

        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                for region in area.regions:
                    if region.type == 'UI':
                        region.tag_redraw()
                        break

        return {'FINISHED'}

    def invoke(self, context, event):
        """
        Display a confirmation dialog before deleting the selected preset.
        """
        wm = context.window_manager
        if not (hasattr(wm, 'crowd_preset') and wm.crowd_preset and wm.crowd_preset != ""):
            try:
                cmx_show_message_box(
                    message="No crowd preset selected to remove.",
                    title="Action Cancelled",
                    icon='INFO')
            except NameError:
                self.report({'INFO'}, "No crowd preset selected to remove.")
            return {'CANCELLED'}

        self.preset_name_to_remove = wm.crowd_preset
        self.bl_label = f"Remove Crowd Preset: '{self.preset_name_to_remove}'?"
        return context.window_manager.invoke_props_dialog(self, width=350)

classes = [
    CMXSourceDataPropertyGroup,
    CMXCrowdModifierPanelState,
    CMX_UL_SourceData,
    CMXAddSourceFromPresetOperator,
    CMXAddSourceDataOperator,
    CMXRemoveSourceDataOperator,
    CMXCrowdDataPropertyGroup,
    CMX_UL_CrowdData,
    CMXAddCrowdDataOperator,
    CMXToggleEditInstanceModeOperator,
    CMXEditInstanceActionOperator,
    CMXResetAllEditInstanceOverridesOperator,
    CMXDuplicateCrowdDataOperator,
    CMXRemoveCrowdDataOperator,
    CMXSetSourceCollectionOperator,
    CMXClearSourceCollectionOperator,
    CMXSetEmitterTypeOperator,
    CMX_MT_EmitterType,
    CMXSetDensityMaskVertexGroupOperator,
    CMX_MT_DensityMaskVertexGroup,
    CMXLoadPresetCrowdOperator,
    CMXSavePresetCrowdOperator,
    CMXRemovePresetCrowdOperator
]

def register():
    global CMX_EDIT_INSTANCE_TIMER_RUNNING
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.WindowManager.crowd_modifier_panels = bpy.props.CollectionProperty(type=CMXCrowdModifierPanelState)
    bpy.types.WindowManager.cmx_crowd_group_source_expanded = bpy.props.BoolProperty(name="Source", default=False)
    bpy.types.WindowManager.cmx_crowd_group_emitter_expanded = bpy.props.BoolProperty(name="Emitter", default=False)
    bpy.types.WindowManager.cmx_crowd_group_placement_expanded = bpy.props.BoolProperty(name="Placement", default=False)
    bpy.types.WindowManager.cmx_crowd_group_variation_expanded = bpy.props.BoolProperty(name="Variation", default=False)
    bpy.types.WindowManager.cmx_crowd_group_assets_expanded = bpy.props.BoolProperty(name="Assets", default=False)
    bpy.types.Scene.crowd_data_items = bpy.props.CollectionProperty(type=CMXCrowdDataPropertyGroup)
    bpy.types.Scene.crowd_data_index = bpy.props.IntProperty(update=_cmx_update_crowd_selection_from_list)
    bpy.types.Scene.source_data_items = bpy.props.CollectionProperty(type=CMXSourceDataPropertyGroup)
    bpy.types.Scene.source_data_index = bpy.props.IntProperty()
    bpy.types.Scene.show_source_list = bpy.props.BoolProperty(name="Show Source List", default=False)
    bpy.types.Scene.show_crowd_list = bpy.props.BoolProperty(name="Show Crowd List", default=False)
    bpy.types.Scene.show_modifier_settings = bpy.props.BoolProperty(name="Show Modifier Settings", default=False)
    bpy.types.Scene.sync_crowd_selection = bpy.props.BoolProperty(
        name="Sync Crowd Selection",
        description="Sync selected Crowd item with the active object in the 3D Viewport",
        default=True,
    )
    bpy.types.Scene.is_syncing_selection = bpy.props.BoolProperty(
        name="Is Syncing Selection",
        default=False,
        options={'HIDDEN', 'SKIP_SAVE'},
    )
    bpy.types.Scene.cmx_edit_instance_crowd_name = bpy.props.StringProperty(
        name="Edit Instance Crowd",
        default="",
        options={'HIDDEN', 'SKIP_SAVE'},
    )
    bpy.types.Scene.cmx_edit_instance_selected_index = bpy.props.IntProperty(
        name="Edit Instance Selected Index",
        default=-1,
        options={'HIDDEN', 'SKIP_SAVE'},
    )
    bpy.types.Scene.cmx_edit_instance_selected_slot = bpy.props.IntProperty(
        name="Edit Instance Selected Slot",
        default=-1,
        options={'HIDDEN', 'SKIP_SAVE'},
    )
    bpy.types.Scene.cmx_edit_instance_selected_original_index = bpy.props.IntProperty(
        name="Edit Instance Selected Original Index",
        default=-1,
        options={'HIDDEN', 'SKIP_SAVE'},
    )
    bpy.types.Scene.cmx_edit_instance_popup_pending = bpy.props.BoolProperty(
        name="Edit Instance Popup Pending",
        default=False,
        options={'HIDDEN', 'SKIP_SAVE'},
    )
    bpy.types.Scene.cmx_edit_instance_popup_visible = bpy.props.BoolProperty(
        name="Edit Instance Popup Visible",
        default=False,
        options={'HIDDEN', 'SKIP_SAVE'},
    )
    bpy.types.Scene.cmx_edit_instance_ui_sync_lock = bpy.props.BoolProperty(
        name="Edit Instance UI Sync Lock",
        default=False,
        options={'HIDDEN', 'SKIP_SAVE'},
    )
    bpy.types.Scene.cmx_edit_instance_last_sync_time = bpy.props.FloatProperty(
        name="Edit Instance Last Sync Time",
        default=0.0,
        options={'HIDDEN', 'SKIP_SAVE'},
    )
    bpy.types.Scene.cmx_edit_instance_proxy_display_as = bpy.props.EnumProperty(
        name="Display As",
        items=CMX_EMPTY_DISPLAY_ITEMS,
        default='CUBE',
        options={'SKIP_SAVE'},
        update=_cmx_update_proxy_display_as,
    )
    bpy.types.Scene.cmx_edit_instance_proxy_show_names = bpy.props.BoolProperty(
        name="Show Point Names",
        default=False,
        options={'SKIP_SAVE'},
        update=_cmx_update_proxy_show_names,
    )
    bpy.types.Scene.cmx_edit_instance_proxy_in_front = bpy.props.BoolProperty(
        name="In Front",
        default=True,
        options={'SKIP_SAVE'},
        update=_cmx_update_proxy_in_front,
    )
    bpy.types.Scene.cmx_edit_instance_ins_vis_only_select = bpy.props.BoolProperty(
        name="Instance Visible Only Select",
        default=False,
        options={'SKIP_SAVE'},
        update=_cmx_update_ins_vis_only_select,
    )
    bpy.types.Scene.cmx_edit_instance_override_vis = bpy.props.BoolProperty(
        name="Override Visibility",
        default=True,
        options={'SKIP_SAVE'},
        update=_cmx_update_selected_override_vis,
    )
    bpy.types.Scene.cmx_edit_instance_override_pos = bpy.props.FloatVectorProperty(
        name="Override Position",
        size=3,
        subtype='TRANSLATION',
        default=CMX_VECTOR_ZERO,
        options={'SKIP_SAVE'},
        update=_cmx_update_selected_override_pos,
    )
    bpy.types.Scene.cmx_edit_instance_override_rot = bpy.props.FloatVectorProperty(
        name="Override Rotation",
        size=3,
        subtype='EULER',
        default=CMX_VECTOR_ZERO,
        options={'SKIP_SAVE'},
        update=_cmx_update_selected_override_rot,
    )
    bpy.types.Scene.cmx_edit_instance_override_scale = bpy.props.FloatProperty(
        name="Override Scale",
        default=0.0,
        options={'SKIP_SAVE'},
        update=_cmx_update_selected_override_scale,
    )
    bpy.types.Scene.cmx_edit_instance_override_speed = bpy.props.FloatProperty(
        name="Override Speed",
        default=1.0,
        options={'SKIP_SAVE'},
        update=_cmx_update_selected_override_speed,
    )
    bpy.types.Scene.cmx_edit_instance_popup_last_index = bpy.props.IntProperty(
        name="Edit Instance Popup Last Index",
        default=-1,
        options={'HIDDEN', 'SKIP_SAVE'},
    )
    bpy.types.Scene.cmx_edit_instance_popup_crowd_name = bpy.props.StringProperty(
        name="Edit Instance Popup Crowd",
        default="",
        options={'HIDDEN', 'SKIP_SAVE'},
    )
    bpy.types.Scene.cmx_edit_instance_popup_target_index = bpy.props.IntProperty(
        name="Edit Instance Popup Target Index",
        default=-1,
        options={'HIDDEN', 'SKIP_SAVE'},
    )
    bpy.types.Scene.cmx_edit_instance_popup_target_slot = bpy.props.IntProperty(
        name="Edit Instance Popup Target Slot",
        default=-1,
        options={'HIDDEN', 'SKIP_SAVE'},
    )
    bpy.types.Scene.cmx_edit_instance_popup_target_original_index = bpy.props.IntProperty(
        name="Edit Instance Popup Target Original Index",
        default=-1,
        options={'HIDDEN', 'SKIP_SAVE'},
    )
    if _cmx_sync_crowd_list_from_viewport not in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.append(_cmx_sync_crowd_list_from_viewport)
    CMX_EDIT_INSTANCE_TIMER_RUNNING = True
    bpy.app.timers.register(_cmx_edit_instance_poll_timer, first_interval=CMX_EDIT_INSTANCE_POLL_INTERVAL, persistent=True)

def unregister():
    global CMX_EDIT_INSTANCE_TIMER_RUNNING
    CMX_EDIT_INSTANCE_TIMER_RUNNING = False
    try:
        _cmx_disable_edit_instance_mode(bpy.context, crowd_name=getattr(bpy.context.scene, "cmx_edit_instance_crowd_name", ""))
    except Exception:
        pass
    if _cmx_sync_crowd_list_from_viewport in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(_cmx_sync_crowd_list_from_viewport)
    for cls in classes:
        bpy.utils.unregister_class(cls)
    del bpy.types.WindowManager.crowd_modifier_panels
    del bpy.types.WindowManager.cmx_crowd_group_source_expanded
    del bpy.types.WindowManager.cmx_crowd_group_emitter_expanded
    del bpy.types.WindowManager.cmx_crowd_group_placement_expanded
    del bpy.types.WindowManager.cmx_crowd_group_variation_expanded
    del bpy.types.WindowManager.cmx_crowd_group_assets_expanded
    del bpy.types.Scene.crowd_data_items
    del bpy.types.Scene.crowd_data_index
    del bpy.types.Scene.source_data_items
    del bpy.types.Scene.source_data_index
    del bpy.types.Scene.show_source_list
    del bpy.types.Scene.show_crowd_list
    del bpy.types.Scene.show_modifier_settings
    del bpy.types.Scene.sync_crowd_selection
    del bpy.types.Scene.is_syncing_selection
    del bpy.types.Scene.cmx_edit_instance_crowd_name
    del bpy.types.Scene.cmx_edit_instance_selected_index
    del bpy.types.Scene.cmx_edit_instance_selected_slot
    del bpy.types.Scene.cmx_edit_instance_selected_original_index
    del bpy.types.Scene.cmx_edit_instance_popup_pending
    del bpy.types.Scene.cmx_edit_instance_popup_visible
    del bpy.types.Scene.cmx_edit_instance_ui_sync_lock
    del bpy.types.Scene.cmx_edit_instance_last_sync_time
    del bpy.types.Scene.cmx_edit_instance_proxy_display_as
    del bpy.types.Scene.cmx_edit_instance_proxy_show_names
    del bpy.types.Scene.cmx_edit_instance_proxy_in_front
    del bpy.types.Scene.cmx_edit_instance_ins_vis_only_select
    del bpy.types.Scene.cmx_edit_instance_override_vis
    del bpy.types.Scene.cmx_edit_instance_override_pos
    del bpy.types.Scene.cmx_edit_instance_override_rot
    del bpy.types.Scene.cmx_edit_instance_override_scale
    del bpy.types.Scene.cmx_edit_instance_override_speed
    del bpy.types.Scene.cmx_edit_instance_popup_last_index
    del bpy.types.Scene.cmx_edit_instance_popup_crowd_name
    del bpy.types.Scene.cmx_edit_instance_popup_target_index
    del bpy.types.Scene.cmx_edit_instance_popup_target_slot
    del bpy.types.Scene.cmx_edit_instance_popup_target_original_index
