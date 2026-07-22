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

import os
import os
from bpy.types import  WindowManager
from bpy.props import EnumProperty, IntProperty, StringProperty, BoolProperty, FloatProperty, FloatVectorProperty
from .OP_preview import *
from .OP_animation  import *
from .OP_update_prop  import *
from .OP_creator import cmx_toggle_hook_preview, cmx_update_hook_falloff

# ---------------------------------------------------------------
# Mesh mode change handler
# ---------------------------------------------------------------
def cmx_on_mesh_mode_change(self, context):
    """Reload Single-Mesh character list/previews when customize state changes."""
    wm = context.window_manager
    from .system_var import CMX_PUB_VAR

    # During Customize ON bootstrap, mesh mode can be forced to SINGLE.
    # Skip the full reload until startup has finished.
    if CMX_PUB_VAR.get("customize_turn_on_pending") or CMX_PUB_VAR.get("customize_turn_on_loading"):
        CMX_PUB_VAR["active_mesh_mode"] = getattr(wm, "cf_mesh_mode", "SINGLE")
        CMX_PUB_VAR["mesh_mode_display"] = getattr(wm, "cf_mesh_mode", "SINGLE")
        return

    if not wm.cf_on_off_toggle:
        CMX_PUB_VAR["active_mesh_mode"] = getattr(wm, "cf_mesh_mode", "SINGLE")
        CMX_PUB_VAR["mesh_mode_display"] = getattr(wm, "cf_mesh_mode", "SINGLE")
        return
    from .OP_common import (
        cmx_get_asset_dir_by_mode,
        cmx_refresh_character_maps_and_list,
        cmx_load_setting_data,
        cmx_get_saved_mode_settings,
        cmx_get_saved_animation_settings,
        cmx_restore_active_char_state,
        cmx_restore_animation_settings,
        cmx_store_mode_settings,
        cmx_has_saved_mode_settings,
    )
    from .OP_char_preset import cmx_set_char_to_preset
    from .system_var import CHAR_LIST, ACTIVE_CHAR, CMX_PUB_VAR, PREVIEW_COLL, CHAR_LATEST_ITEM, CHAR_PREV_SET
    from .OP_preview import cmx_set_character, cmx_char_preview_item

    prev_mode = CMX_PUB_VAR.get("active_mesh_mode") or getattr(wm, "cf_mesh_mode", "SINGLE")
    cmx_store_mode_settings(context, mode=prev_mode, last_mesh_mode=wm.cf_mesh_mode)

    saved_settings = cmx_load_setting_data()
    target_state = cmx_get_saved_mode_settings(wm.cf_mesh_mode, saved_settings)
    target_animation = cmx_get_saved_animation_settings(saved_settings)
    if wm.cf_mesh_mode == "SINGLE":
        target_filter = target_state.get("single_char_filter", "All")
        try:
            wm["single_char_filter"] = target_filter
        except Exception:
            try:
                wm.single_char_filter = target_filter
            except Exception:
                pass

    char_dir = cmx_get_asset_dir_by_mode()
    if not char_dir or not os.path.exists(char_dir):
        CMX_PUB_VAR["active_mesh_mode"] = wm.cf_mesh_mode
        return

    cmx_restore_active_char_state(target_state, wm.cf_mesh_mode)
    cmx_refresh_character_maps_and_list(context)

    if not CHAR_LIST:
        CMX_PUB_VAR["active_mesh_mode"] = wm.cf_mesh_mode
        return

    # Reset preview cache and force update
    char_pcoll = PREVIEW_COLL.get("Char")
    if char_pcoll:
        try:
            char_pcoll.clear()
        except Exception:
            pass
        CHAR_PREV_SET.clear()
        char_pcoll.char_previews_dir = ""
        char_pcoll.char_previews = ()

    # Rebuild enum items and set a valid preview id
    items = cmx_char_preview_item(None, context)
    if not items:
        CMX_PUB_VAR["active_mesh_mode"] = wm.cf_mesh_mode
        return
    target_char = target_state.get("Char_name")
    item_ids = [item[0] for item in items]
    if target_char not in item_ids:
        target_char = items[0][0]

    for key in CHAR_LATEST_ITEM.keys():
        if target_char not in CHAR_LATEST_ITEM[key]:
            CHAR_LATEST_ITEM[key][target_char] = None

    # Force a character reload even if both modes share the same character name.
    ACTIVE_CHAR["Char_name"] = None
    wm.char_previews = target_char
    cmx_set_character(None, context)

    if cmx_has_saved_mode_settings(target_state):
        CMX_PUB_VAR["is_loading_preset"] = True
        try:
            cmx_set_char_to_preset(context, target_state)
        finally:
            CMX_PUB_VAR["is_loading_preset"] = False
    cmx_restore_animation_settings(context, target_animation)
    CMX_PUB_VAR["active_mesh_mode"] = wm.cf_mesh_mode
    CMX_PUB_VAR["mesh_mode_display"] = wm.cf_mesh_mode

