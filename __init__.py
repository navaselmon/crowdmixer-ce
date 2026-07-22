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
import os

from bpy.props import StringProperty, BoolProperty, IntProperty
from bpy.types import Panel, WindowManager, AddonPreferences

from .system_icon import *
from .system_var import *
from .system_property import *
from .OP_common import *
from .OP_preview import *
from .OP_update_prop import cmx_set_shape_keys_batch
from .OP_creator import *
from .OP_link_asset import cmx_get_assets_scene
from .OP_animation import *
from .enum_item_gen import *
from .OP_char_preset import *
from .OP_section_preset import *
from .OP_Spawn import *
from .Panel_Character_Customize import *
from .Panel_Character_Collection import *
from .Panel_Creator_Tool import *
from .Panel_Crowd_Tool import *

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

def _cmx_on_asset_path_changed(self, context):
    """Force the UI to refresh after the asset path picker closes."""
    try:
        asset_dir = cmx_get_asset_dir_by_mode()
        CMX_PUB_VAR["Off_Exist_Path"] = bool(asset_dir and cmx_check_asset_path(asset_dir))
    except Exception:
        CMX_PUB_VAR["Off_Exist_Path"] = False

    _cmx_tag_redraw_all()
    cmx_request_ui_redraw(swap=True)
    cmx_request_ui_redraw(delay=0.05, swap=True)

def _cmx_revert_customize_toggle(wm):
    """Rollback Customize ON without running normal TURN OFF cleanup."""
    CMX_PUB_VAR["customize_turn_on_pending"] = False
    CMX_PUB_VAR["customize_turn_on_loading"] = False
    CMX_PUB_VAR["customize_toggle_internal_change"] = True
    wm.cf_on_off_toggle = False
    _cmx_tag_redraw_all()

def _cmx_preflight_customize_turn_on(context):
    """Validate the current asset path before async loading begins."""
    char_dir = cmx_get_asset_dir_by_mode()
    if cmx_check_asset_path(char_dir):
        CMX_PUB_VAR["Off_Exist_Path"] = True
        return True

    CMX_PUB_VAR["Off_Exist_Path"] = False
    cmx_show_message_box_deferred(
        message="The specified asset could not be found. Please ensure the asset path is correct.",
        title="Warning",
        icon='ERROR',
    )
    return False

