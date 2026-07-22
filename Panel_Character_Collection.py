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
import json
import os
from bpy.props import StringProperty, IntProperty, BoolProperty

from .OP_char_preset import *
from .system_icon import *
from .OP_common import cmx_show_message_box, cmx_set_progress_task, cmx_get_source_dir
from .system_var import ACTIVE_CHAR

def cmx_draw_panel_char_coll(self, context, Main_panel_col):
    """
    Draw the Character Preset Collection Panel UI (Preset List and buttons).
    """
    wm = context.window_manager
    # Load preset items if not already loaded
    if not hasattr(wm, "preset_items") or len(wm.preset_items) == 0:
        try:
            cmx_load_preset_List_data(context)
        except Exception:
            pass

    main_layout = Main_panel_col.column(align=True)
    col = main_layout.column()
    col.label(text="Preset List", icon_value=get_cf_icon("main_panel_crowd_list"))
    col.prop(wm, "cf_preset_edit_mode", text="Edit Preset", toggle=True)

    col_L1 = col.row()
    col_L1.template_list("CMX_UL_PresetData", "", wm, "preset_items", wm, "preset_item_index", rows=20)
    col_L2 = col_L1.column(align=True)
    col_L2.operator("cmx.add_preset_collection_char", text="", icon_value=get_cf_icon("main_panel_preset_collection_add"))
    col_L2.operator("cmx.sort_preset_collection_char", text="", icon='SORTALPHA')

    col_L1 = col.row()
    col_L1.enabled = wm.cf_on_off_toggle
    col_L2 = col_L1.column(align=True)
    col_L2.prop(wm, "char_preview_rotation_z", text="")
    col_L2.operator("cmx.place_char_to_scene", text="Snap to scene", icon_value=get_cf_icon("main_panel_preset_apply"))

def cmx_get_char_preset_file_path():
    """
    Return the absolute path to the char_preset.json file for preset collections/presets.
    """
    data_dir = os.path.join(CURRENT_DIRECTORY, "CMX_Data")
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    return os.path.join(data_dir, "char_preset.json")

def cmx_replace_collection_in_order(collection_order, old_name, new_name):
    """Replace a collection name in an ordered list while keeping its position."""
    updated_order = list(collection_order or [])
    try:
        index = updated_order.index(old_name)
        updated_order[index] = new_name
    except ValueError:
        updated_order.append(new_name)
    return updated_order

class CMXPresetItemPropertyGroup(bpy.types.PropertyGroup):
    """PropertyGroup for individual preset/collection items in the UI list."""
    collection: bpy.props.StringProperty(name="Collection")# type: ignore
    preset: bpy.props.StringProperty(name="Preset")# type: ignore
    is_preset: bpy.props.BoolProperty(name="Is Preset", default=False)# type: ignore
    expanded: bpy.props.BoolProperty(name="Expanded", default=True)# type: ignore

