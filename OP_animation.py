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

import random
import os
from bpy.props import BoolProperty
from bpy.types import Operator
from .OP_link_asset import *
from .OP_common import *
from .system_var import STRIPS_LIST

def cmx_get_animation_dir():
    """Return the Animation directory inside the configured asset root."""
    asset_root = cmx_get_dir_asset_path()
    if not asset_root:
        return None
    return os.path.join(asset_root, "Animation")

def get_root_world_z(obj):
    # Return world Z of root bone (assume first bone)
    if obj and obj.type == 'ARMATURE':
        armature_data = obj.data
        if not armature_data.bones:
            return None
        root_bone = armature_data.bones[0]
        world_position = obj.matrix_world @ root_bone.head
        return world_position[2]
    return None

def _cmx_get_action_fcurves(anim_data):
    """Return F-Curves from legacy and slotted actions."""
    if not anim_data:
        return []

    action = getattr(anim_data, "action", None)
    if action is None:
        return []

    legacy_fcurves = getattr(action, "fcurves", None)
    if legacy_fcurves is not None:
        return list(legacy_fcurves)

    slot = getattr(anim_data, "action_slot", None)
    fcurves = []
    seen = set()

    for layer in getattr(action, "layers", []):
        for strip in getattr(layer, "strips", []):
            channel_bags = []

            if slot is not None and hasattr(strip, "channelbag"):
                try:
                    bag = strip.channelbag(slot, ensure=False)
                except TypeError:
                    try:
                        bag = strip.channelbag(slot)
                    except Exception:
                        bag = None
                except Exception:
                    bag = None
                if bag is not None:
                    channel_bags.append(bag)

            if not channel_bags:
                channel_bags.extend(list(getattr(strip, "channelbags", [])))

            for bag in channel_bags:
                for fcurve in getattr(bag, "fcurves", []):
                    curve_key = getattr(fcurve, "as_pointer", None)
                    curve_key = curve_key() if callable(curve_key) else id(fcurve)
                    if curve_key in seen:
                        continue
                    seen.add(curve_key)
                    fcurves.append(fcurve)

    return fcurves

def scale_root_location_keyframes(obj, scale_factor):
    # Scale all root location keyframes by scale_factor
    if obj.type == 'ARMATURE' and obj.animation_data and obj.animation_data.action:
        for fcurve in _cmx_get_action_fcurves(obj.animation_data):
            if fcurve.data_path.endswith("location"):
                for keyframe in fcurve.keyframe_points:
                    keyframe.co.y *= scale_factor
                    keyframe.handle_left.y *= scale_factor
                    keyframe.handle_right.y *= scale_factor

class CMXUpdateAnimationFromFBX(Operator):
    """
    Operator for batch updating animation FBX files and converting to .blend.
    Normalizes root animation scale.
    """
    bl_idname = "cmx.update_anim_fbx"
    bl_label = "Update requires an empty file. Proceeding may lose data."    

    def execute(self, context):     
        if not context.window_manager.cf_on_off_toggle:
            asset_root = cmx_get_dir_asset_path()
            anim_directory = cmx_get_animation_dir()
            BL_anim_List = []
            FBX_convert_List = []

            if not asset_root or not os.path.isdir(asset_root):
                cmx_show_message_box(
                    message="Asset folder not found. Please ensure the asset path is correct.",
                    title="update status",
                    icon='ERROR')
                return {'CANCELLED'}
            if not anim_directory or not os.path.isdir(anim_directory):
                cmx_show_message_box(
                    message="Animation folder not found in the selected asset folder.",
                    title="update status",
                    icon='ERROR')
                return {'CANCELLED'}

            for path, list_anim_filter_dir, list_file in os.walk(anim_directory):
                for anim_filter_dir in list_anim_filter_dir:
                    anim_filter_dir_path = os.path.join(path, anim_filter_dir)
                    BL_anim_List.clear()
                    for bl_anim_file in os.listdir(anim_filter_dir_path):
                        if bl_anim_file.lower().endswith(".blend"):
                            bl_anim_file_name = bl_anim_file.replace(".blend", "")
                            BL_anim_List.append(bl_anim_file_name)
                    for fbx_anim_file in os.listdir(anim_filter_dir_path):
                        if fbx_anim_file.lower().endswith(".fbx"):
                            fbx_anim_file_name = fbx_anim_file.replace(".fbx", "")
                            if fbx_anim_file_name not in BL_anim_List:
                                FBX_convert_List.append({
                                    "filename": fbx_anim_file_name,
                                    "file_path": anim_filter_dir_path
                                })
                break

            if FBX_convert_List:
                for obj in bpy.data.armatures:
                    bpy.data.armatures.remove(obj)
                for convert_file in FBX_convert_List:
                    fbx_filepath = os.path.join(
                        convert_file["file_path"],
                        convert_file["filename"] + ".fbx"
                    )
                    bpy.ops.import_scene.fbx(filepath=fbx_filepath)
                    # แก้ root scale ที่นี่
                    for obj in context.scene.objects:
                        if obj.type == 'ARMATURE':
                            # ปรับชื่อ action ตามเดิม
                            obj.animation_data.use_nla = True
                            action = obj.animation_data.action
                            if action is not None:
                                action.name = convert_file["filename"]

                            # === Normalize root scale ===
                            world_z = get_root_world_z(obj)
                            if world_z and abs(world_z) > 1e-6:
                                scale_factor = world_z / 0.01
                                if abs(scale_factor) > 1e-6:
                                    # ใช้ 1/scale_factor เพราะต้อง normalize ให้ root = 0.01
                                    scale_root_location_keyframes(obj, 1/scale_factor)

                    bl_filepath = os.path.join(
                        convert_file["file_path"],
                        convert_file["filename"] + ".blend"
                    )
                    bpy.ops.wm.save_as_mainfile(filepath=bl_filepath)
                    for am in bpy.data.armatures:
                        bpy.data.armatures.remove(am)
                    for act in bpy.data.actions:
                        bpy.data.actions.remove(act)
                msg = "Please Restart blender. You have {} Fbx file to update.".format(len(FBX_convert_List))
                cmx_show_message_box(message=msg, title="update status", icon='INFO')
            else:
                msg = "Not have FBX file to update"
                cmx_show_message_box(message=msg, title="update status", icon='INFO')
        else:
            msg = "please turn off Character Customize before update"
            cmx_show_message_box(message=msg, title="update status", icon='INFO')

        self.Confirm = False
        return {'FINISHED'}

    def invoke(self, context, event):
        asset_root = cmx_get_dir_asset_path()
        anim_directory = cmx_get_animation_dir()
        if not asset_root or not os.path.isdir(asset_root):
            cmx_show_message_box(
                message="Asset folder not found. Please ensure the asset path is correct.",
                title="Warning",
                icon='ERROR'
            )
            return {'CANCELLED'}
        if not anim_directory or not os.path.isdir(anim_directory):
            cmx_show_message_box(
                message="Animation folder not found in the selected asset folder.",
                title="Warning",
                icon='ERROR'
            )
            return {'CANCELLED'}

        # ใช้ confirm popup แบบ Yes/No
        return context.window_manager.invoke_confirm(self, event)

