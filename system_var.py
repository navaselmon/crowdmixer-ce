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

import os

CURRENT_DIRECTORY = os.path.dirname(os.path.abspath(__file__))

# Free download page for the CrowdMixer_Asset character/preset library
# (not bundled with the extension - too large for extensions.blender.org).
CMX_ASSET_DOWNLOAD_URL = "https://navalab.gumroad.com/l/cmx_ce_asset"
REQUIRED_KEYS = [
    "Accessory", "Body", "Bone", "Eye", "Foot", "Hair", "Head",
    "Leg", "Proxy", "Torso", "Makeup", "Skin", "Char_name"
]
CM_ASSETTS_SCENE = "CMX_AssetLibrary"
ICON_VIEW_SCALE = 4 
CAM_PREVIEW_LIST = ["07_Foot_Preview_Cam", "06_Leg_Preview_Cam", "05_Torso_Preview_Cam", "04_Accessory_Preview_Cam", "03_Eye_Preview_Cam", "02_Head_Preview_Cam", "01_Hair_Preview_Cam"  ]

BODY_PART = {"Hair", "Head", "Eye", "Torso", "Accessory", "Leg","Foot"}

ASSET_LIBR_EXIST = []
ASSET_LIBR_COLL = {"Proxy", "Bone", "Body", "Hair", "Head", "Eye", "Torso", "Accessory", "Leg","Foot"}
ASSET_PREV_COLL = {"CMX_Proxy","CMX_Bone", "CMX_Body", "CMX_Hair", "CMX_Head", "CMX_Eye", "CMX_Torso", "CMX_Accessory", "CMX_Leg", "CMX_Foot"}

PREVIEW_COLL = {}
PREVIEW_ENUM_ITEMS = {}
PREVIEW_LIST = ["Hair", "Head", "Eye", "Torso", "Accessory", "Leg","Foot", "Makeup", "Skin"]

NO_FILTER_ITEM =  ["Proxy", "Hair", "HeadPreset" ,"Makeup", "BodyPreset", "Skin","Body", "Bone"] 
CLOTHES_FILTER = ["All", "Casual", "Extra", "Uniform", "Sport", "Formal"]

CHAR_LIST = []
CHAR_BLEND_PATHS = {}  # char_name -> absolute .blend path
CHAR_JSON_PATHS = {}   # char_name -> absolute .json path
CHAR_PNG_PATHS = {}    # char_name -> absolute .png path
CHAR_CATEGORY = {}     # char_name -> top-level folder name (Single-Mesh only)

CHAR_PREV_SET = {}  # cache of character previews per asset directory

ANIM_SET = {}
ANIM_SELECT_LIST = {}
ANIMATION_FILTER = []
STRIPS_LIST = {}
CMX_KEYMAP = {}

CMX_PUB_VAR = {}
CMX_PUB_VAR["anim_filter_change"] = False
CMX_PUB_VAR["cloth_filter_latest"] = None
CMX_PUB_VAR["Default_Pose"] = {}
CMX_PUB_VAR["Off_Exist_Path"] = True
# Flags without trailing spaces (fix potential key mismatches)
CMX_PUB_VAR["is_loading_preset"] = False
CMX_PUB_VAR["apply_anim_lock"] = False
CMX_PUB_VAR["customize_turn_on_pending"] = False
CMX_PUB_VAR["customize_turn_on_loading"] = False
CMX_PUB_VAR["customize_toggle_internal_change"] = False
CMX_PUB_VAR["mesh_mode_switch_pending"] = False
CMX_PUB_VAR["mesh_mode_switch_loading"] = False
CMX_PUB_VAR["mesh_mode_pending_target"] = None
CMX_PUB_VAR["mesh_mode_display"] = None
CMX_PUB_VAR["active_mesh_mode"] = None
PRESET_BUILD_STATUS = {}  # collection_name -> "never" | "built" | "dirty"

CLOTH_FIRST_ITEM = {}
for bp in BODY_PART:
    CLOTH_FIRST_ITEM[bp] = {}

CHAR_ITEM_SET = {}
CHAR_ITEM_EXIST = {}
CHAR_LATEST_ITEM = {}
CHANGE_BY_USER = {}
for prev in PREVIEW_LIST:
    CHAR_ITEM_SET[prev] = {}
    CHAR_ITEM_SET[prev]["All"] = {}
    CHAR_ITEM_EXIST[prev] = []
    CHAR_LATEST_ITEM[prev] = {}
    CHANGE_BY_USER[prev] = True
   
ANIM_PREV_EXIST = []

# all data of active char -------------------------
ACTIVE_CHAR = {}
ACTIVE_PREV = {}
ACTIVE_CHAR["Action"] = None
ACTIVE_CHAR["Char_name"] = None
for prev in PREVIEW_LIST:
    ACTIVE_CHAR[prev] = None
    ACTIVE_PREV[prev] = None

CROWD_LATEST_SOURCE = {}

