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
import random
from bpy.props import StringProperty, IntProperty
from bpy.types import Operator
from .OP_common import *
from .system_var import *
from .OP_link_asset import *
from .enum_item_gen import *
from .OP_update_prop import *

def cmx_get_preview_item(context, _preview_key_):
    """
    Get preview property from window manager for the given preview key.
    """
    wm = context.window_manager
    mapping = {
        "Hair": wm.hair_previews,
        "Head": wm.head_previews,
        "Eye": wm.eye_previews,
        "Torso": wm.torso_previews,
        "Accessory": wm.accessory_previews,
        "Leg": wm.leg_previews,
        "Foot": wm.foot_previews,
        "HeadPreset": wm.head_preset,
        "Makeup": wm.makeup_previews,
        "BodyPreset": wm.body_preset,
        "Skin": wm.skin_previews,
    }
    return mapping.get(_preview_key_)

def cmx_set_preview_item(context, _preview_key_, char_item):
    """
    Set preview property in window manager for the given preview key.
    """
    wm = context.window_manager
    if _preview_key_ == "Hair":
        wm.hair_previews = char_item
    elif _preview_key_ == "Head":
        wm.head_previews = char_item
    elif _preview_key_ == "Eye":
        wm.eye_previews = char_item
    elif _preview_key_ == "Torso":
        wm.torso_previews = char_item
    elif _preview_key_ == "Accessory":
        wm.accessory_previews = char_item
    elif _preview_key_ == "Leg":
        wm.leg_previews = char_item
    elif _preview_key_ == "Foot":
        wm.foot_previews = char_item
    elif _preview_key_ == "HeadPreset":
        wm.head_preset = char_item
    elif _preview_key_ == "Makeup":
        wm.makeup_previews = char_item
    elif _preview_key_ == "BodyPreset":
        wm.body_preset = char_item
    elif _preview_key_ == "Skin":
        wm.skin_previews = char_item

def cmx_set_character(self, context):
    """
    Switch to a new character, loading all assets and updating previews.
    """
    wm = context.window_manager
    anim_use_toggle_status = bool(wm.anim_use_toggle)

    if ACTIVE_CHAR["Char_name"] != wm.char_previews:
        char_new = wm.char_previews
        cmx_set_progress_task("Load Char", char_new)
        try:
            ACTIVE_CHAR["Char_name"] = char_new
            if char_new not in ASSET_LIBR_EXIST:
                ASSET_LIBR_EXIST.append(char_new)

            cmx_Remove_character_rig(ACTIVE_CHAR["Char_name"])
            for bp in BODY_PART:
                cmx_unlink_asset("CMX_" + bp)

            # Ensure CHAR_LATEST_ITEM has entry for this character
            for key in CHAR_LATEST_ITEM.keys():
                if ACTIVE_CHAR["Char_name"] not in CHAR_LATEST_ITEM[key]:
                    CHAR_LATEST_ITEM[key][ACTIVE_CHAR["Char_name"]] = None

            for coll in ASSET_PREV_COLL:
                prev_coll = bpy.data.collections.get(coll)
                if prev_coll:
                    prev_coll.hide_viewport = False

            load_errors = cmx_load_character_rig(ACTIVE_CHAR["Char_name"], "CMX_Assets")
            cmx_changes_affecting_cloth(context)

            for _key_ in ["Makeup", "Skin"]:
                item_list = cmx_get_item_list(ACTIVE_CHAR['Char_name'], _key_)
                if item_list:
                    if CHAR_LATEST_ITEM[_key_][ACTIVE_CHAR['Char_name']]:
                        cmx_set_preview_item(context, _key_, CHAR_LATEST_ITEM[_key_][ACTIVE_CHAR['Char_name']])
                    else:
                        full_name_preview = ACTIVE_CHAR['Char_name'] + "_" + item_list[0]
                        cmx_set_preview_item(context, _key_, full_name_preview)

            # Batch-apply shape keys to reduce per-key collection scans
            cmx_set_shape_keys_batch(context, BODY_SHAPE_KEY + FACE_SHAPE_KEY + EMOTION_SHAPE_KEY, "CMX_Body")

            cmx_vis_amature(self, context)
            cmx_vis_proxy(self, context)

            cmx_load_section_preset_items()
            if load_errors:
                cmx_set_progress_error(char_new, load_errors[0])
            else:
                cmx_set_progress_success()
                cmx_set_progress_success_deferred()
        except Exception as e:
            cmx_set_progress_error(char_new, str(e))
            raise

