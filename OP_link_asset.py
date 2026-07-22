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
from .OP_common import *
from .system_var import *
from .enum_item_gen import *

def _cmx_store_default_pose_name(armature_obj, char_name):
    """Cache the armature's original action so animation can be safely removed later."""
    if not armature_obj or not char_name:
        return
    default_pose_map = CMX_PUB_VAR.get("Default_Pose", {})
    if default_pose_map.get(char_name):
        return
    anim_data = getattr(armature_obj, "animation_data", None)
    action = getattr(anim_data, "action", None) if anim_data else None
    if action and getattr(action, "name", None):
        default_pose_map[char_name] = action.name

def cmx_load_character_rig(char_name, preset_coll_name, spawn_to_scene=False, use_proxy=True):
    """
    Load and link character rig assets into the scene, supporting proxy and full/partial loading.
    """
    errors = []
    if spawn_to_scene:
        coll_Bone_name = preset_coll_name

        coll_source_name = preset_coll_name + "_FULL"
        if coll_source_name in bpy.data.collections:
            coll_source = bpy.data.collections[coll_source_name]
        else:
            coll_source = bpy.data.collections.new(coll_source_name)
            preset_collection = bpy.data.collections[preset_coll_name]
            preset_collection.children.link(coll_source)
        
        coll_Body_name = preset_coll_name + "_BODY"
        if coll_Body_name in bpy.data.collections:
            coll_Body = bpy.data.collections[coll_Body_name]
        else:
            coll_Body = bpy.data.collections.new(coll_Body_name)
            coll_source.children.link(coll_Body)
        
        if use_proxy:
            coll_Proxy_name = preset_coll_name + "_PROXY"
            if coll_Proxy_name in bpy.data.collections:
                proxy_collection = bpy.data.collections[coll_Proxy_name]
            else:
                proxy_collection = bpy.data.collections.new(coll_Proxy_name)
                preset_collection = bpy.data.collections[preset_coll_name]
                preset_collection.children.link(proxy_collection)
            # proxy_collection.hide_viewport = True
    else:
        coll_Bone_name = "CMX_Bone"
        coll_Body_name = "CMX_Body"
        coll_Proxy_name = "CMX_Proxy"
        # Keep armatures hidden while Character Customize is still loading.
        bone_collection = bpy.data.collections.get(coll_Bone_name)
        if not bone_collection:
            bone_collection = bpy.data.collections.new(coll_Bone_name)
            bpy.context.scene.collection.children.link(bone_collection)
        bone_collection.hide_viewport = True
        # Keep proxy meshes hidden while Character Customize is still loading.
        proxy_collection = bpy.data.collections.get(coll_Proxy_name)
        if not proxy_collection:
            proxy_collection = bpy.data.collections.new(coll_Proxy_name)
            bpy.context.scene.collection.children.link(proxy_collection)
        proxy_collection.hide_viewport = True

    Item_bone_List = cmx_get_item_list(char_name, "Bone")
    if Item_bone_List:
        for item_bn in Item_bone_List:
            error = cmx_link_asset(char_name, "__Object__", item_bn, coll_Bone_name)
            if error:
                errors.append(error)

    # Apply the current animation as soon as the new armature is linked,
    # so the viewport does not flash back to the default pose during char swaps.
    if (
        not spawn_to_scene and
        bpy.context.window_manager.anim_use_toggle and
        bpy.context.window_manager.anim_previews
    ):
        try:
            cmx_link_action(bpy.context, is_applay=False)
        except Exception as e:
            errors.append(str(e))

    Item_body_List = cmx_get_item_list(char_name, "Body")
    if Item_body_List:
        for item_bd in Item_body_List:
            error = cmx_link_asset(char_name, "__Object__", item_bd, coll_Body_name)
            if error:
                errors.append(error)

    if use_proxy:
        Item_proxy_List = cmx_get_item_list(char_name, "Proxy")
        if Item_proxy_List:
            for item_px in Item_proxy_List:
                error = cmx_link_asset(char_name, "__Object__", item_px, coll_Proxy_name)
                if error:
                    errors.append(error)

    return errors

