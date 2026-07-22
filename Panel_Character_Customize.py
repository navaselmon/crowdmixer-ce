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
from .OP_preview import *
from .OP_section_preset import *
from .OP_Spawn import *
from collections import defaultdict

def cmx_draw_panel_char_custom(self, context, Main_panel_col):
    """
    Draws the main character customization panel including all tabs (Head, Body, Cloth, Animation).
    """
    wm = context.window_manager
    pop_size = cmx_get_popup_preview_size(context)

    label_row = Main_panel_col.row(align=True)
    label_row.alignment = 'CENTER'
    Main_panel_col.separator(factor=0.75)

    row = Main_panel_col.row(align=True)
    row.alignment = 'CENTER'
    row.scale_y = 1.15
    on_off_label = "Customize ON" if wm.cf_on_off_toggle else "Customize OFF"
    split = row.split(factor=0.18, align=True)
    split.column()
    center_row = split.row(align=True)
    center_split = center_row.split(factor=0.78, align=True)
    center_button = center_split.row(align=True)
    center_button.prop(wm, 'cf_on_off_toggle', text=on_off_label, toggle=True, emboss=True, icon_only=False)
    center_split.column()

    use_single = True

    frame = Main_panel_col.box()
    main_layout = frame.column(align=True)

    if use_single:
        filter_row = main_layout.row(align=True)
        filter_row.enabled = wm.cf_on_off_toggle
        filter_row.prop(wm, "single_char_filter", text="")
        main_layout.separator(factor=0.5)

    # Character Preview & Controls
    col = main_layout.column(align=True)
    row_L1 = col.row()
    col_L2 = row_L1.column(align=True)
    col_L3 = col_L2.column(align=True)
    col_L3.enabled = wm.cf_on_off_toggle
    col_L3.template_icon_view(wm, "char_previews", show_labels=True, scale=ICON_VIEW_SCALE + 2, scale_popup=pop_size)
    col_L3.prop(wm, "char_preview_rotation_z", text="")
    col_L3.operator("cmx.place_char_to_scene", text="Snap to scene", icon_value=get_cf_icon("main_panel_preset_apply"))
    col_L3.separator(factor=3.0)

    last_name = getattr(wm, "last_instance_name", "")
    obj = context.active_object
    if obj and obj.instance_type == 'COLLECTION':
        if last_name != obj.name:
            cmx_sync_props_from_instance(context)
            wm.last_instance_name = obj.name
    else:
        wm.last_instance_name = ""

    control_col = row_L1.column(align=True)
    locked_controls = control_col.column(align=True)
    locked_controls.enabled = wm.cf_on_off_toggle
    locked_controls.operator("cmx.add_preset_char", text="", icon_value=get_cf_icon("main_panel_customize_add_ch_preset"))
    locked_controls.separator(factor=0.4)
    locked_controls.prop(wm, 'vis_proxy_toggle', toggle=True, text="", icon_value=get_cf_icon("sub_panel_anim_vis_proxy"))
    locked_controls.prop(wm, 'vis_amature_toggle', toggle=True, text="", icon_value=get_cf_icon("sub_panel_anim_vis_bone"))
    locked_controls.prop(wm, "preview_on_3d_cursor", text="", icon="CURSOR")
    control_col.prop(wm, "show_instance_anim_settings", toggle=True, text="", icon="NLA")

    if wm.show_instance_anim_settings:
        instance_box = col.box()
        instance_box.label(text="Instance Anim Setting")
        col_L2 = instance_box.column(align=True)
        col_L2.prop(wm, "offset_start_frame_ins")
        col_L2.prop(wm, "set_anim_speed_ins")

    

    if use_single:
        # Single-Mesh: show only Animation section
        main_layout.separator(factor=1.0)
        sub_panel_box = main_layout.box()
        sub_panel_box.enabled = wm.cf_on_off_toggle
        sub_panel_frame = sub_panel_box.column()

        col_L2 = sub_panel_frame.column(align=True)

        row_L3 = col_L2.row(align=True)
        row_L3.prop(wm, "anim_filter", text="")

        row_L3 = col_L2.row(align=True)
        col_L2_left = row_L3.column()
        col_L2_left.scale_y = ICON_VIEW_SCALE
        col_L2_left.operator("cmx.previous_item", text="", icon="TRIA_LEFT").icon_view_name = "anim_previews"

        col_L2_center = row_L3.column(align=True)
        col_L2_center.alignment = 'CENTER'
        col_L2_center.template_icon_view(wm, "anim_previews", show_labels=True, scale=ICON_VIEW_SCALE, scale_popup=pop_size)

        col_L2_right = row_L3.column()
        col_L2_right.scale_y = ICON_VIEW_SCALE
        col_L2_right.operator("cmx.next_item", text="", icon="RIGHTARROW").icon_view_name = "anim_previews"

        row_L3 = col_L2.row(align=True)
        row_L3.prop(wm, 'anim_use_toggle', toggle=True, text="Apply", icon_only=True, icon_value=get_cf_icon("sub_panel_anim_apply"))
        row_L3.prop(wm, 'set_frame_range_toggle', toggle=True, text="", icon_value=get_cf_icon("sub_panel_anim_range"))
        return
    else:
        main_layout.separator(factor=1.0)
        row_info_tab = main_layout.row(align=True)
        row_info_tab.alignment = 'CENTER'
        row_info_tab.label(text=f"{wm.cf_customize_tab} Setting")

        row_head_panel = main_layout.row(align=True)
        row_head_panel.label(text="", icon_value=get_cf_icon("head_panel_corner_left"))

        grid = row_head_panel.grid_flow(align=True)
        grid.prop(wm, 'cf_customize_tab', toggle=True, expand=True, icon_only=True)

        row_head_panel.label(text="", icon_value=get_cf_icon("head_panel_corner_right"))

        sub_panel_box = main_layout.box()
        sub_panel_box.enabled = wm.cf_on_off_toggle
        sub_panel_frame = sub_panel_box.column()

        # HEAD TAB
        if wm.cf_customize_tab == "Head":
            col_L0 = sub_panel_frame.column(align=True)
            cmx_draw_preview_set(self, context, "Head Preset", wm, "head_preset", col_L0, pop_size, ICON_VIEW_SCALE, "preset", preset_key="HeadPreset")

            box_L1 = col_L0.box()
            col_L2 = box_L1.column()
            icon = 'DOWNARROW_HLT' if wm.sub_panel_L1_hair_expanded else 'RIGHTARROW'
            col_L2.prop(wm, "sub_panel_L1_hair_expanded", text="Hair", toggle=True, icon=icon, emboss=False)
            if wm.sub_panel_L1_hair_expanded:
                cmx_draw_preview_bodypart(self, context, "Hair", wm, col_L2, pop_size, ICON_VIEW_SCALE)

            box_L1 = col_L0.box()
            col_L2 = box_L1.column()
            icon = 'DOWNARROW_HLT' if wm.sub_panel_L1_makeup_expanded else 'RIGHTARROW'
            col_L2.prop(wm, "sub_panel_L1_makeup_expanded", text="Face", toggle=True, icon=icon, emboss=False)
            if wm.sub_panel_L1_makeup_expanded:
                cmx_draw_preview_set(self, context, "Makeup", wm, "makeup_previews", col_L2, pop_size, ICON_VIEW_SCALE, "subpanel")

            box_L1 = col_L0.box()
            col_L2 = box_L1.column()
            icon = 'DOWNARROW_HLT' if wm.sub_panel_L1_faceshape_expanded else 'RIGHTARROW'
            col_L2.prop(wm, "sub_panel_L1_faceshape_expanded", text="Face Shape", toggle=True, icon=icon, emboss=False)
            if wm.sub_panel_L1_faceshape_expanded:
                row_L3 = col_L2.row()
                row_L3.alignment = 'RIGHT'
                row_L3.prop(wm, "sub_panel_L1_use_guide_faceshape", text="", toggle=False)
                row_L3.label(text="Guide ")
                row_L3.operator("cmx.reset_faceshape", text="Reset")

                group_dict = defaultdict(list)
                for p_name in FACE_SHAPE_KEY:
                    key_body = p_name.replace("Face_Key_", "")
                    parts = key_body.split("_", 1)
                    group, subname = parts if len(parts) == 2 else (parts[0], "")
                    group_dict[group].append((subname, p_name))

                for group, sublist in group_dict.items():
                    group_box = col_L2.box()
                    group_col = group_box.column(align=True)
                    group_col.label(text=group)
                    for subname, p_name in sublist:
                        l_text = subname.replace("_", " ").capitalize()
                        cmx_drow_slide_bar(l_text, p_name, p_name, group_col, wm, "image", use_guide=wm.sub_panel_L1_use_guide_faceshape)

            box_L1 = col_L0.box()
            col_L2 = box_L1.column(align=True)
            icon = 'DOWNARROW_HLT' if wm.sub_panel_L1_emotion_expanded else 'RIGHTARROW'
            col_L2.prop(wm, "sub_panel_L1_emotion_expanded", text="Emotion", toggle=True, icon=icon, emboss=False)
            if wm.sub_panel_L1_emotion_expanded:
                row_L3 = col_L2.row()
                row_L3.alignment = 'RIGHT'
                row_L3.prop(wm, "sub_panel_L1_use_guide_emotion", text="", toggle=False)
                row_L3.label(text="Guide ")
                row_L3.operator("cmx.reset_emotionshape", text="Reset")

                for p_name in EMOTION_SHAPE_KEY:
                    icon_name = p_name
                    l_text = p_name.replace("Emotion_key_", "")
                    cmx_drow_slide_bar(l_text, icon_name, p_name, col_L2, wm, "image", use_guide=wm.sub_panel_L1_use_guide_emotion)

        # BODY TAB
        elif wm.cf_customize_tab == "Body":
            col_L0 = sub_panel_frame.column(align=True)
            cmx_draw_preview_set(self, context, "Body Preset", wm, "body_preset", col_L0, pop_size, ICON_VIEW_SCALE, "preset", preset_key="BodyPreset")

            box_L1 = col_L0.box()
            col_L2 = box_L1.column(align=True)
            icon = 'DOWNARROW_HLT' if wm.sub_panel_L1_skin_expanded else 'RIGHTARROW'
            col_L2.prop(wm, "sub_panel_L1_skin_expanded", text="Skin", toggle=True, icon=icon, emboss=False)
            if wm.sub_panel_L1_skin_expanded:
                cmx_draw_preview_set(self, context, "Skin", wm, "skin_previews", col_L2, pop_size, ICON_VIEW_SCALE, "subpanel")

            box_L1 = col_L0.box()
            col_L2 = box_L1.column()
            icon = 'DOWNARROW_HLT' if wm.sub_panel_L1_bodyshape_expanded else 'RIGHTARROW'
            col_L2.prop(wm, "sub_panel_L1_bodyshape_expanded", text="Body Shape", toggle=True, icon=icon, emboss=False)
            if wm.sub_panel_L1_bodyshape_expanded:
                row_L3 = col_L2.row()
                row_L3.alignment = 'RIGHT'
                row_L3.prop(wm, "sub_panel_L1_use_guide_bodyshape", text="", toggle=False)
                row_L3.label(text="Guide ")
                row_L3.operator("cmx.reset_bodyshape", text="Reset")

                group_dict = defaultdict(list)
                for p_name in BODY_SHAPE_KEY:
                    key_body = p_name.replace("Body_Key_", "")
                    parts = key_body.split("_", 1)
                    group, subname = parts if len(parts) == 2 else (parts[0], "")
                    group_dict[group].append((subname, p_name))

                for group, sublist in group_dict.items():
                    group_box = col_L2.box()
                    group_col = group_box.column(align=True)
                    group_col.label(text=group)
                    for subname, p_name in sublist:
                        l_text = subname.replace("_", " ").capitalize()
                        cmx_drow_slide_bar(l_text, p_name, p_name, group_col, wm, "image", use_guide=wm.sub_panel_L1_use_guide_bodyshape)

        # CLOTH TAB
        elif wm.cf_customize_tab == "Cloth":
            col_L0 = sub_panel_frame.column(align=True)
            row = col_L0.row()
            row.prop(wm, "cloths_filter", text="", icon_value=get_cf_icon("sub_panel_cloth_filter"))
            row.scale_x = 1
            row.operator("cmx.random_item", text="", icon_value=get_cf_icon("sub_panel_cloth_random")).preview_key = "All_BODY_PART"

            vis_status = getattr(wm, "item_off_all", None)
            vis_icon = "sub_panel_cloth_unlink" if vis_status else 'sub_panel_cloth_link'
            row.prop(wm, "item_off_all", toggle=True, text="", emboss=False, icon_value=get_cf_icon(vis_icon))

            cmx_draw_preview_bodypart(self, context, "Head", wm, col_L0, pop_size, ICON_VIEW_SCALE)
            cmx_draw_preview_bodypart(self, context, "Eye", wm, col_L0, pop_size, ICON_VIEW_SCALE)
            cmx_draw_preview_bodypart(self, context, "Torso", wm, col_L0, pop_size, ICON_VIEW_SCALE)
            cmx_draw_preview_bodypart(self, context, "Leg", wm, col_L0, pop_size, ICON_VIEW_SCALE)
            cmx_draw_preview_bodypart(self, context, "Accessory", wm, col_L0, pop_size, ICON_VIEW_SCALE)
            cmx_draw_preview_bodypart(self, context, "Foot", wm, col_L0, pop_size, ICON_VIEW_SCALE)

        # ANIMATION TAB
        elif wm.cf_customize_tab == "Animation":
            col_L2 = sub_panel_frame.column(align=True)

            row_L3 = col_L2.row(align=True)
            row_L3.prop(wm, "anim_filter", text="")

            row_L3 = col_L2.row(align=True)
            col_L2_left = row_L3.column()
            col_L2_left.scale_y = ICON_VIEW_SCALE
            col_L2_left.operator("cmx.previous_item", text="", icon="TRIA_LEFT").icon_view_name = "anim_previews"

            col_L2_center = row_L3.column(align=True)
            col_L2_center.alignment = 'CENTER'
            col_L2_center.template_icon_view(wm, "anim_previews", show_labels=True, scale=ICON_VIEW_SCALE, scale_popup=pop_size)

            col_L2_right = row_L3.column()
            col_L2_right.scale_y = ICON_VIEW_SCALE
            col_L2_right.operator("cmx.next_item", text="", icon="RIGHTARROW").icon_view_name = "anim_previews"

            row_L3 = col_L2.row(align=True)
            row_L3.prop(wm, 'anim_use_toggle', toggle=True, text="Apply", icon_only=True, icon_value=get_cf_icon("sub_panel_anim_apply"))
            row_L3.prop(wm, 'set_frame_range_toggle', toggle=True, text="", icon_value=get_cf_icon("sub_panel_anim_range"))