def _cmx_customize_turn_on_impl(context):
    """Load customize data after the ON toggle has already been drawn."""
    wm = context.window_manager
    if wm.cf_mesh_mode != "SINGLE":
        wm.cf_mesh_mode = "SINGLE"
    saved_settings = cmx_load_setting_data()
    saved_snapshot = cmx_get_saved_mode_settings(wm.cf_mesh_mode, saved_settings)
    saved_animation = cmx_get_saved_animation_settings(saved_settings)

    saved_filter = saved_snapshot.get("single_char_filter", "All")
    try:
        wm["single_char_filter"] = saved_filter
    except Exception:
        try:
            wm.single_char_filter = saved_filter
        except Exception:
            pass

    char_dir = cmx_get_asset_dir_by_mode()
    anim_dir = os.path.join(cmx_get_dir_asset_path(), "Animation")
    if not cmx_check_asset_path(char_dir):
        cmx_show_message_box(message="The specified asset could not be found. Please ensure the asset path is correct.",title="Warning", icon='ERROR')
        CMX_PUB_VAR["Off_Exist_Path"] = False
        return False
    else:
        CMX_PUB_VAR["Off_Exist_Path"] = True

    cmx_set_progress_info("Starting Customizer...")
    cmx_create_asset_collection()

    CMX_PUB_VAR["cloth_filter_latest"] = "All"
    wm.cloths_filter = "All"

    if char_dir and os.path.exists(char_dir):
        cmx_refresh_character_maps_and_list(context)
    else:
        cmx_show_message_box(message="Character folder not found for current mode.", title="Warning", icon='ERROR')
        return False

    if anim_dir and os.path.exists(anim_dir):
        ANIMATION_FILTER.clear()
        for path, list_anim_filter, list_file in os.walk(anim_dir):
            for anim_filter in list_anim_filter:
                ANIMATION_FILTER.append(anim_filter)
                ANIM_SELECT_LIST[anim_filter] = []
                sub_directory = os.path.join(anim_dir, anim_filter)
                for FN in os.listdir(sub_directory):
                    if FN.lower().endswith(".blend"):
                        get_an_nm = FN.replace(".blend", "")
                        ANIM_SELECT_LIST[anim_filter].append(get_an_nm)
            break

    cmx_restore_active_char_state(saved_snapshot, wm.cf_mesh_mode)

    if CHAR_LIST:
        if ACTIVE_CHAR["Char_name"] not in CHAR_LIST:
            ACTIVE_CHAR["Char_name"] = CHAR_LIST[0]
        # Reset preview cache and rebuild enum items for the new path
        char_pcoll = PREVIEW_COLL.get("Char")
        if char_pcoll:
            try:
                char_pcoll.clear()
            except Exception:
                pass
            CHAR_PREV_SET.clear()
            char_pcoll.char_previews_dir = ""
            char_pcoll.char_previews = ()
        items = cmx_char_preview_item(None, bpy.context)
        if items:
            wm.char_previews = items[0][0]
            if ACTIVE_CHAR["Char_name"] not in [it[0] for it in items]:
                ACTIVE_CHAR["Char_name"] = items[0][0]
    else:
        cmx_show_message_box(message="No characters found in current mode folder.", title="Warning", icon='ERROR')
        return False

    for ch in CHAR_LIST:
        for prev in PREVIEW_LIST:
            CHAR_LATEST_ITEM[prev][ch] = None

    cmx_load_section_preset_items()

    load_errors = cmx_load_character_rig(ACTIVE_CHAR["Char_name"], "CMX_Assets")
    if load_errors:
        cmx_set_progress_error(ACTIVE_CHAR["Char_name"], load_errors[0])
        return False

    cmx_changes_affecting_cloth(context)
    cmx_set_face(None, context)
    cmx_set_skin(None, context)
    # Batch set all shape keys to minimize repeated scans/updates
    cmx_set_shape_keys_batch(context, FACE_SHAPE_KEY + BODY_SHAPE_KEY + EMOTION_SHAPE_KEY, "CMX_Body")

    cmx_set_defualt_shader()

    if cmx_has_saved_mode_settings(saved_snapshot):
        CMX_PUB_VAR["is_loading_preset"] = True
        try:
            cmx_set_char_to_preset(context, saved_snapshot)
        finally:
            CMX_PUB_VAR["is_loading_preset"] = False

    cmx_restore_animation_settings(context, saved_animation)

    wm.vis_amature_toggle = False
    wm.vis_proxy_toggle = False
    cmx_set_progress_success()
    cmx_set_progress_success_deferred()

    # Ensure char_previews matches a valid enum item for this mode
    items = cmx_char_preview_item(None, bpy.context)
    if items:
        ids = [it[0] for it in items]
        if ACTIVE_CHAR["Char_name"] not in ids:
            ACTIVE_CHAR["Char_name"] = ids[0]
        wm.char_previews = ACTIVE_CHAR["Char_name"]
        if ACTIVE_CHAR["Char_name"] not in ASSET_LIBR_EXIST:
            ASSET_LIBR_EXIST.append(ACTIVE_CHAR["Char_name"])

    CMX_PUB_VAR["active_mesh_mode"] = wm.cf_mesh_mode
    CMX_PUB_VAR["mesh_mode_display"] = wm.cf_mesh_mode
    cmx_set_progress_info("")
    return True