def cmx_Remove_character_rig(char_name):
    """
    Remove character rig by unlinking all assets in Body, Bone, and Proxy collections.
    """
    cmx_unlink_asset("CMX_Proxy")
    cmx_unlink_asset("CMX_Body")
    cmx_unlink_asset("CMX_Bone")

def cmx_override_character_rig(char_name, collection_name="", spawn_to_scene=False):
    """
    Create library overrides for all character assets in the given collections.
    """
    coll_Bone_name = collection_name
    coll_Body_name = collection_name + "_BODY"
    coll_Proxy_name = collection_name + "_PROXY"
    include_data_overrides = getattr(bpy.context.window_manager, "cf_mesh_mode", "MODULAR") != "SINGLE"

    Item_proxy_List = cmx_get_item_list(char_name, "Proxy")
    if Item_proxy_List:
        for item_px in Item_proxy_List:
            cmx_add_override_Item(item_px, coll_Proxy_name, include_data=include_data_overrides)

    Item_body_List = cmx_get_item_list(char_name, "Body")
    if Item_body_List:
        for item_bd in Item_body_List:
            cmx_add_override_Item(item_bd, coll_Body_name, include_data=include_data_overrides)

    Item_bone_List = cmx_get_item_list(char_name, "Bone")
    if Item_bone_List:
        for item_bn in Item_bone_List:
            cmx_add_override_Item(item_bn, coll_Bone_name, include_data=include_data_overrides)

def cmx_remove_all_asset_libraries():
    """
    Remove all linked asset libraries from the current Blender session.
    """
    for lib in bpy.data.libraries:
        print("libraries in scene : " + lib.name_full)
    for lb_name in ASSET_LIBR_EXIST:
        lb_name_file = lb_name + ".blend"
        lb_dat = bpy.data.libraries.get(lb_name_file)
        if lb_dat:
            bpy.data.libraries.remove(lb_dat)
            print("remove char libarie : " + lb_name_file)

def cmx_link_action(context, is_applay=False, spawn_to_scene=False, bone_coll_name="", act_name="", aim_filter=""):
    """
    Link animation action to the armature in the given collection.
    """
    if spawn_to_scene:
        char_coll_name = bone_coll_name
    else:
        char_coll_name = "CMX_Bone"
        if not aim_filter:
            aim_filter = context.window_manager.anim_filter
        if not act_name:
            act_name = str(context.window_manager.anim_previews).replace((aim_filter + "."), "")

    cmx_set_progress_task("Load Anim", act_name)

    # Animation folder stays at base asset path (not split by mesh mode)
    asset_directory = cmx_get_dir_asset_path()
    directory = os.path.join(asset_directory, "Animation")
    sub_directory = os.path.join(directory, aim_filter)
    blendfile = os.path.join(sub_directory, act_name + ".blend")    
    
    blend_dir_for_blender = blendfile + "/Action/"

    # print("aim_filter       :", aim_filter)
    # print("anim_previews    :", context.window_manager.anim_previews)
    # print("Dir for Blender  :", blend_dir_for_blender)
    # print("Filename         :", act_name)
    # print("-----------------")

    try:
        bpy.ops.wm.link(
            filename=act_name,
            directory=blend_dir_for_blender,
            instance_collections=False,
            link=True,
            autoselect=False
        )
    except Exception as e:
        print("Error to apply animation:", e)
        return

    act_lb_dat = bpy.data.actions.get(act_name)
    if not act_lb_dat:
        print(act_name + " : animation not exist.")
        return

    char_coll = bpy.data.collections.get(char_coll_name)
    if char_coll:
        for ob in char_coll.objects:
            if ob.type == 'ARMATURE':
                ob.animation_data_create()
                _cmx_store_default_pose_name(ob, ACTIVE_CHAR["Char_name"])
                ob.animation_data.action = act_lb_dat

    if not spawn_to_scene:
        set_f_range = context.window_manager.set_frame_range_toggle
        if set_f_range:
            bpy.context.scene.frame_start = int(act_lb_dat.frame_range[0])
            bpy.context.scene.frame_end = int(act_lb_dat.frame_range[1])

        ACTIVE_CHAR["Action"] = act_name
        ACTIVE_CHAR["Action_Filter"] = aim_filter

    if act_name not in ASSET_LIBR_EXIST:
        ASSET_LIBR_EXIST.append(act_name)