class CMX_UL_PresetData(bpy.types.UIList):
    """UIList for displaying and managing character preset collections and presets."""
    def _cmx_ensure_ui_cache(self, items):
        cache_size = len(items)
        cache_signature = tuple(
            (item.collection, bool(item.is_preset), item.preset if item.is_preset else "", bool(getattr(item, "expanded", False)))
            for item in items
        )
        if (
            getattr(self, "_cmx_cache_size", None) == cache_size and
            getattr(self, "_cmx_cache_signature", None) == cache_signature
        ):
            return

        build_state_by_collection = {}
        for item in items:
            if item.is_preset:
                continue
            build_state_by_collection[item.collection] = cmx_get_collection_build_status(item.collection)

        self._cmx_cache_size = cache_size
        self._cmx_cache_signature = cache_signature
        self._cmx_build_state_by_collection = build_state_by_collection

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        wm = context.window_manager
        items = getattr(data, active_propname.replace("_index", "items"), None)
        if items is None:
            items = getattr(data, "preset_items", [])
        self._cmx_ensure_ui_cache(items)

        row = layout.row(align=True)
 
        if not item.is_preset:  # Collection
            icon_val = 'TRIA_DOWN' if item.expanded else 'TRIA_RIGHT'
            op_expand = row.operator("cmx.toggle_preset_collection_expand", text="", icon=icon_val, emboss=False)
            op_expand.collection_name = item.collection
            row.label(text=item.collection, icon_value=get_cf_icon("main_panel_preset_collection"))
            build_state = getattr(self, "_cmx_build_state_by_collection", {}).get(
                item.collection,
                cmx_get_collection_build_status(item.collection)
            )
            if build_state == CMX_BUILD_STATE_BUILT:
                icon_name = "source_build_green"
            elif build_state == CMX_BUILD_STATE_DIRTY:
                icon_name = "source_build_yellow"
            else:
                icon_name = "source_build_gray"
            row.label(text="", icon_value=get_cf_icon(icon_name))
            if not wm.cf_preset_edit_mode:
                op_src = row.operator("cmx.source_data_add_from_preset", text="", icon_value=get_cf_icon("main_panel_crowd_source_build"))
                op_src.preset_collection = item.collection

            if wm.cf_preset_edit_mode:
                op_rename = row.operator(CMXRenamePresetCharOperator.bl_idname, text="", icon_value=get_cf_icon("cf_rename"))
                op_rename.item_index = index
                op_remove = row.operator(CMXRemovePresetCharOperator.bl_idname, text="", icon='X')
                op_remove.item_index = index
        else:  # Preset
            split = layout.split(factor=0.05)
            split.label(text="")
            sub_row = split.row(align=True)
            sub_row.label(text=item.preset, icon_value=get_cf_icon("main_panel_preset_collection_item"))

            if wm.cf_preset_edit_mode:
                op_load = sub_row.operator(CMXLoadPresetCharOperator.bl_idname, text="", icon_value=get_cf_icon("main_panel_preset_apply"))
                op_load.preset_name = item.preset
                op_load.collection_name = item.collection
                sub_row.operator(CMXSavePresetCharOperator.bl_idname, text="", icon_value=get_cf_icon("cf_save_preset")).item_index = index
                sub_row.operator(CMXRenamePresetCharOperator.bl_idname, text="", icon_value=get_cf_icon("cf_rename")).item_index = index
                sub_row.operator(CMXRemovePresetCharOperator.bl_idname, text="", icon='X').item_index = index
            else:
                op_load = sub_row.operator(CMXLoadPresetCharOperator.bl_idname, text="", icon_value=get_cf_icon("main_panel_preset_apply"))
                op_load.preset_name = item.preset
                op_load.collection_name = item.collection

    def filter_items(self, context, data, propname):
        items = getattr(data, propname)
        self._cmx_ensure_ui_cache(items)
        flt_flags = []
        flt_neworder = []
        for idx, item in enumerate(items):
            flt_flags.append(self.bitflag_filter_item)
        return flt_flags, flt_neworder


class CMXTogglePresetCollectionExpandOperator(bpy.types.Operator):
    """Toggle collection expansion without UIList filter reindex jumps."""
    bl_idname = "cmx.toggle_preset_collection_expand"
    bl_label = "Toggle Preset Collection"
    bl_options = {'INTERNAL'}

    collection_name: bpy.props.StringProperty(name="Collection")  # type: ignore

    def execute(self, context):
        wm = context.window_manager
        collection_order = cmx_get_preset_collection_order(context)
        expanded_states = {item.collection: item.expanded for item in wm.preset_items if not item.is_preset}
        expanded_states[self.collection_name] = not expanded_states.get(self.collection_name, False)
        cmx_load_preset_List_data(
            context,
            ordered_collections=collection_order,
            expanded_states_override=expanded_states
        )
        for idx, item in enumerate(wm.preset_items):
            if not item.is_preset and item.collection == self.collection_name:
                wm.preset_item_index = idx
                break
        if context.area:
            context.area.tag_redraw()
        return {'FINISHED'}

