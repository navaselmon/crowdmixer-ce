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

from .system_icon import *
from .OP_common import *
from .system_var import *
import json
import os

def _cmx_get_animation_preview_path(anim_directory, anim_name):
    """Return a preview image path matching the animation file name, if present."""
    if not anim_directory or not anim_name or not os.path.isdir(anim_directory):
        return None

    for ext in (".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"):
        candidate = os.path.join(anim_directory, anim_name + ext)
        if os.path.exists(candidate):
            return candidate

    target_lower = anim_name.lower()
    for file_name in os.listdir(anim_directory):
        stem, ext = os.path.splitext(file_name)
        if stem.lower() != target_lower:
            continue
        if ext.lower() in {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}:
            return os.path.join(anim_directory, file_name)
    return None

def cmx_gen_panel_list(self, context):
    """Generate the list of main addon panels for the UI."""
    items = []

    for item_id, item_name, item_icon_key in CMX_PANEL_TAB:
        if item_name == "Creator Tools":
            continue
        items.append((item_name, item_name, "", get_cf_icon(item_icon_key), item_id))
    return items

def cmx_gen_customize_tab_list(self, context):
    """Generate the enum list for the customize tab."""
    enum_items = []
    for i, panel_name, icon in CMX_CUSTOMIZE_TAB:
        enum_items.append((panel_name, panel_name, "", get_cf_icon(icon), i))
    return enum_items

def cmx_gen_subpanel_head_list(self, context):
    """Generate the enum list for subpanel head."""
    enum_items = []
    for i, subpanel_name, text, icon in CMX_SUBPANEL_TAB_HEAD:
        enum_items.append((subpanel_name, subpanel_name, text, get_cf_icon(icon), i))
    return enum_items

def cmx_clothes_filter_list(self, context):
    """Generate the enum list for clothes filter."""
    enum_items = []
    for i, filter_name in enumerate(CLOTHES_FILTER):
        enum_items.append((filter_name, filter_name, "", 'MOD_CLOTH', i))
    return enum_items

def cmx_anim_filter_list(self, context):
    """Generate the enum list for animation filter."""
    enum_items = []
    for i, filter_name in enumerate(ANIMATION_FILTER):
        enum_items.append((filter_name, filter_name, "", 'ARMATURE_DATA', i))
    return enum_items

def cmx_single_char_filter_list(self, context):
    """Generate enum list for Single-Mesh character folder filter."""
    enum_items = [("All", "All", "Show all characters", 'FILE_FOLDER', 0)]
    if context is None:
        return enum_items
    base_dir = cmx_get_asset_dir_by_mode()
    if not base_dir:
        return enum_items

    for i, folder_name in enumerate(cmx_get_single_mesh_filter_dirs(base_dir), start=1):
        enum_items.append((folder_name, folder_name, f"Show characters in {folder_name}", 'FILE_FOLDER', i))
    return enum_items

def cmx_get_item_list(char_name, _item_key_, filter=None):
    """Get a list of character items from the asset JSON."""
    item_dir = cmx_get_character_json_path(char_name)
    if not item_dir:
        return

    CHAR_ITEM_LIST = {}
    try:
        with open(item_dir, "r", encoding="utf-8-sig") as json_file:
            CHAR_ITEM_LIST = json.load(json_file)
    except:
        return

    if _item_key_ in NO_FILTER_ITEM:
        if _item_key_ in CHAR_ITEM_LIST.keys():
            return CHAR_ITEM_LIST[_item_key_]
        else:
            return None

    elif filter == "All":
        CHAR_ALL_ITEM_LIST = []
        for clt_filter in CLOTHES_FILTER:
            if clt_filter != "All":
                filter_index = _item_key_ + "_" + clt_filter
                assets = CHAR_ITEM_LIST[_item_key_][filter_index]
                if assets:
                    for item in assets:
                        CHAR_ALL_ITEM_LIST.append(item)
        return CHAR_ALL_ITEM_LIST
    else:
        filter_index = _item_key_ + "_" + filter
        return CHAR_ITEM_LIST[_item_key_][filter_index]

def cmx_gen_preview_filter_list(self, context):
    """Generate the enum list for preview filter by body part."""
    enum_items = []
    for i, filter_name in enumerate(BODY_PART):
        enum_items.append((filter_name, filter_name, "", 'FILE_3D', i))
    return enum_items

