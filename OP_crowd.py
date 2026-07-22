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
import json
from functools import partial
from .OP_common import cmx_set_progress_success, cmx_set_progress_task
from .OP_char_preset import *
from .OP_link_asset import *
from .OP_animation import *
from .OP_update_prop import *
from .OP_Spawn import *

def cmx_get_preset_collections_item(self, context):
    """Return a list of preset collection items from char_preset.json"""
    file_path = os.path.join(CURRENT_DIRECTORY, "CMX_Data", "char_preset.json")
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            data = json.load(file)
            return [(key, key, "") for key in data.keys()]
    return []

# def cmx_set_crowd_source_active(self, context):
#     """Activate/deactivate a crowd source, handle loading and removing."""
#     preset_data = cmx_get_preset_collection_data(self.preset_collection)
#     preset_dict = {self.preset_collection: preset_data}

#     if self.active:
        
#         if context.window_manager.cf_on_off_toggle:
#             cmx_add_override_all_active_item()
#             cmx_load_crowd_asset_source(self, context, preset_dict)
#             cmx_remove_override_all_active_item()            
#         else:
#             cmx_load_crowd_asset_source(self, context, preset_dict)
#         # cmx_create_instance_preview(self, context)
#         self.visible = True
#         # cmx_set_source_preview_type(self, context)
#         # cmx_calculate_instance_positions(self, distance=1)
#         # cmx_active_nla(self.name)
#         # cmx_set_random_speed_anim_min(self, context)
#         # cmx_set_random_strat_frame_anim(self, context)
#         # cmx_update_source_start_frame(self, context)
#         # cmx_update_source_anim_speed(self, context)
#     else:
#         cmx_remove_instance_preview(self, self.name)
#         cmx_remove_crowd_asset(preset_dict, self.name)
#         if self.name in STRIPS_LIST:
#             del STRIPS_LIST[self.name]
#         bpy.ops.outliner.orphans_purge(do_recursive=True)
#     return None

def cmx_set_source_preview_type(self, context):
    """Set preview type for source (full/proxy)."""
    if self.active:
        if self.preview_type == 'SOURCE_FULL':
            # cmx_calculate_instance_positions(self, distance=1)
            cmx_instance_preview_is_proxy(self, is_proxy=False)
        elif self.preview_type == 'SOURCE_PROXY':
            # cmx_calculate_instance_positions(self, distance=1)
            cmx_instance_preview_is_proxy(self, is_proxy=True)
    return

CMX_LOAD_QUEUE = []
CMX_PENDING_SAVE_INFO = None

def cmx_schedule_source_save(save_path, collection_name=None):
    """Schedule saving the current blend file to the given path after source load completes."""
    global CMX_PENDING_SAVE_INFO
    CMX_PENDING_SAVE_INFO = {"path": save_path, "collection": collection_name}

def cmx_save_scene_if_pending():
    """Save the current blend file to the pending path, if any."""
    global CMX_PENDING_SAVE_INFO
    if not CMX_PENDING_SAVE_INFO:
        return
    save_path = CMX_PENDING_SAVE_INFO.get("path")
    collection_name = CMX_PENDING_SAVE_INFO.get("collection")
    CMX_PENDING_SAVE_INFO = None
    try:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=save_path, check_existing=False, compress=False)
        print(f"[CMX] Source file saved to: {save_path}")
        try:
            cmx_mark_collection_built(collection_name)
        except Exception:
            pass
    except Exception as e:
        print(f"[CMX ERROR] Failed to save source file: {e}")

def cmx_load_worker(crowd_name, preset_name, preset_values, preset_collection_name, ins_index, ins_count):
    # print(f"[THREAD] Preparing {preset_name}")
    # cmx_set_progress_info(f"[THREAD] Preparing {preset_name}")
    payload = {
        "crowd_name": crowd_name,
        "preset_name": preset_name,
        "preset_values": preset_values,
        "preset_collection_name": preset_collection_name,
        "ins_index" : ins_index,
        "ins_count" : ins_count
    }
    CMX_LOAD_QUEUE.append(payload)