def _cmx_finish_turn_on_deferred():
    wm = getattr(bpy.context, "window_manager", None)
    CMX_PUB_VAR["customize_turn_on_pending"] = False
    if not wm or not wm.cf_on_off_toggle:
        return None

    CMX_PUB_VAR["customize_turn_on_loading"] = True
    load_success = False
    try:
        load_success = _cmx_customize_turn_on_impl(bpy.context)
    except Exception as exc:
        cmx_set_progress_error("Customizer", str(exc))
    finally:
        CMX_PUB_VAR["customize_turn_on_loading"] = False
        _cmx_tag_redraw_all()

    if not load_success and wm.cf_on_off_toggle:
        wm.cf_on_off_toggle = False
    return None

def cmx_turn_on_off(self, context):
    """Turn on/off the Crowd Mixer addon and prepare the asset system."""
    wm = context.window_manager

    if CMX_PUB_VAR.get("customize_toggle_internal_change"):
        CMX_PUB_VAR["customize_toggle_internal_change"] = False
        return None
    
    # TURN ON
    if wm.cf_on_off_toggle:
        if CMX_PUB_VAR.get("customize_turn_on_pending") or CMX_PUB_VAR.get("customize_turn_on_loading"):
            return None
        CMX_PUB_VAR["customize_turn_on_pending"] = True
        if not _cmx_preflight_customize_turn_on(context):
            _cmx_revert_customize_toggle(wm)
            return None
        _cmx_tag_redraw_all()
        try:
            bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)
        except Exception:
            pass
        bpy.app.timers.register(_cmx_finish_turn_on_deferred, first_interval=0.01)

    # TURN OFF
    else:
        CMX_PUB_VAR["customize_turn_on_pending"] = False
        if CMX_PUB_VAR["Off_Exist_Path"]: 
            if wm.anim_use_toggle:
                wm.anim_use_toggle = False
            cmx_save_setting_data(context)
            cmx_reset_props_assets()

            wm.set_frame_range_toggle = True
            wm.preview_on_3d_cursor = False

            cf_coll = bpy.data.collections.get("CMX_Assets")
            if cf_coll:
                bpy.data.collections.remove(cf_coll)

            Ins_loc = bpy.data.objects.get("CMX_Assets")
            if Ins_loc:
                bpy.data.objects.remove(Ins_loc)

            for coll_bp in ASSET_PREV_COLL:
                cf_bp_coll = bpy.data.collections.get(coll_bp)
                if cf_bp_coll:
                    bpy.data.collections.remove(cf_bp_coll)

            for prev in PREVIEW_LIST:
                ACTIVE_CHAR[prev] = None
                ACTIVE_PREV[prev] = None

            CMX_PUB_VAR["active_mesh_mode"] = None
            CMX_PUB_VAR["mesh_mode_switch_pending"] = False
            CMX_PUB_VAR["mesh_mode_switch_loading"] = False
            CMX_PUB_VAR["mesh_mode_pending_target"] = None
            CMX_PUB_VAR["mesh_mode_display"] = wm.cf_mesh_mode
            bpy.ops.outliner.orphans_purge(do_recursive=True)
 
def cmx_reset_props_assets():
    """Reset asset properties and material custom properties."""
    for coll_name in ASSET_PREV_COLL:
        coll = bpy.data.collections.get(coll_name)
        if not coll:
            continue

        for obj in coll.all_objects:
            if coll_name == "CMX_Body" and obj.type == 'MESH':
                key_block = obj.data.shape_keys
                if key_block and key_block.key_blocks:
                    for sk in key_block.key_blocks:
                        sk.value = 0.0

            if obj.type in {'MESH', 'CURVE', 'SURFACE', 'FONT', 'META'}:
                for mat in obj.data.materials:
                    if not mat:
                        continue
                    mat["Pattern_Index"] = 0
                    mat["Face_Index"] = 0
                    mat["Skin_Index"] = 0
                    mat["Color_Input_Ctrl"] = [1.0, 1.0, 1.0, 1.0]
                    mat.id_properties_ui("Pattern_Index").update(min=0, max=100)
                    mat.id_properties_ui("Color_Input_Ctrl").update(subtype='COLOR', min=0.0, max=1.0)