class CMXAddPresetCollectionCharOperator(bpy.types.Operator):
    """Add a new preset collection."""
    bl_idname = "cmx.add_preset_collection_char"
    bl_label = "Add Collection"

    collection_name: bpy.props.StringProperty(name="Collection Name")# type: ignore

    def execute(self, context):
        collection_order = cmx_get_preset_collection_order(context)
        data = cmx_load_char_preset_raw()

        if self.collection_name in data:
            self.report({'ERROR'}, f"Collection '{self.collection_name}' already exists.")
            return {'CANCELLED'}

        data[self.collection_name] = {
            "__meta": {
                "build": False,
                "build_state": CMX_BUILD_STATE_NEVER,
                "build_states": cmx_get_default_build_states(),
            },
            "presets": {}
        }

        ordered_collections = collection_order + [self.collection_name]
        cmx_save_char_preset_raw(cmx_reorder_preset_collection_data(data, ordered_collections))
        cmx_mark_collection_dirty(self.collection_name)
        cmx_load_preset_List_data(context, ordered_collections=ordered_collections)
        context.area.tag_redraw()
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

class CMXLoadPresetCharOperator(bpy.types.Operator):
    """Load a character preset to ACTIVE_CHAR."""
    bl_idname = "cmx.load_preset_char"
    bl_label = "Load Preset"

    preset_name: bpy.props.StringProperty(name="Preset Name")  # type: ignore
    collection_name: bpy.props.StringProperty(name="Collection Name")  # type: ignore

    def execute(self, context):
        if CMX_PUB_VAR["apply_anim_lock"]:

            self.report({'WARNING'}, "Please wait for the current animation to finish applying.")
            return {'CANCELLED'}

        CMX_PUB_VAR["apply_anim_lock"] = True
        CMX_PUB_VAR["is_loading_preset"] = True

        wm = context.window_manager
        if not wm.cf_on_off_toggle:
            cmx_show_message_box(
                message="Character Customize is currently OFF. Please turn it ON to load presets.",
                title="Action Required",
                icon='ERROR')
            CMX_PUB_VAR["apply_anim_lock"] = False
            CMX_PUB_VAR["is_loading_preset"] = False
            return {'CANCELLED'}

        try:
            preset_data = cmx_get_preset_data(self.collection_name, self.preset_name)
            cmx_set_progress_task("Load Preset", self.preset_name)
            cmx_set_char_to_preset(context, preset_data)

            for idx, item in enumerate(wm.preset_items):
                if item.is_preset and item.preset == self.preset_name and item.collection == self.collection_name:
                    wm.preset_item_index = idx
                    break

            cmx_set_progress_success(self.preset_name)
            return {'FINISHED'}
        except Exception as e:
            cmx_set_progress_error(self.preset_name, str(e))
            self.report({'ERROR'}, f"Failed to load preset: {e}")
            return {'CANCELLED'}
        finally:
            CMX_PUB_VAR["apply_anim_lock"] = False
            CMX_PUB_VAR["is_loading_preset"] = False