def cmx_draw_preview_bodypart(self, context, body_path_key, wm, col_L0, pop_size, ICON_VIEW_SCALE):
    """
    Draws the preview controls for a single body part (used in Cloth/Body/Head tabs).
    """
    if body_path_key != "Hair":
        box_L1 = col_L0.box()
        col_L2 = box_L1.column(align=True)
        row_L3 = col_L2.row(align=True)
    else:
        box_L1 = col_L0.column()
        col_L2 = box_L1.column(align=True)
        row_L3 = col_L2.row(align=True)

    sprite = row_L3.split(factor=0.5)
    row_L4_left = sprite
    if body_path_key != "Hair":
        row_L4_left.label(text=body_path_key, icon="MOD_CLOTH")
    else:
        row_L4_left.label(text=" ")

    row_L3 = col_L2.row(align=True)
    col_L2_center = row_L3.column(align=True)
    col_L2_center.alignment = 'CENTER'
    row_L3 = col_L2_center.row(align=True)

    col_L4 = row_L3.column()
    col_L4.scale_y = ICON_VIEW_SCALE
    col_L4.operator("cmx.previous_item", text="", icon="TRIA_LEFT").icon_view_name = BODY_PATH_PROB_COLL[body_path_key][0]

    row_L3.template_icon_view(wm, BODY_PATH_PROB_COLL[body_path_key][0], show_labels=True, scale=ICON_VIEW_SCALE, scale_popup=pop_size)

    col_L4 = row_L3.column()
    col_L4.scale_y = ICON_VIEW_SCALE
    col_L4.operator("cmx.next_item", text="", icon="RIGHTARROW").icon_view_name = BODY_PATH_PROB_COLL[body_path_key][0]

    col_L2_right = row_L3.column()
    col_L2_right.scale_x = 0.25
    col_L2_right.scale_y = ICON_VIEW_SCALE / 3
    col_L2_right.operator("cmx.random_item", text="", emboss=True, icon_value=get_cf_icon("sub_panel_cloth_random")).preview_key = body_path_key

    vis_status = getattr(wm, BODY_PATH_PROB_COLL[body_path_key][2], None)
    vis_icon = "sub_panel_cloth_unlink" if vis_status else 'sub_panel_cloth_link'
    col_L2_right.prop(wm, BODY_PATH_PROB_COLL[body_path_key][2], toggle=True, text="", emboss=False, icon_value=get_cf_icon(vis_icon))
    col_L2_right.prop(wm, BODY_PATH_PROB_COLL[body_path_key][1], icon_only=True)

    row_L3 = col_L2.row(align=True)
    row_L3.alignment = 'LEFT'

    if ACTIVE_CHAR[body_path_key]:
        coll_name = "CMX_" + body_path_key
        collection = bpy.data.collections.get(coll_name)
        obj = collection.objects.get(ACTIVE_CHAR[body_path_key]) if collection else None
        if obj:
            mat = obj.active_material
            if mat and "Pattern_Index" in mat:
                current_index = int(mat["Pattern_Index"])
                try:
                    prop_ui = mat.id_properties_ui("Pattern_Index")
                    max_index = int(prop_ui.as_dict().get("max", current_index))
                except Exception:
                    max_index = current_index

                row = row_L3.row(align=True)
                for i in range(max_index + 1):
                    op = row.operator("cmx.set_pattern_index", text="", icon='SHADING_RENDERED', depress=(i == current_index))
                    op.index = i
                    op.object_name = obj.name
                    op.coll_name = coll_name

