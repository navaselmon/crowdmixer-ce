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
import math
import json
import subprocess
import tempfile
import textwrap
from mathutils import Matrix, Vector
from bpy.types import Operator
from bpy.props import BoolProperty, StringProperty
from .system_var import *
from .OP_common import *
from .OP_crowd import *
from .enum_item_gen import cmx_anim_preview_item

original_bone_names = {}

CMX_ANIM_PREVIEW_IMAGE_EXTS = (
    ".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff",
    ".tga", ".jp2", ".exr", ".hdr", ".dpx", ".cin",
)
CMX_RENDER_IMAGE_EXTENSIONS = {
    "BMP": ".bmp",
    "PNG": ".png",
    "JPEG": ".jpg",
    "JPEG2000": ".jp2",
    "TARGA": ".tga",
    "TARGA_RAW": ".tga",
    "CINEON": ".cin",
    "DPX": ".dpx",
    "OPEN_EXR": ".exr",
    "OPEN_EXR_MULTILAYER": ".exr",
    "HDR": ".hdr",
    "TIFF": ".tif",
    "WEBP": ".webp",
}

# =========================================================
# Hook helper for Creator tool
# =========================================================

CMX_HOOK_MOD_NAME = "CMX_Hook_Helper"
CMX_HOOK_VGROUP = "CMX_HOOK_FALLOFF"
CMX_HOOK_DEBUG_MAT = "CMX_Hook_Falloff_Debug"
CMX_SEPARATE_ACTION_SCRIPT = textwrap.dedent("""\
import bpy
import os
import sys


def _find_armature(name):
    obj = bpy.data.objects.get(name)
    if obj and obj.type == 'ARMATURE':
        return obj
    armatures = [item for item in bpy.data.objects if item.type == 'ARMATURE']
    if len(armatures) == 1:
        return armatures[0]
    return None


def _clear_animation_users(target_armature):
    for obj in bpy.data.objects:
        anim_data = getattr(obj, "animation_data", None)
        if not anim_data:
            continue
        if obj.type == 'ARMATURE':
            for track in list(anim_data.nla_tracks):
                try:
                    anim_data.nla_tracks.remove(track)
                except Exception:
                    pass
        if obj != target_armature:
            try:
                anim_data.action = None
            except Exception:
                pass


def main():
    argv = sys.argv
    if "--" not in argv:
        raise RuntimeError("Missing arguments")
    action_name, output_path, armature_name = argv[argv.index("--") + 1:argv.index("--") + 4]

    action = bpy.data.actions.get(action_name)
    if action is None:
        raise RuntimeError(f"Action not found: {action_name}")

    armature = _find_armature(armature_name)
    if armature is None:
        raise RuntimeError("Target armature not found")

    _clear_animation_users(armature)

    if armature.animation_data is None:
        armature.animation_data_create()
    armature.animation_data.action = action

    frame_start, frame_end = action.frame_range
    scene = bpy.context.scene
    scene.frame_start = int(frame_start)
    scene.frame_end = max(int(frame_start), int(frame_end))

    for other_action in list(bpy.data.actions):
        if other_action.name == action_name:
            continue
        try:
            other_action.use_fake_user = False
        except Exception:
            pass
        bpy.data.actions.remove(other_action)

    try:
        bpy.ops.outliner.orphans_purge(do_recursive=True)
    except Exception:
        pass

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=output_path)


if __name__ == "__main__":
    main()
""")


def _cmx_hook_get_empty_name(obj, index):
    return f"{obj.name}_Hook_{index:03d}"


def _cmx_get_target_armature(context):
    obj = context.view_layer.objects.active
    if obj and obj.type == 'ARMATURE':
        return obj

    armatures = [item for item in context.scene.objects if item.type == 'ARMATURE']
    if len(armatures) == 1:
        return armatures[0]
    return None


def _cmx_unique_action_filepath(directory, action_name, used_names):
    safe_name = bpy.path.clean_name(action_name) or "Action"
    file_stem = safe_name
    suffix = 1
    while file_stem.lower() in used_names:
        file_stem = f"{safe_name}_{suffix:03d}"
        suffix += 1
    used_names.add(file_stem.lower())
    return os.path.join(directory, f"{file_stem}.blend")


def _cmx_is_armature_action(action):
    fcurves = getattr(action, "fcurves", None)
    if not fcurves:
        return True

    object_paths = {
        "location",
        "rotation_euler",
        "rotation_quaternion",
        "rotation_axis_angle",
        "scale",
        "delta_location",
        "delta_rotation_euler",
        "delta_rotation_quaternion",
        "delta_scale",
    }
    for fcurve in fcurves:
        data_path = getattr(fcurve, "data_path", "")
        if data_path.startswith('pose.bones["') or data_path in object_paths:
            return True
    return False


def _cmx_get_anim_render_extension(scene):
    """Return the file extension for the current scene image format, if supported."""
    image_format = getattr(scene.render.image_settings, "file_format", "")
    return CMX_RENDER_IMAGE_EXTENSIONS.get(image_format)


def _cmx_find_existing_anim_preview(anim_directory, anim_name):
    """Return an existing preview image path matching the animation name."""
    if not anim_directory or not anim_name or not os.path.isdir(anim_directory):
        return None
    target_lower = anim_name.lower()
    for file_name in os.listdir(anim_directory):
        stem, ext = os.path.splitext(file_name)
        if stem.lower() == target_lower and ext.lower() in CMX_ANIM_PREVIEW_IMAGE_EXTS:
            return os.path.join(anim_directory, file_name)
    return None


def _cmx_refresh_anim_preview_cache(context):
    """Clear animation preview cache so newly rendered images appear immediately."""
    ANIM_PREV_EXIST.clear()
    ANIM_SET.clear()
    anim_pcoll = PREVIEW_COLL.get("Anim")
    if anim_pcoll:
        try:
            anim_pcoll.clear()
        except Exception:
            pass
        anim_pcoll.anim_previews = ()
        anim_pcoll.anim_filter = ""
    try:
        enum_items = cmx_anim_preview_item(None, context)
        if enum_items:
            current_id = context.window_manager.anim_previews
            valid_ids = [item[0] for item in enum_items]
            if current_id not in valid_ids:
                context.window_manager.anim_previews = enum_items[0][0]
    except Exception:
        pass
    try:
        for area in context.screen.areas:
            area.tag_redraw()
    except Exception:
        pass


def _cmx_hook_ensure_empty(context, name):
    """Create/reuse an empty at the 3D cursor for hook control."""
    empty = bpy.data.objects.get(name)
    if not empty:
        empty = bpy.data.objects.new(name, None)
        empty.empty_display_type = 'CUBE'
        empty.empty_display_size = 0.1
        empty.show_in_front = True
        context.scene.collection.objects.link(empty)
    # keep it at cursor on creation; user can move later
    empty.location = context.scene.cursor.location.copy()
    return empty


def _cmx_next_hook_index(obj):
    existing = [m for m in obj.modifiers if m.type == 'HOOK' and m.name.startswith(CMX_HOOK_MOD_NAME)]
    return len(existing) + 1


def _cmx_first_hook(obj):
    """Return first CMX hook modifier on object, if any."""
    for m in obj.modifiers:
        if m.type == 'HOOK' and m.name.startswith(CMX_HOOK_MOD_NAME):
            return m
    return None


def _cmx_hook_assign_vertices(obj, hook_mod):
    """Assign all vertices to the hook modifier (use API if available, else operator fallback)."""
    mesh = obj.data
    if hasattr(hook_mod, "vertex_indices_set"):
        try:
            hook_mod.vertex_indices_set([v.index for v in mesh.vertices])
            return
        except Exception:
            pass
    view_layer = bpy.context.view_layer
    prev_active = view_layer.objects.active
    prev_selected = list(bpy.context.selected_objects)
    prev_mode = getattr(obj, "mode", "OBJECT")
    try:
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.object.hook_assign(modifier=hook_mod.name)
        bpy.ops.mesh.select_all(action='DESELECT')
    except Exception:
        pass
    finally:
        try:
            bpy.ops.object.mode_set(mode=prev_mode)
        except Exception:
            pass
        try:
            bpy.ops.object.select_all(action='DESELECT')
        except Exception:
            pass
        for o in prev_selected:
            try:
                o.select_set(True)
            except Exception:
                pass
        try:
            view_layer.objects.active = prev_active
        except Exception:
            pass


def _cmx_reset_hook(obj, hook_mod):
    """Reset hook offset so it controls from the current empty position (no manual assign/reset needed)."""
    view_layer = bpy.context.view_layer
    prev_active = view_layer.objects.active
    prev_selected = list(bpy.context.selected_objects)
    prev_mode = getattr(obj, "mode", "OBJECT")
    try:
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.object.hook_reset(modifier=hook_mod.name)
        bpy.ops.mesh.select_all(action='DESELECT')
    except Exception:
        pass
    finally:
        try:
            bpy.ops.object.mode_set(mode=prev_mode)
        except Exception:
            pass
        try:
            bpy.ops.object.select_all(action='DESELECT')
        except Exception:
            pass
        for o in prev_selected:
            try:
                o.select_set(True)
            except Exception:
                pass
        try:
            view_layer.objects.active = prev_active
        except Exception:
            pass


def _cmx_recenter_hook(obj, hook_mod):
    """Run Hook Recenter (center empty to selected verts)."""
    view_layer = bpy.context.view_layer
    prev_active = view_layer.objects.active
    prev_selected = list(bpy.context.selected_objects)
    prev_mode = getattr(obj, "mode", "OBJECT")
    try:
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.object.hook_recenter(modifier=hook_mod.name)
        bpy.ops.mesh.select_all(action='DESELECT')
    except Exception:
        pass
    finally:
        try:
            bpy.ops.object.mode_set(mode=prev_mode)
        except Exception:
            pass
        try:
            bpy.ops.object.select_all(action='DESELECT')
        except Exception:
            pass
        for o in prev_selected:
            try:
                o.select_set(True)
            except Exception:
                pass
        try:
            view_layer.objects.active = prev_active
        except Exception:
            pass


def _cmx_rebuild_hook_weights(obj, empty, radius):
    """Write a vertex group matching hook falloff for debug shading."""
    if not obj or not obj.data:
        return None
    if radius <= 0:
        radius = 0.0001
    vg = obj.vertex_groups.get(CMX_HOOK_VGROUP)
    if not vg:
        vg = obj.vertex_groups.new(name=CMX_HOOK_VGROUP)
    empty_loc = empty.matrix_world.translation
    obj_mat = obj.matrix_world
    for v in obj.data.vertices:
        world_co = obj_mat @ v.co
        dist = (world_co - empty_loc).length
        weight = max(0.0, 1.0 - (dist / radius))
        vg.add([v.index], weight, 'REPLACE')
    return vg


def _cmx_hook_debug_material():
    mat = bpy.data.materials.get(CMX_HOOK_DEBUG_MAT)
    if not mat:
        mat = bpy.data.materials.new(CMX_HOOK_DEBUG_MAT)
    mat.use_nodes = True
    nt = mat.node_tree
    nodes = nt.nodes
    links = nt.links
    nodes.clear()
    attr = nodes.new("ShaderNodeAttribute")
    attr.attribute_name = CMX_HOOK_VGROUP
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (0.0, 0.5, 1.0, 1.0)
    ramp.color_ramp.elements[1].color = (1.0, 0.2, 0.0, 1.0)
    emit = nodes.new("ShaderNodeEmission")
    emit.inputs["Strength"].default_value = 2.0
    out = nodes.new("ShaderNodeOutputMaterial")
    links.new(attr.outputs["Fac"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], emit.inputs["Color"])
    links.new(emit.outputs["Emission"], out.inputs["Surface"])
    # Some Blender versions expose these on Material; guard for compatibility
    try:
        mat.shadow_method = 'NONE'
    except Exception:
        pass
    try:
        mat.blend_method = 'OPAQUE'
    except Exception:
        pass
    return mat


