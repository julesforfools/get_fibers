import bpy

# Primary operator
class OBJECT_OT_recolor_by_angle(bpy.types.Operator):
    """Recolor all fibers according to attachment angle"""
    bl_idname = "curve.recolor_by_angle"
    bl_label = "Recolor by Attachment Angle"
    bl_options = {'REGISTER', 'UNDO'}

    # execute function
    def execute(self, context):

        # create the gradient material
        if not "Gradient_Angle" in bpy.data.materials: # If material doesn't exist yet,
            bpy.data.materials.new("Gradient_Angle") # create it
        mat = bpy.data.materials["Gradient_Angle"]
        mat.use_nodes = True # Use material nodes
        mat.diffuse_color = (100,255,0,255) # Assign Viewport material color
        tree = mat.node_tree
        nodes = tree.nodes


        # select objects in 'Straightened'
        context.view_layer.active_layer_collection = context.view_layer.layer_collection.children['Straightened']

        for ob in bpy.data.collections['Straightened'].all_objects:
            if ob.type == "CURVE":
                ob.select_set(True)
        for ob in context.selected_objects:
                ob.active_material = mat

        return {'FINISHED'}

# Append to scene panel
class SCENE_PT_recolor_by_angle(bpy.types.Panel):
    """Panel for assigning a color gradient to Fibers"""
    bl_label = "Recolor by Angle"
    bl_idname = "SCENE_PT_add_spotlights_above_meshes"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"

    def draw(self, context):

        layout = self.layout

        scene = context.scene
        collection = context.collection

        # Create a simple row.
        layout.label(text=" Choose Collection:")

        row = layout.row()
        #row.template_ID(context, "collection")
        #row.template_ID(context.view_layer.layer_collection, "collection", filter='AVAILABLE')
        #row.template_ID(context.view_layer.layer_collection.collection, "children", filter='AVAILABLE')
        #row.template_ID(context.view_layer.objects, "active", filter='AVAILABLE')
        #row.operator_menu_enum("collection.remove", "select_objects", text = "Select object")

        # Big render button
        layout.label(text=" Recolor by Angle:")
        row = layout.row()
        row.scale_y = 3.0
        row.operator("curve.recolor_by_angle")


# Registration
def register():

    bpy.utils.register_class(OBJECT_OT_recolor_by_angle)
    bpy.utils.register_class(SCENE_PT_recolor_by_angle)


def unregister():
    bpy.utils.unregister_class(OBJECT_OT_recolor_by_angle)
    bpy.utils.unregister_class(SCENE_PT_recolor_by_angle)


if __name__ == "__main__":
    register()