class CMXAddPresetCharOperator(bpy.types.Operator):
    """Add a new character preset to a collection."""
    bl_idname = "cmx.add_preset_char"
    bl_label = "Add Preset"

    collection_name: bpy.props.EnumProperty(
        name="Collection", description="Choose the collection", items=cmx_get_collections)# type: ignore
    preset_name: bpy.props.StringProperty(name="Preset Name")# type: ignore

    def execute(self, context):
        collection_order = cmx_get_preset_collection_order(context)
        data = cmx_load_char_preset_raw()
        record = cmx_normalize_collection_record(data.get(self.collection_name))

        if self.collection_name not in data:
            self.report({'ERROR'}, f"Collection '{self.collection_name}' does not exist.")
            return {'CANCELLED'}

        presets = record.get("presets", {})

        if self.preset_name in presets:
            self.report({'ERROR'}, f"Preset '{self.preset_name}' already exists in collection '{self.collection_name}'.")
            return {'CANCELLED'}

        presets[self.preset_name] = {
            "Char_name": ACTIVE_CHAR["Char_name"],
            "Action": ACTIVE_CHAR.get("Action"),
            "Action_Filter": ACTIVE_CHAR.get("Action_Filter"),
            "mesh_mode": "SINGLE"
        }

        record["presets"] = presets
        data[self.collection_name] = record

        cmx_save_char_preset_raw(cmx_reorder_preset_collection_data(data, collection_order))
        cmx_mark_collection_dirty(self.collection_name)
        expanded_states = {item.collection: item.expanded for item in context.window_manager.preset_items if not item.is_preset}
        expanded_states[self.collection_name] = True
        cmx_load_preset_List_data(
            context,
            ordered_collections=collection_order,
            expanded_states_override=expanded_states
        )
        context.area.tag_redraw()
        # === Auto-select index after add ===
        wm = context.window_manager
        for idx, item in enumerate(wm.preset_items):
            if item.is_preset and item.preset == self.preset_name and item.collection == self.collection_name:
                wm.preset_item_index = idx
                break
        return {'FINISHED'}

    def invoke(self, context, event):
        if context.window_manager.cf_on_off_toggle:
            data = cmx_load_char_preset_raw()

            if self.collection_name:
                record = cmx_normalize_collection_record(data.get(self.collection_name))
                block_count = len(record.get("presets", {})) + 1
                char_name = ACTIVE_CHAR["Char_name"]
                action = "None"
                if ACTIVE_CHAR["Action"]:
                    action = ACTIVE_CHAR["Action"]

                self.preset_name = f"{char_name}-{action[:4]}-{block_count:03}"
                return context.window_manager.invoke_props_dialog(self)
            else:
                self.report({'ERROR'}, "Add a collection to store your preset.")
                return {'CANCELLED'}
        else:
            return {'CANCELLED'}