def cmx_main_thread_processor(self, context):
    try:
        if CMX_LOAD_QUEUE:
            payload = CMX_LOAD_QUEUE.pop(0)
            crowd_name = payload["crowd_name"]
            preset_name = payload["preset_name"]
            preset_values = payload["preset_values"]
            preset_collection_name = payload["preset_collection_name"]
            ins_index = payload["ins_index"]
            ins_count = payload["ins_count"]
            mesh_mode = "SINGLE"
            try:
                context.window_manager.cf_mesh_mode = mesh_mode
            except Exception:
                pass

            preset_collection = bpy.data.collections.get(preset_collection_name)

            # Ensure the main crowd collection exists before linking children
            cmx_crowd_collection = bpy.data.collections.get(crowd_name)
            if not cmx_crowd_collection:
                cmx_crowd_collection = bpy.data.collections.new(crowd_name)
                parent_sources = bpy.data.collections.get("CMX_Sources")
                if not parent_sources:
                    parent_sources = bpy.data.collections.new("CMX_Sources")
                    cm_asset_scene = cmx_get_assets_scene()
                    cm_asset_scene.collection.children.link(parent_sources)
                if cmx_crowd_collection.name not in [c.name for c in parent_sources.children]:
                    parent_sources.children.link(cmx_crowd_collection)

            if not preset_collection:
                preset_collection = bpy.data.collections.new(preset_collection_name)
                cmx_crowd_collection.children.link(preset_collection)

            cmx_set_progress_task("Load Crowd", preset_collection_name)
            cmx_spawn_character_to_scene(bpy.context, preset_values, preset_collection, use_proxy=True)

            cmx_crowd_coll = bpy.data.collections.get("CMX_Sources_Instance")
            if not cmx_crowd_coll:
                cmx_crowd_coll = bpy.data.collections.new("CMX_Sources_Instance")
                bpy.context.scene.collection.children.link(cmx_crowd_coll)

            Crowd_Ins_coll_name = f"{crowd_name}_Instance"
            Crowd_Ins_coll = bpy.data.collections.get(Crowd_Ins_coll_name)
            if not Crowd_Ins_coll:
                Crowd_Ins_coll = bpy.data.collections.new(Crowd_Ins_coll_name)
            if Crowd_Ins_coll.name not in [c.name for c in cmx_crowd_coll.children]:
                cmx_crowd_coll.children.link(Crowd_Ins_coll)

            cmx_create_instance_preview(preset_collection_name, Crowd_Ins_coll, bpy.context)
            cmx_calculate_instance_positions(preset_collection_name, ins_index, ins_count, distance=1)

            return 0.01  
        else:            
            # print("[CMX] Queue done. Set source preview type.")
            cmx_set_progress_success()

            cmx_set_source_preview_type(self, context)
            cmx_active_nla(self.name)
            cmx_set_random_speed_anim_min(self, context)
            cmx_set_random_strat_frame_anim(self, context)
            cmx_update_source_start_frame(self, context)
            cmx_update_source_anim_speed(self, context)
            cmx_save_scene_if_pending()

            return None
    except Exception as e:
        print(f"[CMX ERROR] {e}")
        return None

def cmx_load_crowd_asset_source(self, context, preset_data):
    crowd_name = self.name

    cmx_crowd_collection = bpy.data.collections.get("CMX_Sources")
    if not cmx_crowd_collection:
        cm_asset_scene = cmx_get_assets_scene()
        cmx_crowd_collection = bpy.data.collections.new("CMX_Sources")
        cm_asset_scene.collection.children.link(cmx_crowd_collection)

    for collection_name, presets in preset_data.items():
        crowd_collection_name = crowd_name
        main_collection = bpy.data.collections.get(crowd_collection_name)
        if not main_collection:
            main_collection = bpy.data.collections.new(crowd_collection_name)
            cmx_crowd_collection.children.link(main_collection)

        ins_count = len(presets)
        for ins_index, (preset_name, preset_values) in enumerate(presets.items()):
            preset_collection_name = f"{crowd_name}-{preset_name}"
            cmx_load_worker(crowd_name, preset_name, preset_values, preset_collection_name, ins_index, ins_count)

        # main_collection.hide_viewport = True

    bpy.app.timers.register(partial(cmx_main_thread_processor, self, context))


    CROWD_LATEST_SOURCE[crowd_name] = collection_name 