def _cmx_apply_hook_debug_material(obj):
    """Assign debug material to all slots while backing up originals."""
    mat = _cmx_hook_debug_material()
    slots = obj.material_slots
    backup = [slot.material.name if slot.material else "" for slot in slots] if slots else []
    obj["_cmx_hook_mat_backup"] = "|".join(backup)
    if not slots:
        obj.data.materials.append(mat)
    else:
        for slot in slots:
            slot.material = mat


def _cmx_restore_hook_materials(obj):
    backup_str = obj.get("_cmx_hook_mat_backup")
    if backup_str is None:
        return
    backup = backup_str.split("|") if backup_str else []
    slots = obj.material_slots
    for idx, name in enumerate(backup):
        mat = bpy.data.materials.get(name) if name else None
        if idx < len(slots):
            slots[idx].material = mat
        elif mat:
            obj.data.materials.append(mat)
    if "_cmx_hook_mat_backup" in obj:
        del obj["_cmx_hook_mat_backup"]


def _cmx_enable_hook_preview(context, obj, radius, create_new=False, target_empty=None, target_mod=None, recenter_on_create=False):
    """Create or refresh a hook modifier + empty. Supports multiple hooks."""
    hook = None
    empty = None

    if target_mod:
        hook = obj.modifiers.get(target_mod)
    if target_empty:
        empty = target_empty
    if not hook and not create_new:
        hook = _cmx_first_hook(obj)
        empty = hook.object if hook else None

    if create_new or not hook:
        idx = _cmx_next_hook_index(obj)
        hook_name = f"{CMX_HOOK_MOD_NAME}_{idx:03d}"
        empty_name = _cmx_hook_get_empty_name(obj, idx)
        hook = obj.modifiers.get(hook_name)
        if not hook:
            hook = obj.modifiers.new(hook_name, type='HOOK')
        empty = _cmx_hook_ensure_empty(context, empty_name)

    # Link both ways for later falloff edits when selecting the empty
    empty["_cmx_hook_target_obj"] = obj.name
    empty["_cmx_hook_mod_name"] = hook.name

    hook.object = empty
    hook.use_falloff_uniform = True
    hook.falloff_radius = radius
    _cmx_hook_assign_vertices(obj, hook)
    _cmx_rebuild_hook_weights(obj, empty, radius)  # for debug shader only
    hook.show_viewport = True
    hook.show_render = True
    if recenter_on_create:
        _cmx_recenter_hook(obj, hook)
    _cmx_apply_hook_debug_material(obj)
    return hook, empty


def _cmx_disable_hook_preview(obj):
    hooks = [m for m in obj.modifiers if m.type == 'HOOK' and m.name.startswith(CMX_HOOK_MOD_NAME)]
    for hook in hooks:
        hook.show_viewport = False
        hook.show_render = False
    _cmx_restore_hook_materials(obj)


def cmx_toggle_hook_preview(self, context):
    """WindowManager update: toggle hook preview on the active mesh."""
    obj = context.object
    radius = getattr(context.window_manager, "cmx_hook_falloff", 0.5)
    if getattr(context.window_manager, "cmx_hook_preview_toggle", False):
        # If an empty is active and linked, update its target; else use active mesh
        if obj and obj.type == 'EMPTY' and obj.get("_cmx_hook_target_obj"):
            target = bpy.data.objects.get(obj.get("_cmx_hook_target_obj"))
            mod_name = obj.get("_cmx_hook_mod_name")
            if target and target.type == 'MESH':
                _cmx_enable_hook_preview(context, target, radius, create_new=False, target_empty=obj, target_mod=mod_name, recenter_on_create=False)
            return
        if obj and obj.type == 'MESH':
            _cmx_enable_hook_preview(context, obj, radius, create_new=False, recenter_on_create=False)
    else:
        if obj and obj.type == 'MESH':
            _cmx_disable_hook_preview(obj)


def cmx_update_hook_falloff(self, context):
    """WindowManager update: adjust falloff radius + weights for active mesh hook."""
    obj = context.object
    radius = max(0.0001, getattr(context.window_manager, "cmx_hook_falloff", 0.5))

    # If an empty is active and linked, drive its paired modifier
    if obj and obj.type == 'EMPTY' and obj.get("_cmx_hook_target_obj"):
        target = bpy.data.objects.get(obj.get("_cmx_hook_target_obj"))
        mod_name = obj.get("_cmx_hook_mod_name")
        if target and target.type == 'MESH' and mod_name:
            _cmx_enable_hook_preview(context, target, radius, create_new=False, target_empty=obj, target_mod=mod_name, recenter_on_create=False)
        return

    # Otherwise, update the active mesh (first CMX hook)
    if obj and obj.type == 'MESH':
        _cmx_enable_hook_preview(context, obj, radius, create_new=False, recenter_on_create=False)


class CMXCreateHookWithEmptyOperator(Operator):
    """Create a hook modifier tied to a helper empty at the 3D cursor."""
    bl_idname = "cmx.create_hook_with_empty"
    bl_label = "Create Hook (Cursor)"

    def execute(self, context):
        obj = context.object
        if not obj or obj.type != 'MESH':
            self.report({'WARNING'}, "Active object must be a mesh to add a hook.")
            return {'CANCELLED'}
        radius = getattr(context.window_manager, "cmx_hook_falloff", 0.5)
        _cmx_enable_hook_preview(context, obj, radius, create_new=True, recenter_on_create=True)
        # turn on preview toggle so the UI reflects current state but without creating another hook
        context.window_manager.cmx_hook_preview_toggle = True
        self.report({'INFO'}, "Hook modifier + helper empty created.")
        return {'FINISHED'}


# =========================================================
# Temporary Rest Pose Bind Utilities
# =========================================================

def _cmx_find_active_armature(context):
    obj = context.object
    if obj and obj.type == 'ARMATURE':
        return obj
    # Fallback: find first selected armature
    for o in context.selected_objects:
        if o.type == 'ARMATURE':
            return o
    return None

# Ensure armature scale is (1,1,1); if not, apply scale transform safely and restore selection/active state.
def _cmx_apply_scale_if_needed(context, obj, eps=1e-4):
    sc = obj.scale
    if abs(sc.x - 1) < eps and abs(sc.y - 1) < eps and abs(sc.z - 1) < eps:
        return False
    view_layer = context.view_layer
    prev_active = view_layer.objects.active
    prev_selected = [o for o in context.selected_objects]
    prev_mode = getattr(obj, "mode", None)
    try:
        try:
            bpy.ops.object.select_all(action='DESELECT')
        except Exception:
            pass
        try:
            obj.select_set(True)
            view_layer.objects.active = obj
        except Exception:
            pass
        if prev_mode and obj.mode != 'OBJECT':
            try:
                bpy.ops.object.mode_set(mode='OBJECT')
            except Exception:
                pass
        try:
            bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        except Exception:
            pass
    finally:
        # restore selection/active
        try:
            bpy.ops.object.select_all(action='DESELECT')
        except Exception:
            pass
        for o in prev_selected:
            try:
                o.select_set(True)
            except Exception:
                pass
        try:
            view_layer.objects.active = prev_active
        except Exception:
            pass
        # restore mode on obj if needed
        if prev_mode and obj.mode != prev_mode:
            try:
                bpy.ops.object.mode_set(mode=prev_mode)
            except Exception:
                pass
    return True

# (old rest/pose property helpers removed)

def _cmx_clear_pose_transforms(arm_obj):
    prev_mode = arm_obj.mode
    if prev_mode != 'POSE':
        bpy.ops.object.mode_set(mode='POSE')
    try:
        bpy.ops.pose.select_all(action='SELECT')
        bpy.ops.pose.rot_clear()
        bpy.ops.pose.loc_clear()
        bpy.ops.pose.scale_clear()
        bpy.ops.pose.select_all(action='DESELECT')
    finally:
        if prev_mode != 'POSE':
            bpy.ops.object.mode_set(mode=prev_mode)

# =========================================================
# (old pose property helpers removed)

# (old corrective shape key helpers removed)

def _cmx_bone_topo_order(arm_obj):
    bones = arm_obj.data.bones
    order = []
    def visit(b):
        order.append(b)
        for c in b.children:
            visit(c)
    roots = [b for b in bones if b.parent is None]
    for r in roots:
        visit(r)
    return [b.name for b in order]

# (old absolute pose property helpers removed)

def _cmx_apply_abs_pose_under_current_rest(arm_obj, data):
    # Build rest local matrices from current rest
    rest_local = {}
    for b in arm_obj.data.bones:
        if b.parent:
            rest_local[b.name] = b.parent.matrix_local.inverted() @ b.matrix_local
        else:
            rest_local[b.name] = b.matrix_local.copy()
    # Helper to get target matrix from saved data
    def to_matrix(flat):
        return Matrix(((flat[0], flat[1], flat[2], flat[3]),
                       (flat[4], flat[5], flat[6], flat[7]),
                       (flat[8], flat[9], flat[10], flat[11]),
                       (flat[12], flat[13], flat[14], flat[15])))
    # Ensure POSE mode
    prev_mode = arm_obj.mode
    if prev_mode != 'POSE':
        try:
            bpy.ops.object.mode_set(mode='POSE')
        except Exception:
            pass
    try:
        order = _cmx_bone_topo_order(arm_obj)
        # Track parent resulting pose to compute children
        result_pose = {}
        for name in order:
            pb = arm_obj.pose.bones.get(name)
            if not pb:
                continue
            # Determine parent pose matrix to use
            parent = pb.parent
            if parent:
                M_parent = result_pose.get(parent.name)
                if M_parent is None:
                    # Fallback to current parent pose
                    M_parent = parent.matrix.copy()
            else:
                M_parent = Matrix.Identity(4)
            # Get target pose for this bone
            flat = data.get(name)
            if not flat:
                # Keep current
                result_pose[name] = pb.matrix.copy()
                continue
            M_target = to_matrix(flat)
            R_local = rest_local.get(name, Matrix.Identity(4))
            # Solve for basis in bone local space
            try:
                M_basis = R_local.inverted() @ M_parent.inverted() @ M_target
                # Decompose to loc/rot/scale toรักษาการยืด (stretch)
                loc, rot, sca = M_basis.decompose()
                # Apply rotation to the proper mode
                if pb.rotation_mode == 'QUATERNION':
                    pb.rotation_quaternion = rot
                elif pb.rotation_mode == 'AXIS_ANGLE':
                    axis, angle = rot.to_axis_angle()
                    pb.rotation_axis_angle[0] = angle
                    pb.rotation_axis_angle[1] = axis.x
                    pb.rotation_axis_angle[2] = axis.y
                    pb.rotation_axis_angle[3] = axis.z
                else:
                    pb.rotation_euler = rot.to_euler(pb.rotation_mode)
                # Location and Scale
                pb.location = loc
                pb.scale = sca
            except Exception:
                pass
            # Store resulting pose after assignment
            result_pose[name] = pb.matrix.copy()
    finally:
        if prev_mode != 'POSE':
            try:
                bpy.ops.object.mode_set(mode=prev_mode)
            except Exception:
                pass