def cmx_apply_animation(self, context):
    """Apply or unlink animation depending on toggle state."""
    if CMX_PUB_VAR["is_loading_preset"]:
        return
    
    is_applay = True
    if context.window_manager.anim_use_toggle:
        cmx_link_action(context, is_applay)
    else:
        cmx_unlink_action()

def cmx_active_nla(source_coll_name):
    """
    Build STRIPS_LIST[source_coll_name] as list of (armature_name, track_name, strip_name)
    """
    import bpy
    source_coll = bpy.data.collections.get(source_coll_name)
    all_ob_in_coll = source_coll.all_objects if source_coll else []
    strips_list = []
    if source_coll and all_ob_in_coll:
        amature_list = [obj for obj in all_ob_in_coll if obj.type == 'ARMATURE']
        for am in amature_list:
            if am.animation_data and am.animation_data.nla_tracks:
                for trk in am.animation_data.nla_tracks:
                    for strip in trk.strips:
                        try:                            
                            _ = strip.id_data
                            strips_list.append((am.name, trk.name, strip.name))
                        except Exception as e:
                            print(f"Skip invalid strip: {e}")
            elif am.animation_data and am.animation_data.action:
                # auto create NLA track/strip หากจำเป็น
                track = am.animation_data.nla_tracks.new()
                strip = track.strips.new(am.animation_data.action.name, 1, am.animation_data.action)
                strip.repeat = 99
                am.animation_data.action = None
                strips_list.append((am.name, track.name, strip.name))
    STRIPS_LIST[source_coll_name] = strips_list

def build_strip_index(source_coll_name):
    """
    Build dict: {(armature_name, track_name, strip_name): strip_object}
    """
    import bpy
    index = {}
    source_coll = bpy.data.collections.get(source_coll_name)
    if not source_coll:
        return index
    for obj in source_coll.all_objects:
        if obj.type == "ARMATURE" and obj.animation_data and obj.animation_data.nla_tracks:
            arm_name = obj.name
            for trk in obj.animation_data.nla_tracks:
                trk_name = trk.name
                for strip in trk.strips:
                    strip_name = strip.name
                    try:
                        if (strip and hasattr(strip, "id_data")
                            and strip.id_data is not None
                            and hasattr(strip, "scale")
                            and isinstance(strip.scale, float)):
                            index[(arm_name, trk_name, strip_name)] = strip
                    except Exception:
                        continue
    return index

def safe_strips_list(source_coll_name):
    """
    Return [strip_obj, ...] จาก STRIPS_LIST ที่เป็นชื่อ
    """
    strips_name_list = STRIPS_LIST.get(source_coll_name, [])
    strip_index = build_strip_index(source_coll_name)
    result = []
    for key in strips_name_list:
        s = strip_index.get(key)
        if s:
            result.append(s)
    return result