class CMXRemovePresetCharOperator(bpy.types.Operator):
    """Remove the selected preset or collection from file/list."""
    bl_idname = "cmx.remove_preset_char"
    bl_label = "Remove Preset"
    bl_description = "Remove the selected preset or collection"

    item_index: IntProperty()# type: ignore
    dont_ask_again_session: BoolProperty(
        name="Don't ask again this session",
        description="Skip this confirmation for the rest of the current Blender session",
        default=False
    )# type: ignore

    def invoke(self, context, event):
        wm = context.window_manager
        if not (wm.preset_items and 0 <= self.item_index < len(wm.preset_items)):
            self.report({'WARNING'}, "Invalid item index for remove.")
            return {'CANCELLED'}
        item = wm.preset_items[self.item_index]
        if item.is_preset and getattr(wm, "cf_skip_delete_confirmation_session", False):
            return self.execute(context)
        self.bl_label = f"Remove {'Preset' if item.is_preset else 'Collection'}: '{item.preset if item.is_preset else item.collection}'?"
        return context.window_manager.invoke_props_dialog(self, width=350)

    def draw(self, context):
        wm = context.window_manager
        item = wm.preset_items[self.item_index]
        layout = self.layout
        if item.is_preset:
            layout.prop(self, "dont_ask_again_session")
        layout.label(text=f"Delete {'Preset' if item.is_preset else 'Collection'} [ {item.preset if item.is_preset else item.collection} ] ?", icon='ERROR')

    def execute(self, context):
        wm = context.window_manager
        if not (wm.preset_items and 0 <= self.item_index < len(wm.preset_items)):
            self.report({'ERROR'}, "Invalid item index for remove.")
            return {'CANCELLED'}
        item = wm.preset_items[self.item_index]
        collection_order = cmx_get_preset_collection_order(context)
        if item.is_preset and self.dont_ask_again_session:
            wm.cf_skip_delete_confirmation_session = True

        data = cmx_load_char_preset_raw()

        if item.is_preset:
            parent_collection = item.collection
            preset_name = item.preset
            if parent_collection in data:
                record = cmx_normalize_collection_record(data[parent_collection])
                presets_in_collection = record.get("presets", {})
                if preset_name in presets_in_collection:
                    del presets_in_collection[preset_name]
                    record["presets"] = presets_in_collection
                    data[parent_collection] = record
                else:
                    self.report({'ERROR'}, f"Preset '{preset_name}' not found in collection '{parent_collection}'.")
                    return {'CANCELLED'}
            else:
                self.report({'ERROR'}, f"Preset '{preset_name}' in collection '{parent_collection}' not found in JSON.")
                return {'CANCELLED'}
        else:
            collection_name = item.collection
            if collection_name in data:
                del data[collection_name]
                cmx_remove_collection_status(collection_name)
                collection_order = [name for name in collection_order if name != collection_name]
                source_dir = cmx_get_source_dir(create_if_missing=False)
                if source_dir:
                    source_blend_path = os.path.join(source_dir, f"{collection_name}.blend")
                    if os.path.exists(source_blend_path):
                        try:
                            os.remove(source_blend_path)
                        except Exception as exc:
                            self.report({'WARNING'}, f"Collection removed, but failed to delete source file: {exc}")
            else:
                self.report({'ERROR'}, f"Collection '{collection_name}' not found in JSON.")
                return {'CANCELLED'}

        cmx_save_char_preset_raw(cmx_reorder_preset_collection_data(data, collection_order))
        if item.is_preset:
            cmx_mark_collection_dirty(parent_collection)
        self.report({'INFO'}, f"Item removed successfully.")

        cmx_load_preset_List_data(context, ordered_collections=collection_order)
        context.area.tag_redraw()
        return {'FINISHED'}