def _cmx_get_current_preset_collection_names():
    """Return preset collection names from the current char preset file, preserving JSON order."""
    file_path = os.path.join(CURRENT_DIRECTORY, "CMX_Data", "char_preset.json")
    if not os.path.exists(file_path):
        return []

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)
    except Exception:
        return []

    if not isinstance(data, dict):
        return []
    return list(data.keys())

def cmx_source_blend_items(self, context):
    """
    Build source enum items from the current preset collection list.
    Only .blend files that still match current preset collections are shown.
    """
    enum_items = []
    source_dir = cmx_get_source_dir(create_if_missing=False)
    if not source_dir or not os.path.isdir(source_dir):
        return enum_items

    preset_collections = _cmx_get_current_preset_collection_names()
    blend_paths_by_name = {}
    for fn in os.listdir(source_dir):
        if not fn.lower().endswith(".blend"):
            continue
        name = os.path.splitext(fn)[0]
        blend_paths_by_name[name] = os.path.join(source_dir, fn)

    source_names = [name for name in preset_collections if name in blend_paths_by_name]
    if not preset_collections:
        source_names = sorted(blend_paths_by_name)

    for idx, name in enumerate(source_names):
        full_path = blend_paths_by_name[name]
        enum_items.append((name, name, full_path, get_cf_icon("main_panel_crowd_source"), idx))
    return enum_items

def cmx_char_preview_item(self, context):
    """Generate character preview enum items for UI thumbnails."""
    enum_items = []
    if not context.window_manager.cf_on_off_toggle:
        return enum_items

    directory = cmx_get_asset_dir_by_mode()
    if not directory:
        return enum_items
    cache_key = f"{directory}::{getattr(context.window_manager, 'single_char_filter', 'All')}"
    default_char_preview_path = os.path.join(CURRENT_DIRECTORY, "CMX_Icons", "CMX_Char_Default.png")
    char_pcoll = PREVIEW_COLL["Char"]
    # Use cache if directory unchanged and cache is available
    if cache_key == char_pcoll.char_previews_dir and char_pcoll.char_previews:
        return char_pcoll.char_previews

    if directory and os.path.exists(directory):
        try:
            for i, char_name in enumerate(CHAR_LIST):
                preview_path = cmx_get_character_png_path(char_name)
                if preview_path and os.path.exists(preview_path):
                    if char_name in char_pcoll:
                        thumb = char_pcoll[char_name]
                    else:
                        thumb = char_pcoll.load(char_name, preview_path, 'IMAGE')
                    enum_items.append((char_name, char_name, "", thumb.icon_id, i))
                else:
                    if char_name in char_pcoll:
                        thumb = char_pcoll[char_name]
                    else:
                        thumb = char_pcoll.load(char_name, default_char_preview_path, 'IMAGE')
                    enum_items.append((char_name, char_name, "Char", thumb.icon_id, i))
        except:
            return char_pcoll.char_previews

    # Fallback: if no previews built but CHAR_LIST has entries, create default entries
    if not enum_items and CHAR_LIST:
        for i, char_name in enumerate(CHAR_LIST):
            thumb = char_pcoll.load(char_name, default_char_preview_path, 'IMAGE')
            enum_items.append((char_name, char_name, "Char", thumb.icon_id, i))

    char_pcoll.char_previews = enum_items
    char_pcoll.char_previews_dir = cache_key
    return char_pcoll.char_previews

def cmx_anim_preview_item(self, context):
    """Generate animation preview enum items for UI thumbnails."""
    enum_items = []
    if not context.window_manager.cf_on_off_toggle:
        return enum_items

    anim_pcoll = PREVIEW_COLL["Anim"]
    aim_filter = context.window_manager.anim_filter
    if not aim_filter and ANIMATION_FILTER:
        aim_filter = ANIMATION_FILTER[0]
        context.window_manager.anim_filter = aim_filter

    if aim_filter in ANIM_PREV_EXIST:
        anim_pcoll.anim_previews = ANIM_SET[aim_filter]
        return ANIM_SET[aim_filter]
    else:
        # Animation folder is at base asset path (not split by mesh mode)
        asset_directory = cmx_get_dir_asset_path()
        if not asset_directory:
            return enum_items
        directory = os.path.join(asset_directory, "Animation")

        if directory and os.path.exists(directory):
            anim_preview_exist = []
            for anim_flt in ANIMATION_FILTER:
                sub_directory = os.path.join(directory, anim_flt)
                ANIM_SET[anim_flt] = []
                for FN in os.listdir(sub_directory):
                    if FN.lower().endswith(".blend"):
                        get_an_nm = FN.replace(".blend", "")
                        anim_preview_exist.append(get_an_nm)
                try:
                    for i, anim_name in enumerate(anim_preview_exist):
                        full_anim_name = anim_flt + "." + anim_name
                        preview_path = _cmx_get_animation_preview_path(sub_directory, anim_name)
                        if preview_path:
                            if full_anim_name in anim_pcoll:
                                thumb = anim_pcoll[full_anim_name]
                            else:
                                thumb = anim_pcoll.load(full_anim_name, preview_path, 'IMAGE')
                            icon_id = thumb.icon_id
                        else:
                            icon_id = get_cf_icon_image("Default_Anim")
                        ANIM_SET[anim_flt].append((full_anim_name, anim_name, "Char", icon_id, i))
                except:
                    return anim_pcoll.anim_previews
                anim_preview_exist.clear()
            enum_items = ANIM_SET[aim_filter]

            anim_pcoll.anim_previews = enum_items
            anim_pcoll.anim_filter = aim_filter
            ANIM_PREV_EXIST.append(aim_filter)        
        
        return enum_items