def cmx_draw_preview_bodypart(self, context, body_path_key, wm, col_L0, pop_size, ICON_VIEW_SCALE):
    """
    Draws the preview controls for a single body part (used in Cloth/Body/Head tabs).
    """
    if body_path_key != "Hair":
        box_L1 = col_L0.box()
        col_L2 = box_L1.column(align=True)
        row_L3 = col_L2.row(align=True)
    else:
        box_L1 = col_L0.column()
        col_L2 = box_L1.column(align=True)
        row_L3 = col_L2.row(align=True)

    sprite = row_L3.split(factor=0.5)
    row_L4_left = sprite
    if body_path_key != "Hair":
        row_L4_left.label(text=body_path_key, icon="MOD_CLOTH")
    else:
        row_L4_left.label(text=" ")

    row_L3 = col_L2.row(align=True)
    col_L2_center = row_L3.column(align=True)
    col_L2_center.alignment = 'CENTER'
    row_L3 = col_L2_center.row(align=True)

    col_L4 = row_L3.column()
    col_L4.scale_y = ICON_VIEW_SCALE
    col_L4.operator("cmx.previous_item", text="", icon="TRIA_LEFT").icon_view_name = BODY_PATH_PROB_COLL[body_path_key][0]

    row_L3.template_icon_view(wm, BODY_PATH_PROB_COLL[body_path_key][0], show_labels=True, scale=ICON_VIEW_SCALE, scale_popup=pop_size)

    col_L4 = row_L3.column()
    col_L4.scale_y = ICON_VIEW_SCALE
    col_L4.operator("cmx.next_item", text="", icon="RIGHTARROW").icon_view_name = BODY_PATH_PROB_COLL[body_path_key][0]

    col_L2_right = row_L3.column()
    col_L2_right.scale_x = 0.25
    col_L2_right.scale_y = ICON_VIEW_SCALE / 3
    col_L2_right.operator("cmx.random_item", text="", emboss=True, icon_value=get_cf_icon("sub_panel_cloth_random")).preview_key = body_path_key

    vis_status = getattr(wm, BODY_PATH_PROB_COLL[body_path_key][2], None)
    vis_icon = "sub_panel_cloth_unlink" if vis_status else 'sub_panel_cloth_link'
    col_L2_right.prop(wm, BODY_PATH_PROB_COLL[body_path_key][2], toggle=True, text="", emboss=False, icon_value=get_cf_icon(vis_icon))
    col_L2_right.prop(wm, BODY_PATH_PROB_COLL[body_path_key][1], icon_only=True)

    row_L3 = col_L2.row(align=True)
    row_L3.alignment = 'LEFT'

    if ACTIVE_CHAR[body_path_key]:
        coll_name = "CMX_" + body_path_key
        collection = bpy.data.collections.get(coll_name)
        obj = collection.objects.get(ACTIVE_CHAR[body_path_key]) if collection else None
        if obj:
            mat = obj.active_material
            if mat and "Pattern_Index" in mat:
                current_index = int(mat["Pattern_Index"])
                try:
                    prop_ui = mat.id_properties_ui("Pattern_Index")
                    max_index = int(prop_ui.as_dict().get("max", current_index))
                except Exception:
                    max_index = current_index

                row = row_L3.row(align=True)
                for i in range(max_index + 1):
                    op = row.operator("cmx.set_pattern_index", text="", icon='SHADING_RENDERED', depress=(i == current_index))
                    op.index = i
                    op.object_name = obj.name
                    op.coll_name = coll_name