def cmx_set_animation(self, context):
    """
    Set the current animation on the active character.
    """
    act_name = context.window_manager.anim_previews
    applay_status = context.window_manager.anim_use_toggle

    if applay_status:
        cmx_set_progress_task("Load Anim", act_name)
        ACTIVE_CHAR["Action"] = act_name
        cmx_link_action(context, is_applay=False)
        cmx_set_progress_success()
        # print("cmx_link_action by : cmx_set_animation")
        # print("----------------------------------------------------------------------------------------:")

def cmx_set_preview_on_3d_cursor(self, context):
    """
    Set the character asset location to the 3D cursor if the toggle is on.
    """
    wm = context.window_manager
    ch_loc = bpy.data.objects.get("CMX_Assets")
    if wm.preview_on_3d_cursor:
        if ch_loc:
            ch_loc.location = bpy.context.scene.cursor.location

        keymaps_3DV = wm.keyconfigs.active.keymaps['3D View']
        df_km_3dcursor = keymaps_3DV.keymap_items["view3d.cursor3d"]
        CMX_KEYMAP["keymap"] = wm.keyconfigs.addon.keymaps.new(name='3D View', space_type='VIEW_3D')
        CMX_KEYMAP["keymap_input"] = CMX_KEYMAP["keymap"].keymap_items.new(
            "cmx.follow_3dcursor", type=df_km_3dcursor.type, value="RELEASE", shift=df_km_3dcursor.shift
        )
    else:
        if ch_loc:
            ch_loc.location = (0.0, 0.0, 0.0)
        if CMX_KEYMAP:
            CMX_KEYMAP["keymap"].keymap_items.remove(CMX_KEYMAP["keymap_input"])
            wm.keyconfigs.addon.keymaps.remove(CMX_KEYMAP["keymap"])
            CMX_KEYMAP.clear()

def cmx_set_hair(self, context): cmx_set_item_by_key(self, context, "Hair")
def cmx_set_head(self, context): cmx_set_item_by_key(self, context, "Head")
def cmx_set_eye(self, context): cmx_set_item_by_key(self, context, "Eye")
def cmx_set_torso(self, context): cmx_set_item_by_key(self, context, "Torso")
def cmx_set_accessory(self, context): cmx_set_item_by_key(self, context, "Accessory")
def cmx_set_leg(self, context): cmx_set_item_by_key(self, context, "Leg")
def cmx_set_foot(self, context): cmx_set_item_by_key(self, context, "Foot")

def cmx_set_item_by_key(self, context, _body_part_key_):
    """
    Set an item for the given body part, update preview and asset linking.
    """
    Preview = cmx_get_preview_item(context, _body_part_key_)
    cmx_set_progress_task(f"Load {_body_part_key_}", Preview)
    raw_item_name = str(Preview).replace((ACTIVE_CHAR['Char_name'] + "_"), "")
    cmx_unlink_asset("CMX_" + _body_part_key_)
    ACTIVE_CHAR[_body_part_key_] = raw_item_name
    CHAR_LATEST_ITEM[_body_part_key_][ACTIVE_CHAR['Char_name']] = Preview
    ACTIVE_PREV[_body_part_key_] = Preview

    coll_bp_name = "CMX_" + _body_part_key_
    load_error = cmx_link_asset(ACTIVE_CHAR['Char_name'], "__Object__", ACTIVE_CHAR[_body_part_key_], coll_bp_name)
    if load_error:
        cmx_set_progress_error(raw_item_name, load_error)
        return
    cmx_set_color_item_by_key(self, context, _body_part_key_)

    new_obj = None
    target_coll = bpy.data.collections.get(coll_bp_name)
    if target_coll:
        for obj in target_coll.objects:
            if obj.name == raw_item_name:
                new_obj = obj
                break

    if new_obj and new_obj.type == 'MESH' and new_obj.active_material:
        pattern_key = _body_part_key_ + "_Shader"
        current_pattern_index = ACTIVE_CHAR.get(pattern_key)
        if current_pattern_index is not None:
            cmx_shader_selector(current_pattern_index, new_obj.name, coll_bp_name, from_OP=False)
        # else: # If pattern_index is None, do nothing

    if _body_part_key_ in ["Head", "Hair"]:
        cmx_set_shapekey_single_object()
    cmx_set_progress_success(raw_item_name)

