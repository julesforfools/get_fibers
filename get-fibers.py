import sys
from mathutils import Vector
import bpy
import math
import os
import numpy as np

print(sys.argv[0:])
print(len(sys.argv))
#Blender 2.79-2.91 not supported!
#Blender 2.92 supported! (New Attribute shader node required)
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
FIBER_DIAM = float(sys.argv[7])*SCALE_MULT if len(sys.argv) == 8 else 0.01/SCALE_MULT

#--------------------------------------------------------------------------
# Declare Functions Related to getting Muscle Architecture data from fibers
#--------------------------------------------------------------------------

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
def CreatePointAtLocation(location,size=FIBER_DIAM):
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

### Turn lines array into list of vectors
def CreateFiberFromTextData(pack, scale):
    lsPoints = []
    for d in pack:
        point = Vector((float(d[2]),float(d[3]),float(d[4]))) * scale
        #print(point)
        lsPoints.append(point)
    length = 0
    if len(lsPoints) >= 2:
        p0 = lsPoints[0]
        p1 = lsPoints[-1]
        length = math.sqrt( (p1.x - p0.x)*(p1.x - p0.x) +  (p1.y - p0.y)*(p1.y - p0.y) + (p1.z - p0.z)*(p1.z - p0.z) )
    return lsPoints, length

#### Get the fiber direction, do quality check and redo fiber points ###
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
    vdir = vdir/len(vecs) # get first mean vector
    vdir_95 = vdir.normalized()-vdir.normalized()*0.05
    # Estimate improved direction vector
    vecs2 =[]
    schmecs=[]
    for v in vecs:
        if (vdir.normalized()-v.normalized()) <= vdir_95:
            vecs2.append(v)
        else:
            schmecs.append(v)
    vdir2 = Vector((0,0,0))
    for v in vecs2:
        vdir2 += v
    vdir2 = vdir2/len(vecs2)
    # Get rid of bad points
    bad_vecs_ind = []
    for i in range(0, len(schmecs)):
        bad_vecs_ind.append(vecs.index(schmecs[i]))
    newPoints = fiberPoints
    for i in range(0, len(bad_vecs_ind)):
        #print(i)
        if bad_vecs_ind[i] == 0:
            del(newPoints[0])
            bad_vecs_ind = [x-1 for x in bad_vecs_ind]
        if bad_vecs_ind[i] == bad_vecs_ind[i-1]+1:
            del(newPoints[bad_vecs_ind[i]])
            bad_vecs_ind = [x-1 for x in bad_vecs_ind]
        if bad_vecs_ind[i] == len(newPoints)-2:
            del(newPoints[-1])
    # Return direction Vector and good Points
    return vdir2.normalized(), newPoints


#### Get the essential fiber parameters, slope and intercept to group them afterwards ###
def GetFiberEssentials(newfiberPoints, fiberDirection, length):
    # Create Numpy Array from Vectors
    newParray = np.array([])
    for i in range(0, len(newfiberPoints)):
        newParray = np.append(newParray, newfiberPoints[i][0]) # x components
        newParray = np.append(newParray, newfiberPoints[i][1]) # y components
        newParray = np.append(newParray, newfiberPoints[i][2]) # z components
    newParray = np.reshape(newParray, (len(newfiberPoints), 3))
    # Create numpy array for fiber midpoint and fiber direction
    essentials = np.array([newfiberPoints[0][0],newfiberPoints[0][1],newfiberPoints[0][2],np.mean(newParray[:,0]), np.mean(newParray[:,1]), np.mean(newParray[:,2]), newfiberPoints[-1][0],newfiberPoints[-1][1],newfiberPoints[-1][2], fiberDirection[0], fiberDirection[1], fiberDirection[2], length])
    return newParray, essentials

#### Helper function to return the smallest ID of fibers that have not been checked yet
def not_in_it(A, B):
    for i in A:
        if i not in B:
            return i

#### Reduce the number of streamlines, based on proximity ###
def fibers_sort_mid_fast(df, ids, radius):
    for i in range(0, len(df)):
        if df[i,12] == 0:
            continue
        print("checking:", i)
        for j in range(0, len(df)):
            if df[j,12] == 0:
                continue
            d = np.sqrt(((df[i,3]-df[j,3])**2)+((df[i,4]-df[j,4])**2)+((df[i,5]-df[j,5])**2)) # Distance of two points in 3D space
            if d <= radius and df[i,12] > df[j,12]: #the condition: if fibers are close together and second fiber is shorter
                df[j] = np.zeros(13)
                #print("skipping:", j)
    for i in ids:
        if df[i,12] == -1:
            continue
        elif df[i,12] == 0:
            ids[i] = -1
    return(df, ids)

