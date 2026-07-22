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
from .system_icon import get_cf_icon
from .enum_item_gen import cmx_source_blend_items
from .system_var import ACTIVE_CHAR
from .OP_link_asset import cmx_load_character_rig
from .OP_common import cmx_get_source_dir, cmx_get_dir_asset_path, cmx_check_asset_path


class CMXSourceBlendItem(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name="Name")  # type: ignore
    file_path: bpy.props.StringProperty(name="File Path")  # type: ignore


class CMX_UL_SourceBlend(bpy.types.UIList):
    """UIList for saved source .blend files."""

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        split = layout.split(factor=0.7)
        split.label(text=item.name, icon_value=get_cf_icon("main_panel_crowd_source"))
        split.label(text=os.path.basename(item.file_path))


class CMXRefreshSourceListOperator(bpy.types.Operator):
    """Refresh the source .blend list from CMX-Source folder."""
    bl_idname = "cmx.source_refresh_list"
    bl_label = "Refresh Source List"

    def execute(self, context):
        wm = context.window_manager
        enum_items = cmx_source_blend_items(None, context)
        wm.cmx_source_items.clear()
        for name, _, path, _, _ in enum_items:
            item = wm.cmx_source_items.add()
            item.name = name
            item.file_path = path
        if wm.cmx_source_items:
            wm.cmx_source_index = min(wm.cmx_source_index, len(wm.cmx_source_items) - 1)
        else:
            wm.cmx_source_index = 0
        context.area.tag_redraw()
        return {'FINISHED'}


def cmx_draw_panel_source(self, context, Main_panel_col):
    """
    Draw the Source panel: list saved sources and load active character assets.
    """
    wm = context.window_manager
    main_layout = Main_panel_col.column(align=True)
    col = main_layout.column(align=True)
    col.label(text="Source Library", icon_value=get_cf_icon("main_panel_crowd_source"))

    row = col.row(align=True)
    row.template_list("CMX_UL_SourceBlend", "", wm, "cmx_source_items", wm, "cmx_source_index", rows=8)
    row_operators = row.column(align=True)
    row_operators.operator("cmx.source_refresh_list", text="", icon='FILE_REFRESH')

    col.separator(factor=1.0)
    # Additional actions can be added here if needed


classes = [
    CMXSourceBlendItem,
    CMX_UL_SourceBlend,
    CMXRefreshSourceListOperator,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.WindowManager.cmx_source_items = bpy.props.CollectionProperty(type=CMXSourceBlendItem)
    bpy.types.WindowManager.cmx_source_index = bpy.props.IntProperty()


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    del bpy.types.WindowManager.cmx_source_items
    del bpy.types.WindowManager.cmx_source_index
