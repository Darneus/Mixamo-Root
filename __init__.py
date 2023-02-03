"""
    Copyright (C) 2022  Richard Perry
    Copyright (C) Johngoss725 (Average Godot Enjoyer)

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

    Note that Johngoss725's original contributions were published under a
    Creative Commons 1.0 Universal License (CC0-1.0) located at
    <https://github.com/Johngoss725/Mixamo-To-Godot>.
"""

bl_info = {
    "name": "Mixamo Root",
    "author": "Richard Perry, Johngoss725",
    "version": (1, 1, 2),
    "blender": (3, 4, 0),
    "location": "3D View > UI (Right Panel) > Mixamo Tab",
    "description": ("Script to bake insert root motion bone for Mixamo Animations"),
    "warning": "",  # used for warning icon and text in addons panel
    "wiki_url": "https://github.com/RichardPerry/mixamo_root_bones/wiki",
    "tracker_url": "https://github.com/enziop/mixamo_root_bones/issues",
    "category": "Animation"
}

import os
import bpy
from bpy_extras.io_utils import ImportHelper

from bpy.types import Operator
from bpy.types import PropertyGroup
from bpy.types import Panel
from bpy.types import OperatorFileListElement

from bpy.props import CollectionProperty
from bpy.props import StringProperty

try:
    from . import mixamoroot
except SystemError:
    import mixamoroot

if "bpy" in locals():
    from importlib import reload

    if "mixamoroot" in locals():
        reload(mixamoroot)


class MixamoPropertyGroup(PropertyGroup):
    """Property container for options and paths of Mixamo Root"""
    hip_name: bpy.props.StringProperty(
        name="Hip Bone",
        description="Name to identify the hip bone if not MixamoRig:Hips",
        maxlen=256,
        default="Hips",
        subtype='NONE')
    root_name: bpy.props.StringProperty(
        name="Root Bone",
        description="Name to save the root bone, default is Root",
        maxlen=256,
        default="Root",
        subtype='NONE')
    name_prefix: bpy.props.StringProperty(
        name="Mixamo Prefix",
        description="Prefix of mixamo armature components to help identification, if not default of 'mixamorig:'",
        maxlen=256,
        default="mixamorig:",
        subtype='NONE')
    target_prefix: bpy.props.StringProperty(
        name="Target Prefix",
        description="Replacement prefix of mixamo armature.",
        maxlen=256,
        default="",
        subtype='NONE')
    change_prefix: bpy.props.BoolProperty(
        name="Change Prefix",
        description="Changes the prefix of the mixamo armature to the target prefix.",
        default=True)
    insert_root: bpy.props.BoolProperty(
        name="Insert Root",
        description="Inserts a root bone at the base of the model aligned with the hip's horizontal plane coordinates",
        default=True)
    delete_armatures: bpy.props.BoolProperty(
        name="Delete Armatures",
        description="Deletes all imported armature in the blend file. This assumes you've imported mixamo armatures "
                    "for animations all applied to the same model",
        default=True)
    delete_applied_armatures: bpy.props.BoolProperty(
        name="Delete Armatures",
        description="Deletes all armatures for applied animations after the process is complete",
        default=False)
    push_nla: bpy.props.BoolProperty(
        name="Push To NLA",
        description="Pushes all the actions created for the control rig to the NLA",
        default=False)