def cmx_item_off_by_key(context, _body_part_key_):
    """
    Turn off (unlink) a body part or all body parts.
    """
    wm = context.window_manager
    if _body_part_key_ == "All":
        for body_path_key in PROP_BP_ITEM_OFF.keys():
            if body_path_key not in ["All", "Hair"]:
                if getattr(wm, "item_off_all"):
                    setattr(wm, PROP_BP_ITEM_OFF[body_path_key], True)
                else:
                    setattr(wm, PROP_BP_ITEM_OFF[body_path_key], False)
    else:
        item_off_is_true = cmx_get_item_off_prop(context, _body_part_key_)
        if item_off_is_true:
            cmx_unlink_asset("CMX_" + _body_part_key_)
            ACTIVE_CHAR[_body_part_key_] = None
        else:
            cloth_item_list_not_empty = cmx_get_item_list(ACTIVE_CHAR['Char_name'], _body_part_key_,
                                                          filter=context.window_manager.cloths_filter)
            if cloth_item_list_not_empty:
                cmx_set_preview_item(context, _body_part_key_,
                                    CHAR_LATEST_ITEM[_body_part_key_][ACTIVE_CHAR['Char_name']])

def cmx_set_clothes_filter(self, context):
    """
    Update the clothes filter and refresh visible items if changed.
    """
    cloth_filter = context.window_manager.cloths_filter
    if CMX_PUB_VAR["cloth_filter_latest"] != cloth_filter:
        cmx_changes_affecting_cloth(context)
    CMX_PUB_VAR["cloth_filter_latest"] = cloth_filter
    ACTIVE_CHAR["cloth_filter"] = cloth_filter

def cmx_set_gen_preview_filter(self, context):
    """
    For debugging: Print current gen preview filter.
    """
    pass

def cmx_set_single_char_filter(self, context):
    """Refresh character list and previews when Single-Mesh folder filter changes."""
    from .system_property import cmx_on_mesh_mode_change
    cmx_on_mesh_mode_change(self, context)

def cmx_set_anim_filter(self, context):
    """
    Ensure the animation filter index is valid.
    """
    if CMX_PUB_VAR["is_loading_preset"]:
        return
    
    enum_items = cmx_anim_preview_item(None, context)
    if enum_items:
        context.window_manager.anim_previews = enum_items[0][0]
    else:
        context.window_manager.anim_previews = ""

def cmx_set_face(self, context):
    """
    Set the current makeup item for the active character.
    """
    _item_key_ = "Makeup"
    Preview = cmx_get_preview_item(context, _item_key_)
    cmx_set_progress_task("Load Makeup", Preview)
    item_name = str(Preview).replace((ACTIVE_CHAR['Char_name'] + "_"), "")
    cmx_connect_cf_makeup_node(ACTIVE_CHAR['Char_name'], item_name)
    ACTIVE_CHAR[_item_key_] = item_name
    ACTIVE_PREV[_item_key_] = Preview
    CHAR_LATEST_ITEM[_item_key_][ACTIVE_CHAR['Char_name']] = cmx_get_preview_item(context, _item_key_)
    cmx_set_progress_success()

