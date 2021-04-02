import sys
from mathutils import Vector
import bpy
import math
import os

print(sys.argv[0:])

#Blender 2.79 not supported!
#Blender 2.81 supported!
#----------------------------------------------------------------------------------------------------------------
# run line:
# ../blender-2.80/blender start-fibers.blend -P read-fibers.py -- markers-input.txt lines-fibers.swc
#----------------------------------------------------------------------------------------------------------------

#sys.argv is a list in Python, which contains the command-line arguments passed to the script.
#sys.argv[0] is the directory, sys.argv[1] is the script, etc..
FILE_MARKERS = sys.argv[4]
FILE_FIBERS = sys.argv[5]
SCALE_MULT = sys.argv[6]
### Set the scale for visualization in Blender ###
if SCALE_MULT == 'mm':
    SCALE_MULT = 1
if SCALE_MULT == 'um':
    SCALE_MULT = 0.001


### Read Apodeme/Tendon Data from 4 landmarks ###
def ReadApodemeData(filename, scale):
    p1,p2,p3,p4 = Vector((0,0,0)), Vector((0,0,0)), Vector((0,0,0)), Vector((0,0,0)) #p1,p2 are the apodeme/tendon landmarks at the origin. p3,p4 are the apodeme/tendon landmarks along the line of action.
    lines = []
    with open(filename, 'r') as f:
        lines = f.readlines()
    for i in range(0,len(lines)):
        line = lines[i]
        if line.startswith("@1"):
            pointData = []
            for k in range(1,5):
                if i + k < len(lines):
                    pointData.append(lines[i+k])
            if len(pointData) == 4:
                points = []
                for pd in pointData:
                    points.append(pd.split(' '))
                p1 = Vector((float(points[0][0]),float(points[0][1]),float(points[0][2])))*scale
                p2 = Vector((float(points[1][0]),float(points[1][1]),float(points[1][2])))*scale
                p3 = Vector((float(points[2][0]),float(points[2][1]),float(points[2][2])))*scale
                p4 = Vector((float(points[3][0]),float(points[3][1]),float(points[3][2])))*scale
    return p1,p2,p3,p4

### Calculate orientation of force production ###
def GetApodemeDirection(p1,p2,p3,p4):
    v12mid = (p1+p2)/2 #Vector(( (p1.x+p2.x)/2.0, (p1.y+p2.y)/2.0, (p1.z+p2.z)/2.0 ))
    v34mid = (p3+p4)/2 #Vector(( (p3.x+p4.x)/2.0, (p3.y+p4.y)/2.0, (p3.z+p4.z)/2.0 ))
    return v12mid - v34mid, v12mid, v34mid

### Create Points from landmarks ###
def CreatePointAtLocation(location,size=0.05):
    bpy.ops.mesh.primitive_cube_add(size=size, calc_uvs=True,location=location)


### Read Muscle Fiber Data from swc-file ###
def ReadFiberData(filename):                                    # start the function
    textlines=[]                                                # create an empty list object
    with open(filename, 'r') as f:                              # load the file into python
        textlines = f.readlines()
    textlines = [l.rstrip('\n').lstrip() for l in textlines]    # remove the '\n' that indicates a new line
    lines=[]                                                    # create an empty list object for the final output
    for line in textlines:                                      # initiate final iterating loop
        data = line.split(' ')                                  # the current line is assignes to 'data', it is split by space
        if len(data) <=  0:                                     # this finishes the loop when there are no lines left
            continue
        pack = None                                             # Create NoneType object, which will be one fiber as an element to be appended to the list
        if data[-1] == "-1":                                    # '[-1]' conveniently indexes the last position
            pack = []                                           # if we hit a '-1' we restart pack
            lines.append(pack)                                  # if we hit a '-1' we append pack to lines
        else:
            pack = lines[-1]                                    # if we don't hit a '-1' we use the current (last) index in pack
        pack.append(data)                                       # we add the current line to pack
    return lines