def cmx_draw_preview_set(
    self, context, label_text, wm, property_name, col_L0, pop_size, ICON_VIEW_SCALE, style, preset_key=""
):
    """
    Draws a preview set UI for either a preset selector or a subpanel icon view in Blender UI.

    """
    if style == "preset":
        box_L1 = col_L0.box()
        col_L1 = box_L1.column(align=True)
        row_L2 = col_L1.row()
        row_L2.label(text=label_text, icon_value=get_cf_icon("cf_preset_panel"))

        row_L2 = col_L1.row(align=True)
        col_L3_center = row_L2.column(align=True)
        col_L3_center.alignment = 'CENTER'
        col_L3_center.template_icon_view(
            wm, property_name, show_labels=True, scale=ICON_VIEW_SCALE, scale_popup=pop_size
        )
        col_L3_right = row_L2.column(align=True)

        if preset_key == "HeadPreset":
            col_L3_right.operator(
                "cmx.preset_add_item_head", text="", icon_value=get_cf_icon("cf_new_preset")
            )
            remove_op = col_L3_right.operator(
                "cmx.preset_remove_item_headbody", text="", icon_value=get_cf_icon("main_panel_crowd_remove")
            )
            remove_op.preset_key = preset_key
            apply_op = col_L3_center.operator(
                "cmx.preset_apply_item_headbody", text="Apply", icon_value=get_cf_icon("main_panel_preset_apply")
            )
            apply_op.preset_key = preset_key

        elif preset_key == "BodyPreset":
            col_L3_right.operator(
                "cmx.preset_add_item_body", text="", icon_value=get_cf_icon("cf_new_preset")
            )
            remove_op = col_L3_right.operator(
                "cmx.preset_remove_item_headbody", text="", icon_value=get_cf_icon("main_panel_crowd_remove")
            )
            remove_op.preset_key = preset_key
            apply_op = col_L3_center.operator(
                "cmx.preset_apply_item_headbody", text="Apply", icon_value=get_cf_icon("main_panel_preset_apply")
            )
            apply_op.preset_key = preset_key

    elif style == "subpanel":
        row_L2 = col_L0.row(align=True)
        col_L3_center = row_L2.column()
        col_L3_center.alignment = 'CENTER'
        row_L4 = col_L3_center.row(align=True)

        col_L5 = row_L4.column()
        col_L5.scale_y = ICON_VIEW_SCALE
        col_L5.operator("cmx.previous_item", text="", icon="TRIA_LEFT").icon_view_name = property_name

        row_L4.template_icon_view(
            wm, property_name, show_labels=True, scale=ICON_VIEW_SCALE, scale_popup=pop_size
        )

        col_L5 = row_L4.column()
        col_L5.scale_y = ICON_VIEW_SCALE
        col_L5.operator("cmx.next_item", text="", icon="RIGHTARROW").icon_view_name = property_name

        col_L3_right = row_L2.column(align=True)
        col_L3_right.operator(
            "cmx.random_item", text="", icon_value=get_cf_icon("sub_panel_cloth_random")
        ).preview_key = property_name
 