def _cmx_apply_saved_rest_as_pose_safe(arm_obj, data):
    # Ensure we are in pose position (not REST display)
    try:
        arm_obj.data.pose_position = 'POSE'
    except Exception:
        pass
    # Temporarily mute constraints and unlock transforms while applying
    constraint_states = {}
    lock_states = {}
    for pb in arm_obj.pose.bones:
        states = []
        for c in pb.constraints:
            states.append((c, c.mute))
            c.mute = True
        if states:
            constraint_states[pb.name] = states
        lock_states[pb.name] = (
            tuple(getattr(pb, 'lock_location', (False, False, False))),
            tuple(getattr(pb, 'lock_rotation', (False, False, False))),
            getattr(pb, 'lock_rotation_w', False),
            getattr(pb, 'lock_rotations_4d', False),
            tuple(getattr(pb, 'lock_scale', (False, False, False))),
        )
        try:
            pb.lock_location = (False, False, False)
            pb.lock_rotation = (False, False, False)
            pb.lock_rotation_w = False
            pb.lock_rotations_4d = False
            pb.lock_scale = (False, False, False)
        except Exception:
            pass
    try:
        _cmx_clear_pose_transforms(arm_obj)
        _cmx_apply_abs_pose_under_current_rest(arm_obj, data)
    finally:
        for pb_name, states in constraint_states.items():
            for c, muted in states:
                try:
                    c.mute = muted
                except Exception:
                    pass
        for pb_name, locks in lock_states.items():
            pb = arm_obj.pose.bones.get(pb_name)
            if not pb:
                continue
            try:
                loc, rot, rot_w, rot4d, sca = locks
                pb.lock_location = loc
                pb.lock_rotation = rot
                pb.lock_rotation_w = rot_w
                pb.lock_rotations_4d = rot4d
                pb.lock_scale = sca
            except Exception:
                pass

def _cmx_copy_armature_for_snap(arm_obj):
    dup = arm_obj.copy()
    dup.data = arm_obj.data.copy()
    dup.name = f"{arm_obj.name}_CMX_SNAP_REF"
    dup.matrix_world = arm_obj.matrix_world.copy()
    # Link into a hidden helper collection
    try:
        snap_coll = bpy.data.collections.get("CMX_SnapRef")
        if not snap_coll:
            snap_coll = bpy.data.collections.new("CMX_SnapRef")
            bpy.context.scene.collection.children.link(snap_coll)
        snap_coll.objects.link(dup)
        snap_coll.hide_viewport = True
    except Exception:
        # fallback to scene root
        try:
            bpy.context.scene.collection.objects.link(dup)
        except Exception:
            pass
    # Make it unobtrusive
    try:
        dup.display_type = 'WIRE'
    except Exception:
        pass
    dup.show_in_front = True
    dup.hide_render = True
    try:
        dup.hide_set(True)
    except Exception:
        pass
    # Freeze reference: force POSE position and mute all constraints so it won't follow anything
    try:
        dup.data.pose_position = 'POSE'
    except Exception:
        pass
    for pb in dup.pose.bones:
        for c in pb.constraints:
            try:
                c.mute = True
            except Exception:
                pass
    # Remember reference name on original
    arm_obj["cmx_snap_ref_obj"] = dup.name
    return dup

def _cmx_build_abs_pose_from_editbones(arm_obj):
    """Collect absolute matrices (armature space) from current edit bones."""
    data = {}
    prev_mode = arm_obj.mode
    switched = False
    try:
        if prev_mode != 'EDIT':
            bpy.context.view_layer.objects.active = arm_obj
            bpy.ops.object.mode_set(mode='EDIT')
            switched = True
        for eb in arm_obj.data.edit_bones:
            try:
                m = eb.matrix.copy()
                data[eb.name] = [f for r in m for f in r]
            except Exception:
                pass
    finally:
        if switched:
            try:
                bpy.ops.object.mode_set(mode=prev_mode)
            except Exception:
                pass
    return data

def _cmx_find_snap_ref_for(arm_obj):
    ref_name = arm_obj.get("cmx_snap_ref_obj")
    if ref_name:
        return bpy.data.objects.get(ref_name)
    return None

def _cmx_build_abs_pose_from_armature(src_arm, dst_arm):
    """Build absolute pose matrices for dst_arm space using src_arm pose but aligned to dst rest pose."""
    data = {}
    prev_pose_pos = getattr(src_arm.data, "pose_position", 'POSE')
    try:
        # Force display in POSE position so pb.matrix reflects actual pose, not rest
        if prev_pose_pos != 'POSE':
            src_arm.data.pose_position = 'POSE'
        for pb in src_arm.pose.bones:
            try:
                dst_bone = dst_arm.data.bones.get(pb.name)
                if not dst_bone:
                    continue
                # Pose relative to source rest
                src_rest = pb.bone.matrix_local
                delta = src_rest.inverted() @ pb.matrix
                # Apply same delta on destination rest
                dst_rest = dst_bone.matrix_local
                M_dst = dst_rest @ delta
                data[pb.name] = [f for r in M_dst for f in r]
            except Exception:
                pass
    finally:
        if getattr(src_arm.data, "pose_position", 'POSE') != prev_pose_pos:
            try:
                src_arm.data.pose_position = prev_pose_pos
            except Exception:
                pass
    return data

def _cmx_bone_names_topo(arm_obj):
    names = []
    def visit(b):
        names.append(b.name)
        for c in b.children:
            visit(c)
    for r in [b for b in arm_obj.data.bones if b.parent is None]:
        visit(r)
    return names

def _cmx_snap_edit_bones_from_reference(target_arm, ref_arm):
    """Snap target edit bones by matching only head/tail to reference.
    Does not touch scale; avoids matrix/roll changes unless required by connection constraints.
    """
    # Transform from reference armature space -> target armature space
    T = target_arm.matrix_world.inverted() @ ref_arm.matrix_world
    prev_mode = target_arm.mode
    if prev_mode != 'EDIT':
        try:
            bpy.context.view_layer.objects.active = target_arm
            bpy.ops.object.mode_set(mode='EDIT')
        except Exception:
            pass
    try:
        order = _cmx_bone_names_topo(ref_arm)
        eps = 1e-6
        for name in order:
            rb = ref_arm.data.bones.get(name)
            eb = target_arm.data.edit_bones.get(name)
            if not rb or not eb:
                continue
            # Compute new head/tail in target armature local space
            head_new = (T @ rb.head_local.to_4d()).to_3d()
            tail_new = (T @ rb.tail_local.to_4d()).to_3d()
            # Compute desired roll direction (reference Z axis in target space)
            M_ref_local = T @ rb.matrix_local
            z_axis_target = (M_ref_local.to_3x3() @ Vector((0.0, 0.0, 1.0))).normalized()
            # Apply head first; if connected to parent, Blender may clamp to parent tail automatically
            eb.head = head_new
            # Ensure non-zero length
            if (tail_new - head_new).length < eps:
                # Keep current direction but tiny length
                dir_y = (eb.tail - eb.head)
                if dir_y.length < eps:
                    dir_y = Vector((0, 0.01, 0))
                tail_new = eb.head + dir_y
            eb.tail = tail_new
            # Align roll to match reference orientation
            try:
                eb.align_roll(z_axis_target)
            except Exception:
                pass
    finally:
        if prev_mode != 'EDIT':
            try:
                bpy.ops.object.mode_set(mode=prev_mode)
            except Exception:
                pass

class CMXCopyBonesFromSelectedOperator(Operator):
    """Copy bone head/tail and roll from another selected Armature onto the active Armature (rest pose)."""
    bl_idname = "cmx.copy_bones_from_selected"
    bl_label = "Copy Bones From Selected"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        target_arm = context.view_layer.objects.active
        if not target_arm or target_arm.type != 'ARMATURE':
            self.report({'WARNING'}, "Set an Armature as the active target.")
            return {'CANCELLED'}
        source_arm = next((obj for obj in context.selected_objects if obj.type == 'ARMATURE' and obj != target_arm), None)
        if not source_arm:
            self.report({'WARNING'}, "Select another Armature to copy from.")
            return {'CANCELLED'}
        _cmx_snap_edit_bones_from_reference(target_arm, source_arm)
        self.report({'INFO'}, f"Copied bone positions from {source_arm.name} to {target_arm.name}.")
        return {'FINISHED'}

class CMXCopyPoseFromSelectedOperator(Operator):
    """Copy pose transforms from another selected Armature onto the active Armature so bound meshes follow."""
    bl_idname = "cmx.copy_pose_from_selected"
    bl_label = "Copy Pose From Selected"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        target_arm = context.view_layer.objects.active
        if not target_arm or target_arm.type != 'ARMATURE':
            self.report({'WARNING'}, "Set an Armature as the active target.")
            return {'CANCELLED'}
        source_arm = next((obj for obj in context.selected_objects if obj.type == 'ARMATURE' and obj != target_arm), None)
        if not source_arm:
            self.report({'WARNING'}, "Select another Armature to copy the pose from.")
            return {'CANCELLED'}
        _cmx_apply_scale_if_needed(context, target_arm)
        _cmx_apply_scale_if_needed(context, source_arm)
        _cmx_snap_pose_from_ref_via_constraints(target_arm, source_arm)
        self.report({'INFO'}, f"Copied pose from {source_arm.name} to {target_arm.name} (via Copy Transforms bake).")
        return {'FINISHED'}

class CMXCopyPoseApplyMeshesOperator(Operator):
    """Copy pose from another Armature, bake bound meshes, set pose as new rest, then rebind armature modifiers."""
    bl_idname = "cmx.copy_pose_from_selected_apply_mesh"
    bl_label = "Copy Pose From Selected + Apply Mesh"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        target_arm = context.view_layer.objects.active
        if not target_arm or target_arm.type != 'ARMATURE':
            self.report({'WARNING'}, "Set an Armature as the active target.")
            return {'CANCELLED'}
        source_arm = next((obj for obj in context.selected_objects if obj.type == 'ARMATURE' and obj != target_arm), None)
        if not source_arm:
            self.report({'WARNING'}, "Select another Armature to copy the pose from.")
            return {'CANCELLED'}
        _cmx_apply_scale_if_needed(context, target_arm)
        _cmx_apply_scale_if_needed(context, source_arm)
        # Copy pose via Copy Transforms + bake
        _cmx_snap_pose_from_ref_via_constraints(target_arm, source_arm)
        # Apply armature deform on meshes bound to target
        bound = _cmx_find_meshes_bound_to_armature(target_arm)
        if bound:
            _cmx_apply_modifiers(context, bound)
        # Apply current pose as new rest pose
        _cmx_apply_pose_as_rest(context, target_arm)
        # Re-add armature deform modifiers
        if bound:
            _cmx_readd_armature_modifiers(target_arm, bound)
        self.report({'INFO'}, f"Copied pose and applied to {len(bound)} mesh(es) as new rest pose.")
        return {'FINISHED'}

class CMXApplyCurrentPoseAsRestWithMeshesOperator(Operator):
    """Apply current pose as rest pose; bake bound meshes, then re-add armature deform modifiers."""
    bl_idname = "cmx.apply_pose_as_rest_with_mesh"
    bl_label = "Apply Current Pose As Rest + Mesh"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        arm_obj = _cmx_find_active_armature(context)
        if not arm_obj:
            self.report({'WARNING'}, "Select an Armature.")
            return {'CANCELLED'}
        bound = _cmx_find_meshes_bound_to_armature(arm_obj)
        if bound:
            _cmx_apply_modifiers(context, bound)
        _cmx_apply_pose_as_rest(context, arm_obj)
        if bound:
            _cmx_readd_armature_modifiers(arm_obj, bound)
        _cmx_apply_scale_if_needed(context, arm_obj)
        self.report({'INFO'}, f"Applied pose as rest; rebinding {len(bound)} mesh(es).")
        return {'FINISHED'}