### Turn lines array into ...
def CreateFiberFromTextData(pack, scale):
    lsPoints = []
    for d in pack:
        point = Vector((float(d[2]),float(d[3]),float(d[4]))) * scale
        #print(point)
        lsPoints.append(point)
    length = 0
    if len(lsPoints) > 2:
        p0 = lsPoints[0]
        p1 = lsPoints[-1]
        length = math.sqrt( (p1.x - p0.x)*(p1.x - p0.x) +  (p1.y - p0.y)*(p1.y - p0.y) + (p1.z - p0.z)*(p1.z - p0.z) )
    return lsPoints, length

#### Get the fiber direction ###
def GetFiberDirection(fiberPoints):
    vecs=[] #Create Empty list of vectors
    for i in range(0, len(fiberPoints)-1):
        p0 = fiberPoints[i]
        p1 = fiberPoints[i + 1]
        v = p1 - p0 #Directional vector from next to current point
        vecs.append(v)
    vdir = Vector((0,0,0))
    for v in vecs:
        vdir += v
    vdir = vdir/len(vecs)
    #CreateCurve([p0, p1] , 0.1, (0,255,0,255), False)
    return vdir.normalized()


### Create Curves from fiber data ###
def CreateCurve(dataPoints,thickness,color,use_cyclic,collection):
    # create the Curve Data object
    curveData = bpy.data.curves.new('myCurveData', type='CURVE')
    curveData.dimensions = '3D'
    curveData.resolution_u = 3                                  # quality of the curve in the view
    curveData.render_resolution_u = 5                           # quality of the curve in Render
    curveData.bevel_depth = thickness                           # Thickness
    curveData.bevel_resolution = 3                              # quality of the bevel
    curveData.fill_mode = 'FULL'                                # type of bevel
    curveData.use_fill_caps = True                              # close the curve at both caps
    # map points to spline
    polyline = curveData.splines.new('NURBS')                   # create a polyline in the curveData
    polyline.points.add(len(dataPoints)-1)                      # specify the total number of points
    i = 0
    for p in dataPoints:                                        # open the loop. for each index(i) and tuple(coord)
        polyline.points[i].co = Vector((p.x, p.y, p.z,1))       # assign to the point at index, the corresponded x,y,z
        i+=1
    curveData.splines[0].use_cyclic_u = use_cyclic              # specify if the curve is cyclic or not
    curveData.splines[0].use_endpoint_u = True                  # draw including endpoints
    curveOBJ = bpy.data.objects.new(str(collection), curveData) # crete new curve obj with the curveData
    scene = bpy.context.scene                                   # get reference to our scene
    scene.collection.objects.link(curveOBJ)
    bpy.data.collections[collection].objects.link(curveOBJ)
    #creating and assigning material
    if str(collection) in bpy.data.materials:                   # if there already is a material for our collection, then
        mat = bpy.data.materials[str(collection)]               # the new object is added to the same material
    else:                                                       # else:
        mat = bpy.data.materials.new(str(collection))           # Create new material
        mat.diffuse_color = color                               # set diffuse color to our color in viewport
    curveOBJ.active_material = mat                              # assign this material to our curveObject
    curveOBJ.material_slots[0].link = 'OBJECT'                  # link material in slot 0 to object
    curveOBJ.material_slots[0].material = mat                   # link material in slot 0 to our material
    bpy.context.view_layer.objects.active = curveOBJ            # Set new curve object as active object
    return curveOBJ                                             # return reference to this curve object