CMX_PANEL_TAB =[ 
                [0,"Crowd Manager",'head_panel_crowd'],
                [1,"Character Customization" ,'head_panel_char_costom'],
                [2,"Preset Collection" ,'head_panel_char_coll'],
                [3,"Creator Tools",'head_panel_creator']
            ]
CMX_CUSTOMIZE_TAB =[ 
                [0,"Head" ,'sub_panel_head'],
                [1,"Body" ,'sub_panel_body'],
                [2,"Cloth",'sub_panel_cloth'],
                [3,"Animation",'sub_panel_anim']
            ]
CMX_SUBPANEL_TAB_HEAD =[ 
                [0,"hair" ,"Hair", 'head_panel_char_costom'],
                [1,"face_shape","Face Shape" ,'head_panel_char_coll'],
                [2,"makeup", "Makeup", 'head_panel_crowd'],
                [3,"emotion","Emotion", 'head_panel_creator']
            ]

FACE_SHAPE_KEY  =  [    "Face_Key_Forehead_Wide",
                        "Face_Key_Forehead_Narrow",   
                        "Face_Key_Eye_Wide", 
                        "Face_Key_Eye_Narrow",                      
                        "Face_Key_Nose_Wide",
                        "Face_Key_Nose_Narrow",
                        "Face_Key_Nose_Tip_Up",
                        "Face_Key_Nose_Tip_Down",
                        "Face_Key_Nose_Bridge_Up",
                        "Face_Key_Nose_Bridge_Down",                        
                        "Face_Key_Cheek_Wide",  
                        "Face_Key_Cheek_Narrow",                           
                        "Face_Key_Buccal_Add",
                        "Face_Key_Buccal_Remove",                     
                        "Face_Key_Jaw_Wide", 
                        "Face_Key_Jaw_Narrow",
                        "Face_Key_Jaw_Up",
                        "Face_Key_Jaw_Down",
                        "Face_Key_Mouth_Wide", 
                        "Face_Key_Mouth_Narrow", 
                        "Face_Key_Lip_Thick",
                        "Face_Key_Lip_Thin",
                        "Face_Key_Chin_Wide",
                        "Face_Key_Chin_Narrow",                      
                        "Face_Key_Chin_Up",                        
                        "Face_Key_Chin_Down",                        
                        "Face_Key_Chin_Cleft",
                    ]

EMOTION_SHAPE_KEY  =  [ "Emotion_key_Anger",
                        "Emotion_key_Anticipation",
                        "Emotion_key_Disgust",
                        "Emotion_key_Fear",
                        "Emotion_key_Joy",
                        "Emotion_key_Sadness",
                        "Emotion_key_Surprise",
                        "Emotion_key_Trust"
                    ]

BODY_SHAPE_KEY =   [    "Body_Key_Health_Fat",
                        "Body_Key_Health_Thin",
                        "Body_Key_Health_Muscle",
                        "Body_Key_Torso_Neck",
                        "Body_Key_Torso_BuffaloHump",
                        "Body_Key_Torso_Lats",
                        "Body_Key_Torso_Belly",
                        "Body_Key_Leg_Bottom",
                        "Body_Key_Torso_Chest",
                        "Body_Key_Torso_Breasts",                        
                        "Body_Key_Arm_Shoulder",
                        "Body_Key_Arm_ArmUpper",
                        "Body_Key_Arm_ArmLower",
                        "Body_Key_Arm_Hand",                        
                        "Body_Key_Leg_LegUpper",
                        "Body_Key_Leg_LegLower",
                        "Body_Key_Leg_Foot", 
                        ]

HEAD_PRESET_PROP =  [   "Char_name",
                        "Hair",  
                        "Hair_Shader",
                        "Hair_Color",
                        "Makeup",
                        "Face_Key_Forehead_Wide",
                        "Face_Key_Forehead_Narrow",   
                        "Face_Key_Eye_Wide", 
                        "Face_Key_Eye_Narrow",                      
                        "Face_Key_Nose_Wide",
                        "Face_Key_Nose_Narrow",
                        "Face_Key_Nose_Tip_Up",
                        "Face_Key_Nose_Tip_Down",
                        "Face_Key_Nose_Bridge_Up",
                        "Face_Key_Nose_Bridge_Down",                        
                        "Face_Key_Cheek_Wide",  
                        "Face_Key_Cheek_Narrow",                           
                        "Face_Key_Buccal_Add",
                        "Face_Key_Buccal_Remove",                     
                        "Face_Key_Jaw_Wide", 
                        "Face_Key_Jaw_Narrow",
                        "Face_Key_Jaw_Up",
                        "Face_Key_Jaw_Down",
                        "Face_Key_Mouth_Wide", 
                        "Face_Key_Mouth_Narrow", 
                        "Face_Key_Lip_Thick",
                        "Face_Key_Lip_Thin",
                        "Face_Key_Chin_Wide",
                        "Face_Key_Chin_Narrow",                      
                        "Face_Key_Chin_Up",                        
                        "Face_Key_Chin_Down",                        
                        "Face_Key_Chin_Cleft",
                        "Emotion_key_Anger",
                        "Emotion_key_Anticipation",
                        "Emotion_key_Disgust",
                        "Emotion_key_Fear",
                        "Emotion_key_Joy",
                        "Emotion_key_Sadness",
                        "Emotion_key_Surprise",
                        "Emotion_key_Trust"
                        
                        ]

