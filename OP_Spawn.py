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
from .OP_link_asset import *
from .OP_preview import *
from .OP_animation import *

def cmx_spawn_character_to_scene(context, setting_values, target_collection, use_proxy=False):
    """Spawn character into the scene with given settings."""
    char_name = setting_values.get("Char_name")
    if not char_name:
        print("[CMX ERROR] Missing Char_name in preset values; abort spawn.")
        return

    cmx_load_character_rig(char_name, target_collection.name, spawn_to_scene=True, use_proxy=use_proxy)
    coll_asset_name = target_collection.name + "_FULL"
    for key in ["Hair", "Head", "Eye", "Torso", "Accessory", "Leg", "Foot"]:
        if key in setting_values and setting_values[key]:
            object_name = setting_values[key]
            cmx_link_asset(setting_values["Char_name"], "__Object__", object_name, coll_asset_name, spawn_to_scene=True)
            object_name_ov = cmx_find_objects_in_collection_by_name(coll_asset_name, object_name)
            if key + "_Shader" in setting_values:
                index = setting_values[key + "_Shader"]
                cmx_shader_selector(index, object_name_ov, coll_asset_name)
                cmx_set_color_spawn_item(setting_values.get(key + "_Color"), object_name_ov, coll_asset_name)
    cmx_override_character_rig(setting_values["Char_name"], target_collection.name)
    coll_asset_body_name = target_collection.name + "_BODY"

    action_name = setting_values.get("Action")
    if action_name:
        cmx_link_action(
            bpy.context,
            spawn_to_scene=True,
            bone_coll_name=target_collection.name,
            act_name=action_name,
            aim_filter=setting_values.get("Action_Filter")
        )
        print("cmx_link_action by : cmx_spawn_character_to_scene")
    for obj in target_collection.objects:
        if obj.type == 'ARMATURE':
            obj.hide_viewport = True

    
    #show proxy for loading 
    if use_proxy:
        char_coll_source_name = target_collection.name + "_FULL"
        char_coll_source = bpy.data.collections.get(char_coll_source_name)
        char_coll_source.hide_viewport = True 

    if setting_values["Char_name"] not in ASSET_LIBR_EXIST:
        ASSET_LIBR_EXIST.append(setting_values["Char_name"])

def cmx_find_objects_in_collection_by_name(collection_name, prefix):
    """Find object in collection by prefix name."""
    collection = bpy.data.collections.get(collection_name)
    if not collection:
        return []
    for obj in collection.objects:
        if obj.name.startswith(prefix):
            return obj.name

def cmx_set_exclude_for_collection(collection_name, exclude=True):
    """Set exclude flag for collection in view layer."""
    view_layer = bpy.context.view_layer
    def find_layer_collection(layer_coll, coll_name):
        if layer_coll.collection.name == coll_name:
            return layer_coll
        for child in layer_coll.children:
            found = find_layer_collection(child, coll_name)
            if found:
                return found
        return None
    layer_coll = find_layer_collection(view_layer.layer_collection, collection_name)
    if layer_coll:
        layer_coll.exclude = exclude

class CMXPLaceCharToSceneOperator(bpy.types.Operator):
    """Override & Bake All Assets (with Sub-Collections)"""
    bl_idname = "cmx.place_char_to_scene"
    bl_label = "Override & Bake All Assets (with Sub-Collections)"
    bl_description = "Override all objects in CMX_Assets (excluding CMX_Proxy), move them to a new sub-collection in CMX_Placement, and hide armatures in CMX_Bone before moving"
    
    def execute(self, context):
        cmx_set_progress_info("Snapping Character to scene...")

        scene = context.scene
        place_coll = bpy.data.collections.get("CMX_Placement")
        if not place_coll:
            place_coll = bpy.data.collections.new("CMX_Placement")
            context.scene.collection.children.link(place_coll)
        Linked_Char_coll = bpy.data.collections.get("Linked_Character")
        char_name = ACTIVE_CHAR.get("Char_name", "Character")
        anim_name = ACTIVE_CHAR.get("Action", "neutral") or "neutral"
        bake_sub_name = f"{char_name}_{anim_name}"
        bake_sub_coll = bpy.data.collections.new(bake_sub_name)
        Linked_Char_coll.children.link(bake_sub_coll)
        setting_values = ACTIVE_CHAR
        cmx_add_override_all_active_item()
        cmx_spawn_character_to_scene(context, setting_values, bake_sub_coll, use_proxy=False)
        cmx_remove_override_all_active_item()
        cmx_active_nla(bake_sub_coll.name)
        cf_assets_coll = bpy.data.collections.get("CMX_Assets")
        cf_assets_instance = next((obj for obj in scene.collection.objects if obj.instance_type == 'COLLECTION' and obj.instance_collection == cf_assets_coll), None)
        bake_instance = bpy.data.objects.new(bake_sub_coll.name, None)
        bake_instance.instance_type = 'COLLECTION'
        bake_instance.instance_collection = bake_sub_coll
        if cf_assets_instance:
            bake_instance.location = cf_assets_instance.location
            bake_instance.rotation_euler = cf_assets_instance.rotation_euler
            bake_instance.scale = cf_assets_instance.scale
            bake_instance.empty_display_type = 'ARROWS'
            bake_instance.empty_display_size = 0.2
        else:
            bake_instance.location = (0, 0, 0)
        place_coll.objects.link(bake_instance)
        armature_obj = next((obj for obj in bake_sub_coll.objects if obj.type == 'ARMATURE'), None)
        if not armature_obj:
            self.report({'WARNING'}, "No armature found in bake_sub_coll.")
            return {'FINISHED'}
        cmx_set_progress_info("")
        self.report({'INFO'}, f"Placed instance of {bake_sub_coll.name} to scene and set up drivers.")
        return {'FINISHED'}

def register():
    bpy.utils.register_class(CMXPLaceCharToSceneOperator)

def unregister():
    bpy.utils.unregister_class(CMXPLaceCharToSceneOperator)