def cmx_create_asset_collection():
    """Create main collection for assets and sub-collections for each asset type."""
    sc_coll = bpy.context.scene.collection
    cm_asset_scene = cmx_get_assets_scene()

    cf_asset_coll = bpy.data.collections.get("CMX_Assets")
    if not cf_asset_coll:
        cf_asset_coll = bpy.data.collections.new("CMX_Assets")
        cm_asset_scene.collection.children.link(cf_asset_coll)
        if cf_asset_coll.name not in sc_coll.objects:
            instance = bpy.data.objects.new(cf_asset_coll.name, None)
            instance.instance_type = 'COLLECTION'
            instance.instance_collection = cf_asset_coll
            sc_coll.objects.link(instance)
            instance.show_instancer_for_viewport = False

    Linked_Char_coll = bpy.data.collections.get("Linked_Character")
    if not Linked_Char_coll:
        Linked_Char_coll = bpy.data.collections.new("Linked_Character")
        cm_asset_scene.collection.children.link(Linked_Char_coll)

    for coll_bp in ASSET_PREV_COLL:
        cf_bp_coll = bpy.data.collections.get(coll_bp)
        if not cf_bp_coll:
            cf_bp_coll = bpy.data.collections.new(coll_bp)
            bpy.data.collections["CMX_Assets"].children.link(cf_bp_coll)

def cmx_preview_regis():
    """Register preview collections for characters, body parts, and animations."""
    char_pcoll = bpy.utils.previews.new()
    char_pcoll.char_previews_dir = ""
    char_pcoll.char_previews = ()
    PREVIEW_COLL["Char"] = char_pcoll

    for prev in PREVIEW_LIST:
        pcoll_prev = bpy.utils.previews.new()
        PREVIEW_COLL[prev] = pcoll_prev

    anim_pcoll = bpy.utils.previews.new()
    anim_pcoll.anim_filter = ""
    anim_pcoll.anim_char = ""
    anim_pcoll.anim_previews = ()
    PREVIEW_COLL["Anim"] = anim_pcoll

def cmx_preview_unregis():
    """Unregister and clear all preview collections."""
    for pcoll in PREVIEW_COLL.values():
        bpy.utils.previews.remove(pcoll)
    PREVIEW_COLL.clear()

def cmx_load_presets_on_scene_update(dummy):
    """Load preset list data on scene update."""
    try:
        cmx_load_preset_List_data(bpy.context)
    except Exception as e:
        print(f"[CrowdMixer] Failed to load preset list on scene update: {e}")

class CMXMainPanel(Panel):
    """Main panel for the Crowd Mixer UI."""
    bl_label = "CrowdMixer-2.0-Ce"
    bl_idname = "CMX_PT_main_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Crowd-Mixer"

    def draw(self, context):
        layout = self.layout
        wm = context.window_manager
        visible_panel_tabs = {
            "Crowd Manager",
            "Character Customization",
            "Preset Collection",
        }

        if wm.cf_panel_tab not in visible_panel_tabs:
            wm.cf_panel_tab = "Crowd Manager"

        thumpnail_col = layout.column()
        split = thumpnail_col.split(factor=0.4)
        left_col = split.row(align=True)
        right_col = split.row(align=True)

        Main_panel_col = layout.column(align=True)
        row_info_tab = Main_panel_col.row(align=True)
        split_info = row_info_tab.split(factor=0.92, align=True)
        info_left = split_info.row(align=True)
        info_left.alignment = 'CENTER'
        info_left.label(text=f"{wm.cf_panel_tab}")
        info_right = split_info.row(align=True)
        info_right.alignment = 'RIGHT'
        info_right.operator(
            "cmx.open_help_url", text="", icon_value=get_cf_icon("cf_help")
        ).url = "https://discord.gg/v6BZ7Tntbe"

        row_tab = Main_panel_col.row(align=True)
        grid_menu_bar = row_tab.grid_flow(align=True)
        row_tab.scale_y = 1.2
        grid_menu_bar.prop(wm, 'cf_panel_tab', toggle=True, expand=True, icon_only=True)

        if wm.cf_panel_tab == "Character Customization":
            cmx_draw_panel_char_custom(self, context, Main_panel_col)
        elif wm.cf_panel_tab == "Preset Collection":
            cmx_draw_panel_char_coll(self, context, Main_panel_col)
        elif wm.cf_panel_tab == "Crowd Manager":
            cmx_draw_panel_crowd(self, context, Main_panel_col)
        elif wm.cf_panel_tab == "Creator Tools":
            cmx_draw_panel_creator(self, context, Main_panel_col)

    def invoke(self, context, event):
        if event.type == 'LEFTMOUSE' and event.value == 'DOUBLE_CLICK':
            wm = context.window_manager
            item = wm.my_items[wm.my_item_index]
            if item.is_preset:
                print("Double-clicked on preset:", item.preset)
        return {'FINISHED'}

    def draw_header(self, context):
        layout = self.layout
        layout.label(icon_value=get_cf_icon("cf_logo"))