#--------------------------------------------------------------------------
# Create a button in the scene tab to recolor the Straightened FIbers
#--------------------------------------------------------------------------
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

        # assign nodes to variables
        node_bsdf = nodes['Principled BSDF']
        nodes.new('ShaderNodeValToRGB')
        node_ramp = nodes['ColorRamp']
        nodes.new('ShaderNodeMath')
        node_math = nodes['Math']
        nodes.new('ShaderNodeValue')
        node_value = nodes['Value']

        # link the nodes together, bsdf is already linked to Output node
        tree.links.new(node_ramp.outputs['Color'], node_bsdf.inputs['Base Color']) # Connect ColorRamp and BSDF
        tree.links.new(node_math.outputs['Value'], node_ramp.inputs[0]) # Connect Math and ColorRamp
        #tree.links.new(node_value.outputs['Value'], node_math.inputs[0]) # Connect Value and Math, not yet supported

        # customize the nodes
        # color ramp Blue/Red gradient
        node_ramp.color_ramp.elements[0].color = (0,0,1,1)
        node_ramp.color_ramp.elements[1].color = (1,0,0,1) # Don't use RGB 0/255 here, it fs up the ramp
        # Math module division and by 90
        node_math.operation = "DIVIDE"
        node_math.inputs[1].default_value = 90 # Assume muscle fibers attach at not more than 90 degrees
        # value needs an input!
        node_value.outputs[0].default_value = 0
        #node_value.driver_add("attachment_angle") not yet supported

        # placeholder vor value node: Object Info node and pass index
        nodes.new('ShaderNodeObjectInfo')
        node_info = nodes['Object Info']
        tree.links.new(node_info.outputs[2], node_math.inputs[0])

        # select objects in 'Straightened'
        context.view_layer.active_layer_collection = context.view_layer.layer_collection.children['Straightened']

        # act out the recoloring
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

#--------------------------------------------------------------------------
#### Adjust the scene for tomography data ####
#--------------------------------------------------------------------------
#The units are not carried over correctly, so what has been at an x-position of 1000 micrometers would now be at 1000 m, which is out of bounds for the Blender viewer standard!
#That's why one arg is SCALE_MULT, the outcommented codes below expand the viewer scene if you do 3D analysis on elephants or what not

#bpy.context.scene.unit_settings.scale_length = 1e-05
#bpy.context.scene.unit_settings.length_unit = 'MICROMETERS'
#bpy.context.space_data.clip_end = 10000 * SCALE_MULT
#SCREEN_AREA.spaces.active.clip_end = 10000 * SCALE_MULT

for SCREEN_AREA in bpy.context.screen.areas:
    if SCREEN_AREA.type == 'VIEW_3D':
        break

#Delete the default objects
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
context = bpy.context
scene = context.scene

for c in scene.collection.children:
    scene.collection.children.unlink(c)
for c in bpy.data.collections:
    if not c.users:
        bpy.data.collections.remove(c)

#--------------------------------------------------------------------------
#Automated file input and image/scene generation via blender/python console
#--------------------------------------------------------------------------

####Create layers for different visualizations####
tendon_col = bpy.data.collections.new("Tendon/Apodeme")
bpy.context.scene.collection.children.link(tendon_col)
fibers_col = bpy.data.collections.new("Fibers")
bpy.context.scene.collection.children.link(fibers_col)
normalized_col = bpy.data.collections.new("Normalized")
bpy.context.scene.collection.children.link(normalized_col)
straight_col = bpy.data.collections.new("Straightened")
bpy.context.scene.collection.children.link(straight_col)

####Read and draw the apodeme####
p1,p2,p3,p4 = ReadApodemeData(FILE_MARKERS, SCALE_MULT)

#data verts points in Blender
CreatePointAtLocation(p1)
CreatePointAtLocation(p2)
CreatePointAtLocation(p3)
CreatePointAtLocation(p4)

directionVector, v12mid, v34mid = GetApodemeDirection(p1,p2,p3,p4)
#apodeme - directional
CreateCurve(dataPoints = [v34mid,v12mid], thickness = 0.05, color = (0,1,0,1), use_cyclic = False, collection = "Tendon/Apodeme")
#normalized apodeme
normalApodeme = directionVector.normalized()
CreateCurve(dataPoints = [Vector((0,0,0)),normalApodeme], thickness = 0.05, color = (0,1,0,1), use_cyclic = False, collection = "Tendon/Apodeme")