class CMXRenamePresetCharOperator(bpy.types.Operator):
    """
    Operator for renaming a preset or collection in the character preset UI.
    """
    bl_idname = "cmx.rename_preset_char"
    bl_label = "Rename"
    bl_description = "Rename the selected preset or collection"

    item_index: IntProperty() # type: ignore
    new_name: StringProperty(
        name="New Name",
        description="Enter the new name for the item"
    ) # type: ignore

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "new_name", text="")

    def invoke(self, context, event):
        wm = context.window_manager
        if not (wm.preset_items and 0 <= self.item_index < len(wm.preset_items)):
            self.report({'WARNING'}, "No item selected to rename.")
            return {'CANCELLED'}

        item_to_rename = wm.preset_items[self.item_index]
        if not item_to_rename.is_preset:
            self.new_name = item_to_rename.collection
            self.bl_label = f"Rename Collection: '{item_to_rename.collection}'"
        else:
            self.new_name = item_to_rename.preset
            self.bl_label = f"Rename Preset: '{item_to_rename.preset}' (in {item_to_rename.collection})"
        return wm.invoke_props_dialog(self, width=250)

    def execute(self, context):
        wm = context.window_manager
        if not (wm.preset_items and 0 <= self.item_index < len(wm.preset_items)):
            self.report({'ERROR'}, "No valid item selected for renaming.")
            return {'CANCELLED'}

        item_to_rename = wm.preset_items[self.item_index]
        new_name_final = self.new_name.strip()
        if not new_name_final:
            self.report({'WARNING'}, "New name cannot be empty.")
            return {'CANCELLED'}

        collection_order = cmx_get_preset_collection_order(context)
        data = cmx_load_char_preset_raw()
        data_changed = False
        ordered_collections = list(collection_order)

        if not item_to_rename.is_preset:  # Rename Collection
            old_collection_key = item_to_rename.collection
            if new_name_final == old_collection_key:
                self.report({'INFO'}, "Name is unchanged.")
                return {'CANCELLED'}
            if new_name_final in data:
                self.report({'ERROR'}, f"A collection named '{new_name_final}' already exists.")
                return {'CANCELLED'}
            if old_collection_key in data:
                record = cmx_normalize_collection_record(data.pop(old_collection_key))
                data[new_name_final] = record
                ordered_collections = cmx_replace_collection_in_order(collection_order, old_collection_key, new_name_final)
                data_changed = True
            else:
                self.report({'ERROR'}, f"Original collection '{old_collection_key}' not found in JSON.")
                return {'CANCELLED'}
        else:  # Rename Preset
            parent_collection_key = item_to_rename.collection
            old_preset_key = item_to_rename.preset
            if new_name_final == old_preset_key:
                self.report({'INFO'}, "Name is unchanged.")
                return {'CANCELLED'}
            if parent_collection_key not in data:
                self.report({'ERROR'}, f"Parent collection '{parent_collection_key}' not found in JSON.")
                return {'CANCELLED'}
            record = cmx_normalize_collection_record(data[parent_collection_key])
            presets = record.get("presets", {})
            if new_name_final in presets:
                self.report({'ERROR'}, f"A preset named '{new_name_final}' already exists in collection '{parent_collection_key}'.")
                return {'CANCELLED'}
            if old_preset_key in presets:
                presets[new_name_final] = presets.pop(old_preset_key)
                record["presets"] = presets
                data[parent_collection_key] = record
                data_changed = True
            else:
                self.report({'ERROR'}, f"Original preset '{old_preset_key}' not found in collection '{parent_collection_key}'.")
                return {'CANCELLED'}

        if data_changed:
            try:
                cmx_save_char_preset_raw(cmx_reorder_preset_collection_data(data, ordered_collections))
            except Exception as e:
                self.report({'ERROR'}, f"Error writing JSON file: {e}")
                return {'CANCELLED'}
            if not item_to_rename.is_preset:
                cmx_mark_collection_dirty(new_name_final)
                expanded_states = {item.collection: item.expanded for item in wm.preset_items if not item.is_preset}
                if old_collection_key in expanded_states:
                    expanded_states[new_name_final] = expanded_states.pop(old_collection_key)
            else:
                cmx_mark_collection_dirty(parent_collection_key)
                expanded_states = {item.collection: item.expanded for item in wm.preset_items if not item.is_preset}
                expanded_states[parent_collection_key] = True
            cmx_load_preset_List_data(
                context,
                ordered_collections=ordered_collections,
                expanded_states_override=expanded_states
            )
            context.area.tag_redraw()
            # === Auto-select index after rename ===
            for idx, item in enumerate(wm.preset_items):
                if not item_to_rename.is_preset and not item.is_preset and item.collection == new_name_final:
                    wm.preset_item_index = idx
                    break
                if item_to_rename.is_preset and item.is_preset and item.preset == new_name_final and item.collection == item_to_rename.collection:
                    wm.preset_item_index = idx
                    break
            self.report({'INFO'}, f"Item renamed to '{new_name_final}'.")
        return {'FINISHED'}