class CMXCreateArmatureSnapRefOperator(Operator):
    """Duplicate active Armature as a temporary snap reference."""
    bl_idname = "cmx.create_arm_snap_ref"
    bl_label = "Create Snap Reference (Duplicate)"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        arm_obj = _cmx_find_active_armature(context)
        if not arm_obj:
            self.report({'WARNING'}, "Select an Armature.")
            return {'CANCELLED'}
        ref = _cmx_copy_armature_for_snap(arm_obj)
        if ref:
            self.report({'INFO'}, f"Created snap reference: {ref.name}")
            return {'FINISHED'}
        self.report({'ERROR'}, "Failed to create snap reference.")
        return {'CANCELLED'}

class CMXSnapFromRefAndDeleteOperator(Operator):
    """Snap current Armature EDIT bones from stored reference (rest-level), then delete the reference."""
    bl_idname = "cmx.snap_from_ref_delete"
    bl_label = "Snap Edit Bones From Ref + Delete"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        arm_obj = _cmx_find_active_armature(context)
        if not arm_obj:
            self.report({'WARNING'}, "Select an Armature.")
            return {'CANCELLED'}
        ref = _cmx_find_snap_ref_for(arm_obj)
        if not ref or ref.type != 'ARMATURE':
            self.report({'WARNING'}, "No snap reference found. Create one first.")
            return {'CANCELLED'}
        # Snap EDIT bones (rest) from the reference armature
        _cmx_snap_edit_bones_from_reference(arm_obj, ref)
        # Delete reference and clear prop
        try:
            del arm_obj["cmx_snap_ref_obj"]
        except Exception:
            pass
        try:
            bpy.data.objects.remove(ref, do_unlink=True)
        except Exception:
            pass
        self.report({'INFO'}, "Snapped from reference and removed it.")
        return {'FINISHED'}

class CMXPreviewEditAsPoseOperator(Operator):
    """Apply current Edit Bones as a temporary Pose so meshes follow while previewing/binding."""
    bl_idname = "cmx.preview_edit_as_pose"
    bl_label = "Preview Edit As Pose"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        arm_obj = _cmx_find_active_armature(context)
        if not arm_obj:
            self.report({'WARNING'}, "Select an Armature.")
            return {'CANCELLED'}
        data = _cmx_build_abs_pose_from_editbones(arm_obj)
        if not data:
            self.report({'WARNING'}, "No edit bones captured.")
            return {'CANCELLED'}
        _cmx_apply_saved_rest_as_pose_safe(arm_obj, data)
        self.report({'INFO'}, "Applied current Edit Bones as Pose (temporary preview).")
        return {'FINISHED'}

class CMXClearPoseOperator(Operator):
    """Clear all pose transforms on the active armature."""
    bl_idname = "cmx.clear_pose_all"
    bl_label = "Clear Pose"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        arm_obj = _cmx_find_active_armature(context)
        if not arm_obj:
            self.report({'WARNING'}, "Select an Armature.")
            return {'CANCELLED'}
        _cmx_clear_pose_transforms(arm_obj)
        self.report({'INFO'}, "Cleared pose transforms.")
        return {'FINISHED'}

class CMXSnapPoseFromRefOperator(Operator):
    """Snap current Pose from stored reference so meshes follow (does not edit Rest Pose)."""
    bl_idname = "cmx.snap_pose_from_ref"
    bl_label = "Snap Pose From Ref (Mesh Follows)"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        arm_obj = _cmx_find_active_armature(context)
        if not arm_obj:
            self.report({'WARNING'}, "Select an Armature.")
            return {'CANCELLED'}
        ref = _cmx_find_snap_ref_for(arm_obj)
        if not ref or ref.type != 'ARMATURE':
            self.report({'WARNING'}, "No snap reference found. Create one first.")
            return {'CANCELLED'}
        # Build absolute pose of reference in target armature space
        data = _cmx_build_abs_pose_from_armature(ref, arm_obj)
        # Apply safely (handles constraints + clear pose)
        _cmx_apply_saved_rest_as_pose_safe(arm_obj, data)
        self.report({'INFO'}, "Snapped pose from reference (mesh follows).")
        return {'FINISHED'}

def _cmx_snap_pose_from_ref_via_constraints(arm_obj, ref_arm):
    """Snap pose by adding temporary Copy Transforms constraints from ref, then bake (visual_transform_apply)."""
    # Ensure pose position and mode
    try:
        arm_obj.data.pose_position = 'POSE'
    except Exception:
        pass
    ref_prev_pose_pos = getattr(ref_arm.data, "pose_position", 'POSE')
    try:
        if ref_prev_pose_pos != 'POSE':
            ref_arm.data.pose_position = 'POSE'
    except Exception:
        pass
    prev_mode = arm_obj.mode
    if prev_mode != 'POSE':
        try:
            bpy.context.view_layer.objects.active = arm_obj
            bpy.ops.object.mode_set(mode='POSE')
        except Exception:
            pass

    # Mute existing constraints + unlock
    constraint_states = {}
    lock_states = {}
    for pb in arm_obj.pose.bones:
        states = []
        for c in pb.constraints:
            states.append((c, c.mute))
            c.mute = True
        if states:
            constraint_states[pb.name] = states
        lock_states[pb.name] = (
            tuple(getattr(pb, 'lock_location', (False, False, False))),
            tuple(getattr(pb, 'lock_rotation', (False, False, False))),
            getattr(pb, 'lock_rotation_w', False),
            getattr(pb, 'lock_rotations_4d', False),
            tuple(getattr(pb, 'lock_scale', (False, False, False))),
        )
        try:
            pb.lock_location = (False, False, False)
            pb.lock_rotation = (False, False, False)
            pb.lock_rotation_w = False
            pb.lock_rotations_4d = False
            pb.lock_scale = (False, False, False)
        except Exception:
            pass

    # Add temporary constraints
    created = []
    try:
        for pb in arm_obj.pose.bones:
            if not ref_arm.pose.bones.get(pb.name):
                continue
            ct = pb.constraints.new(type='COPY_TRANSFORMS')
            ct.name = 'CMX_SNAP_REF'
            ct.target = ref_arm
            ct.subtarget = pb.name
            ct.target_space = 'WORLD'
            ct.owner_space = 'WORLD'
            ct.influence = 1.0
            created.append((pb, ct))

        # Select all pose bones and bake visual transforms
        try:
            bpy.ops.pose.select_all(action='SELECT')
        except Exception:
            pass
        try:
            bpy.ops.pose.visual_transform_apply()
        except Exception:
            pass
    finally:
        # Remove temp constraints
        for pb, ct in created:
            try:
                pb.constraints.remove(ct)
            except Exception:
                pass
        # Restore locks + constraint states
        for pb_name, states in constraint_states.items():
            for c, muted in states:
                try:
                    c.mute = muted
                except Exception:
                    pass
        for pb_name, locks in lock_states.items():
            pb = arm_obj.pose.bones.get(pb_name)
            if not pb:
                continue
            try:
                loc, rot, rot_w, rot4d, sca = locks
                pb.lock_location = loc
                pb.lock_rotation = rot
                pb.lock_rotation_w = rot_w
                pb.lock_rotations_4d = rot4d
                pb.lock_scale = sca
            except Exception:
                pass

    # Restore mode
    if prev_mode != 'POSE':
        try:
            bpy.ops.object.mode_set(mode=prev_mode)
        except Exception:
            pass
    # Restore reference pose display
    if getattr(ref_arm.data, "pose_position", 'POSE') != ref_prev_pose_pos:
        try:
            ref_arm.data.pose_position = ref_prev_pose_pos
        except Exception:
            pass

def _cmx_find_meshes_bound_to_armature(target_arm):
    items = []
    for obj in bpy.data.objects:
        if obj.type != 'MESH':
            continue
        for mod in obj.modifiers:
            if mod.type == 'ARMATURE' and getattr(mod, "object", None) == target_arm:
                items.append((obj, mod.name))
    return items

def _cmx_apply_modifiers(context, items):
    view_layer = context.view_layer
    prev_active = view_layer.objects.active
    prev_selected = [o for o in context.selected_objects]
    try:
        try:
            bpy.ops.object.mode_set(mode='OBJECT')
        except Exception:
            pass
        for obj, mod_name in items:
            mod = obj.modifiers.get(mod_name)
            if not mod:
                continue
            try:
                bpy.ops.object.select_all(action='DESELECT')
            except Exception:
                pass
            try:
                obj.select_set(True)
            except Exception:
                pass
            try:
                view_layer.objects.active = obj
            except Exception:
                pass
            try:
                bpy.ops.object.modifier_apply(modifier=mod_name)
            except Exception:
                pass
    finally:
        try:
            bpy.ops.object.select_all(action='DESELECT')
        except Exception:
            pass
        for o in prev_selected:
            try:
                o.select_set(True)
            except Exception:
                pass
        try:
            view_layer.objects.active = prev_active
        except Exception:
            pass

def _cmx_readd_armature_modifiers(target_arm, items):
    for obj, mod_name in items:
        try:
            mod = obj.modifiers.new(mod_name, 'ARMATURE')
            mod.object = target_arm
        except Exception:
            pass

def _cmx_apply_pose_as_rest(context, arm_obj):
    view_layer = context.view_layer
    prev_active = view_layer.objects.active
    prev_selected = [o for o in context.selected_objects]
    prev_mode = arm_obj.mode
    prev_pose_pos = getattr(arm_obj.data, "pose_position", 'POSE')
    try:
        try:
            bpy.ops.object.select_all(action='DESELECT')
        except Exception:
            pass
        try:
            arm_obj.select_set(True)
            view_layer.objects.active = arm_obj
        except Exception:
            pass
        try:
            arm_obj.data.pose_position = 'POSE'
        except Exception:
            pass
        if prev_mode != 'POSE':
            try:
                bpy.ops.object.mode_set(mode='POSE')
            except Exception:
                pass
        try:
            bpy.ops.pose.armature_apply()
        except Exception:
            pass
    finally:
        if prev_mode != arm_obj.mode:
            try:
                bpy.ops.object.mode_set(mode=prev_mode)
            except Exception:
                pass
        try:
            arm_obj.data.pose_position = prev_pose_pos
        except Exception:
            pass
        try:
            bpy.ops.object.select_all(action='DESELECT')
        except Exception:
            pass
        for o in prev_selected:
            try:
                o.select_set(True)
            except Exception:
                pass
        try:
            view_layer.objects.active = prev_active
        except Exception:
            pass

class CMXSnapPoseFromRefBakeOperator(Operator):
    """Snap Pose from reference via temporary constraints and bake (mesh follows)."""
    bl_idname = "cmx.snap_pose_from_ref_bake"
    bl_label = "Snap Pose From Ref (Bake)"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        arm_obj = _cmx_find_active_armature(context)
        if not arm_obj:
            self.report({'WARNING'}, "Select an Armature.")
            return {'CANCELLED'}
        ref = _cmx_find_snap_ref_for(arm_obj)
        if not ref or ref.type != 'ARMATURE':
            self.report({'WARNING'}, "No snap reference found. Create one first.")
            return {'CANCELLED'}
        _cmx_snap_pose_from_ref_via_constraints(arm_obj, ref)
        self.report({'INFO'}, "Snapped pose from reference (baked).")
        return {'FINISHED'}