def cmx_set_skin(self, context):
    """
    Set the current skin item for the active character.
    """
    _item_key_ = "Skin"
    Preview = cmx_get_preview_item(context, _item_key_)
    cmx_set_progress_task("Load Skin", Preview)
    item_name = str(Preview).replace((ACTIVE_CHAR['Char_name'] + "_"), "")
    cmx_connect_cf_skin_node(ACTIVE_CHAR['Char_name'], item_name)
    ACTIVE_CHAR[_item_key_] = item_name
    ACTIVE_PREV[_item_key_] = Preview
    CHAR_LATEST_ITEM[_item_key_][ACTIVE_CHAR['Char_name']] = cmx_get_preview_item(context, _item_key_)
    cmx_set_progress_success()

def cmx_vis_amature(self, context):
    char_coll = bpy.data.collections.get("CMX_Bone")
    if char_coll:
        char_coll.hide_viewport = not context.window_manager.vis_amature_toggle

def cmx_vis_amature_bake(self, context):
    """
    Show or hide armature objects in the active collection depending on the toggle.
    """
    active_coll_in_outline = bpy.context.view_layer.active_layer_collection
    active_coll = bpy.data.collections.get(active_coll_in_outline.name)
    if active_coll:
        for obj in active_coll.all_objects:
            if obj.type == 'ARMATURE':
                obj.hide_viewport = not context.window_manager.vis_amature_toggle_bake

def cmx_vis_proxy(self, context):
    """
    Show or hide proxy/other collections depending on the proxy toggle.
    """
    if context.window_manager.vis_proxy_toggle:
        for coll in ASSET_PREV_COLL:
            char_coll = bpy.data.collections.get(coll)
            if char_coll:
                if coll == "CMX_Proxy":
                    char_coll.hide_viewport = False
                elif coll != "CMX_Bone":
                    char_coll.hide_viewport = True
    else:
        for coll in ASSET_PREV_COLL:
            char_coll = bpy.data.collections.get(coll)
            if char_coll:
                if coll == "CMX_Proxy":
                    char_coll.hide_viewport = True
                elif coll != "CMX_Bone":
                    char_coll.hide_viewport = False

def cmx_rendom_item(self, context, _preview_key_):
    """
    Randomize and select a new item in the preview enum.
    """
    def get_new_random_item(current, items):
        if len(items) <= 1:
            return items[0][0]
        choices = [i[0] for i in items if i[0] != current]
        return random.choice(choices) if choices else current

    wm = context.window_manager

    if _preview_key_ in BODY_PART:
        item_list = CHAR_ITEM_SET[_preview_key_][ACTIVE_CHAR["Char_name"]]
        if item_list:
            current_val = getattr(wm, f"{_preview_key_.lower()}_previews", None)
            new_val = get_new_random_item(current_val, item_list)
            setattr(wm, f"{_preview_key_.lower()}_previews", new_val)
    elif _preview_key_ == "All_BODY_PART":
        for bp in BODY_PART:
            if bp != "Hair":
                item_list = CHAR_ITEM_SET[bp][ACTIVE_CHAR["Char_name"]]
                if item_list:
                    current_val = getattr(wm, f"{bp.lower()}_previews", None)
                    new_val = get_new_random_item(current_val, item_list)
                    setattr(wm, f"{bp.lower()}_previews", new_val)
    else:
        item_list = PREVIEW_ENUM_ITEMS[_preview_key_]
        if item_list:
            current_val = getattr(wm, _preview_key_, None)
            new_val = get_new_random_item(current_val, item_list)
            setattr(wm, _preview_key_, new_val)
    return {'FINISHED'}

def cmx_shader_selector(index, object_name, coll_name, from_OP=False):
    obj = cmx_get_object_in_collection(object_name, coll_name)
    if not obj:
        return {'CANCELLED'}
    mat = obj.active_material
    if not mat:
        return {'CANCELLED'}
    if "Pattern_Index" not in mat:
        return {'CANCELLED'}

    if mat.override_library:
        mat["Pattern_Index"] = index
    else:
        mat["Pattern_Index"] = index

    try:
        mat.id_properties_ui("Pattern_Index").update()
    except Exception:
        pass

    mat.update_tag()
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            area.tag_redraw()
            
    if from_OP:
        key = str(coll_name).replace("CMX_", "") + "_Shader"
        ACTIVE_CHAR[key] = index