####Read and draw the fibers, calculate the angles####
#for each fiber:
filepath = bpy.data.filepath
directory = os.path.dirname(filepath)
fiberFilePath = os.path.join(directory,FILE_FIBERS)
allFiberlines = ReadFiberData(fiberFilePath)

rawDirections = []
rawLengths = []

#bpy.ops.object.select_all(action='DESELECT')

for i in range(0, len(allFiberlines)):
    lines = allFiberlines[i]
    #create fiber from data
    fiberPoints, length = CreateFiberFromTextData(lines, SCALE_MULT)
    rawLengths.append(length)
    #if we got enough points:
    if len(fiberPoints):
        #individual fiber - directional
        CreateCurve(dataPoints = fiberPoints, thickness = 0.05, color = (1,0,0,1), use_cyclic = False, collection = "Fibers")
        fiberDirection = GetFiberDirection(fiberPoints)
        #compute angle
        angle = math.degrees(fiberDirection.angle(normalApodeme, Vector((0,0,0)))) # store this in a custom property and save to .csv
        if angle >= 90:
            angle = abs(angle - 180)
            #append for output to *.csv
            rawDirections.append(angle)
            #create direction curve flipped
            CreateCurve(dataPoints = [fiberPoints[0], fiberPoints[0]+fiberDirection*length], thickness = 0.05,  color = (1,0.5,0,1), use_cyclic = False, collection = "Straightened")
            bpy.context.object.data["attachment_angle"] = angle # Add Custom Property to straightened for later visualization
            bpy.context.object.pass_index = int(angle) # placeholder until adding driver works
            #draw nomalized flipped fiber at origin for debug and and clear visualization:
            CreateCurve(dataPoints = [Vector((0,0,0)),-(fiberDirection)], thickness = 0.05, color = (1,0,0,1), use_cyclic = False, collection = "Normalized")
            bpy.context.object.data["attachment_angle"] = angle # Add Custom Property to normalized for later visualization
            bpy.context.object.pass_index = int(angle) # placeholder until adding driver works
        else:
            #append for output to *.csv
            rawDirections.append(angle)
            #create direction curve
            CreateCurve(dataPoints = [fiberPoints[0], fiberPoints[0]+fiberDirection*length], thickness = 0.05, color = (1,0.5,0,1), use_cyclic = False, collection = "Straightened")
            bpy.context.object.data["attachment_angle"] = angle # Add Custom Property to straightened
            bpy.context.object.pass_index = int(angle) # placeholder until adding driver works
            #draw nomalized fiber at origin for debug and clear visualization:
            CreateCurve(dataPoints = [Vector((0,0,0)),fiberDirection], thickness = 0.05, color = (1,0,0,1), use_cyclic = False, collection = "Normalized")
            bpy.context.object.data["attachment_angle"] = angle # Add Custom Property to normalized for later visualization
            bpy.context.object.pass_index = int(angle) # placeholder until adding driver works

    #curveOBJ.select_set(state=True)
    #context.view_layer.objects.active = curveOBJ.select_set(state=True)
    #curveOBJ.select_set(state=False)




#--------------------------------------------------------------------------
# Write attachment angles to one column - csv
#--------------------------------------------------------------------------
FILE_DIRECTIONS =  os.path.join(directory,"out-directions.csv")
strDirections=[str(s) for s in rawDirections]
with open(FILE_DIRECTIONS,'w') as f:
    f.writelines('\n'.join(strDirections))

#--------------------------------------------------------------------------
# Write fiber lengths to one column - csv
#--------------------------------------------------------------------------
FILE_LENGTHS =  os.path.join(directory,"out-lengths.csv")
strLengths=[str(s) for s in rawLengths]
with open(FILE_LENGTHS,'w') as f:
    f.writelines('\n'.join(strLengths))