def cmx_unlink_action():
    """
    Unlink current action from the armature and restore default pose if available.
    """
    char_coll = bpy.data.collections.get("CMX_Bone")
    char_name = ACTIVE_CHAR.get("Char_name")
    default_pose_name = CMX_PUB_VAR.get("Default_Pose", {}).get(char_name) if char_name else None
    if char_coll:
        for ob in char_coll.objects:
            if ob.type == 'ARMATURE':
                if ob.animation_data:
                    if default_pose_name:
                        act = bpy.data.actions.get(default_pose_name)
                        if act:
                            ob.animation_data.action = act
                            continue
                    ob.animation_data.action = None
    ACTIVE_CHAR["Action"] = None
    ACTIVE_CHAR["Action_Filter"] = None

def cmx_link_asset(char_name, section, item_name, link_collection_name, spawn_to_scene=False):
    """
    Link an asset (object or collection) from an external .blend file into the current scene.
    """
    blendfile = cmx_get_character_blend_path(char_name)
    if not blendfile or not os.path.exists(blendfile):
        msg = f"Blend file not found for '{char_name}'"
        print(f"cmx_link_asset: {msg}")
        return msg
    directory = blendfile + section

    if not item_name:
        msg = "Item name is empty"
        print(f"cmx_link_asset: {msg}")
        return msg

    elif section == "__Object__":
        with bpy.data.libraries.load(blendfile, link=True) as (data_from, data_to):
            obj_names = list(data_from.objects)
            chosen_name = None

            # 1) exact
            if item_name in obj_names:
                chosen_name = item_name
            else:
                # 2) case-insensitive exact
                item_lower = str(item_name).lower()
                for nm in obj_names:
                    if nm.lower() == item_lower:
                        chosen_name = nm
                        break

            # 3) prefix/contains fallback (common when names have suffixes)
            if not chosen_name:
                for nm in obj_names:
                    nm_lower = nm.lower()
                    item_lower = str(item_name).lower()
                    if nm_lower.startswith(item_lower) or item_lower in nm_lower:
                        chosen_name = nm
                        break

            # 4) collection-kind heuristic fallback
            if not chosen_name and obj_names:
                coll_name_lower = str(link_collection_name).lower()
                if "bone" in coll_name_lower:
                    chosen_name = next((nm for nm in obj_names if "armature" in nm.lower()), None)
                elif "proxy" in coll_name_lower:
                    chosen_name = next((nm for nm in obj_names if "proxy" in nm.lower()), None)
                elif "body" in coll_name_lower:
                    chosen_name = next(
                        (nm for nm in obj_names if "armature" not in nm.lower() and "proxy" not in nm.lower()),
                        None
                    )
                if not chosen_name:
                    chosen_name = obj_names[0]

            if chosen_name:
                data_to.objects = [chosen_name]
            else:
                msg = f"Object '{item_name}' not found"
                print(f"cmx_link_asset: {msg} in '{blendfile}'")
                return msg
        
        if not data_to.objects:
            msg = f"Failed to link '{item_name}'"
            print(f"cmx_link_asset: {msg} from '{blendfile}'")
            return msg
        obj = data_to.objects[0]
        if obj:
            collection = bpy.data.collections.get(link_collection_name)
            if not collection:
                collection = bpy.data.collections.new(link_collection_name)
                bpy.context.scene.collection.children.link(collection)
            if obj.name not in collection.objects:
                collection.objects.link(obj)
        if spawn_to_scene:
            cmx_add_override_Item(item_name, link_collection_name)
        return None

    elif section == "__Collection__":
        char_coll_exist = bpy.data.collections.get(item_name)
        if char_coll_exist:
            return None
        else:
            bpy.context.view_layer.active_layer_collection = link_collection_name
            bpy.ops.wm.link(
                filename=item_name,
                directory=directory,
                instance_collections=False,
                link=True,
                autoselect=False,
                active_collection=True
            )
        return None