class CMXSnapPoseRefApplyMeshesOperator(Operator):
    """Snap pose from reference, apply bound meshes, set pose as new rest, then rebind armature modifiers."""
    bl_idname = "cmx.snap_pose_from_ref_apply_mesh"
    bl_label = "Snap Pose From Ref + Apply Mesh"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        arm_obj = _cmx_find_active_armature(context)
        if not arm_obj:
            self.report({'WARNING'}, "Select an Armature.")
            return {'CANCELLED'}
        ref = _cmx_find_snap_ref_for(arm_obj)
        if not ref or ref.type != 'ARMATURE':
            self.report({'WARNING'}, "No snap reference found. Create one first.")
            return {'CANCELLED'}
        # 1) Snap pose from reference (baked via Copy Transforms)
        _cmx_snap_pose_from_ref_via_constraints(arm_obj, ref)
        # 2) Apply armature deform on meshes bound to target
        bound = _cmx_find_meshes_bound_to_armature(arm_obj)
        if bound:
            _cmx_apply_modifiers(context, bound)
        # 3) Apply current pose as new rest pose
        _cmx_apply_pose_as_rest(context, arm_obj)
        # 4) Re-add armature modifiers to meshes
        if bound:
            _cmx_readd_armature_modifiers(arm_obj, bound)
        self.report({'INFO'}, f"Snapped pose from reference and applied to {len(bound)} mesh(es).")
        return {'FINISHED'}

# (old operators for stored-pose/rest workflows removed)

def cmx_create_and_connect_mix_nodes(material):
    """Create color control nodes and connect them in the material."""
    color_panel_node = (0.5, 0.0, 0.0)
    for node in material.node_tree.nodes:
        if node.name == "Color_Input_CF":
            return
    output_node = cmx_find_output_node(material)
    if output_node is None:
        return
    value_node = cmx_create_value_node(material, output_node)
    value_node.location = (output_node.location.x - 1800, output_node.location.y + 300)
    combine_rgb_node = cmx_create_combine_rgb_node(material, output_node)
    combine_rgb_node.location = (output_node.location.x - 1800, output_node.location.y - 200)
    attr_node_1 = material.node_tree.nodes.new('ShaderNodeAttribute')
    attr_node_1.name = "cf_color_probability"
    attr_node_1.attribute_name = "cf_color_probability"
    attr_node_1.attribute_type = 'INSTANCER'
    attr_node_1.location = (output_node.location.x - 1800, output_node.location.y + 200)
    attr_node_2 = material.node_tree.nodes.new('ShaderNodeAttribute')
    attr_node_2.name = "cf_override_color"
    attr_node_2.attribute_name = "cf_override_color"
    attr_node_2.attribute_type = 'INSTANCER'
    attr_node_2.location = (output_node.location.x - 1800, output_node.location.y)
    math_node = material.node_tree.nodes.new('ShaderNodeMath')
    math_node.operation = 'ADD'
    math_node.location = (output_node.location.x - 1600, output_node.location.y + 200)
    material.node_tree.links.new(value_node.outputs[0], math_node.inputs[0])
    material.node_tree.links.new(attr_node_1.outputs['Fac'], math_node.inputs[1])
    mix_node = material.node_tree.nodes.new('ShaderNodeMixRGB')
    mix_node.blend_type = 'MIX'
    mix_node.use_clamp = True
    mix_node.location = (output_node.location.x - 1600, output_node.location.y)
    material.node_tree.links.new(combine_rgb_node.outputs[0], mix_node.inputs[1])
    material.node_tree.links.new(attr_node_2.outputs['Color'], mix_node.inputs[2])
    material.node_tree.links.new(attr_node_1.outputs['Fac'], mix_node.inputs['Fac'])
    for node in material.node_tree.nodes:
        if node.inputs and node.type.startswith('BSDF'):
            first_mix_node = material.node_tree.nodes.new('ShaderNodeMixRGB')
            first_mix_node.blend_type = 'HUE'
            first_mix_node.location = node.location
            first_mix_node.location.x -= 200
            first_mix_node.use_custom_color = True
            first_mix_node.color = color_panel_node
            material.node_tree.links.new(math_node.outputs[0], first_mix_node.inputs['Fac'])
            first_input_socket = node.inputs[0]
            link_found = False
            for link in material.node_tree.links:
                if link.to_node == node and link.to_socket == first_input_socket:
                    original_input = link.from_socket
                    material.node_tree.links.remove(link)
                    material.node_tree.links.new(original_input, first_mix_node.inputs[1])
                    material.node_tree.links.new(mix_node.outputs[0], first_mix_node.inputs[2])
                    second_mix_node = material.node_tree.nodes.new('ShaderNodeMixRGB')
                    second_mix_node.location = node.location
                    second_mix_node.location.x -= 400
                    second_mix_node.use_custom_color = True
                    second_mix_node.color = color_panel_node
                    material.node_tree.links.new(math_node.outputs[0], second_mix_node.inputs['Fac'])
                    second_mix_node.inputs[1].default_value = (0.0, 0.0, 0.0, 1.0)
                    material.node_tree.links.new(second_mix_node.outputs[0], first_mix_node.inputs['Fac'])
                    material.node_tree.links.new(original_input, second_mix_node.inputs[2])
                    material.node_tree.links.new(first_mix_node.outputs[0], first_input_socket)
                    link_found = True
                    break
            if not link_found:
                default_value = material.node_tree.nodes.new('ShaderNodeRGB')
                default_value.outputs[0].default_value = (1.0, 1.0, 1.0, 1.0)
                default_value.location = (first_mix_node.location.x - 200, first_mix_node.location.y)
                material.node_tree.links.new(default_value.outputs[0], first_mix_node.inputs[1])
                material.node_tree.links.new(mix_node.outputs[0], first_mix_node.inputs[2])
                second_mix_node = material.node_tree.nodes.new('ShaderNodeMixRGB')
                second_mix_node.location = node.location
                second_mix_node.location.x -= 400
                second_mix_node.location.y += 200
                second_mix_node.use_custom_color = True
                second_mix_node.color = color_panel_node
                material.node_tree.links.new(math_node.outputs[0], second_mix_node.inputs['Fac'])
                second_mix_node.inputs[1].default_value = (0.0, 0.0, 0.0, 1.0)
                material.node_tree.links.new(second_mix_node.outputs[0], first_mix_node.inputs['Fac'])
                material.node_tree.links.new(default_value.outputs[0], second_mix_node.inputs[2])
                material.node_tree.links.new(first_mix_node.outputs[0], first_input_socket)
                material.node_tree.links.new(second_mix_node.outputs[0], first_mix_node.inputs['Fac'])

def cmx_find_output_node(material):
    """Find and return the Material Output node."""
    for node in material.node_tree.nodes:
        if node.type == 'OUTPUT_MATERIAL':
            return node
    return None

def cmx_create_combine_rgb_node(material, output_node):
    """Create Combine RGB node."""
    combine_rgb_node = material.node_tree.nodes.new('ShaderNodeCombineRGB')
    combine_rgb_node.name = "Color_Input_CF"
    combine_rgb_node.label = "Color_Input_CF"
    combine_rgb_node.location = (output_node.location.x - 1500, output_node.location.y)
    combine_rgb_node.use_custom_color = True
    combine_rgb_node.color = (0.5, 0.0, 0.0)
    return combine_rgb_node

def cmx_create_value_node(material, output_node):
    """Create Value node."""
    value_node = material.node_tree.nodes.new('ShaderNodeValue')
    value_node.name = "Opacity_Input_CF"
    value_node.outputs[0].default_value = 1.0
    value_node.location = (output_node.location.x - 1500, output_node.location.y + 100)
    value_node.use_custom_color = True
    value_node.color = (0.5, 0.0, 0.0)
    return value_node


class CMXSaveSeparateActionsOperator(Operator):
    """Save one Blender file per action for the selected armature."""
    bl_idname = "cmx.save_separate_actions"
    bl_label = "Save Separate Actions"

    def execute(self, context):
        wm = context.window_manager
        armature = _cmx_get_target_armature(context)
        if armature is None:
            self.report({'WARNING'}, "Select the target armature, or leave only one armature in the scene.")
            return {'CANCELLED'}

        output_dir = bpy.path.abspath(wm.cmx_separate_action_output_dir).strip()
        if not output_dir:
            self.report({'WARNING'}, "Choose an output folder first.")
            return {'CANCELLED'}

        action_names = [action.name for action in bpy.data.actions if _cmx_is_armature_action(action)]
        if not action_names:
            action_names = [action.name for action in bpy.data.actions]
        if not action_names:
            self.report({'WARNING'}, "No actions found in this file.")
            return {'CANCELLED'}

        blender_binary = bpy.app.binary_path
        if not blender_binary or not os.path.exists(blender_binary):
            self.report({'ERROR'}, "Blender executable was not found.")
            return {'CANCELLED'}

        os.makedirs(output_dir, exist_ok=True)

        temp_source = tempfile.NamedTemporaryFile(delete=False, suffix=".blend")
        temp_script = tempfile.NamedTemporaryFile(delete=False, suffix=".py", mode="w", encoding="utf-8")
        temp_source_path = temp_source.name
        temp_script_path = temp_script.name
        temp_source.close()
        try:
            temp_script.write(CMX_SEPARATE_ACTION_SCRIPT)
            temp_script.close()

            bpy.ops.wm.save_as_mainfile(filepath=temp_source_path, copy=True)

            used_names = set()
            saved_files = []
            failures = []

            for action_name in action_names:
                output_path = _cmx_unique_action_filepath(output_dir, action_name, used_names)
                command = [
                    blender_binary,
                    "-b",
                    temp_source_path,
                    "--python",
                    temp_script_path,
                    "--",
                    action_name,
                    output_path,
                    armature.name,
                ]
                result = subprocess.run(command, capture_output=True, text=True)
                if result.returncode == 0 and os.path.exists(output_path):
                    saved_files.append(output_path)
                else:
                    error_text = (result.stderr or result.stdout or "Unknown error").strip()
                    failures.append(f"{action_name}: {error_text}")

            if failures:
                message = "\n".join(failures[:6])
                if len(failures) > 6:
                    message += f"\n...and {len(failures) - 6} more"
                cmx_show_message_box(
                    message=message,
                    title=f"Saved {len(saved_files)} / {len(action_names)} action files",
                    icon='ERROR'
                )
                self.report({'WARNING'}, f"Saved {len(saved_files)} action file(s), failed {len(failures)}.")
                return {'CANCELLED'}

            self.report({'INFO'}, f"Saved {len(saved_files)} action file(s) to {output_dir}")
            return {'FINISHED'}
        finally:
            for temp_path in (temp_source_path, temp_script_path):
                try:
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                except Exception:
                    pass

class CMXCreatePreviewCamOperator(Operator):
    """Create preview cameras for rendering item previews."""
    bl_idname = "cmx.create_preview_cam"
    bl_label = "create preview camera"

    def execute(self, context):
        if not bpy.data.collections.get("CMX_Preview_Cam"):
            cam_preview_coll = bpy.data.collections.new(name="CMX_Preview_Cam")
            bpy.context.scene.collection.children.link(cam_preview_coll)
        else:
            cam_preview_coll = bpy.data.collections["CMX_Preview_Cam"]
        location_z = 0
        for preview_cam in CAM_PREVIEW_LIST:
            if not context.scene.objects.get(preview_cam):
                camera_data = bpy.data.cameras.new(name=preview_cam)
                camera_object = bpy.data.objects.new(preview_cam, camera_data)
                camera_object.rotation_mode = 'XYZ'
                camera_object.rotation_euler = (math.radians(90), 0, 0)
                camera_object.location = (0, -1, location_z)
                location_z += 0.3
                cam_preview_coll.objects.link(camera_object)
        return {'FINISHED'}

