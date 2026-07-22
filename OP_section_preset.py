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
from .OP_common import cmx_set_progress_error, cmx_set_progress_success, cmx_set_progress_task
from .system_var import *
from .enum_item_gen  import *
from .OP_char_preset import *

def cmx_add_preset_section_item(preset_key, name, context):
    """Add a preset section item and create icon image."""
    char_name = ACTIVE_CHAR['Char_name']
    if preset_key != "CrowdPreset":
        preset_by_char = f"{preset_key}_{char_name}"
        if preset_by_char not in PREVIEW_COLL:
            PREVIEW_COLL[preset_by_char] = bpy.utils.previews.new()
        icon_preview_collection = PREVIEW_COLL[preset_by_char]
    else:
        if preset_key not in PREVIEW_COLL:
            PREVIEW_COLL[preset_key] = bpy.utils.previews.new()
        icon_preview_collection = PREVIEW_COLL[preset_key]
    if preset_key == "HeadPreset":
        preset_path = "Head"
    elif preset_key == "BodyPreset":
        preset_path = "Body"
    else:
        return False, "Invalid preset key."
    char_folder = os.path.join(CURRENT_DIRECTORY, "CMX_Preset", preset_path, char_name) if preset_key != "CrowdPreset" else os.path.join(CURRENT_DIRECTORY, "CMX_Preset", "Crowd")
    if not os.path.exists(char_folder):
        os.makedirs(char_folder, exist_ok=True)
    image_path = os.path.join(char_folder, f"{name}.png")
    bpy.context.scene.render.filepath = image_path
    bpy.ops.render.opengl(write_still=True)
    json_file_path = os.path.join(char_folder, "items_data.json")
    data = {'items': []}
    if os.path.exists(json_file_path):
        with open(json_file_path, 'r') as f:
            data = json.load(f)
    if any(item['name'] == name for item in data['items']):
        return False, "Item name already exists."
    preset_data = {}
    if preset_key == "HeadPreset":
        for key, value in ACTIVE_CHAR.items():
            if key in HEAD_PRESET_PROP:
                preset_data[key] = value
    elif preset_key == "BodyPreset":
        for key, value in ACTIVE_CHAR.items():
            if key in BODY_PRESET_PROP:
                preset_data[key] = value
    data['items'].append({'name': name, 'image_path': f"{name}.png", 'data': preset_data})
    with open(json_file_path, 'w') as f:
        json.dump(data, f, indent=4)
    thumbnail = icon_preview_collection.load(name, image_path, 'IMAGE')
    icon_preview_collection[name] = thumbnail
    if preset_key == "HeadPreset":
        context.window_manager.head_preset = name
    elif preset_key == "BodyPreset":
        context.window_manager.body_preset = name
    elif preset_key == "CrowdPreset":
        context.window_manager.crowd_preset = name
    return True, "Item added successfully."

def cmx_remove_preset_section_item(preset_key, name, context):
    """Remove a preset section item and its files."""
    char_name = ACTIVE_CHAR.get('Char_name')
    if preset_key == "HeadPreset":
        preset_path = "Head"
    elif preset_key == "BodyPreset":
        preset_path = "Body"
    elif preset_key == "CrowdPreset":
        preset_path = "Crowd"
    else:
        return False, "Invalid preset key."
    if preset_key != "CrowdPreset":
        char_folder = os.path.join(CURRENT_DIRECTORY, "CMX_Preset", preset_path, char_name)
        preview_key = f"{preset_key}_{char_name}"
    else:
        char_folder = os.path.join(CURRENT_DIRECTORY, "CMX_Preset", "Crowd")
        preview_key = preset_key
    json_file_path = os.path.join(char_folder, "items_data.json")
    if not os.path.exists(json_file_path):
        return False, "Preset data file not found."
    with open(json_file_path, 'r') as f:
        data = json.load(f)
    data['items'] = [item for item in data['items'] if item['name'] != name]
    with open(json_file_path, 'w') as f:
        json.dump(data, f, indent=4)
    image_path = os.path.join(char_folder, f"{name}.png")
    if os.path.exists(image_path):
        os.remove(image_path)
    if preview_key in PREVIEW_COLL and name in PREVIEW_COLL[preview_key]:
        del PREVIEW_COLL[preview_key][name]
    if preview_key in PREVIEW_COLL and PREVIEW_COLL[preview_key].keys():
        first_item = list(PREVIEW_COLL[preview_key].keys())[0]
        if preset_key == "HeadPreset":
            context.window_manager.head_preset = first_item
        elif preset_key == "BodyPreset":
            context.window_manager.body_preset = first_item
        elif preset_key == "CrowdPreset":
            context.window_manager.crowd_preset = first_item
    return True, "Item removed successfully."