def cmx_set_defualt_shader():
    """
    Save Pattern_Index from each material in collections to ACTIVE_CHAR dict.
    """
    for collection_name in { "CMX_Hair", "CMX_Head", "CMX_Eye", "CMX_Torso", "CMX_Accessory", "CMX_Leg", "CMX_Foot" }:
        collection = bpy.data.collections.get(collection_name)
        if not collection:
            continue
        for obj in collection.objects:
            if not obj or not obj.active_material:
                continue
            material = obj.active_material
            key = collection_name.replace("CMX_", "") + "_Shader"
            if "Pattern_Index" in material:
                index = int(material["Pattern_Index"])
                ACTIVE_CHAR[key] = index
                try:
                    prop_ui = material.id_properties_ui("Pattern_Index")
                    prop_ui.update(min=0, max=prop_ui.as_dict().get("max", index))
                except Exception:
                    pass
            else:
                ACTIVE_CHAR[key] = None

def cmx_connect_cf_skin_node(char_name, cf_skin_name, collection_name="CMX_Body"):
    """
    Set Skin_Index for character mesh material by skin name.
    """
    json_path = cmx_get_character_json_path(char_name)
    if not json_path or not os.path.exists(json_path):
        return
    try:
        with open(json_path, 'r', encoding='utf-8-sig') as f:
            data = json.load(f)
            skin_names = data.get("Skin", [])
    except Exception:
        return
    if not skin_names or cf_skin_name not in skin_names:
        return
    index = skin_names.index(cf_skin_name)
    collection = bpy.data.collections.get(collection_name)
    if not collection:
        return
    for obj in collection.objects:
        if not obj or obj.type != 'MESH':
            continue
        material = obj.active_material
        if not material:
            continue
        material["Skin_Index"] = index
        try:
            material.id_properties_ui("Skin_Index").update(min=0, max=len(skin_names)-1)
        except:
            pass
        material.update_tag()

def cmx_connect_cf_makeup_node(char_name, cf_makeup_name, collection_name="CMX_Body"):
    """
    Set Face_Index for character mesh material by makeup name.
    """
    json_path = cmx_get_character_json_path(char_name)
    if not json_path or not os.path.exists(json_path):
        return
    try:
        with open(json_path, 'r', encoding='utf-8-sig') as f:
            data = json.load(f)
            skin_names = data.get("Makeup", [])
    except Exception:
        return
    if not skin_names or cf_makeup_name not in skin_names:
        return
    index = skin_names.index(cf_makeup_name)
    collection = bpy.data.collections.get(collection_name)
    if not collection:
        return
    for obj in collection.objects:
        if not obj or obj.type != 'MESH':
            continue
        material = obj.active_material
        if not material:
            continue
        material["Face_Index"] = index
        try:
            material.id_properties_ui("Face_Index").update(min=0, max=len(skin_names)-1)
        except:
            pass
        material.update_tag()

def cmx_changes_affecting_cloth(context): 
    """
    Update preview item and asset data when cloth filter changes.
    """
    cloth_filter = bpy.context.window_manager.cloths_filter
    ACTIVE_CHAR["cloth_filter"] = cloth_filter
    for bp in BODY_PART:
        cloth_item_list_filter = cmx_get_item_list(ACTIVE_CHAR['Char_name'], bp, filter=cloth_filter)
        raw_item_name = str(CHAR_LATEST_ITEM[bp][ACTIVE_CHAR['Char_name']]).replace((ACTIVE_CHAR['Char_name'] + "_"), "")
        if not cmx_get_item_off_prop(context, bp):
            if cloth_item_list_filter:
                if raw_item_name in cloth_item_list_filter:
                    cmx_set_preview_item(context, bp, CHAR_LATEST_ITEM[bp][ACTIVE_CHAR['Char_name']])
                else:
                    cl_full_name_preview = ACTIVE_CHAR['Char_name'] + "_" + cloth_item_list_filter[0]
                    cmx_set_preview_item(context, bp, cl_full_name_preview)
            else:
                cmx_unlink_asset("CMX_" + bp)
                ACTIVE_CHAR[bp] = None
        elif cloth_item_list_filter:
            ACTIVE_CHAR[bp] = None
            if raw_item_name not in cloth_item_list_filter:
                CHAR_LATEST_ITEM[bp][ACTIVE_CHAR['Char_name']] = ACTIVE_CHAR['Char_name'] + "_" + cloth_item_list_filter[0]