def fibers_sort_start_fast(df, ids, radius):
    for i in range(0, len(df)):
        if df[i,12] == 0:
            continue
        #print("checking:", i)
        for j in range(0, len(df)):
            if df[j,12] == 0:
                continue
            d = np.sqrt(((df[i,0]-df[j,0])**2)+((df[i,1]-df[j,1])**2)+((df[i,2]-df[j,2])**2)) # Distance of two points in 3D space
            if d <= radius and df[i,12] > df[j,12]: #the condition: if fibers are close together and second fiber is shorter
                df[j] = np.zeros(13)
                #print("skipping:", j)
    for i in ids:
        if df[i,12] == -1:
            continue
        elif df[i,12] == 0:
            ids[i] = -1
    return(df, ids)

def fibers_sort_end_fast(df, ids, radius):
    for i in range(0, len(df)):
        if df[i,12] == 0:
            continue
        #print("checking:", i)
        for j in range(0, len(df)):
            if df[j,12] == 0:
                continue
            d = np.sqrt(((df[i,6]-df[j,6])**2)+((df[i,7]-df[j,7])**2)+((df[i,8]-df[j,8])**2)) # Distance of two points in 3D space
            if d <= radius and df[i,12] > df[j,12]: #the condition: if fibers are close together and second fiber is shorter
                df[j] = np.zeros(13)
                #print("skipping:", j)
    for i in ids:
        if df[i,12] == -1:
            continue
        elif df[i,12] == 0:
            ids[i] = -1
    return(df, ids)

def fibers_sort_t(df, ids, radius):
    # Assign t and x-intercept
    df = np.c_[df, np.zeros(len(df))] # add t column, index 13
    for i in range(0, len(df)):
        if df[i,12] == 0:
            continue
        df[i,13] = (-df[i,3])/df[i,9] # calculate and assign t
    df = np.c_[df, np.zeros(len(df))] # add aX column == 0
    for i in range(0, len(df)):
        if df[i,12] == 0:
            continue
        df[i,14] = df[i,3]+(df[i,13]*df[i,9]) # calculate and assign aX
    df = np.c_[df, np.zeros(len(df))] # add aY column
    for i in range(0, len(df)):
        if df[i,12] == 0:
            continue
        df[i,15] = df[i,4]+(df[i,13]*df[i,10]) # calculate and assign aY
    df = np.c_[df, np.zeros(len(df))] # add aZ column
    for i in range(0, len(df)):
        if df[i,12] == 0:
            continue
        df[i,16] = df[i,5]+(df[i,13]*df[i,11]) # calculate and assign aZ
    # Begin Cleanup
    for i in range(0, len(df)):
        if df[i,12] == 0:
            continue
        #print("checking:", i)
        for j in range(0, len(df)):
            if df[j,12] == 0:
                continue
            d = np.sqrt(((df[i,15]-df[j,15])**2)+((df[i,16]-df[j,16])**2)) # Distance of two points in 2D space
            angle = (df[i,9]*df[j,9]+df[i,10]*df[j,10]+df[i,11]*df[j,11])/((np.sqrt(df[i,9]**2+df[i,10]**2+df[i,11]**2))*(np.sqrt(df[j,9]**2+df[j,10]**2+df[j,11]**2)))
            if d <= radius and angle > 0.9 and df[i,12] > df[j,12]: #the condition: if fibers are close together and second fiber is shorter
                df[j] = np.zeros(17)
                print("skipping:", j)
    for i in ids:
        if df[i,12] == -1:
            continue
        elif df[i,12] == 0:
            ids[i] = -1
    return(df, ids)

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