def cf_property_regis():
    # Animation & visibility toggles
    WindowManager.anim_use_toggle = BoolProperty(
        name="Apply Animation", description="Toggle apply animation", default=False, update=cmx_apply_animation
    )
    WindowManager.vis_amature_toggle = BoolProperty(
        name="Show Armature", description="Show/hide character armature", default=False, update=cmx_vis_amature
    )
    WindowManager.vis_proxy_toggle = BoolProperty(
        name="Show Proxy", description="Show/hide proxy mesh", default=False, update=cmx_vis_proxy
    )
    WindowManager.vis_amature_toggle_bake = BoolProperty(
        name="Show Armature (Baked)", description="Show/hide armature after bake", default=False, update=cmx_vis_amature_bake
    )
    WindowManager.set_frame_range_toggle = BoolProperty(
        name="Set Frame Range", description="Toggle to set frame range", default=True
    )
    WindowManager.preview_on_3d_cursor = BoolProperty(
        name="Follow 3D Cursor", description="Move preview to 3D cursor", default=False, update=cmx_set_preview_on_3d_cursor
    )
    WindowManager.cf_skip_delete_confirmation_session = BoolProperty(
        name="Skip Delete Confirmation", description="Don't ask to confirm deletion this session", default=False
    )
    WindowManager.cf_preset_edit_mode = BoolProperty(
        name="Edit Presets", description="Toggle edit mode for presets", default=False
    )
    WindowManager.cf_mesh_mode = EnumProperty(
        name="Mesh UI Mode",
        description="Lite edition uses Single-Mesh customization only",
        items=[
            ("SINGLE", "Single-Mesh", "Show simplified single-mesh UI"),
        ],
        default="SINGLE",
        update=cmx_on_mesh_mode_change,
    )
    WindowManager.single_char_filter = EnumProperty(
        name="Single Character Filter",
        description="Filter Single-Mesh characters by top-level folder",
        items=cmx_single_char_filter_list,
        update=cmx_set_single_char_filter
    )

    # Main UI, preview and instance controls
    WindowManager.random_append_count = IntProperty(
        name="Randomize Count", description="Number of random assets to append", default=1, min=1, max=100
    )
    WindowManager.locater_size = IntProperty(
        name="Locator Size", description="Size of locator objects", default=1
    )
    WindowManager.cmx_hook_preview_toggle = BoolProperty(
        name="Hook Preview",
        description="Toggle the hook helper preview/material on the active mesh",
        default=False,
        update=cmx_toggle_hook_preview
    )
    WindowManager.cmx_hook_falloff = FloatProperty(
        name="Hook Falloff",
        description="Falloff radius for the helper hook",
        default=0.5,
        min=0.01,
        max=100.0,
        precision=3,
        update=cmx_update_hook_falloff
    )
    WindowManager.cmx_bake_output_dir = StringProperty(
        name="Bake Output Directory",
        subtype='DIR_PATH',
        description="Folder to save baked textures (blank = blend file folder or temp)"
    )
    WindowManager.cmx_separate_action_output_dir = StringProperty(
        name="Separate Action Output Directory",
        subtype='DIR_PATH',
        description="Folder to save one .blend file per action"
    )
    WindowManager.cmx_anim_preview_write_mode = EnumProperty(
        name="Animation Preview Write Mode",
        description="Choose whether to overwrite existing animation preview images",
        items=[
            ("MISSING", "Only Missing", "Render only previews that do not exist yet"),
            ("OVERWRITE", "Overwrite All", "Render and replace previews even if they already exist"),
        ],
        default="MISSING",
    )
    WindowManager.cmx_bake_color = BoolProperty(
        name="Bake Color",
        description="Bake diffuse color (selected to active)",
        default=True,
    )
    WindowManager.cmx_bake_normal = BoolProperty(
        name="Bake Normal",
        description="Bake normal map (selected to active)",
        default=True,
    )
    WindowManager.cmx_bake_ss_mask = BoolProperty(
        name="Create SS Mask",
        description="Create subsurface mask image and hook to materials",
        default=True,
    )
    WindowManager.offset_start_frame_ins = IntProperty(
        name="Instance Start Frame", description="Start frame for instance", default=0, update=cmx_update_offset_to_instance
    )
    WindowManager.set_anim_speed_ins = FloatProperty(
        name="Instance Speed", description="Animation speed for instance", default=1.0, min=0.01, update=cmx_update_anim_speed_to_instance
    )
    WindowManager.show_instance_anim_settings = BoolProperty(
        name="Show Instance Anim",
        description="Show or hide the instance animation settings panel",
        default=False,
    )
    WindowManager.cmx_bake_texture_size = IntProperty(
        name="Bake Texture Size",
        description="Resolution (width and height) for the generated bake textures",
        default=1024,
        min=64,
        max=16384,
    )
    WindowManager.char_preview_rotation_z = FloatProperty(
        name="Preview Rot Z", description="Character preview rotation (Z axis)",
        subtype='ANGLE', default=0.0, min=-3.14159, max=3.14159, step=100, precision=2,
        update=cmx_update_cf_assets_instance_rotation
    )
    WindowManager.progress_info_render = StringProperty(
        name="Render Info", description="Show rendering progress", default=""
    )
    WindowManager.body_part_key = StringProperty(
        name="Body Part Key", description="Body part identifier", default=""
    )
    WindowManager.coll_name_use_nla = StringProperty(
        name="Collection NLA Name", description="Name for NLA collection", default=""
    )
    WindowManager.last_instance_name = StringProperty(
        name="Last Instance", description="Last instance name", default=""
    )

    WindowManager.color_property_skin = FloatVectorProperty(
        name="Skin Color", description="Skin color (RGBA)",
        subtype="COLOR", size=4, min=0.0, max=1.0, default=(1.0, 1.0, 1.0, 1.0)
    )

    # EnumProperties (Tabs, Filters, Preview, etc.)
    WindowManager.cf_panel_tab = EnumProperty(
        name="Panel Tab", description="Main panel tab", items=cmx_gen_panel_list
    )
    WindowManager.cf_customize_tab = EnumProperty(
        name="Customize Tab", description="Character customize tab", items=cmx_gen_customize_tab_list
    )
    WindowManager.cf_subpanel_tab_head = EnumProperty(
        name="Subpanel (Head)", description="Subpanel tab for head", items=cmx_gen_subpanel_head_list
    )
    WindowManager.cloths_filter = EnumProperty(
        name="Cloth Filter", description="Filter clothing items", items=cmx_clothes_filter_list, update=cmx_set_clothes_filter
    )
    WindowManager.anim_filter = EnumProperty(
        name="Animation Filter", description="Filter animation type", items=cmx_anim_filter_list, update=cmx_set_anim_filter
    )
    WindowManager.gen_preview_filter = EnumProperty(
        name="Preview Filter", description="Filter for generating previews", items=cmx_gen_preview_filter_list, update=cmx_set_gen_preview_filter
    )
    WindowManager.char_previews = EnumProperty(
        name="Character Preview", description="Character preview list", items=cmx_char_preview_item, update=cmx_set_character
    )
    WindowManager.anim_previews = EnumProperty(
        name="Animation Preview", description="Animation preview list", items=cmx_anim_preview_item, update=cmx_set_animation
    )
    WindowManager.head_preset = EnumProperty(
        name="Head Preset", description="Select head preset", items=cmx_headpreset_preview_item
    )
    WindowManager.crowd_preset = EnumProperty(
        name="Crowd Preset", description="Select crowd preset", items=cmx_crowdpreset_preview_item
    )
    WindowManager.makeup_previews = EnumProperty(
        name="Makeup", description="Face makeup options", items=cmx_makeup_previews_item, update=cmx_set_face
    )
    WindowManager.body_preset = EnumProperty(
        name="Body Preset", description="Select body preset", items=cmx_bodypreset_preview_item
    )
    WindowManager.skin_previews = EnumProperty(
        name="Skin Preview", description="Skin material previews", items=cmx_skin_previews_item, update=cmx_set_skin
    )
    WindowManager.hair_previews = EnumProperty(
        name="Hair Preview", description="Hair asset previews", items=cmx_hair_previews_item, update=cmx_set_hair
    )
    WindowManager.head_previews = EnumProperty(
        name="Head Preview", description="Head asset previews", items=cmx_head_previews_item, update=cmx_set_head
    )
    WindowManager.eye_previews = EnumProperty(
        name="Eye Preview", description="Eye asset previews", items=cmx_eye_previews_item, update=cmx_set_eye
    )
    WindowManager.torso_previews = EnumProperty(
        name="Torso Preview", description="Torso asset previews", items=cmx_torso_previews_item, update=cmx_set_torso
    )
    WindowManager.accessory_previews = EnumProperty(
        name="Accessory Preview", description="Accessory asset previews", items=cmx_accessory_previews_item, update=cmx_set_accessory
    )
    WindowManager.leg_previews = EnumProperty(
        name="Leg Preview", description="Leg asset previews", items=cmx_leg_previews_item, update=cmx_set_leg
    )
    WindowManager.foot_previews = EnumProperty(
        name="Foot Preview", description="Foot asset previews", items=cmx_foot_previews_item, update=cmx_set_foot
    )

    # Dynamic properties from dicts/lists (use concise name/desc)
    for prop_name_key in PROP_BP_ITEM_OFF.keys():
        prop_type = BoolProperty(
            name=PROP_BP_ITEM_OFF[prop_name_key].replace("_", " ").title(),
            description=f"Toggle visibility for {prop_name_key.lower()}",
            default=False,
            update=create_update_callback(prop_name_key, "item_off")
        )
        setattr(WindowManager, PROP_BP_ITEM_OFF[prop_name_key], prop_type)

    for prop_name_key in PROP_COLOR.keys():
        prop_type = FloatVectorProperty(
            name=PROP_COLOR[prop_name_key].replace("_", " ").title(),
            description=f"Color for {prop_name_key.lower()}",
            subtype="COLOR",
            size=4,
            min=0.0,
            max=1.0,
            default=(1.0, 1.0, 1.0, 0.0),
            update=create_update_callback(prop_name_key, "item_color")
        )
        setattr(WindowManager, PROP_COLOR[prop_name_key], prop_type)

    for prop_name in BODY_SHAPE_KEY + FACE_SHAPE_KEY + EMOTION_SHAPE_KEY:
        prop_type = FloatProperty(
            name=prop_name.replace("_", " ").title(),
            description=f"Shape key: {prop_name}",
            default=0,
            min=0,
            max=1,
            update=create_update_callback(prop_name, "shapekey")
        )
        setattr(WindowManager, prop_name, prop_type)

    for prop_name_key in EXPANDED_BOOLEAN:
        prop_type = BoolProperty(
            name=prop_name_key.replace("_", " ").title(),
            description=f"Expand/collapse: {prop_name_key.replace('_', ' ')}",
            default=False
        )
        setattr(WindowManager, prop_name_key, prop_type)
 