def cmx_remove_crowd_asset(preset_data, crowd_name):
    """Remove crowd asset collections and their sub-collections."""
    for collection_name, presets in preset_data.items():
        for preset_name, preset_values in presets.items():
            sub_collection_name = f"{crowd_name}-{preset_name}"
            if sub_collection_name in bpy.data.collections:
                sub_collection = bpy.data.collections[sub_collection_name]
                cmx_unlink_asset(sub_collection.name)
                bpy.data.collections.remove(sub_collection)
        main_collection_name = crowd_name
        if main_collection_name in bpy.data.collections:
            main_collection = bpy.data.collections[main_collection_name]
            for obj in main_collection.objects:
                bpy.data.objects.remove(obj, do_unlink=True)
            bpy.data.collections.remove(main_collection)

def cmx_create_instance_preview(Coll_for_Ins, cmx_crowd_coll, context):
    """
    Create a collection instance object for collection `Coll_for_Ins`
    and link it into CMX_Sources_Instance collection.
    """
    import bpy

    target_coll = bpy.data.collections.get(Coll_for_Ins)
    if not target_coll:
        print(f"[CMX] Collection '{Coll_for_Ins}' not found")
        return

    # สร้าง instance object
    instance = bpy.data.objects.new(Coll_for_Ins, None)
    instance.instance_type = 'COLLECTION'
    instance.instance_collection = target_coll
    instance.show_instancer_for_viewport = False

    cmx_crowd_coll.objects.link(instance)

def cmx_remove_instance_preview(self, source_collection):
    """Remove instance preview collection and objects."""
    crowd_coll_name = source_collection
    Ins_coll_name = f"{crowd_coll_name}_Instance"
    Ins_coll = bpy.data.collections.get(Ins_coll_name)
    if not Ins_coll:
        return None
    objects_to_delete = list(Ins_coll.objects)
    for obj in objects_to_delete:
        bpy.data.objects.remove(obj, do_unlink=True)
    bpy.data.collections.remove(Ins_coll)

def cmx_calculate_instance_positions(crowd_coll_name, ins_index, ins_count, distance=5):
    """
    Move the single instance object inside <crowd_coll_name>_Instance collection
    to the position calculated by ins_index and ins_count.
    """
    instance_obj = bpy.data.objects.get(crowd_coll_name)
    if not instance_obj:
        return
    total_width = (ins_count - 1) * distance
    start_x = -total_width / 2
    x_position = start_x + ins_index * distance
    
    instance_obj.location = (x_position, 0, 0)
    print(f"[CMX] Placed instance = {instance_obj.name}")
    print(f"[CMX] Calculated total width '{total_width}'  start_x ={start_x}ins_index ={ins_index}  ins_count={ins_count}  distance={distance}  x_position={x_position}")

def cmx_instance_preview_is_proxy(self, is_proxy=False):
    """Toggle between proxy and full asset collections for crowd instances."""
    preset_data = cmx_get_preset_collection_data(self.preset_collection)
    preset_dict = {self.preset_collection: preset_data}
    crowd_name = self.name
    for collection_name, presets in preset_dict.items():
        for preset_name, preset_values in presets.items():
            preset_collection_name = f"{crowd_name}-{preset_name}"
            coll_asset_full_name = preset_collection_name + "_FULL"
            if coll_asset_full_name in bpy.data.collections:
                coll_asset_full = bpy.data.collections.get(coll_asset_full_name)
                coll_asset_full.hide_viewport = is_proxy
            coll_asset_proxy_name = preset_collection_name + "_PROXY"
            if coll_asset_proxy_name in bpy.data.collections:
                coll_asset_proxy = bpy.data.collections.get(coll_asset_proxy_name)
                coll_asset_proxy.hide_viewport = not is_proxy

def cmx_refresh_modifier_display(modifier):
    """Force modifier to refresh its display in the viewport."""
    if modifier:
        original_state = modifier.show_viewport
        modifier.show_viewport = False
        bpy.context.view_layer.update()
        modifier.show_viewport = original_state
        bpy.context.view_layer.update()