def cmx_drow_slide_bar(l_text, icon_name, prop_name, col, wm, style, use_guide=True):
    """
    Draws a labeled slider UI element with either icon or image style.

    Args:
        l_text (str): The label text for the slider.
        icon_name (str): Icon or image identifier.
        prop_name (str): The property name to control.
        col: The Blender UI column/layout to draw into.
        wm: The Blender window manager (property context).
        style (str): 'icon' or 'image' (type of slider).
        use_guide (bool): Whether to display the guide image (for 'image' style).
    """
    if style == "icon":
        col.alignment = 'LEFT'
        split = col.split(factor=0.1)
        left_col = split.column(align=True)
        right_col = split.column(align=True)
        left_col.label(icon_value=get_cf_icon(icon_name))
        right_col.prop(wm, prop_name, text=l_text, slider=True, icon_value=get_cf_icon(icon_name))

    elif style == "image":
        if use_guide:
            col.template_icon(icon_value=get_cf_icon_image(icon_name), scale=4.5)
            col.prop(wm, prop_name, text=l_text, slider=True)
        else:
            split_L1 = col.split(factor=0.4, align=True)
            left_col = split_L1.column(align=True)
            right_col = split_L1.column(align=True)
            left_col.alignment = 'RIGHT'
            left_col.label(text=l_text)
            right_col.prop(wm, prop_name, text="", slider=True)

def cmx_sync_props_from_instance(context):
    """
    Synchronize animation properties (offset and speed) from the active collection instance to the WindowManager.
    Looks for the first armature with NLA strips and applies its first strip settings.
    """
    obj = context.active_object
    if obj and obj.instance_type == 'COLLECTION':
        src_coll = obj.instance_collection
        if not src_coll:
            return
        for armature_obj in src_coll.objects:
            if armature_obj.type == 'ARMATURE':
                if armature_obj.animation_data and armature_obj.animation_data.nla_tracks:
                    for track in armature_obj.animation_data.nla_tracks:
                        for strip in track.strips:
                            context.window_manager.offset_start_frame_ins = int(strip.frame_start)
                            context.window_manager.set_anim_speed_ins = float(getattr(strip, "scale", 1.0))
                            return  # Sync only the first found strip

         