class OBJECT_OT_ImportTPose(Operator, ImportHelper):
    """Operator for importing animations and inserting root bones"""
    bl_idname = "mixamo.import_tpose"
    bl_label = "Init with mixamo T-Pose"
    bl_description = "Init with mixamo T-Pose and inserts root bone."
    bl_options = {'PRESET', 'UNDO'}

    filter_glob: bpy.props.StringProperty(
        default="*.fbx",
        options={'HIDDEN'}
    )

    def execute(self, context):
        mixamo = context.scene.mixamo

        hip_name = mixamo.hip_name
        root_name = mixamo.root_name

        change_prefix = mixamo.change_prefix
        name_prefix = mixamo.name_prefix
        target_prefix = mixamo.target_prefix

        insert_root = mixamo.insert_root

        if self.filepath == '':
            self.report({'ERROR_INVALID_INPUT'}, "Error: no Source File set.")
            return {'CANCELLED'}
        if hip_name == '':
            self.report({'ERROR_INVALID_INPUT'}, "Error: no Hip Bone Name set.")
            return {'CANCELLED'}
        if root_name == '':
            self.report({'ERROR_INVALID_INPUT'}, "Error: no Root Bone Name set.")
            return {'CANCELLED'}

        if not change_prefix:
            target_prefix = name_prefix

        mixamoroot.import_tpose(
            self.filepath,
            root_bone_name=root_name,
            hip_bone_name=hip_name,
            name_prefix=name_prefix,
            target_prefix=target_prefix,
            insert_root=insert_root
        )

        return {'FINISHED'}


class OBJECT_OT_ImportAnimations(Operator, ImportHelper):
    """Operator for importing animations and inserting root bones"""
    bl_idname = "mixamo.import_animations"
    bl_label = "Imports Animations"
    bl_description = "Imports mixamo animations, insert root bones, and merges into a single armature"
    bl_options = {'PRESET', 'UNDO'}

    filename_ext = ".fbx"

    filter_glob: StringProperty(
        default="*.fbx",
        options={'HIDDEN'},
        maxlen=255,
    )

    files: CollectionProperty(type=bpy.types.PropertyGroup)

    def execute(self, context):
        mixamo = context.scene.mixamo

        hip_name = mixamo.hip_name
        root_name = mixamo.root_name

        change_prefix = mixamo.change_prefix
        name_prefix = mixamo.name_prefix
        target_prefix = mixamo.target_prefix

        insert_root = mixamo.insert_root

        if hip_name == '':
            self.report({'ERROR_INVALID_INPUT'}, "Error: no Hip Bone Name set.")
            return {'CANCELLED'}
        if root_name == '':
            self.report({'ERROR_INVALID_INPUT'}, "Error: no Root Bone Name set.")
            return {'CANCELLED'}

        if not change_prefix:
            target_prefix = name_prefix

        print("[Mixamo Root] Importing Animations: " + str(self.files))

        folder = (os.path.dirname(self.filepath))
        anim_files = []

        if len(self.files) == 1 and (self.files[0].name == "" or self.files[0].name == "*"):
            print("[Mixamo Root] No files selected, importing all files in folder: " + folder)
            for file in os.listdir(folder):
                if file.endswith(self.filename_ext):
                    anim_files.append(os.path.join(folder, file))
        else:
            for file in self.files:
                anim_files.append(os.path.join(folder, file.name))

        mixamoroot.import_animations(
            files=anim_files,
            root_bone_name=root_name,
            hip_bone_name=hip_name,
            name_prefix=name_prefix,
            target_prefix=target_prefix,
            insert_root=insert_root,
            delete_armatures=mixamo.delete_armatures
        )

        return {'FINISHED'}


class OBJECT_OT_ApplyAnimations(Operator):
    """Operator for applying all imported animations to a target control rig"""
    bl_idname = "mixamo.applyanims"
    bl_label = "Apply Animations"
    bl_description = "Applies all the imported mixamo animations, to a single mixamo control rig. ONLY for mixamo control rigs generated with mixamo addon"

    def execute(self, context):
        mixamo = context.scene.mixamo
        mixamo_control_rig = context.scene.mixamo_control_rig
        delete_applied_armatures = mixamo.delete_applied_armatures
        control_rig = mixamo_control_rig
        push_nla = mixamo.push_nla
        if control_rig == '' or control_rig == None or bpy.data.objects[control_rig.name].type != "ARMATURE":
            self.report({'ERROR_INVALID_INPUT'}, "Error: No valid control rig armature selected")
            return {'CANCELLED'}
        if delete_applied_armatures == True:
            self.report({'WARNING'}, "Delete Armatures set to true, imported animation armatures will be removed.")
        mixamoroot.apply_all_anims(delete_applied_armatures=delete_applied_armatures, control_rig=control_rig,
                                   push_nla=push_nla)
        return {'FINISHED'}