def cmx_hair_previews_item(self, context):
    """Generate hair preview enum items."""
    bp_off = context.window_manager.item_off_hair
    enum_items = cmx_previews_item_by_key(self, context, "Hair", bp_off)
    PREVIEW_ENUM_ITEMS["hair_previews"] = enum_items
    return enum_items

def cmx_head_previews_item(self, context):
    """Generate head preview enum items."""
    bp_off = context.window_manager.item_off_head
    enum_items = cmx_previews_item_by_key(self, context, "Head", bp_off)
    PREVIEW_ENUM_ITEMS["head_previews"] = enum_items
    return enum_items

def cmx_eye_previews_item(self, context):
    """Generate eye preview enum items."""
    bp_off = context.window_manager.item_off_eye
    enum_items = cmx_previews_item_by_key(self, context, "Eye", bp_off)
    PREVIEW_ENUM_ITEMS["eye_previews"] = enum_items
    return enum_items

def cmx_torso_previews_item(self, context):
    """Generate torso preview enum items."""
    bp_off = context.window_manager.item_off_torso
    enum_items = cmx_previews_item_by_key(self, context, "Torso", bp_off)
    PREVIEW_ENUM_ITEMS["torso_previews"] = enum_items
    return enum_items

def cmx_accessory_previews_item(self, context):
    """Generate accessory preview enum items."""
    bp_off = context.window_manager.item_off_Accessory
    enum_items = cmx_previews_item_by_key(self, context, "Accessory", bp_off)
    PREVIEW_ENUM_ITEMS["accessory_previews"] = enum_items
    return enum_items

def cmx_leg_previews_item(self, context):
    """Generate leg preview enum items."""
    bp_off = context.window_manager.item_off_leg
    enum_items = cmx_previews_item_by_key(self, context, "Leg", bp_off)
    PREVIEW_ENUM_ITEMS["leg_previews"] = enum_items
    return enum_items

def cmx_foot_previews_item(self, context):
    """Generate foot preview enum items."""
    bp_off = context.window_manager.item_off_foot
    enum_items = cmx_previews_item_by_key(self, context, "Foot", bp_off)
    PREVIEW_ENUM_ITEMS["foot_previews"] = enum_items
    return enum_items

def cmx_makeup_previews_item(self, context):
    """Generate makeup preview enum items."""
    bp_off = False
    enum_items = cmx_previews_item_by_key(self, context, "Makeup", bp_off)
    PREVIEW_ENUM_ITEMS["makeup_previews"] = enum_items
    return enum_items

def cmx_skin_previews_item(self, context):
    """Generate skin preview enum items."""
    bp_off = False
    enum_items = cmx_previews_item_by_key(self, context, "Skin", bp_off)
    PREVIEW_ENUM_ITEMS["skin_previews"] = enum_items
    return enum_items