class CMXPreferences(AddonPreferences):
    """Addon preferences for Crowd Mixer."""
    bl_idname = __package__

    folder_path: StringProperty(
        name="Asset Path",
        subtype='DIR_PATH',
        default="",
        description="Choose a directory for your addon",
        update=_cmx_on_asset_path_changed,
    ) # type: ignore
    show_creator_tools_tab: BoolProperty(
        name="Show Creator Tools Tab",
        description="If unchecked, the 'Creator Tools' tab will be hidden from the main panel.",
        default=False,
    ) # type: ignore
    popup_preview_size: IntProperty(
        name="Popup Size",
        description="Preview popup size used in icon views",
        default=5,
        min=2,
        max=8,
    ) # type: ignore

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "folder_path")
        if not self.folder_path:
            info_row = layout.row(align=True)
            info_row.label(text="Character assets are a separate free download.", icon='INFO')
            if CMX_ASSET_DOWNLOAD_URL:
                info_row.operator(
                    "cmx.open_help_url",
                    text="Get Character Assets",
                    icon_value=get_cf_icon("cf_help"),
                ).url = CMX_ASSET_DOWNLOAD_URL
        row = layout.row(align=True)
        row.prop(self, "popup_preview_size", text="Popup Size")
        row.operator("cmx.update_anim_fbx", text="Update Anim", icon_value=get_cf_icon("sub_panel_anim_update"))

classes = [
    CMXMainPanel,
    CMXPreferences
]

def register():
    """Register all classes, properties, and handlers for the addon."""
    WindowManager.cf_on_off_toggle = BoolProperty(default=False, update=cmx_turn_on_off)

    cmx_preview_regis()
    cf_property_regis()
    icon_system_regis()
    Image_system_regis()

    for cls in classes:
        bpy.utils.register_class(cls)

    OP_preview.register()
    OP_creator.register()
    OP_animation.register()
    OP_common.register()
    Panel_Character_Collection.register()
    Panel_Crowd_Tool.register()
    OP_section_preset.register()
    OP_Spawn.register()

    cmx_load_section_preset_items()
    cmx_load_preset_List_data(bpy.context)
    if cmx_load_presets_on_scene_update not in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(cmx_load_presets_on_scene_update)

    # enum_item_gen.cmx_build_all_anim_previews()

def unregister():
    """Unregister all classes, properties, and handlers for the addon."""
    cmx_preview_unregis()
    cf_property_unregis()
    icon_system_unregis()
    Image_system_unregis()

    for cls in classes:
        bpy.utils.unregister_class(cls)

    OP_preview.unregister()
    OP_creator.unregister()
    OP_animation.unregister()
    OP_common.unregister()
    Panel_Character_Collection.unregister()
    Panel_Crowd_Tool.unregister()
    OP_section_preset.unregister()
    OP_Spawn.unregister()

    del WindowManager.cf_on_off_toggle

if __name__ == "__main__":
    register()