class CMXRemovePreviewCamOperator(Operator):
    """Remove preview cameras and collection."""
    bl_idname = "cmx.remove_preview_cam_cf"
    bl_label = "remove preview camera"

    def execute(self, context):
        for preview_cam in CAM_PREVIEW_LIST:
            cam_obj = bpy.data.objects.get(preview_cam)
            cam_data = bpy.data.cameras.get(preview_cam)
            if cam_obj:
                bpy.data.objects.remove(cam_obj)
                bpy.data.cameras.remove(cam_data)
        cam_preview_coll = bpy.data.collections.get("CMX_Preview_Cam")
        if cam_preview_coll:
            bpy.data.collections.remove(cam_preview_coll)
        return {'FINISHED'}

class CMXRenderItemPreviewOperator(Operator):
    """Render preview images for each item in collection."""
    bl_idname = "cmx.render_item_preview_cf"
    bl_label = "generate preview"
    cancelRender = None
    rendering = None
    renderQueue = None
    timerEvent = None

    def pre_render(self, dummy_A, dummy_B):
        self.rendering = True

    def post_render(self, dummy_A, dummy_B):
        ren_item = self.renderQueue[0]
        bpy.data.objects[ren_item["obj"]].hide_render = True
        self.renderQueue.pop(0)
        self.rendering = False

    def on_render_cancel(self):
        self.cancelRender = True

    def execute(self, context):
        """Prepare and start batch preview render."""
        self.cancelRender = False
        self.rendering = False
        cmx_set_progress_info("Prepare to Render")
        preview_filter = context.window_manager.gen_preview_filter
        preview_cam = ""
        char_dir_path = ""
        try:
            filepath = bpy.data.filepath
            current_folder = os.path.dirname(filepath)
            char_name = bpy.path.basename(bpy.data.filepath).replace(".blend", "")
            directory = char_name
            char_dir_path = os.path.join(current_folder, directory)
            if not os.path.exists(char_dir_path):
                os.mkdir(char_dir_path)
            for item_dir in BODY_PART:
                item_dir_path = os.path.join(char_dir_path, item_dir)
                if not os.path.exists(item_dir_path):
                    os.mkdir(item_dir_path)
        except:
            return {"CANCELLED"}
        bpy.context.scene.render.image_settings.file_format = 'PNG'
        bpy.context.scene.render.image_settings.color_mode = 'RGBA'
        self.renderQueue = []
        for cam_name in CAM_PREVIEW_LIST:
            if preview_filter in cam_name:
                preview_cam = cam_name
                break
        cam_preview_coll = bpy.data.objects.get(preview_cam)
        if cam_preview_coll:
            item_dir = preview_filter
            item_dir_path = os.path.join(char_dir_path, item_dir) + "\\"
            select_bodypart_collection = bpy.data.collections.get(preview_filter)
            if select_bodypart_collection:
                for item in select_bodypart_collection.all_objects:
                    self.renderQueue.append({"cam": preview_cam, "path": item_dir_path, "obj": item.name})
        bpy.app.handlers.render_pre.append(self.pre_render)
        bpy.app.handlers.render_post.append(self.post_render)
        bpy.app.handlers.render_cancel.append(self.on_render_cancel)
        self.timerEvent = context.window_manager.event_timer_add(1.0, window=context.window)
        context.window_manager.modal_handler_add(self)
        return {"RUNNING_MODAL"}

    def modal(self, context, event):
        if event.type == 'ESC':
            self.on_render_cancel()
            cmx_show_message_box(message="Render Preview is Cancel", title="Render status", icon='INFO')
            return {'RUNNING_MODAL'}
        if event.type == 'TIMER':
            if not self.renderQueue or self.cancelRender is True:
                bpy.app.handlers.render_pre.remove(self.pre_render)
                bpy.app.handlers.render_post.remove(self.post_render)
                bpy.app.handlers.render_cancel.remove(self.on_render_cancel)
                context.window_manager.event_timer_remove(self.timerEvent)
                self.report({"INFO"}, "RENDER QUEUE FINISHED")
                return {"FINISHED"}
            elif self.rendering is False and self.cancelRender is False:
                ren_item = self.renderQueue[0]
                item = bpy.data.objects[ren_item["obj"]]
                item.hide_render = False
                cam_preview_item = bpy.data.objects[ren_item["cam"]]
                context.scene.camera = cam_preview_item
                bpy.context.scene.render.filepath = ren_item["path"] + item.name
                bpy.ops.render.render(use_viewport=False, write_still=True)
        in_queue = len(self.renderQueue)
        if in_queue:
            cmx_set_progress_info("Rendering : " + str(in_queue))
        else:
            context.window_manager.progress_info_render = "Render Done"
            cmx_set_progress_info("Render Done")
        return {"PASS_THROUGH"}


class CMXRenderAnimPreviewOperator(Operator):
    """Render animation preview images from the active viewport for the current animation filter."""
    bl_idname = "cmx.render_anim_preview_cf"
    bl_label = "render animation preview"
    bl_description = "Viewport-render animation previews next to each animation blend file"

    _timer = None
    _queue = None
    _view_area = None
    _view_region = None
    _original_anim_filter = ""
    _original_anim_preview = ""
    _original_anim_use = False
    _original_render_filepath = ""
    _processed_count = 0
    _skipped_count = 0

    def _cleanup(self, context):
        if self._timer:
            try:
                context.window_manager.event_timer_remove(self._timer)
            except Exception:
                pass
            self._timer = None
        _cmx_refresh_anim_preview_cache(context)

    def _restore_animation_state(self, context):
        wm = context.window_manager
        try:
            context.scene.render.filepath = self._original_render_filepath
        except Exception:
            pass
        try:
            if self._original_anim_filter:
                wm.anim_filter = self._original_anim_filter
        except Exception:
            pass
        try:
            if self._original_anim_preview:
                wm.anim_previews = self._original_anim_preview
        except Exception:
            pass
        try:
            wm.anim_use_toggle = self._original_anim_use
        except Exception:
            pass

    def _render_next(self, context):
        if not self._queue:
            return False

        item = self._queue.pop(0)
        cmx_link_action(context, is_applay=False, act_name=item["anim_name"], aim_filter=item["anim_filter"])
        try:
            context.view_layer.update()
        except Exception:
            pass

        cmx_set_progress_task("Render Anim", item["anim_name"])
        context.scene.render.filepath = item["output_path"]
        with context.temp_override(
            window=context.window,
            screen=context.screen,
            area=self._view_area,
            region=self._view_region,
            scene=context.scene,
        ):
            bpy.ops.render.opengl(write_still=True, view_context=True)
        self._processed_count += 1
        return True

    def execute(self, context):
        wm = context.window_manager
        if not wm.cf_on_off_toggle:
            cmx_show_message_box(
                message="Please turn on Character Customize before rendering animation previews.",
                title="Animation Preview",
                icon='ERROR'
            )
            return {'CANCELLED'}

        if not context.area or context.area.type != 'VIEW_3D':
            cmx_show_message_box(
                message="Run this from the 3D Viewport so the current viewport can be rendered.",
                title="Animation Preview",
                icon='ERROR'
            )
            return {'CANCELLED'}

        view_region = next((region for region in context.area.regions if region.type == 'WINDOW'), None)
        if view_region is None:
            cmx_show_message_box(
                message="No viewport window region was found for rendering.",
                title="Animation Preview",
                icon='ERROR'
            )
            return {'CANCELLED'}

        asset_directory = cmx_get_dir_asset_path()
        if not asset_directory:
            cmx_show_message_box(message="Asset folder is not configured.", title="Animation Preview", icon='ERROR')
            return {'CANCELLED'}

        anim_filter = wm.anim_filter or (ANIMATION_FILTER[0] if ANIMATION_FILTER else "")
        if not anim_filter:
            cmx_show_message_box(message="No animation filter was found.", title="Animation Preview", icon='ERROR')
            return {'CANCELLED'}

        anim_directory = os.path.join(asset_directory, "Animation", anim_filter)
        if not os.path.isdir(anim_directory):
            cmx_show_message_box(message="Animation folder not found for the current filter.", title="Animation Preview", icon='ERROR')
            return {'CANCELLED'}

        render_ext = _cmx_get_anim_render_extension(context.scene)
        if not render_ext:
            cmx_show_message_box(
                message="Current render image format is not supported for animation previews.",
                title="Animation Preview",
                icon='ERROR'
            )
            return {'CANCELLED'}

        anim_names = sorted(ANIM_SELECT_LIST.get(anim_filter, []))
        if not anim_names:
            enum_items = cmx_anim_preview_item(None, context)
            anim_names = [item[1] for item in enum_items if item[0].startswith(anim_filter + ".")]
        if not anim_names:
            cmx_show_message_box(message="No animations found in the current filter.", title="Animation Preview", icon='ERROR')
            return {'CANCELLED'}

        write_mode = getattr(wm, "cmx_anim_preview_write_mode", "MISSING")
        queue = []
        skipped_count = 0
        for anim_name in anim_names:
            output_path = os.path.join(anim_directory, anim_name + render_ext)
            existing_preview = _cmx_find_existing_anim_preview(anim_directory, anim_name)
            if write_mode == "MISSING" and existing_preview:
                skipped_count += 1
                continue
            queue.append({
                "anim_name": anim_name,
                "anim_filter": anim_filter,
                "output_path": output_path,
            })

        if not queue:
            cmx_set_progress_success()
            self.report({'INFO'}, "All animation previews already exist.")
            _cmx_refresh_anim_preview_cache(context)
            return {'FINISHED'}

        self._view_area = context.area
        self._view_region = view_region
        self._queue = queue
        self._processed_count = 0
        self._skipped_count = skipped_count
        self._original_anim_filter = wm.anim_filter
        self._original_anim_preview = wm.anim_previews
        self._original_anim_use = wm.anim_use_toggle
        self._original_render_filepath = context.scene.render.filepath

        if wm.anim_filter != anim_filter:
            wm.anim_filter = anim_filter
        if not wm.anim_use_toggle:
            wm.anim_use_toggle = True

        self._timer = context.window_manager.event_timer_add(0.1, window=context.window)
        context.window_manager.modal_handler_add(self)
        cmx_set_progress_task("Render Anim", queue[0]["anim_name"])
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        if event.type == 'ESC':
            self._restore_animation_state(context)
            self._cleanup(context)
            cmx_set_progress_info("Canceled.")
            self.report({'INFO'}, "Animation preview rendering canceled.")
            return {'CANCELLED'}

        if event.type != 'TIMER':
            return {'PASS_THROUGH'}

        if self._queue:
            try:
                self._render_next(context)
            except Exception as e:
                self._restore_animation_state(context)
                self._cleanup(context)
                cmx_set_progress_error("Anim Preview", str(e))
                self.report({'ERROR'}, f"Failed to render animation preview: {e}")
                return {'CANCELLED'}
            return {'PASS_THROUGH'}

        self._restore_animation_state(context)
        self._cleanup(context)
        cmx_set_progress_success()
        self.report(
            {'INFO'},
            f"Rendered {self._processed_count} animation previews. Skipped {self._skipped_count} existing previews."
        )
        return {'FINISHED'}

