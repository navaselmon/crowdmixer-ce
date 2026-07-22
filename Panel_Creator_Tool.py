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
from bpy.types import Panel


def cmx_draw_panel_creator(self, context, Main_panel_col):
    """
    Draws the Creator tools panel for utility operators in Crowd Mixer.

    Includes operators for creating templates, baking maps,
    preview camera tools, and bone/mesh utility operations.
    """
    wm = context.window_manager

    main_layout = Main_panel_col.column(align=True)
    compact = 1.15
    primary = 1.25

    def _draw_group_header(group_box, prop_name, title, title_icon):
        expanded = getattr(wm, prop_name, True)
        row = group_box.row(align=True)
        arrow_icon = "DOWNARROW_HLT" if expanded else "RIGHTARROW"
        row.prop(wm, prop_name, text="", toggle=True, emboss=False, icon=arrow_icon)
        row.prop(wm, prop_name, text=title, toggle=True, emboss=False, icon=title_icon)
        return getattr(wm, prop_name, True)

    # Group 1: collection template/json tools
    group_box = main_layout.box()
    if _draw_group_header(group_box, "creator_group_template_expanded", "Template Tools", "TOOL_SETTINGS"):
        col = group_box.column(align=True)
        col.scale_y = compact
        col.operator("cmx.create_collection_template_cf", text="Create Collection Template", icon="LINENUMBERS_ON")
        col.operator("cmx.create_json_item_list", text="Create Item List .json", icon="DOCUMENTS")
    main_layout.separator(factor=0.3)

    # Group 2: bake tools
    group_box = main_layout.box()
    if _draw_group_header(group_box, "creator_group_bake_expanded", "Bake Output", "RENDER_STILL"):
        row = group_box.row(align=True)
        row.scale_y = compact
        row.prop(wm, "cmx_bake_output_dir", text="")

        row = group_box.row(align=True)
        row.scale_y = compact
        row.prop(wm, "cmx_bake_color", text="Color")
        row.prop(wm, "cmx_bake_normal", text="Normal")
        row.prop(wm, "cmx_bake_ss_mask", text="SS Mask")

        row = group_box.row(align=True)
        row.scale_y = primary
        row.prop(wm, "cmx_bake_texture_size", text="Bake Size")
        row.operator("cmx.bake_selected_to_active", text="Bake", icon="RENDER_STILL")
    main_layout.separator(factor=0.3)

    # Group 3: save one blend file per action
    group_box = main_layout.box()
    if _draw_group_header(group_box, "creator_group_action_save_expanded", "Save Separate Actions", "ACTION"):
        row = group_box.row(align=True)
        row.scale_y = compact
        row.prop(wm, "cmx_separate_action_output_dir", text="")

        row = group_box.row(align=True)
        row.scale_y = primary
        row.operator("cmx.save_separate_actions", text="Save Separate Action Files", icon="FILE_BLEND")
    main_layout.separator(factor=0.3)

    # Group 4: preview camera/render item preview
    group_box = main_layout.box()
    if _draw_group_header(group_box, "creator_group_preview_expanded", "Preview", "IMAGE_RGB"):
        row = group_box.row(align=True)
        row.scale_y = compact
        row.operator("cmx.create_preview_cam", text="Create Preview Cam", icon="VIEW_CAMERA")
        row.operator("cmx.remove_preview_cam_cf", text="Remove Preview Cam", icon="OUTLINER_DATA_CAMERA")

        col = group_box.column(align=True)
        col.scale_y = compact
        col.prop(wm, "gen_preview_filter", text="Item")

        row = col.row(align=True)
        row.scale_y = primary
        row.operator("cmx.render_item_preview_cf", text="Render Item Preview", icon="IMAGE_RGB")

        group_box.separator(factor=0.4)
        row = group_box.row(align=True)
        row.scale_y = compact
        row.prop(wm, "anim_filter", text="Anim Filter")

        row = group_box.row(align=True)
        row.scale_y = compact
        row.prop(wm, "cmx_anim_preview_write_mode", text="")

        row = group_box.row(align=True)
        row.scale_y = primary
        row.operator("cmx.render_anim_preview_cf", text="Render Anim Preview", icon="RENDER_STILL")
    main_layout.separator(factor=0.3)

    # Group 5: rename bones for mirror transformation
    group_box = main_layout.box()
    if _draw_group_header(group_box, "creator_group_mirror_expanded", "Mirror Bone Names", "ARMATURE_DATA"):
        row = group_box.row(align=True)
        row.scale_y = compact
        row.operator("cmx.rename_bones", text="Rename Bones", icon="RENDER_ANIMATION")
        row.operator("cmx.restore_bones", text="Restore Name", icon="PLAY")
    main_layout.separator(factor=0.3)

    # Group 6: bone remap pose/restpose
    group_box = main_layout.box()
    if _draw_group_header(group_box, "creator_group_remap_expanded", "Bone Remap Pose/Restpose", "POSE_HLT"):
        row = group_box.row(align=True)
        row.scale_y = compact
        row.operator("cmx.copy_bones_from_selected", text="[Edit] Active -> Source", icon="SNAP_ON")

        row = group_box.row(align=True)
        row.scale_y = compact
        row.operator("cmx.copy_pose_from_selected", text="[Pose] Active -> Source", icon="POSE_HLT")

        row = group_box.row(align=True)
        row.scale_y = compact
        row.operator("cmx.copy_pose_from_selected_apply_mesh", text="[RestPose + Mesh] Active -> Source", icon="MESH_DATA")

        row = group_box.row(align=True)
        row.scale_y = compact
        row.operator("cmx.apply_pose_as_rest_with_mesh", text="Apply Pose + Mesh -> RestPose", icon="ARMATURE_DATA")

        row = group_box.row(align=True)
        row.scale_y = compact
        row.operator("cmx.preview_edit_as_pose", text="Preview Edit As Pose", icon="POSE_HLT")
        row.operator("cmx.clear_pose_all", text="Clear Pose", icon="LOOP_BACK")
    main_layout.separator(factor=0.3)

    # Group 7: mesh face utilities
    group_box = main_layout.box()
    if _draw_group_header(group_box, "creator_group_mesh_expanded", "Mesh Check", "MESH_DATA"):
        row = group_box.row(align=True)
        row.scale_y = compact
        row.operator("cmx.highlight_concave_faces", text="Highlight Concave Faces", icon="OUTLINER_DATA_MESH")
