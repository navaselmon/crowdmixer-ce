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

import bpy.utils.previews
import os
from .system_var import *

PREVIEW_ICON_COLL = {}
Preview_Icon_key = {"cf_logo","cf_turn_on", "cf_turn_off", "Not_Available","cf_help","cf_save_preset","cf_new_preset","cf_preset_panel","cf_rename",
                    "head_panel_char_costom","head_panel_char_coll","head_panel_crowd","head_panel_creator","head_panel_customize","head_panel_corner_left","head_panel_corner_right",
                    "head_panel_panel_info",
                    "sub_panel_head", "sub_panel_body", "sub_panel_cloth", "sub_panel_anim",
                    "sub_panel_cloth_random","sub_panel_cloth_off", "sub_panel_cloth_filter", "sub_panel_cloth_pattern","sub_panel_cloth_link","sub_panel_cloth_unlink",
                    "sub_panel_body_shape_oval","sub_panel_body_shape_triangle", "sub_panel_body_shape_inverted", "sub_panel_body_shape_rectangle", "sub_panel_body_shape_hourglass",
                    "sub_panel_head_shape_oval","sub_panel_head_shape_triangle", "sub_panel_head_shape_inverted", "sub_panel_head_shape_rectangle", "sub_panel_head_shape_hourglass",
                    "sub_panel_anim_vis_bone","sub_panel_anim_vis_proxy","sub_panel_anim_range","sub_panel_anim_update","sub_panel_anim_apply",
                    "main_panel_crowd_source","CMX_Stadium_Crowd","CMX_Standing_Crowd","CMX_Flow_Curve_Crowd","main_panel_crowd_add","main_panel_crowd_remove","main_panel_crowd_list",
                    "main_panel_preset_collection","main_panel_preset_apply","main_panel_customize_add_ch_preset","main_panel_preset_collection_item",
                    "main_panel_preset_collection_add","main_panel_crowd_source_add","main_panel_crowd_source_build","main_panel_crowd_duplicate",
                    "source_build_gray", "source_build_green", "source_build_yellow"
                    
                }
PREVIEW_IMAGE_COLL = {}
Preview_Image_key = {"Not_Available", "Default_Anim",
                     "Body_Key_Health_Fat","Body_Key_Health_Thin","Body_Key_Health_Muscle","Body_Key_Torso_Neck","Body_Key_Torso_BuffaloHump",
                     "Body_Key_Torso_Lats","Body_Key_Torso_Belly","Body_Key_Leg_Bottom","Body_Key_Torso_Chest","Body_Key_Torso_Breasts",                        
                     "Body_Key_Arm_Shoulder","Body_Key_Arm_ArmUpper","Body_Key_Arm_ArmLower","Body_Key_Arm_Hand","Body_Key_Leg_LegUpper",
                     "Body_Key_Leg_LegLower","Body_Key_Leg_Foot",
                     
                     "Face_Key_Forehead_Wide","Face_Key_Forehead_Narrow","Face_Key_Eye_Wide","Face_Key_Eye_Narrow","Face_Key_Nose_Wide","Face_Key_Nose_Narrow",
                     "Face_Key_Nose_Tip_Up","Face_Key_Nose_Tip_Down","Face_Key_Nose_Bridge_Up","Face_Key_Nose_Bridge_Down","Face_Key_Cheek_Wide",  
                     "Face_Key_Cheek_Narrow","Face_Key_Buccal_Add","Face_Key_Buccal_Remove","Face_Key_Jaw_Wide","Face_Key_Jaw_Narrow","Face_Key_Jaw_Up",
                     "Face_Key_Jaw_Down","Face_Key_Mouth_Wide","Face_Key_Mouth_Narrow","Face_Key_Lip_Thick","Face_Key_Lip_Thin","Face_Key_Chin_Wide",
                     "Face_Key_Chin_Narrow","Face_Key_Chin_Up","Face_Key_Chin_Down","Face_Key_Chin_Cleft",
                     
                     "Emotion_key_Anger","Emotion_key_Anticipation","Emotion_key_Disgust","Emotion_key_Fear","Emotion_key_Joy","Emotion_key_Sadness",
                     "Emotion_key_Surprise","Emotion_key_Trust"
                }

def icon_system_regis():
    for icon_key in Preview_Icon_key:
        icon_system_pcoll = bpy.utils.previews.new()   
        
        subpanel_head_preview_path = os.path.join(CURRENT_DIRECTORY ,"CMX_Icons",icon_key+".svg" )
        icon_system_pcoll.load(icon_key+"_icon", subpanel_head_preview_path, 'IMAGE')

        PREVIEW_ICON_COLL[icon_key] = icon_system_pcoll
     
def Image_system_regis():
    for Image_key in Preview_Image_key:
        Image_system_pcoll = bpy.utils.previews.new()
        
        subpanel_head_preview_path =  os.path.join(CURRENT_DIRECTORY , "CMX_Images",Image_key+".png")
        Image_system_pcoll.load(Image_key+"_image", subpanel_head_preview_path, 'IMAGE')

        PREVIEW_IMAGE_COLL[Image_key] = Image_system_pcoll

def icon_system_unregis():
    for pcoll in PREVIEW_ICON_COLL.values():
        bpy.utils.previews.remove(pcoll)
    PREVIEW_ICON_COLL.clear()

def Image_system_unregis():
    for pcoll in PREVIEW_IMAGE_COLL.values():
        bpy.utils.previews.remove(pcoll)
    PREVIEW_IMAGE_COLL.clear()

def get_cf_icon(Icon_key):
    if Icon_key in PREVIEW_ICON_COLL.keys():
        pcoll = PREVIEW_ICON_COLL[Icon_key]
        cf_icon = pcoll[Icon_key+"_icon"] 
        return cf_icon.icon_id 
    else:
        pcoll = PREVIEW_ICON_COLL["Not_Available"]
        return pcoll["Not_Available_icon"].icon_id 

def get_cf_icon_image(Icon_image_key):
    if Icon_image_key in PREVIEW_IMAGE_COLL.keys():
        pcoll = PREVIEW_IMAGE_COLL[Icon_image_key]
        cf_icon = pcoll[Icon_image_key+"_image"] 
        return cf_icon.icon_id     
    else:
        pcoll = PREVIEW_IMAGE_COLL["Not_Available"]
        return pcoll["Not_Available_image"].icon_id 

def get_cf_color_palette_icon(Icon_key):
    pcoll = PREVIEW_ICON_COLL["color_palette"]
    cf_icon = pcoll[Icon_key+"_icon"] 
    return cf_icon.icon_id 
                