def cmx_unlink_asset(collection_name):
    """
    Unlink all objects from the specified collection and remove their overrides.
    """
    if collection_name not in bpy.data.collections:
        print(f"Collection '{collection_name}' not found.")
        return False
    collection = bpy.data.collections[collection_name]
    for obj in collection.objects:
        cmx_remove_override_Item(obj.name, collection_name)
    objects_to_unlink = list(collection.objects)
    for obj in objects_to_unlink:
        collection.objects.unlink(obj)

def cmx_link_asset_For_Crowd_Prop(context, library_filename, internal_item_name, crowd_item_name_for_path, data_block_type, relative_path_to_lib_dir=""):
    """
    Link asset (object or collection) for crowd prop usage with support for nested collections.
    """
    addon_prefs = context.preferences.addons[__package__].preferences
    asset_root_path = getattr(addon_prefs, 'folder_path', "")
    if not asset_root_path:
        print("Error: Addon asset folder_path not set in Preferences.")
        return None

    path_parts_for_join = [asset_root_path]
    if relative_path_to_lib_dir:
        path_parts_for_join.append(relative_path_to_lib_dir)
    path_parts_for_join.append(library_filename)
    full_library_path = os.path.normpath(os.path.join(*path_parts_for_join))

    if not os.path.exists(full_library_path):
        print(f"Error (cmx_link_asset_For_Crowd_Prop): Library file not found: {full_library_path}")
        return None

    base_coll = context.scene.collection
    cmx_crowds_coll = base_coll.children.get("CMX_Crowds") or bpy.data.collections.new("CMX_Crowds")
    if "CMX_Crowds" not in base_coll.children:
        base_coll.children.link(cmx_crowds_coll)

    crowd_specific_coll = cmx_crowds_coll.children.get(crowd_item_name_for_path) or bpy.data.collections.new(crowd_item_name_for_path)
    if crowd_item_name_for_path not in cmx_crowds_coll.children:
        cmx_crowds_coll.children.link(crowd_specific_coll)

    # target_prop_coll = crowd_specific_coll.children.get("Prop") or 
    target_prop_coll_name = f"{crowd_item_name_for_path}_Prop"
    target_prop_coll = crowd_specific_coll.children.get(target_prop_coll_name)
    if not target_prop_coll:
        target_prop_coll = bpy.data.collections.new(target_prop_coll_name)
        target_prop_coll.hide_render = True
        target_prop_coll.hide_viewport = True

    if target_prop_coll_name not in crowd_specific_coll.children:
        crowd_specific_coll.children.link(target_prop_coll)

    # loaded_data_block = None
    try:
        with bpy.data.libraries.load(full_library_path, link=True) as (data_from, data_to):
            if data_block_type == "EXTERNAL_FROM_ADDON_OBJECT":
                if internal_item_name in data_from.objects:
                    data_to.objects = [internal_item_name]
                else:
                    print(f"Error: Object '{internal_item_name}' not found in lib '{library_filename}'.")
                    return None
            elif data_block_type == "EXTERNAL_FROM_ADDON_COLLECTION":
                if internal_item_name in data_from.collections:
                    data_to.collections = [internal_item_name]
                else:
                    print(f"Error: Collection '{internal_item_name}' not found in lib '{library_filename}'.")
                    return None
            else:
                print(f"Error: Unknown data_block_type '{data_block_type}'.")
                return None
    except RuntimeError as e:
        print(f"RuntimeError loading lib '{full_library_path}': {e}")
        return None
    except Exception as e:
        print(f"General error loading lib '{full_library_path}': {e}")
        return None

    final_linked_item_for_modifier = None
    if data_block_type == "EXTERNAL_FROM_ADDON_OBJECT" and data_to.objects:
        linked_obj_blueprint = data_to.objects[0]
        existing_obj = next((obj for obj in target_prop_coll.objects if obj.name == linked_obj_blueprint.name and obj.library == linked_obj_blueprint.library), None)
        if existing_obj:
            final_linked_item_for_modifier = existing_obj
        else:
            target_prop_coll.objects.link(linked_obj_blueprint)
            final_linked_item_for_modifier = target_prop_coll.objects.get(linked_obj_blueprint.name)
    elif data_block_type == "EXTERNAL_FROM_ADDON_COLLECTION" and data_to.collections:
        linked_coll_blueprint = data_to.collections[0]
        instance_name = f"{linked_coll_blueprint.name}_inst"
        existing_instance = next((obj for obj in target_prop_coll.objects if obj.name == instance_name and obj.instance_type == 'COLLECTION' and obj.instance_collection == linked_coll_blueprint), None)
        if existing_instance:
            final_linked_item_for_modifier = existing_instance
        else:
            empty_instance = bpy.data.objects.new(instance_name, None)
            empty_instance.instance_type = 'COLLECTION'
            empty_instance.instance_collection = linked_coll_blueprint
            target_prop_coll.objects.link(empty_instance)
            final_linked_item_for_modifier = empty_instance

    return final_linked_item_for_modifier