def cmx_force_override_property(obj, prop_name, value):
    """
    Force Blender to create override entry for custom property.
    """
    if not hasattr(obj, "override_library") or obj.override_library is None:
        obj[prop_name] = value
        return
    orig = obj.override_library.reference
    orig_value = orig.get(prop_name) if orig else None
    if orig_value == value:
        if isinstance(value, (int, float)):
            temp = value + 1 if value < 1e6 else value - 1
        elif isinstance(value, (list, tuple)) and len(value) > 0:
            temp = list(value)
            temp[0] = value[0] + 0.01 if isinstance(value[0], (int, float)) else value[0]
        else:
            temp = None
        if temp is not None:
            obj[prop_name] = temp
    obj[prop_name] = value

def cmx_get_previews_enum_items(previews_name):
    """
    Get enum preview items by name.
    """
    if previews_name == "anim_previews":
        return PREVIEW_COLL["Anim"].anim_previews
    else:
        return PREVIEW_ENUM_ITEMS[previews_name]

def cmx_set_shapekey_single_object():
    """
    Set one shape key value to 1 and others to 0 based on hair object name in head collection.
    """
    head_collection = bpy.data.collections.get("CMX_Head")
    hair_collection = bpy.data.collections.get("CMX_Hair")
    if not head_collection or not hair_collection:
        return
    head_obj = head_collection.objects[0] if head_collection.objects else None
    hair_obj = hair_collection.objects[0] if hair_collection.objects else None
    if not head_obj or not hair_obj:
        return
    if not head_obj.data.shape_keys:
        return
    for key_block in head_obj.data.shape_keys.key_blocks:
        key_block.value = 0
    hair_name = hair_obj.name
    if hair_name in head_obj.data.shape_keys.key_blocks:
        head_obj.data.shape_keys.key_blocks[hair_name].value = 1

def cmx_load_section_preset_items():
    """
    Load/refresh icon preview collections for all preset sections.
    """
    char_name = ACTIVE_CHAR.get('Char_name')
    if char_name:
        preset_section = [["BodyPreset", "Body"], ["HeadPreset", "Head"], ["CrowdPreset", "Crowd"]]
    else:
        preset_section = [["CrowdPreset", "Crowd"]]
    for preset_key, preset_path in preset_section:
        if preset_key != "CrowdPreset":
            preset_key_by_char = f"{preset_key}_{char_name}"
            if preset_key_by_char in PREVIEW_COLL:
                bpy.utils.previews.remove(PREVIEW_COLL[f"{preset_key}_{char_name}"])
        elif preset_key in PREVIEW_COLL:
            bpy.utils.previews.remove(PREVIEW_COLL[preset_key])
        icon_preview_collection = bpy.utils.previews.new()
        if preset_key != "CrowdPreset":
            PREVIEW_COLL[f"{preset_key}_{char_name}"] = icon_preview_collection
        else:
            PREVIEW_COLL[preset_key] = icon_preview_collection
        if preset_key in ["BodyPreset", "HeadPreset"]:
            char_folder = os.path.join(CURRENT_DIRECTORY, "CMX_Preset", preset_path, char_name)
        else:
            char_folder = os.path.join(CURRENT_DIRECTORY, "CMX_Preset", preset_path)
        if not os.path.exists(char_folder):
            os.makedirs(char_folder, exist_ok=True)
        json_file_path = os.path.join(char_folder, "items_data.json")
        if not os.path.exists(json_file_path):
            with open(json_file_path, 'w') as f:
                json.dump({'items': []}, f, indent=4, sort_keys=True)
        if os.path.exists(json_file_path):
            with open(json_file_path, 'r') as f:
                data = json.load(f)
            for item in data['items']:
                icon_path = os.path.join(char_folder, item['image_path'])
                if os.path.exists(icon_path):
                    thumbnail = icon_preview_collection.load(item['name'], icon_path, 'IMAGE')
                    icon_preview_collection[item['name']] = thumbnail