def cmx_apply_preset_section_item(preset_key, name, context):
    """Apply a preset section item by name."""
    cmx_set_progress_task("Load Preset", name)
    if preset_key == "HeadPreset":
        preset_path = "Head"
    elif preset_key == "BodyPreset":
        preset_path = "Body"
    char_folder = os.path.join(CURRENT_DIRECTORY, "CMX_Preset", preset_path, ACTIVE_CHAR['Char_name'])
    json_file_path = os.path.join(char_folder, "items_data.json")
    data = json.load(open(json_file_path))
    for item in data['items']:
        if item['name'] == name:
            preset_data = item["data"]
            try:
                cmx_set_char_to_preset(context, preset_data)
                cmx_set_progress_success(name)
            except Exception as e:
                cmx_set_progress_error(name, str(e))
                raise

class CMXPresetAddItemHeadOperator(bpy.types.Operator):
    """Add a new HeadPreset item and render its icon."""
    bl_idname = "cmx.preset_add_item_head"
    bl_label = "Add New Item"
    bl_description = "Add a new item and capture a viewport render as its icon"

    item_name: bpy.props.StringProperty(name="Preset Name", default="New Item") # type: ignore

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        success, message = cmx_add_preset_section_item("HeadPreset", self.item_name, context)
        if not success:
            self.report({'ERROR'}, message)
            return {'CANCELLED'}
        self.report({'INFO'}, message)
        return {'FINISHED'}

class CMXPresetAddItemBodyOperator(bpy.types.Operator):
    """Add a new BodyPreset item and render its icon."""
    bl_idname = "cmx.preset_add_item_body"
    bl_label = "Add New Item"
    bl_description = "Add a new item and capture a viewport render as its icon"

    item_name: bpy.props.StringProperty(name="Preset Name", default="New Item") # type: ignore

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        success, message = cmx_add_preset_section_item("BodyPreset", self.item_name, context)
        if not success:
            self.report({'ERROR'}, message)
            return {'CANCELLED'}
        self.report({'INFO'}, message)
        return {'FINISHED'}

class CMXPresetRemoveItemOperator(bpy.types.Operator):
    """Remove the selected preset item."""
    bl_idname = "cmx.preset_remove_item_headbody"
    bl_label = "Remove Selected Item"
    bl_description = "Remove the selected item and its associated data"
    preset_key: bpy.props.StringProperty(name="", default="") # type: ignore

    def execute(self, context):
        item_name = ""
        if self.preset_key == "HeadPreset":
            item_name = context.window_manager.head_preset
        elif self.preset_key == "BodyPreset":
            item_name = context.window_manager.body_preset
        if item_name:
            cmx_remove_preset_section_item(self.preset_key, item_name, context)
            self.report({'INFO'}, f"Removed item: {item_name}")
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, "No item selected.")
            return {'CANCELLED'}

class CMXPresetApplyOperator(bpy.types.Operator):
    """Apply the selected preset item."""
    bl_idname = "cmx.preset_apply_item_headbody"
    bl_label = "Apply Selected Item"
    bl_description = "Apply the selected preset"
    preset_key: bpy.props.StringProperty(name="", default="") # type: ignore

    def execute(self, context):
        item_name = ""
        if self.preset_key == "HeadPreset":
            item_name = context.window_manager.head_preset
        elif self.preset_key == "BodyPreset":
            item_name = context.window_manager.body_preset
        if item_name:
            cmx_apply_preset_section_item(self.preset_key, item_name, context)
            self.report({'INFO'}, f"Applied item: {item_name}")
            return {'FINISHED'}
        else:
            self.report({'ERROR'}, "No item selected.")
            return {'CANCELLED'}

class CMXResetFaceshapeOperator(bpy.types.Operator):
    """Reset all face shape sliders."""
    bl_idname = "cmx.reset_faceshape"
    bl_label = "Reset face shape"

    def execute(self, context):
        for key in FACE_SHAPE_KEY:
            setattr(context.window_manager, key, 0)
        return {'FINISHED'}

class CMXResetBodyshapeOperator(bpy.types.Operator):
    """Reset all body shape sliders."""
    bl_idname = "cmx.reset_bodyshape"
    bl_label = "Reset body shape"

    def execute(self, context):
        for key in BODY_SHAPE_KEY:
            setattr(context.window_manager, key, 0)
        return {'FINISHED'}

class CMXResetEmotionshapeOperator(bpy.types.Operator):
    """Reset all emotion shape sliders."""
    bl_idname = "cmx.reset_emotionshape"
    bl_label = "Reset emotion shape"

    def execute(self, context):
        for key in EMOTION_SHAPE_KEY:
            setattr(context.window_manager, key, 0)
        return {'FINISHED'}

classes = [
    CMXPresetApplyOperator,
    CMXPresetAddItemHeadOperator,
    CMXPresetAddItemBodyOperator,
    CMXPresetRemoveItemOperator,
    CMXResetFaceshapeOperator,
    CMXResetBodyshapeOperator,
    CMXResetEmotionshapeOperator
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