def cmx_add_override_Item(object_name, collection_name, include_data=True):
    """
    Add library override for the given object and its data/materials.
    """
    object_item = cmx_get_object_in_collection(object_name, collection_name)
    if not object_item:
        return
    if not object_item.override_library:
        object_item.override_create(remap_local_usages=True)
    if include_data and object_item.type in {'MESH', 'ARMATURE'}:
        if object_item.data and not object_item.data.override_library:
            object_item.data.override_create(remap_local_usages=True)
    if include_data:
        for mat_sl in object_item.material_slots:
            mat = mat_sl.material
            if mat and mat.library and not mat.override_library:
                mat.override_create(remap_local_usages=True)

def cmx_remove_override_Item(object_name, collection_name):
    """
    Remove library override for the given object, data, and materials.
    """
    object_item = cmx_get_object_in_collection(object_name, collection_name)
    if not object_item:
        return
    if object_item.override_library:
        if object_item.type == 'MESH':
            if object_item.material_slots:
                for mat_sl in object_item.material_slots:
                    if mat_sl.material and mat_sl.material.override_library:
                        mat_sl.material.override_library.destroy(do_hierarchy=True)
            if object_item.data and object_item.data.override_library:
                object_item.data.override_library.destroy(do_hierarchy=True)
        object_item.override_library.destroy(do_hierarchy=True)

def cmx_add_override_all_active_item():
    """
    Add library override to all active items in ASSET_PREV_COLL collections.
    """
    for collection_name in ASSET_PREV_COLL:
        if collection_name in bpy.data.collections:
            collection = bpy.data.collections[collection_name]
            for obj in collection.objects:
                cmx_add_override_Item(obj.name, collection_name)

def cmx_remove_override_all_active_item():
    """
    Remove library override from all active items in ASSET_PREV_COLL collections.
    """
    for collection_name in ASSET_PREV_COLL:
        if collection_name in bpy.data.collections:
            collection = bpy.data.collections[collection_name]
            for obj in collection.objects:
                cmx_remove_override_Item(obj.name, collection_name)

def cmx_get_object_in_collection(object_name, collection_name):
    """
    Return the object with given name from a specific collection, or None if not found.
    """
    if collection_name not in bpy.data.collections:
        print(f"Collection '{collection_name}' not found.")
        return None
    collection = bpy.data.collections[collection_name]
    if object_name not in [obj.name for obj in collection.objects]:
        print(f"Object '{object_name}' not found in collection '{collection_name}'.")
        return None
    return collection.objects[object_name]

def cmx_get_assets_scene():
    """
    Return the main asset scene, creating it if necessary.
    """
    if CM_ASSETTS_SCENE in bpy.data.scenes:
        return bpy.data.scenes[CM_ASSETTS_SCENE]
    else:
        return bpy.data.scenes.new(CM_ASSETTS_SCENE)