class CMXSetPatternIndexOperator(bpy.types.Operator):
    """Set Pattern Index on a specified object in a collection."""
    bl_idname = "cmx.set_pattern_index"
    bl_label = "Set Pattern Index"

    index: IntProperty() # type: ignore
    object_name: StringProperty() # type: ignore
    coll_name: StringProperty() # type: ignore

    def execute(self, context):
        cmx_shader_selector(self.index, self.object_name, self.coll_name, from_OP=True)
        context.view_layer.update()
        return {'FINISHED'}

class CMXFollow3dCursorOperator(Operator):
    """Move CMX_Assets to 3D cursor position."""
    bl_idname = "cmx.follow_3dcursor"
    bl_label = "follow 3Dcursor"

    def execute(self, context):
        ch_loc = bpy.data.objects.get("CMX_Assets")
        if ch_loc:
            ch_loc.location = bpy.context.scene.cursor.location
        return {"FINISHED"}

class CMXRandomItemOperator(Operator):
    """Randomize item selection for a preview key."""
    bl_idname = "cmx.random_item"
    bl_label = "random item"

    preview_key: StringProperty(default="") # type: ignore

    def execute(self, context):
        _preview_key_ = self.preview_key
        cmx_rendom_item(self, context, _preview_key_)
        return {'FINISHED'}

class CMXNextItemOperator(Operator):
    """Cycles to the next item in the specified EnumProperty, wrapping around."""
    bl_idname = "cmx.next_item"
    bl_label = "Next Item"

    icon_view_name: StringProperty(default="") # type: ignore

    def execute(self, context):
        active_preview_name = getattr(context.window_manager, self.icon_view_name)
        enum_items = cmx_get_previews_enum_items(self.icon_view_name)
        if not enum_items:
            self.report({'INFO'}, "No items to cycle through.")
            return {'CANCELLED'}
        identifiers = [item[0] for item in enum_items]
        num_items = len(identifiers)
        try:
            current_index = identifiers.index(active_preview_name)
        except ValueError:
            current_index = 0
        next_index = (current_index + 1) % num_items
        next_preview_name = identifiers[next_index]
        setattr(context.window_manager, self.icon_view_name, next_preview_name)
        return {'FINISHED'}

class CMXPreviousItemOperator(Operator):
    """Cycles to the previous item in the specified EnumProperty, wrapping around."""
    bl_idname = "cmx.previous_item"
    bl_label = "Previous Item"

    icon_view_name: StringProperty(default="") # type: ignore

    def execute(self, context):
        active_preview_name = getattr(context.window_manager, self.icon_view_name)
        enum_items = cmx_get_previews_enum_items(self.icon_view_name)
        if not enum_items:
            self.report({'INFO'}, "No items to cycle through.")
            return {'CANCELLED'}
        identifiers = [item[0] for item in enum_items]
        num_items = len(identifiers)
        try:
            current_index = identifiers.index(active_preview_name)
        except ValueError:
            current_index = 0
        previous_index = (current_index - 1 + num_items) % num_items
        previous_preview_name = identifiers[previous_index]
        setattr(context.window_manager, self.icon_view_name, previous_preview_name)
        return {'FINISHED'}

classes = [
    CMXRandomItemOperator,
    CMXFollow3dCursorOperator,
    CMXNextItemOperator,
    CMXPreviousItemOperator,
    CMXSetPatternIndexOperator
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