### Estimate Muscle volume from fiber data ###
def CalcVolume(source_col, target_col, size):
    for obj in bpy.context.selected_objects:
        obj.select_set(False)
    for obj in bpy.data.collections[source_col].all_objects:
            if obj.type == "CURVE":
                obj.select_set(True)
    bpy.ops.object.duplicate()
    for obj in bpy.context.selected_objects:
        bpy.data.collections[source_col].objects.unlink(obj)
        bpy.data.collections[target_col].objects.link(obj)
    # Create a volume based on fibers
    bpy.context.view_layer.objects.active = bpy.data.collections[target_col].all_objects[0]
    bpy.ops.object.convert(target='MESH')
    bpy.ops.object.join()
    bpy.ops.object.modifier_add(type='REMESH')
    bpy.context.object.modifiers["Remesh"].voxel_size = size
    bpy.ops.object.modifier_apply(modifier="Remesh")
    bpy.ops.object.duplicate()
    bpy.ops.object.modifier_add(type='SUBSURF')
    bpy.context.object.modifiers["Subdivision"].levels = 3
    bpy.context.object.modifiers["Subdivision"].render_levels = 3
    bpy.ops.object.modifier_add(type='SHRINKWRAP')
    bpy.context.object.modifiers["Shrinkwrap"].wrap_method = 'PROJECT'
    bpy.context.object.modifiers["Shrinkwrap"].wrap_mode = 'OUTSIDE'
    bpy.context.object.modifiers["Shrinkwrap"].use_negative_direction = True
    bpy.context.object.modifiers["Shrinkwrap"].target = bpy.data.collections[target_col].all_objects[0]
    bpy.context.object.modifiers["Shrinkwrap"].offset = size/2
    bpy.ops.object.modifier_apply(modifier="Subdivision")
    bpy.ops.object.modifier_apply(modifier="Shrinkwrap")
    # Calculate Object Volume by calculating mass with density of 1
    bpy.ops.rigidbody.objects_add(type='ACTIVE')
    bpy.ops.rigidbody.mass_calculate(material='Custom')
    vol = bpy.context.object.rigid_body.mass
    return vol

# Create Collections to display different versions of muscle fibers
def FiberColCreate():
    tendon_col = bpy.data.collections.new("Tendon/Apodeme")
    bpy.context.scene.collection.children.link(tendon_col)
    mesh_col = bpy.data.collections.new("Mesh")
    bpy.context.scene.collection.children.link(mesh_col)
    fibers_col = bpy.data.collections.new("Fibers")
    bpy.context.scene.collection.children.link(fibers_col)
    normalized_col = bpy.data.collections.new("Normalized")
    bpy.context.scene.collection.children.link(normalized_col)
    straight_col = bpy.data.collections.new("Straightened")
    bpy.context.scene.collection.children.link(straight_col)

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
FiberColCreate()

####Read and draw the apodeme####
p1,p2,p3,p4 = ReadApodemeData(FILE_MARKERS, SCALE_MULT)

#data verts points in Blender
CreatePointAtLocation(p1)
CreatePointAtLocation(p2)
CreatePointAtLocation(p3)
CreatePointAtLocation(p4)

directionVector, v12mid, v34mid = GetApodemeDirection(p1,p2,p3,p4)
#apodeme - directional
CreateCurve(dataPoints = [v34mid,v12mid], thickness = FIBER_DIAM/2, color = (0,1,0,1), use_cyclic = False, collection = "Tendon/Apodeme")
#normalized apodeme
normalApodeme = directionVector.normalized()
CreateCurve(dataPoints = [Vector((0,0,0)),normalApodeme], thickness = FIBER_DIAM/2, color = (0,1,0,1), use_cyclic = False, collection = "Tendon/Apodeme")

####Read and draw the fibers, calculate the angles####
#for each fiber:

filepath = bpy.data.filepath
directory = os.path.dirname(filepath)
fiberFilePath = os.path.join(directory,FILE_FIBERS)
print("Reading Fibers Now")
allFiberLines = ReadFiberData(fiberFilePath)


rawDirections = []
rawLengths = []
print(type(FIBER_DIAM))
radius = FIBER_DIAM/SCALE_MULT/2
print("radius:", radius)

print("Cleaning Fibers Now")
#bpy.ops.object.select_all(action='DESELECT')
fiber_essentials = np.array([])
for i in range(0, len(allFiberLines)):
    #print("processing fiber:", i)
    fiber = allFiberLines[i]
    points, length = CreateFiberFromTextData(fiber, 1) #create fibers as array
    direction, newPoints = GetFiberDirection(points)
    newParray, essentials = GetFiberEssentials(newPoints, direction, length)
    fiber_essentials = np.append(fiber_essentials, essentials)