BODY_PRESET_PROP = [    "Char_name",                        
                        "Skin",
                        "Body_Key_Health_Fat",
                        "Body_Key_Health_Thin",
                        "Body_Key_Health_Muscle",
                        "Body_Key_Torso_Neck",
                        "Body_Key_Torso_BuffaloHump",
                        "Body_Key_Torso_Lats",
                        "Body_Key_Torso_Belly",
                        "Body_Key_Leg_Bottom",
                        "Body_Key_Torso_Chest",
                        "Body_Key_Torso_Breasts",                        
                        "Body_Key_Arm_Shoulder",
                        "Body_Key_Arm_ArmUpper",
                        "Body_Key_Arm_ArmLower",
                        "Body_Key_Arm_Hand",                        
                        "Body_Key_Leg_LegUpper",
                        "Body_Key_Leg_LegLower",
                        "Body_Key_Leg_Foot",                    
                        ]

BODY_PATH_PROB_COLL = { "Hair"      :["hair_previews","color_property_hair","item_off_hair"],
                        "Head"      :["head_previews","color_property_head","item_off_head"], 
                        "Eye"       :["eye_previews" ,"color_property_eye","item_off_eye"], 
                        "Torso"     :["torso_previews","color_property_torso","item_off_torso"], 
                        "Accessory" :["accessory_previews","color_property_Accessory","item_off_Accessory"], 
                        "Leg"       :["leg_previews" ,"color_property_leg","item_off_leg"],
                        "Foot"      :["foot_previews" ,"color_property_foot","item_off_foot"]
                        }

PROP_BP_ITEM_PREVIEW = {    "Hair":"hair_previews",
                            "Head":"head_previews",
                            "Eye":"eye_previews",
                            "Torso":"torso_previews",
                            "Accessory":"accessory_previews",
                            "Leg":"leg_previews",
                            "Foot":"foot_previews"
                        }

PROP_BP_ITEM_OFF = {    "Hair":"item_off_hair",
                        "Head":"item_off_head",
                        "Eye":"item_off_eye",
                        "Torso":"item_off_torso",
                        "Accessory":"item_off_Accessory",
                        "Leg":"item_off_leg",
                        "Foot":"item_off_foot",
                        "All":"item_off_all"
                        }

PROP_COLOR =  { "Hair":"color_property_hair",
                "Head":"color_property_head",
                "Eye":"color_property_eye",
                "Torso":"color_property_torso",
                "Accessory":"color_property_Accessory",
                "Leg":"color_property_leg",
                "Foot":"color_property_foot"
                }

EXPANDED_BOOLEAN = [    "sub_panel_head_expanded",
                        "sub_panel_body_expanded",
                        "sub_panel_clothes_expanded",
                        "sub_panel_animation_expanded",
                        "sub_panel_L1_hair_expanded",
                        "sub_panel_L1_faceshape_expanded",
                        "sub_panel_L1_makeup_expanded",
                        "sub_panel_L1_emotion_expanded",
                        "sub_panel_L1_use_guide_faceshape",
                        "sub_panel_L1_use_guide_emotion",
                        "sub_panel_L1_skin_expanded",
                        "sub_panel_L1_bodyshape_expanded",
                        "sub_panel_L1_Health_expanded",
                        "sub_panel_L1_use_guide_bodyshape",
                        "sub_panel_L1_use_guide_health",
                        "sub_panel_crowd_modifier_expanded",
                        "creator_group_template_expanded",
                        "creator_group_bake_expanded",
                        "creator_group_action_save_expanded",
                        "creator_group_preview_expanded",
                        "creator_group_mirror_expanded",
                        "creator_group_remap_expanded",
                        "creator_group_mesh_expanded"
                    ]

FACE_INDEX = {
    "Australia":0,
    "Brazil":1,
    "China":2, 
    "Egypt":3,
    "Ethiopia":4,
    "Greece":5,
    "India":6, 
    "Indonesia":7,
    "Israel":8,
    "Italy":9,
    "Japan":10,
    "Mexico":11,
    "Nigeria":12,
    "Pakistan":13,
    "Russia":14,
    "SouthAfrica":15
}

CHAR_OPT = {"Makeup": [ "Australia",
                        "Brazil",
                        "China", 
                        "Egypt",
                        "Ethiopia",
                        "Greece",
                        "India", 
                        "Indonesia",
                        "Israel",
                        "Italy",
                        "Japan",
                        "Mexico",
                        "Nigeria",
                        "Pakistan",
                        "Russia",
                        "SouthAfrica"],
            "Skin":[    "Fair",
                        "Medium",
                        "Tan",
                        "Brown"  ]}

SOURCE_SCIKET_NAME =  {"source_main", "source_mix01", "source_mix02", "source_mix03"}