def cmx_previews_item_by_key(self, context, _item_key_, bp_off):
    """Generate preview enum items for the specified body part."""
    enum_items = []
    enum_items_filter = []

    if not context.window_manager.cf_on_off_toggle or bp_off:
        CHAR_ITEM_SET[_item_key_][ACTIVE_CHAR["Char_name"]] = enum_items
        return enum_items

    base_dir = cmx_get_asset_dir_by_mode()
    if not base_dir:
        CHAR_ITEM_SET[_item_key_][ACTIVE_CHAR["Char_name"]] = enum_items
        return enum_items
    if not base_dir:
        CHAR_ITEM_SET[_item_key_][ACTIVE_CHAR["Char_name"]] = enum_items
        return enum_items
    char_name = ACTIVE_CHAR.get("Char_name")
    if not char_name:
        CHAR_ITEM_SET[_item_key_][ACTIVE_CHAR["Char_name"]] = enum_items
        return enum_items
    directory = os.path.join(base_dir, char_name, _item_key_)
    cl_filter = context.window_manager.cloths_filter
    pcoll = PREVIEW_COLL[_item_key_]

    if ACTIVE_CHAR["Char_name"] in CHAR_ITEM_EXIST[_item_key_]:
        if cl_filter == "All":
            CHAR_ITEM_SET[_item_key_][ACTIVE_CHAR["Char_name"]] = CHAR_ITEM_SET[_item_key_]["All"][ACTIVE_CHAR["Char_name"]]
            return CHAR_ITEM_SET[_item_key_][ACTIVE_CHAR["Char_name"]]
        else:
            Item_List_Filter = cmx_get_item_list(ACTIVE_CHAR["Char_name"], _item_key_, filter=cl_filter)
            for item in CHAR_ITEM_SET[_item_key_]["All"][ACTIVE_CHAR["Char_name"]]:
                if item[1] in Item_List_Filter:
                    enum_items_filter.append(item)
            CHAR_ITEM_SET[_item_key_][ACTIVE_CHAR["Char_name"]] = enum_items_filter
            return CHAR_ITEM_SET[_item_key_][ACTIVE_CHAR["Char_name"]]

    Item_List = cmx_get_item_list(ACTIVE_CHAR["Char_name"], _item_key_, filter="All")
    if not Item_List:
        CHAR_ITEM_SET[_item_key_][ACTIVE_CHAR["Char_name"]] = enum_items
        return enum_items

    if directory and os.path.exists(directory):
        image_paths = {}
        preview_exist = []
        for FN in os.listdir(directory):
            if FN.lower().endswith(".png"):
                get_item_nm = FN.replace(".png", "")
                if get_item_nm in Item_List:
                    image_paths[get_item_nm] = FN
                    preview_exist.append(get_item_nm)
        try:
            for i, item_name in enumerate(Item_List):
                full_item_name = ACTIVE_CHAR["Char_name"] + "_" + item_name
                if item_name in preview_exist:
                    filepath = os.path.join(directory, image_paths[item_name])
                    thumb = pcoll.load(full_item_name, filepath, 'IMAGE')
                    enum_items.append((full_item_name, item_name, "", thumb.icon_id, i))
                else:
                    enum_items.append((full_item_name, item_name, "", get_cf_icon("Not_Available"), i))
        except:
            return enum_items
    else:
        for i, item_name in enumerate(Item_List):
            full_item_name = ACTIVE_CHAR["Char_name"] + "_" + item_name
            enum_items.append((full_item_name, item_name, "", get_cf_icon("Not_Available"), i))

    CHAR_ITEM_EXIST[_item_key_].append(ACTIVE_CHAR["Char_name"])
    CHAR_ITEM_SET[_item_key_]["All"][ACTIVE_CHAR["Char_name"]] = enum_items
    CHAR_ITEM_SET[_item_key_][ACTIVE_CHAR["Char_name"]] = enum_items
    return enum_items

def cmx_headpreset_preview_item(self, context):
    """Generate head preset preview enum items."""
    items = []
    char_name = ACTIVE_CHAR.get('Char_name')
    preset_by_char = f"HeadPreset_{char_name}"
    if not bpy.context.window_manager.cf_on_off_toggle or preset_by_char not in PREVIEW_COLL:
        return items
    for item_name, preview in PREVIEW_COLL[preset_by_char].items():
        items.append((item_name, item_name, "", preview.icon_id, len(items)))
    return items

def cmx_bodypreset_preview_item(self, context):
    """Generate body preset preview enum items."""
    items = []
    char_name = ACTIVE_CHAR.get('Char_name')
    preset_by_char = f"BodyPreset_{char_name}"
    if not bpy.context.window_manager.cf_on_off_toggle or preset_by_char not in PREVIEW_COLL:
        return items
    for item_name, preview in PREVIEW_COLL[preset_by_char].items():
        items.append((item_name, item_name, "", preview.icon_id, len(items)))
    return items

def cmx_crowdpreset_preview_item(self, context):
    """Generate crowd preset preview enum items."""
    items = []
    for item_name, preview in PREVIEW_COLL["CrowdPreset"].items():
        items.append((item_name, item_name, "", preview.icon_id, len(items)))
    return items