def cf_property_unregis():
   
    del WindowManager.anim_use_toggle               
    del WindowManager.vis_amature_toggle   
    del WindowManager.vis_proxy_toggle         
    del WindowManager.vis_amature_toggle_bake       
    del WindowManager.set_frame_range_toggle        
    del WindowManager.preview_on_3d_cursor          
    del WindowManager.cf_skip_delete_confirmation_session
    del WindowManager.cf_preset_edit_mode
    del WindowManager.cf_mesh_mode
    del WindowManager.single_char_filter
              
    #sub panel main character customize
    del WindowManager.sub_panel_head_expanded     
    del WindowManager.sub_panel_body_expanded     
      
    del WindowManager.random_append_count              
    del WindowManager.locater_size     
    del WindowManager.cmx_hook_preview_toggle
    del WindowManager.cmx_hook_falloff
    del WindowManager.cmx_bake_output_dir
    del WindowManager.cmx_separate_action_output_dir
    del WindowManager.cmx_anim_preview_write_mode
    del WindowManager.cmx_bake_color
    del WindowManager.cmx_bake_normal
    del WindowManager.cmx_bake_ss_mask
    del WindowManager.offset_start_frame_ins               
    del WindowManager.set_anim_speed_ins 
    del WindowManager.show_instance_anim_settings
    del WindowManager.cmx_bake_texture_size 
    del WindowManager.char_preview_rotation_z    
        
    del WindowManager.progress_info_render       
    del WindowManager.body_part_key                  
    del WindowManager.coll_name_use_nla  
    del WindowManager.last_instance_name              
       
   
    del WindowManager.color_property_skin          

    #--------------------------------------------------------- Enum Property --------------------------------------------------------------------#
    del WindowManager.cf_panel_tab     
    del WindowManager.cf_customize_tab           
    del WindowManager.cf_subpanel_tab_head        

    del WindowManager.cloths_filter                
    del WindowManager.anim_filter                  
    del WindowManager.gen_preview_filter           
       
   
    #--->> Character Previw
    del WindowManager.char_previews                
    # Animation Previw
    del WindowManager.anim_previews                

    #--->> Face Previw
    del WindowManager.head_preset                      
    # del WindowManager.face_shape                   
    del WindowManager.makeup_previews                       
    # del WindowManager.emotion                      

    #--->> Body Previw
    del WindowManager.body_preset                  
    #del WindowManager.body_shape                  
    del WindowManager.skin_previews                       

    #--->> Cloth Previw
    del WindowManager.hair_previews                
    del WindowManager.head_previews                
    del WindowManager.eye_previews                 
    del WindowManager.torso_previews               
    del WindowManager.accessory_previews                
    del WindowManager.leg_previews                 
    del WindowManager.foot_previews       


    for p_name in BODY_SHAPE_KEY + FACE_SHAPE_KEY + EMOTION_SHAPE_KEY + EXPANDED_BOOLEAN:
        if hasattr(WindowManager, p_name):
            delattr(WindowManager, p_name)
    
    for p_name in PROP_BP_ITEM_OFF.values():
        if hasattr(WindowManager, p_name):
            delattr(WindowManager, p_name)                

def create_update_callback(key_name,prop_type):
    if prop_type == "shapekey":
        def update_shapekey_property(self, context):
            cmx_set_shape_by_key(context, key_name,"CMX_Body")
        return update_shapekey_property
    elif prop_type == "item_off":
        def update_itemoff_property(self, context):
            cmx_item_off_by_key(context, key_name)
        return update_itemoff_property
    elif prop_type == "item_color":
        def update_item_color_property(self, context):
            cmx_set_color_item_by_key(self, context, key_name)
        return update_item_color_property
   