class CMXSavePresetCharOperator(bpy.types.Operator):
    """
    Operator for saving current ACTIVE_CHAR over an existing preset.
    """
    bl_idname = "cmx.save_preset_char"
    bl_label = "Save Preset"
    bl_description = "Save current character data over the selected preset item"

    item_index: IntProperty() # type: ignore

    def invoke(self, context, event):
        wm = context.window_manager
        if not wm.cf_on_off_toggle:
            cmx_show_message_box(
                message="Character Customize is currently OFF. Please turn it ON to get settings from the character.",
                title="Action Required",
                icon='ERROR')
            return {'CANCELLED'}

        if not (wm.preset_items and 0 <= self.item_index < len(wm.preset_items)):
            self.report({'WARNING'}, "Invalid item index for saving.")
            return {'CANCELLED'}
        item = wm.preset_items[self.item_index]
        if not item.is_preset:
            self.report({'WARNING'}, "Cannot overwrite a collection. Please select a preset item.")
            return {'CANCELLED'}
        self.bl_label = f"Overwrite Preset '{item.preset}' in '{item.collection}'?"
        return context.window_manager.invoke_props_dialog(self, width=350)

    def draw(self, context):
        wm = context.window_manager
        item = wm.preset_items[self.item_index]
        layout = self.layout
        layout.label(text=f"Replace Preset [ {item.preset} ] with current character ?", icon='ERROR')

    def execute(self, context):
        wm = context.window_manager
        if not (wm.preset_items and 0 <= self.item_index < len(wm.preset_items)):
            self.report({'ERROR'}, "Invalid item index for saving.")
            return {'CANCELLED'}
        item = wm.preset_items[self.item_index]
        if not item.is_preset:
            self.report({'ERROR'}, "Cannot overwrite a collection. Please select a preset item.")
            return {'CANCELLED'}

        collection_name = item.collection
        preset_name = item.preset
        collection_order = cmx_get_preset_collection_order(context)

        data = cmx_load_char_preset_raw()
        record = cmx_normalize_collection_record(data.get(collection_name))
        presets = record.get("presets", {})

        presets[preset_name] = {
            "Char_name": ACTIVE_CHAR["Char_name"],
            "Action": ACTIVE_CHAR.get("Action"),
            "Action_Filter": ACTIVE_CHAR.get("Action_Filter"),
            "mesh_mode": "SINGLE"
        }

        record["presets"] = presets
        data[collection_name] = record

        try:
            cmx_save_char_preset_raw(cmx_reorder_preset_collection_data(data, collection_order))
            self.report({'INFO'}, f"Preset '{preset_name}' saved successfully.")
        except Exception as e:
            self.report({'ERROR'}, f"Error writing JSON file: {e}")
            return {'CANCELLED'}

        cmx_mark_collection_dirty(collection_name)
        cmx_load_preset_List_data(context, ordered_collections=collection_order)
        context.area.tag_redraw()
        # === Auto-select index after save ===
        for idx, item in enumerate(wm.preset_items):
            if item.is_preset and item.preset == preset_name and item.collection == collection_name:
                wm.preset_item_index = idx
                break
        return {'FINISHED'}

class CMXSortPresetCollectionCharOperator(bpy.types.Operator):
    """Sort preset collections and their member presets alphabetically."""
    bl_idname = "cmx.sort_preset_collection_char"
    bl_label = "Sort Collections"
    bl_description = "Sort preset collections and presets alphabetically"

    def execute(self, context):
        data = cmx_load_char_preset_raw()
        sorted_collections = sorted(data.keys(), key=str.casefold)
        reordered_data = cmx_reorder_preset_collection_data(data, sorted_collections)
        for collection_name in list(reordered_data.keys()):
            reordered_data[collection_name] = cmx_sort_presets_in_collection_record(reordered_data[collection_name])
        cmx_save_char_preset_raw(reordered_data)
        cmx_load_preset_List_data(context, ordered_collections=sorted_collections)
        context.area.tag_redraw()
        return {'FINISHED'}

classes = [
    CMXPresetItemPropertyGroup,
    CMX_UL_PresetData,
    CMXTogglePresetCollectionExpandOperator,
    CMXAddPresetCollectionCharOperator,
    CMXSortPresetCollectionCharOperator,
    CMXAddPresetCharOperator,
    CMXRenamePresetCharOperator,
    CMXRemovePresetCharOperator,
    CMXLoadPresetCharOperator,
    CMXSavePresetCharOperator
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.WindowManager.preset_items = bpy.props.CollectionProperty(type=CMXPresetItemPropertyGroup)
    bpy.types.WindowManager.preset_item_index = bpy.props.IntProperty()

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    del bpy.types.WindowManager.preset_items
    del bpy.types.WindowManager.preset_item_index

   