def cmx_delete_unused_node_groups(node_group):
    """Recursively delete unused node groups."""
    for node in node_group.nodes:
        if node.type == 'GROUP' and node.node_tree:
            cmx_delete_unused_node_groups(node.node_tree)
    if node_group.users == 0:
        bpy.data.node_groups.remove(node_group)

def cmx_remove_object_and_associated_data(obj_name):
    """Remove object and its associated node groups from Blender."""
    obj = bpy.data.objects.get(obj_name)
    if not obj:
        return
    node_groups_to_check = []
    for mod in obj.modifiers:
        if mod.type == 'NODES' and mod.node_group:
            node_groups_to_check.append(mod.node_group)
    if obj.users_collection:
        for col in obj.users_collection:
            col.objects.unlink(obj)
    bpy.data.objects.remove(obj)
    for node_group in node_groups_to_check:
        cmx_delete_unused_node_groups(node_group)

def cmx_set_crowd_visible(self, context):
    """Set the visibility of a crowd collection."""
    coll_crowd_name = self.name
    if coll_crowd_name in bpy.data.collections:
        coll_source = bpy.data.collections.get(coll_crowd_name)
        coll_source.hide_viewport = not self.visible
        coll_source.hide_render = not self.visible

def cmx_get_source_list_item(self, context):
    """Return list of source_data_items from scene."""
    scene = context.scene
    return [(item.name, item.name, "") for item in scene.source_data_items]

def _cmx_set_collection_tree_visibility(collection, visible):
    """Apply visibility to a collection, its objects, and nested child collections."""
    if not collection:
        return False

    applied = False
    try:
        collection.hide_viewport = not visible
        collection.hide_render = not visible
        applied = True
    except Exception:
        pass

    for obj in list(getattr(collection, "objects", [])):
        try:
            obj.hide_viewport = not visible
            obj.hide_render = not visible
            applied = True
        except Exception:
            pass

    for child_collection in list(getattr(collection, "children", [])):
        if _cmx_set_collection_tree_visibility(child_collection, visible):
            applied = True

    return applied

def cmx_set_source_visible(self, context):
    """Set the visibility of the source collection instance."""
    source_name = str(getattr(self, "name", "") or "").strip()
    if not source_name:
        return

    visible = bool(getattr(self, "visible", True))
    instance_collection = bpy.data.collections.get(f"{source_name}_Instance")
    applied = _cmx_set_collection_tree_visibility(instance_collection, visible)
    if not applied:
        _cmx_set_collection_tree_visibility(bpy.data.collections.get(source_name), visible)

def cmx_load_crowd_object(item_data):
    """Load a crowd object from a blend file and add it to the correct collection."""
    cmx_set_progress_task("Load Crowd", item_data.name)
    modifier = None
    obj = None
    blend_file_path = os.path.join(CURRENT_DIRECTORY, "GeometryNodes", "Geo_Node_Templat.blend")
    
    get_coll = bpy.data.collections.get(item_data.name)
    if get_coll:
        crowd_node_coll = get_coll
    else:
        crowd_node_coll = bpy.data.collections.new(item_data.name)
    with bpy.data.libraries.load(blend_file_path, link=False) as (data_from, data_to):
        if item_data.crowd_obj_name in data_from.objects:
            data_to.objects = [item_data.crowd_obj_name]

    if data_to.objects:
        obj = data_to.objects[0]
        if obj.name in bpy.context.scene.collection.objects:
            bpy.context.scene.collection.objects.unlink(obj)
        crowd_node_coll.objects.link(obj)
        
        if obj.modifiers:
            modifier = obj.modifiers[0]
    
    if "CMX_Crowds" not in bpy.data.collections:
        cf_crowds_collection = bpy.data.collections.new("CMX_Crowds")
        bpy.context.scene.collection.children.link(cf_crowds_collection)
    else:
        cf_crowds_collection = bpy.data.collections["CMX_Crowds"]
    
    if crowd_node_coll.name not in cf_crowds_collection.children:
        cf_crowds_collection.children.link(crowd_node_coll)

    return modifier