def cmx_set_random_strat_frame_anim(self, context):
    """
    Randomizes NLA strips' frame_start based on self.start_frame and self.random_start.
    """
    source_item = self
    base_start_frame = source_item.start_frame
    max_random_offset = source_item.random_start
    if max_random_offset <= 0:
        return
    strip_index = build_strip_index(source_item.name)
    strips_name_list = STRIPS_LIST.get(source_item.name, [])
    for key in strips_name_list:
        st = strip_index.get(key)
        if not st:
            continue
        try:
            ran_num = random.randint(0, max_random_offset)
            frame_range = st.frame_end - st.frame_start
            st.frame_start = base_start_frame + ran_num
            st.frame_end = st.frame_start + frame_range
        except Exception as e:
            print("Random frame error:", e)
    bpy.context.view_layer.update()

def cmx_set_random_speed_anim_min(self, context):
    source_item = self
    base_anim_speed = source_item.anim_speed
    speed_variation_range = source_item.random_speed
    if speed_variation_range <= 0 or base_anim_speed <= 0:
        return
    strip_index = build_strip_index(source_item.name)
    strips_name_list = STRIPS_LIST.get(source_item.name, [])
    for key in strips_name_list:
        strip = strip_index.get(key)
        if not strip:
            continue
        try:
            random_offset = random.uniform(-speed_variation_range, speed_variation_range)
            final_speed = max(0.01, base_anim_speed + random_offset)
            strip.scale = 1.0 / final_speed
        except Exception as e:
            print("Random speed error:", e)
    bpy.context.view_layer.update()

def cmx_update_source_start_frame(self, context):
    source_item = self
    base_frame = source_item.start_frame
    strip_index = build_strip_index(source_item.name)
    strips_name_list = STRIPS_LIST.get(source_item.name, [])
    for key in strips_name_list:
        strip = strip_index.get(key)
        if not strip:
            continue
        try:
            strip.frame_start = base_frame
        except Exception as e:
            print("Set frame_start error:", e)
    cmx_set_random_strat_frame_anim(self, context)

def cmx_update_source_anim_speed(self, context):
    source_item = self
    base_speed = getattr(source_item, "anim_speed", None)
    if not base_speed or base_speed <= 0:
        return
    base_scale = 1.0 / base_speed   
    strip_index = build_strip_index(source_item.name)
    strips_name_list = STRIPS_LIST.get(source_item.name, [])
    for key in strips_name_list:
        strip = strip_index.get(key)
        if not strip:
            continue
        try:
            strip.scale = base_scale
        except Exception as e:
            print("Set scale error:", e)
    try:
        cmx_set_random_speed_anim_min(self, context)
    except Exception as e:
        print(f"cmx_set_random_speed_anim_min error: {e}")

def safe_strips_list(strips):
    safe = []
    for s in strips:
        try:            
            _ = repr(s)
            if (
                s is not None
                and hasattr(s, "id_data")
                and s.id_data is not None
                and hasattr(s, "scale")
                and isinstance(s.scale, float)
            ):
                safe.append(s)
        except Exception as e:
            print("Skip unsafe strip:", e)
    return safe

def cmx_update_offset_to_instance(self, context):
    """
    Update instance collection NLA strip offset from WindowManager property.
    """
    obj = context.active_object
    if obj and obj.instance_type == 'COLLECTION':
        offset = context.window_manager.offset_start_frame_ins
        src_coll = obj.instance_collection
        if not src_coll:
            return
        for armature_obj in src_coll.objects:
            if armature_obj.type == 'ARMATURE':
                if armature_obj.animation_data and armature_obj.animation_data.nla_tracks:
                    for track in armature_obj.animation_data.nla_tracks:
                        for strip in track.strips:
                            strip.frame_start = offset
        bpy.context.view_layer.update()
        bpy.context.scene.frame_set(bpy.context.scene.frame_current)

def cmx_update_anim_speed_to_instance(self, context):
    """
    Update instance collection NLA strip speed from WindowManager property.
    """
    obj = context.active_object
    if obj and obj.instance_type == 'COLLECTION':
        anim_speed = context.window_manager.set_anim_speed_ins
        if anim_speed <= 0:
            return
        new_strip_scale = 1.0 / anim_speed
        src_coll = obj.instance_collection
        if not src_coll:
            return
        for armature_obj in src_coll.objects:
            if armature_obj.type == 'ARMATURE':
                if armature_obj.animation_data and armature_obj.animation_data.nla_tracks:
                    for track in armature_obj.animation_data.nla_tracks:
                        for strip in track.strips:
                            if hasattr(strip, "scale"):
                                strip.scale = new_strip_scale
        bpy.context.view_layer.update()
        bpy.context.scene.frame_set(bpy.context.scene.frame_current)

classes = [
    CMXUpdateAnimationFromFBX
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