class CMXCreateCollectionTemplateOperator(Operator):
    """Create template asset and body part collections."""
    bl_idname = "cmx.create_collection_template_cf"
    bl_label = "create collection template"

    def execute(self, context):
        scene_root = bpy.context.scene.collection

        def ensure_collection(name, parent, color=None):
            col = bpy.data.collections.get(name)
            if not col:
                col = bpy.data.collections.new(name)
                parent.children.link(col)
            elif col.name not in parent.children:
                parent.children.link(col)
            if color:
                try:
                    col.color_tag = color
                except Exception:
                    pass
            return col

        # Root
        root = ensure_collection("CMX_BodyPart", scene_root, color='COLOR_01')

        # Main categories and their sub-filters
        layout = {
            "Hair": [],
            "Head": ["Head_Casual", "Head_Extra", "Head_Uniform", "Head_Sport", "Head_Formal"],
            "Eye": ["Eye_Casual", "Eye_Extra", "Eye_Uniform", "Eye_Sport", "Eye_Formal"],
            "Torso": ["Torso_Casual", "Torso_Extra", "Torso_Uniform", "Torso_Sport", "Torso_Formal"],
            "Leg": ["Leg_Casual", "Leg_Extra", "Leg_Uniform", "Leg_Sport", "Leg_Formal"],
            "Accessory": ["Accessory_Casual", "Accessory_Extra", "Accessory_Uniform", "Accessory_Sport", "Accessory_Formal"],
            "Foot": ["Foot_Casual", "Foot_Extra", "Foot_Uniform", "Foot_Sport", "Foot_Formal"],
            "Body": [],
            "Proxy": [],
            "Bone": [],
        }

        for cat, subcats in layout.items():
            cat_col = ensure_collection(cat, root, color='COLOR_04')
            for sub in subcats:
                ensure_collection(sub, cat_col, color='COLOR_05')

        return {'FINISHED'}

class CMXCreateJsonItemListOperator(bpy.types.Operator):
    """Create asset list json file for the character."""
    bl_idname = "cmx.create_json_item_list"
    bl_label = "create item list"

    def execute(self, context):
        wr_list = {}
        coll_nofilter = {"Proxy", "Hair", "Body", "Bone"}
        for bp_coll in bpy.data.collections:
            if bp_coll.name in ASSET_LIBR_COLL:
                wr_list[bp_coll.name] = {}
                if bp_coll.name in coll_nofilter:
                    asset_list = []
                    for h_obj in bp_coll.objects:
                        asset_list.append(h_obj.name)
                    wr_list[bp_coll.name] = asset_list
                    continue
                for filter_coll in bp_coll.children:
                    asset_filter_list = []
                    for obj in filter_coll.objects:
                        asset_filter_list.append(obj.name)
                    wr_list[bp_coll.name][filter_coll.name] = asset_filter_list

        wr_list["Makeup"] = list(CHAR_OPT.get("Makeup", []))
        wr_list["Skin"] = list(CHAR_OPT.get("Skin", []))
        try:
            filepath = bpy.data.filepath
            current_folder = os.path.dirname(filepath)
            char_name = bpy.path.basename(filepath).replace(".blend", "")
            wr_list["Char_name"] = char_name
            # <<<<<<<  os.path.join >>>>>>>
            json_path = os.path.join(current_folder, char_name + ".json")
            with open(json_path, "w", encoding="utf-8") as file:
                json.dump(wr_list, file, indent=2, sort_keys=False)
            cmx_show_message_box(message="Generate asset data complete.", title="Generate status", icon='CHECKMARK')
        except Exception as e:
            print("Error:", e)
            cmx_show_message_box(message="Generate asset data error !", title="Generate status", icon='ERROR')
        return {'FINISHED'}


class CMXCreateColorCtrlNodeOperator(Operator):
    """Create color control node in all selected mesh objects' materials."""
    bl_idname = "object.create_color_ctrl_node_cf"
    bl_label = "create color ctrl"

    def execute(self, context): 
        for obj in bpy.context.selected_objects:
            if obj.type == 'MESH':
                obj.hide_viewport = False
                obj.hide_set(False)
                for material in obj.data.materials:
                    if material and material.use_nodes:
                        try:
                            cmx_create_and_connect_mix_nodes(material)
                        except Exception as e:
                            pass
        return {'FINISHED'}