fiber_essentials = np.reshape(fiber_essentials, (len(allFiberLines), 13))
print("Finished Cleaning Fibers")

df = fiber_essentials
ids = np.array(range(0, len(df)))
ids_copy = ids.copy()

df, ids = fibers_sort_mid_fast(df, ids, radius)
df, ids = fibers_sort_start_fast(df, ids, radius)
df, ids = fibers_sort_end_fast(df, ids, radius)
df, ids = fibers_sort_t(df, ids, radius)

winner_ids = np.array([])
for i in range(0, len(ids)):
    if ids[i] != -1:
        winner_ids = np.append(winner_ids, ids[i])
winner_ids = winner_ids.astype(int)

print("No. of winners:", len(winner_ids))

fibers_array = np.array(allFiberLines)
winners = fibers_array[winner_ids]

for i in range(0, len(winners)):
    #print("working fiber no.:", i)
    lines = winners[i]
    #create fiber from data
    fiberPoints, length = CreateFiberFromTextData(lines, SCALE_MULT)
    rawLengths.append(length)
    #if we got enough points:
    if len(fiberPoints):
        #individual fiber - directional
        CreateCurve(dataPoints = fiberPoints, thickness = FIBER_DIAM/2, color = (1,0,0,1), use_cyclic = False, collection = "Fibers")
        fiberDirection, newPoints = GetFiberDirection(fiberPoints)
        #compute pennation angle
        angle = math.degrees(fiberDirection.angle(normalApodeme, Vector((0,0,0)))) # store this in a custom property and save to .csv
        if angle >= 90:
            angle = abs(angle - 180)
            #append for output to *.csv
            rawDirections.append(angle)
            #create direction curve flipped
            CreateCurve(dataPoints = [fiberPoints[0], fiberPoints[0]+fiberDirection*length], thickness = FIBER_DIAM/2,  color = (1,0.5,0,1), use_cyclic = False, collection = "Straightened")
            bpy.context.object.data["attachment_angle"] = angle # Add Custom Property to straightened for later visualization
            bpy.context.object.pass_index = int(angle) # placeholder until adding driver works
            #draw nomalized flipped fiber at origin for debug and and clear visualization:
            CreateCurve(dataPoints = [Vector((0,0,0)),-(fiberDirection)], thickness = FIBER_DIAM/2, color = (1,0,0,1), use_cyclic = False, collection = "Normalized")
            bpy.context.object.data["attachment_angle"] = angle # Add Custom Property to normalized for later visualization
            bpy.context.object.pass_index = int(angle) # placeholder until adding driver works
        else:
            #append for output to *.csv
            rawDirections.append(angle)
            #create direction curve
            CreateCurve(dataPoints = [fiberPoints[0], fiberPoints[0]+fiberDirection*length], thickness = FIBER_DIAM/2, color = (1,0.5,0,1), use_cyclic = False, collection = "Straightened")
            bpy.context.object.data["attachment_angle"] = angle # Add Custom Property to straightened
            bpy.context.object.pass_index = int(angle) # placeholder until adding driver works
            #draw nomalized fiber at origin for debug and clear visualization:
            CreateCurve(dataPoints = [Vector((0,0,0)),fiberDirection], thickness = FIBER_DIAM/2, color = (1,0,0,1), use_cyclic = False, collection = "Normalized")
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

#--------------------------------------------------------------------------
# Write Summary to csv
#--------------------------------------------------------------------------
def my_mean(sample):
    return sum(sample) / len(sample)
len1 = my_mean(rawLengths)
vol1 = CalcVolume("Fibers", "Mesh", FIBER_DIAM)
ang1 = my_mean(rawDirections)
print("Volume [mm3]: ", vol1)
print("Avg Length [mm] ", len1)
print("Avg Angle [deg] ",ang1)
print("# fibers", len(rawLengths))
print(math.cos(math.pi/(ang1)))
pcsa2 = (vol1*(math.cos(ang1*math.pi/180)))/len1
print("PCSA2 [mm2]: ", pcsa2)

#--------------------------------------------------------------------------
# Write Winners to csv
#--------------------------------------------------------------------------
FILE_WINNERS =  os.path.join(directory,"winner-fibers.csv")
np.savetxt(FILE_WINNERS, winners, delimiter=',', fmt='%s')
