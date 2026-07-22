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
from .system_var import *
from .OP_link_asset import *

_prop_map = {
    "Hair": "item_off_hair",
    "Head": "item_off_head",
    "Eye": "item_off_eye",
    "Torso": "item_off_torso",
    "Leg": "item_off_leg",
    "Accessory": "item_off_Accessory", 
    "Foot": "item_off_foot",
}

def cmx_get_item_off_prop(context, _body_part_key_):
    wm = context.window_manager
    prop = _prop_map.get(_body_part_key_)
    return getattr(wm, prop, None)

def cmx_set_item_off_prop(context, _body_part_key_, status):
    wm = context.window_manager
    prop = _prop_map.get(_body_part_key_)
    if prop:
        setattr(wm, prop, status)

def cmx_set_color_item_by_key(self, context, body_part):
    """Set custom property 'Color_Input_Ctrl' on the material in the specified object."""
    if ACTIVE_CHAR[body_part] is None:
        return
    item_name = ACTIVE_CHAR[body_part]
    color_prop = cmx_get_color_prop(context, body_part)
    coll_asset_name = f"CMX_{body_part}"
    coll = bpy.data.collections.get(coll_asset_name)
    if not coll:
        return
    obj_exist = coll.objects.get(item_name) if hasattr(coll.objects, "get") else None
    if not obj_exist:
        obj_exist = next((o for o in coll.objects if o.name == item_name), None)
    if not obj_exist:
        return
    if obj_exist.type == 'MESH' and obj_exist.material_slots:
        for mat_sl in obj_exist.material_slots:
            mat = mat_sl.material
            if not mat:
                continue
            if "Color_Input_Ctrl" not in mat:
                mat["Color_Input_Ctrl"] = [1.0, 1.0, 1.0, 1.0]
            arr = list(color_prop)[:4]
            while len(arr) < 4:
                arr.append(1.0)
            mat["Color_Input_Ctrl"] = arr
            mat.id_properties_ui("Color_Input_Ctrl").update(
                subtype='COLOR', min=0.0, max=1.0, default=[1.0, 1.0, 1.0, 1.0]
            )
            ACTIVE_CHAR[f"{body_part}_Color"] = arr
            mat.update_tag()

def cmx_set_color_spawn_item(item_color, object_name, coll_asset_name):
    """Set color property for object spawned to scene."""
    coll = bpy.data.collections.get(coll_asset_name)
    if not coll:
        return
    # obj = coll.objects.get(object_name) if hasattr(coll.objects, "get") else None
    obj = next((o for o in coll.objects if o.name == object_name), None)

    if not obj:
        obj = next((o for o in coll.objects if o.name == object_name), None)
    if not obj:
        return
    if obj.type == 'MESH' and obj.material_slots:
        for mat_sl in obj.material_slots:
            mat = mat_sl.material
            if not mat:
                continue
            if "Color_Input_Ctrl" not in mat:
                mat["Color_Input_Ctrl"] = [1.0, 1.0, 1.0, 1.0]
            arr = list(item_color)[:4]
            while len(arr) < 4:
                arr.append(1.0)
            mat["Color_Input_Ctrl"] = arr
            mat.id_properties_ui("Color_Input_Ctrl").update(
                subtype='COLOR', min=0.0, max=1.0, default=[1.0, 1.0, 1.0, 1.0]
            )
            mat.update_tag()

_color_map = {
    "Hair": "color_property_hair",
    "Head": "color_property_head",
    "Eye": "color_property_eye",
    "Torso": "color_property_torso",
    "Accessory": "color_property_Accessory",  
    "Leg": "color_property_leg",
    "Foot": "color_property_foot",
    "Hair_Color": "color_property_hair",
    "Head_Color": "color_property_head",
    "Eye_Color": "color_property_eye",
    "Torso_Color": "color_property_torso",
    "Accessory_Color": "color_property_Accessory",
    "Leg_Color": "color_property_leg",
    "Foot_Color": "color_property_foot",
}

def cmx_get_color_prop(context, _body_part_key_):
    wm = context.window_manager
    prop = _color_map.get(_body_part_key_)
    return getattr(wm, prop, None)

def cmx_set_color_prop(context, _body_part_key_, color_value):
    wm = context.window_manager
    prop = _color_map.get(_body_part_key_)
    if prop:
        setattr(wm, prop, color_value)

def cmx_set_shape_by_key(context, _key_, collection_name, is_source=False, preset_value=0.0):
    """Set shape key value by key on objects in collection."""
    collection = bpy.data.collections.get(collection_name)
    if not collection:
        return
    for obj in collection.objects:
        if obj.type == 'MESH' and obj.data.shape_keys:
            shape_key = obj.data.shape_keys.key_blocks.get(_key_)
            if shape_key:
                if is_source and preset_value:
                    shape_key.value = preset_value
                else:
                    shape_key.value = getattr(context.window_manager, _key_)
                    ACTIVE_CHAR[_key_] = shape_key.value
            else:
                ACTIVE_CHAR[_key_] = None

def cmx_set_shape_keys_batch(context, keys, collection_name, is_source=False, preset_values=None):
    """Set multiple shape key values in a single pass over the collection's meshes.
    Reduces repeated per-key iteration over objects for better performance during initialization/switch.

    - keys: list of shape key names to apply
    - is_source/preset_values: optional source-mode values mapping
    """
    collection = bpy.data.collections.get(collection_name)
    if not collection:
        return

    wm = context.window_manager
    # Prepare value map once
    value_map = {}
    for key in keys:
        if is_source and isinstance(preset_values, dict) and key in preset_values:
            value_map[key] = preset_values[key]
        else:
            value_map[key] = getattr(wm, key, 0.0)

    for obj in collection.objects:
        if obj.type == 'MESH' and obj.data.shape_keys and obj.data.shape_keys.key_blocks:
            key_blocks = obj.data.shape_keys.key_blocks
            for key, val in value_map.items():
                sk = key_blocks.get(key)
                if sk:
                    sk.value = val
                    ACTIVE_CHAR[key] = val
                else:
                    ACTIVE_CHAR[key] = None

def cmx_update_cf_assets_instance_rotation(self, context):
    """Update rotation for all instances of CMX_Assets in scene."""
    scene = context.scene
    cf_assets_coll = bpy.data.collections.get("CMX_Assets")
    if not cf_assets_coll:
        return
    for obj in scene.collection.objects:
        if obj.instance_type == 'COLLECTION' and obj.instance_collection == cf_assets_coll:
            obj.rotation_euler[2] = self.char_preview_rotation_z