class CMXBakeSelectedToActiveOperator(bpy.types.Operator):
    """Bake diffuse color (color only) then normal from selected to active, auto-creating target images."""
    bl_idname = "cmx.bake_selected_to_active"
    bl_label = "Bake Color + Normal (Sel->Active)"
    bl_options = {'REGISTER', 'UNDO'}

    def _ensure_material(self, obj):
        if obj.data.materials:
            return
        mat = bpy.data.materials.new(name=f"{obj.name}_BakeMat")
        mat.use_nodes = True
        obj.data.materials.append(mat)

    def _get_principled(self, nt):
        return next((n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'), None)

    def _ensure_image_node(self, nt, image):
        node = next((n for n in nt.nodes if n.type == 'TEX_IMAGE' and n.image == image), None)
        if not node:
            node = nt.nodes.new("ShaderNodeTexImage")
            node.image = image
        return node

    def _ensure_normal_node(self, nt):
        node = next((n for n in nt.nodes if n.type == 'NORMAL_MAP'), None)
        if not node:
            node = nt.nodes.new("ShaderNodeNormalMap")
        node.space = 'TANGENT'
        return node

    def _connect_ss_mask(self, nt, img_node):
        principled = self._get_principled(nt)
        if not principled:
            return
        ss_socket = principled.inputs.get('Subsurface')
        if not ss_socket:
            return
        color_out = img_node.outputs.get("Color") or (img_node.outputs[0] if img_node.outputs else None)
        if not color_out:
            return
        for link in list(nt.links):
            if link.to_node == principled and link.to_socket == ss_socket:
                nt.links.remove(link)
        nt.links.new(color_out, ss_socket)

    def _connect_color(self, nt, img_node):
        principled = self._get_principled(nt)
        if not principled:
            return
        for link in list(nt.links):
            if link.to_node == principled and link.to_socket == principled.inputs['Base Color']:
                nt.links.remove(link)
        out_socket = img_node.outputs.get("Color") or (img_node.outputs[0] if img_node.outputs else None)
        if out_socket:
            nt.links.new(out_socket, principled.inputs['Base Color'])

    def _connect_normal(self, nt, img_node):
        principled = self._get_principled(nt)
        if not principled:
            return
        normal_node = self._ensure_normal_node(nt)
        color_socket = img_node.outputs.get("Color") or (img_node.outputs[0] if img_node.outputs else None)
        if color_socket:
            for link in list(nt.links):
                if link.to_node == normal_node and link.to_socket == normal_node.inputs['Color']:
                    nt.links.remove(link)
            nt.links.new(color_socket, normal_node.inputs['Color'])
        for link in list(nt.links):
            if link.to_node == principled and link.to_socket == principled.inputs['Normal']:
                nt.links.remove(link)
        if normal_node.outputs:
            nt.links.new(normal_node.outputs['Normal'], principled.inputs['Normal'])

    def _ensure_image(self, obj, suffix, size, colorspace):
        image_name = f"{obj.name}{suffix}"
        image = bpy.data.images.get(image_name)
        if not image:
            image = bpy.data.images.new(image_name, width=size, height=size, alpha=True)
        elif image.size[0] != size or image.size[1] != size:
            try:
                image.scale(size, size)
            except Exception:
                pass
        try:
            image.colorspace_settings.name = colorspace
        except Exception:
            pass
        return image

    def _activate_image_on_materials(self, obj, image, connect_kind=None):
        self._ensure_material(obj)
        for slot in obj.material_slots:
            mat = slot.material
            if not mat:
                continue
            if not mat.use_nodes:
                mat.use_nodes = True
            nt = mat.node_tree
            if not nt:
                continue
            img_node = self._ensure_image_node(nt, image)
            nt.nodes.active = img_node
            if connect_kind == "COLOR":
                self._connect_color(nt, img_node)
            elif connect_kind == "NORMAL":
                self._connect_normal(nt, img_node)
            elif connect_kind == "SS_MASK":
                self._connect_ss_mask(nt, img_node)

    def _resolve_bake_output_dir(self, context):
        """Return a usable directory for saving baked images."""
        wm = context.window_manager
        raw_dir = getattr(wm, "cmx_bake_output_dir", "") or ""
        if raw_dir:
            path = bpy.path.abspath(raw_dir)
        else:
            blend_dir = os.path.dirname(bpy.data.filepath) if bpy.data.filepath else ""
            path = blend_dir or bpy.app.tempdir
        if path and not os.path.exists(path):
            try:
                os.makedirs(path, exist_ok=True)
            except Exception:
                path = bpy.app.tempdir
                if path and not os.path.exists(path):
                    path = ""
        return path

    def _save_image_to_dir(self, image, directory):
        """Save an image to the target directory as PNG."""
        if not image or not directory:
            return None
        safe_name = "".join(c if c not in "\\/:*?\"<>|" else "_" for c in image.name)
        filepath = os.path.join(directory, f"{safe_name}.png")
        try:
            image.filepath_raw = filepath
            image.file_format = 'PNG'
            image.save()
            return filepath
        except Exception:
            return None

    def execute(self, context):
        scene = context.scene
        wm = context.window_manager
        bake_size = max(64, int(getattr(wm, "cmx_bake_texture_size", 2048)))
        bake_color = getattr(wm, "cmx_bake_color", True)
        bake_normal = getattr(wm, "cmx_bake_normal", True)
        bake_ss_mask = getattr(wm, "cmx_bake_ss_mask", True)

        if not (bake_color or bake_normal or bake_ss_mask):
            self.report({'WARNING'}, "No bake outputs selected.")
            return {'CANCELLED'}

        active_obj = context.view_layer.objects.active
        if not active_obj or active_obj.type != 'MESH':
            self.report({'ERROR'}, "Active object must be a mesh to receive the bake.")
            return {'CANCELLED'}

        source_objs = [obj for obj in context.selected_objects if obj != active_obj]
        if not source_objs:
            self.report({'ERROR'}, "Select at least one source object (selected to active).")
            return {'CANCELLED'}

        if scene.render.engine != 'CYCLES':
            self.report({'ERROR'}, "Please switch the render engine to Cycles before baking.")
            return {'CANCELLED'}

        prev_mode = context.mode
        try:
            if prev_mode != 'OBJECT':
                bpy.ops.object.mode_set(mode='OBJECT')
        except Exception:
            pass

        bake_settings = scene.render.bake
        prev_settings = {
            "use_selected_to_active": bake_settings.use_selected_to_active,
            "use_pass_direct": bake_settings.use_pass_direct,
            "use_pass_indirect": bake_settings.use_pass_indirect,
            "use_pass_color": bake_settings.use_pass_color,
            "target": getattr(bake_settings, "target", 'IMAGE_TEXTURES')
        }

        color_img = None
        normal_img = None
        ss_mask_img = None
        result = {'FINISHED'}
        saved_paths = []
        output_dir = self._resolve_bake_output_dir(context)
        try:
            bake_settings.use_selected_to_active = True
            if hasattr(bake_settings, "target"):
                bake_settings.target = 'IMAGE_TEXTURES'

            # Bake diffuse color only
            if bake_color:
                bake_settings.use_pass_direct = False
                bake_settings.use_pass_indirect = False
                bake_settings.use_pass_color = True
                color_img = self._ensure_image(active_obj, "_Col", bake_size, "sRGB")
                self._activate_image_on_materials(active_obj, color_img, connect_kind="COLOR")
                bpy.ops.object.bake(type='DIFFUSE')

            # Bake normal map
            if bake_normal:
                normal_img = self._ensure_image(active_obj, "_NM", bake_size, "Non-Color")
                self._activate_image_on_materials(active_obj, normal_img, connect_kind="NORMAL")
                bpy.ops.object.bake(type='NORMAL')

            # Create subsurface mask image (no bake) and wire to subsurface weight
            if bake_ss_mask:
                ss_mask_img = self._ensure_image(active_obj, "_SS_mask", bake_size, "Non-Color")
                self._activate_image_on_materials(active_obj, ss_mask_img, connect_kind="SS_MASK")

            if output_dir:
                for img in (color_img, normal_img, ss_mask_img):
                    if img:
                        saved = self._save_image_to_dir(img, output_dir)
                        if saved:
                            saved_paths.append(saved)
        except Exception as ex:
            result = {'CANCELLED'}
            self.report({'ERROR'}, f"Bake failed: {ex}")
        finally:
            bake_settings.use_selected_to_active = prev_settings["use_selected_to_active"]
            bake_settings.use_pass_direct = prev_settings["use_pass_direct"]
            bake_settings.use_pass_indirect = prev_settings["use_pass_indirect"]
            bake_settings.use_pass_color = prev_settings["use_pass_color"]
            if hasattr(bake_settings, "target"):
                bake_settings.target = prev_settings["target"]
            if prev_mode != 'OBJECT':
                try:
                    bpy.ops.object.mode_set(mode=prev_mode)
                except Exception:
                    pass

        if result == {'FINISHED'}:
            baked_names = [img.name for img in (color_img, normal_img, ss_mask_img) if img]
            baked_label = " / ".join(baked_names) if baked_names else "No images"
            if saved_paths:
                self.report({'INFO'}, f"Baked {baked_label} at {bake_size}px -> saved {len(saved_paths)} file(s) to {output_dir}")
            else:
                self.report({'INFO'}, f"Baked {baked_label} at {bake_size}px")
        return result

class CMXRenameBonesOperator(bpy.types.Operator):
    """Rename bones by replacing 'Left' and 'Right' with .L and .R"""
    bl_idname = "cmx.rename_bones"
    bl_label = "Rename Bones"
    bl_description = "Rename bones by replacing 'Left' and 'Right' with .L and .R"
    
    def execute(self, context):
        armature = context.object
        if armature and armature.type == 'ARMATURE':
            for bone in armature.data.bones:
                original_name = bone.name 
                new_name = original_name.replace("Left", "").replace("Right", "")
                if "Left" in original_name:
                    new_name += ".L"
                elif "Right" in original_name:
                    new_name += ".R"
                bone.name = new_name
                original_bone_names[bone.name] = original_name
            self.report({'INFO'}, "Bones renamed successfully")
        else:
            self.report({'WARNING'}, "No armature selected or selected object is not an armature")
        return {'FINISHED'}

class CMXRestoreBonesOperator(bpy.types.Operator):
    """Restore original bone names before renaming"""
    bl_idname = "cmx.restore_bones"
    bl_label = "Restore Original Bone Names"
    bl_description = "Restore original bone names before renaming"
    
    def execute(self, context):
        armature = context.object
        if armature and armature.type == 'ARMATURE':
            for bone in armature.data.bones:
                original_name = original_bone_names.get(bone.name)
                if original_name:
                    bone.name = original_name
            self.report({'INFO'}, "Original bone names restored successfully")
        else:
            self.report({'WARNING'}, "No armature selected or selected object is not an armature")
        return {'FINISHED'}
 
class CMXHighlightConcaveFacesOperator(bpy.types.Operator):
    """Highlight Concave Faces in Edit Mode"""
    bl_idname = "cmx.highlight_concave_faces"
    bl_label = "Highlight Concave Faces"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        obj = context.object
        if not obj or obj.type != 'MESH':
            self.report({'ERROR'}, "กรุณาเลือก Mesh Object เท่านั้น")
            return {'CANCELLED'}
        if context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        mesh = obj.data
        concave_faces = []
        for face in mesh.polygons:
            verts = [mesh.vertices[v].co for v in face.vertices]
            normal = face.normal
            directions = []
            for i in range(len(verts)):
                v1 = verts[i] - verts[i - 1]
                v2 = verts[(i + 1) % len(verts)] - verts[i]
                cross = v1.cross(v2).normalized()
                directions.append(cross.dot(normal))
            if any(d < 0 for d in directions):
                concave_faces.append(face.index)
        if concave_faces:
            self.report({'INFO'}, f"พบ {len(concave_faces)} Concave Face(s)")
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.object.mode_set(mode='OBJECT')
            for face_index in concave_faces:
                mesh.polygons[face_index].select = True
            bpy.ops.object.mode_set(mode='EDIT')
            text_info = "Successfully highlighted concave faces in Edit Mode!"
        else:
            text_info = "No concave faces found."
        cmx_show_message_box(message=text_info, title="Concave faces", icon='INFO')
        return {'FINISHED'}

class CMXAddPatternIndexOperator(bpy.types.Operator):
    """Add custom property 'Pattern_Index' (0-3) to all materials of selected objects"""
    bl_idname = "cmx.add_pattern_index"
    bl_label = "Add Pattern_Index to Materials"
    bl_description = "Add custom property 'Pattern_Index' (0-3) to all materials of selected objects and link it to a node named 'Pattern_Index'"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        selected_objects = context.selected_objects
        if not selected_objects:
            self.report({'WARNING'}, "No objects selected.")
            return {'CANCELLED'}
        added_count = 0
        for obj in selected_objects:
            if obj.type != 'MESH':
                continue
            for slot in obj.material_slots:
                mat = slot.material
                if not mat or not mat.use_nodes:
                    continue
                if "Pattern_Index" not in mat:
                    mat["Pattern_Index"] = 0
                    mat.id_properties_ui("Pattern_Index").update(min=0, max=3)
                    added_count += 1
        self.report({'INFO'}, f"Added Pattern_Index to {added_count} materials")
        return {'FINISHED'}

class CMXCFAddColorInputCtrlOperator(bpy.types.Operator):
    """Add Color_Input_Ctrl property and drivers to selected object's materials (Combine RGB & Opacity)"""
    bl_idname = "cmx.add_color_input_ctrl"
    bl_label = "Add Color Input Ctrl"
    bl_description = "Add Color_Input_Ctrl property and drivers to selected object's materials (Combine RGB & Opacity)"

    def execute(self, context):
        for obj in context.selected_objects:
            for slot in obj.material_slots:
                mat = slot.material
                if not mat or not mat.use_nodes:
                    continue
                if "Color_Input_Ctrl" not in mat:
                    mat["Color_Input_Ctrl"] = [0.0, 0.0, 0.0, 0.0]
                mat.id_properties_ui("Color_Input_Ctrl").update(
                    subtype='COLOR', min=0.0, max=1.0, default=[0.0, 0.0, 0.0, 0.0]
                )
                nt = mat.node_tree
                color_node = nt.nodes.get("Color_Input_CF")
                opacity_node = nt.nodes.get("Opacity_Input_CF")
                if not color_node and not opacity_node:
                    continue
                if color_node and color_node.type == 'COMBINE_RGB':
                    for i in range(3):
                        inp = color_node.inputs[i]
                        try:
                            inp.driver_remove("default_value", -1)
                        except:
                            pass
                        drv = inp.driver_add("default_value").driver
                        drv.type = 'SCRIPTED'
                        drv.expression = f'var[{i}]'
                        var = drv.variables.new()
                        var.name = "var"
                        var.type = 'SINGLE_PROP'
                        var.targets[0].id_type = 'MATERIAL'
                        var.targets[0].id = mat
                        var.targets[0].data_path = '["Color_Input_Ctrl"]'
                        drv.variables[0].targets[0].id = mat
                        drv.variables[0].targets[0].data_path = '["Color_Input_Ctrl"]'
                if opacity_node and len(opacity_node.outputs) > 0:
                    outp = opacity_node.outputs[0]
                    try:
                        outp.driver_remove("default_value", -1)
                    except:
                        pass
                    drv = outp.driver_add("default_value").driver
                    drv.type = 'SCRIPTED'
                    drv.expression = 'var[3]'
                    var = drv.variables.new()
                    var.name = "var"
                    var.type = 'SINGLE_PROP'
                    var.targets[0].id_type = 'MATERIAL'
                    var.targets[0].id = mat
                    var.targets[0].data_path = '["Color_Input_Ctrl"]'
                    drv.variables[0].targets[0].id = mat
                    drv.variables[0].targets[0].data_path = '["Color_Input_Ctrl"]'
        bpy.context.view_layer.update()
        for area in bpy.context.screen.areas:
            area.tag_redraw()
        self.report({'INFO'}, "Color_Input_Ctrl and drivers added.")
        return {'FINISHED'}

class CMXAddColorInputDriverOperator(bpy.types.Operator):
    """Add Color_Input_Ctrl property and drivers to selected object's materials"""
    bl_idname = "cmx.add_color_input_driver"
    bl_label = "Add Color Input Ctrl"
    bl_description = "Add Color_Input_Ctrl property and drivers to selected object's materials"

    def execute(self, context):
        for obj in context.selected_objects:
            for slot in obj.material_slots:
                mat = slot.material
                if not mat or not mat.use_nodes:
                    continue
                nt = mat.node_tree
                color_node = nt.nodes.get("Color_Input_CF")
                opacity_node = nt.nodes.get("Opacity_Input_CF")
                if not color_node and not opacity_node:
                    continue
                if color_node:
                    for i in range(3):
                        inp = color_node.inputs[i] if i < len(color_node.inputs) else None
                        if inp:
                            if inp.is_linked or inp.is_output:
                                continue
                            if inp.driver_remove("default_value", -1):
                                pass
                            drv = inp.driver_add("default_value").driver
                            drv.type = 'AVERAGE'
                            var = drv.variables.new()
                            var.name = "var"
                            var.type = 'SINGLE_PROP'
                            var.targets[0].id_type = 'MATERIAL'
                            var.targets[0].id = mat
                            var.targets[0].data_path = f'["Color_Input_Ctrl"][{i}]'
                if opacity_node and len(opacity_node.inputs) > 0:
                    outp = opacity_node.inputs[0]
                    drv = outp.driver_add("default_value").driver
                    drv.type = 'AVERAGE'
                    var = drv.variables.new()
                    var.name = "var"
                    var.type = 'SINGLE_PROP'
                    var.targets[0].id_type = 'MATERIAL'
                    var.targets[0].id = mat
                    var.targets[0].data_path = '["Color_Input_Ctrl"][3]'
        self.report({'INFO'}, "Color_Input_Ctrl and drivers added.")
        return {'FINISHED'}

classes = [
    CMXCreateHookWithEmptyOperator,
    CMXSaveSeparateActionsOperator,
    CMXCreatePreviewCamOperator,
    CMXRemovePreviewCamOperator,
    CMXRenderItemPreviewOperator,
    CMXRenderAnimPreviewOperator,
    CMXCreateCollectionTemplateOperator,
    CMXCreateJsonItemListOperator,
    CMXCreateColorCtrlNodeOperator,
    CMXBakeSelectedToActiveOperator,
    CMXCopyBonesFromSelectedOperator,
    CMXCopyPoseFromSelectedOperator,
    CMXCopyPoseApplyMeshesOperator,
    CMXApplyCurrentPoseAsRestWithMeshesOperator,
    CMXCreateArmatureSnapRefOperator,
    CMXSnapFromRefAndDeleteOperator,
    CMXPreviewEditAsPoseOperator,
    CMXClearPoseOperator,
    CMXSnapPoseFromRefOperator,
    CMXSnapPoseFromRefBakeOperator,
    CMXSnapPoseRefApplyMeshesOperator,
    CMXRenameBonesOperator,
    CMXRestoreBonesOperator,
    CMXHighlightConcaveFacesOperator,
    CMXAddPatternIndexOperator,
    CMXCFAddColorInputCtrlOperator,
    CMXAddColorInputDriverOperator
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