class MIXAMOCONV_VIEW_3D_PT_mixamoroot(Panel):
    """Creates a Tab in the Toolshelve in 3D_View"""
    bl_label = "Mixamo Root"
    bl_idname = "MIXAMOCONV_VIEW_3D_PT_mixamoroot"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Mixamo"

    def draw_import_helpers(self):
        layout = self.layout

        scene = bpy.context.scene

        box = layout.box()
        box.label(text="Import Helpers")

        # Options for how to do the conversion
        row = box.row()
        row.prop(scene.mixamo, "insert_root", toggle=True)

        row = box.row()
        row.prop(scene.mixamo, "change_prefix", toggle=True)
        row.prop(scene.mixamo, "delete_armatures", toggle=True)

        row = box.row()
        row.prop(scene.mixamo, "hip_name")

        row = box.row()
        row.prop(scene.mixamo, "root_name")

        row = box.row()
        row.prop(scene.mixamo, "name_prefix")

        row = box.row()
        row.prop(scene.mixamo, "target_prefix")

        row = box.row()
        row.scale_y = 2.0
        row.operator("mixamo.import_tpose")

        row = box.row()
        row.scale_y = 2.0
        row.operator("mixamo.import_animations")

    def draw(self, context):
        layout = self.layout

        scene = bpy.context.scene

        self.draw_import_helpers()

        box = layout.box()
        box.label(text="Animation Helpers")
        row = box.row()
        box.label(text="Control Rig:")
        row = box.row()
        row.prop(scene, "mixamo_control_rig")
        row = box.row()
        row.prop(scene.mixamo, "delete_applied_armatures", toggle=True)  # todo delete_applied_armatures
        row.prop(scene.mixamo, "push_nla", toggle=True)
        row = box.row()
        # box.prop(scene.mixamo, "mixamo.applyanims") # todo
        row.operator("mixamo.applyanims")
        # status_row = box.row()

classes = (
    OBJECT_OT_ImportTPose,
    OBJECT_OT_ImportAnimations,
    OBJECT_OT_ApplyAnimations,
    MIXAMOCONV_VIEW_3D_PT_mixamoroot,
)


def register():
    bpy.utils.register_class(MixamoPropertyGroup)
    bpy.types.Scene.mixamo_control_rig = bpy.props.PointerProperty(
        type=bpy.types.Object,
        name="",
        description="The control rig generated by mixamo, used as target for the animation application function")
    bpy.types.Scene.mixamo = bpy.props.PointerProperty(type=MixamoPropertyGroup)
    for cls in classes:
        bpy.utils.register_class(cls)
    '''
    bpy.utils.register_class(OBJECT_OT_ImportTPose)
    bpy.utils.register_class(OBJECT_OT_ImportAnimations)
    bpy.utils.register_class(OBJECT_OT_ApplyAnimations)
    bpy.utils.unregister_class(MixamorootPanel)
    '''


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    bpy.utils.unregister_class(MixamoPropertyGroup)
    '''
    bpy.utils.unregister_class(MixamoPropertyGroup)
    bpy.utils.register_class(OBJECT_OT_ImportTPose)
    bpy.utils.register_class(OBJECT_OT_ImportAnimations)
    bpy.utils.register_class(OBJECT_OT_ApplyAnimations)
    bpy.utils.unregister_class(MixamorootPanel)
    '''
    del bpy.types.Scene.mixamo_control_rig


if __name__ == "__main__":
    register()
