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
        if not "Gradient_Angle" in bpy.data.materials:                          # If material doesn't exist yet,
            bpy.data.materials.new("Gradient_Angle")                            # create it
        mat = bpy.data.materials["Gradient_Angle"]                              # Assign material to variable
        mat.use_nodes = True                                                    # Use material nodes
        mat.diffuse_color = (100,255,0,255)                                     # Assign Viewport material color
        tree = mat.node_tree                                                    # Assign node tree to variable
        nodes = tree.nodes                                                      # Assign nodes to variable
        #list(bpy.data.materials["Gradient_Angle"].node_tree.nodes)

        # assign nodes to variables
        node_bsdf = nodes['Principled BSDF']
        nodes.new('ShaderNodeValToRGB')
        node_ramp = nodes['ColorRamp']
        nodes.new('ShaderNodeMath')
        node_math = nodes['Math']
        #nodes.new('ShaderNodeValue')
        #node_value = nodes['Value']
        nodes.new('ShaderNodeAttribute')
        node_attribute = nodes['Attribute']

        # link the nodes together, bsdf is already linked to Output node
        tree.links.new(node_ramp.outputs['Color'], node_bsdf.inputs['Base Color']) # Connect ColorRamp and BSDF
        tree.links.new(node_math.outputs['Value'], node_ramp.inputs[0]) # Connect Math and ColorRamp
        #tree.links.new(node_value.outputs['Value'], node_math.inputs[0]) # Connect Value and Math, not supported
        tree.links.new(node_attribute.outputs[2], node_math.inputs[0])

        # customize the nodes
        # color ramp Blue/Red gradient
        node_ramp.color_ramp.elements[0].color = (0,0,1,1)
        node_ramp.color_ramp.elements[1].color = (1,0,0,1) # Don't use RGB 0/255 here, it fs up the ramp
        # color ramp sets stops at min and max angles for clearer visualization
        angles = []
        for ob in bpy.data.collections['Straightened'].all_objects:
            angles.append(ob.data["attachment_angle"])
        node_ramp.color_ramp.elements[0].position = min(angles)/90
        node_ramp.color_ramp.elements[1].position = max(angles)/90
        # Math module division and by 90
        node_math.operation = "DIVIDE"
        node_math.inputs[1].default_value = 90
        # Give Value an input # not supported
        # node_value.outputs[0].default_value = 0
        # driv = node_value.outputs[0].driver_add("default_value")
        # driv.driver.expression = "100"
        # Give Attribute an input
        node_attribute.attribute_type = 'OBJECT'
        node_attribute.attribute_name = 'attachment_angle'

        # placeholder for attribute node: Object Info node and pass index
        #nodes.new('ShaderNodeObjectInfo')
        #node_info = nodes['Object Info']
        #tree.links.new(node_info.outputs[2], node_math.inputs[0])

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

        # Create a row to choose collection, not yet supported
        #layout.label(text=" Choose Collection:")
        #row = layout.row()
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
