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
MIN_LENGTH = sys.argv[7]
### Set the scale for visualization in Blender ###
if SCALE_MULT == 'mm':
    SCALE_MULT = 0.01
if SCALE_MULT == 'um':
    SCALE_MULT = 10


### Read Apodeme/Tendon Data from 4 landmarks ###
def ReadApodemeData(filename):
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
                p1 = Vector((float(points[0][0]),float(points[0][1]),float(points[0][2])))#*SCALE_MULT
                p2 = Vector((float(points[1][0]),float(points[1][1]),float(points[1][2])))#*SCALE_MULT
                p3 = Vector((float(points[2][0]),float(points[2][1]),float(points[2][2])))#*SCALE_MULT
                p4 = Vector((float(points[3][0]),float(points[3][1]),float(points[3][2])))#*SCALE_MULT
    return p1,p2,p3,p4

def GetApodemeDirection(p1,p2,p3,p4):
    v12mid = (p1+p2)/2 #Vector(( (p1.x+p2.x)/2.0, (p1.y+p2.y)/2.0, (p1.z+p2.z)/2.0 ))
    v34mid = (p3+p4)/2 #Vector(( (p3.x+p4.x)/2.0, (p3.y+p4.y)/2.0, (p3.z+p4.z)/2.0 ))
    return v12mid - v34mid, v12mid, v34mid


### Read Muscle Fiber Data from lines-file ###
def ReadStreamData(filename):
    textlines=[]
    with open(filename, 'r') as f:
        textlines = f.readlines()
    textlines = [l.rstrip('\n').lstrip() for l in textlines]
    lines=[]                                                    # create an empty list object for the final output
    pack=[]                                                     # create object pack that gets appended to lines
    for line in textlines:                                      # initiate final iterating loop
        if line.startswith('object'):                           # this finishes the loop when the last line is hit
            continue
        if line.startswith('material'):                         # when the line starts with 'material' we consider this fiber finished
            if len(pack) < MIN_LENGTH:                          # if the streamline doesn't reach a specific threshold length we skip it
                pack = []
            else:
                lines.append(pack)                              # else, if we hit 'material...' we append pack to the lines object
                pack = []
        else:
            data = line.split('\t')                             # the current line is assigned to 'data', it is split by tab
            pack.append(data)                                   # we add the current line to pack
    return lines

### Create Points from landmarks ###
def CreatePointAtLocation(location,size=0.1):
    #scene = bpy.context.scene
    bpy.ops.mesh.primitive_cube_add(size=size, calc_uvs=True,location=location) #size=size * 0.01 * SCALE_MULT
    #cube = bpy.context.active_object

### Create Curves from apodeme data ###
def CreateCurve(dataPoints,thickness,color,use_cyclic,collection):
    # create the Curve Data object
    curveData = bpy.data.curves.new('myCurveData', type='CURVE')
    curveData.dimensions = '3D'
    curveData.resolution_u = 3                          # quality of the curve in the view
    curveData.render_resolution_u = 3                   # quality of the curve in Render
    curveData.bevel_depth = thickness                   # Thickness
    curveData.bevel_resolution = 3                      # quality of the bevel
    curveData.fill_mode = 'FULL'                        # type of bevel
    # map points to spline
    polyline = curveData.splines.new('NURBS')           # create a polyline in the curveData
    polyline.points.add(len(dataPoints)-1)                  # specify the total number of points
    i = 0
    for p in dataPoints:                                    # open the loop. for each index(i) and tuple(coord)
        polyline.points[i].co = Vector((p.x, p.y, p.z,1))  # assign to the point at index, the corresponded x,y,z
        i+=1
    curveData.splines[0].use_cyclic_u = use_cyclic      # specify if the curve is cyclic or not
    curveData.splines[0].use_endpoint_u = True          # draw including endpoints
    curveOBJ = bpy.data.objects.new('myCurve', curveData) # crete new curve obj with the curveData
    scene = bpy.context.scene                            # get reference to our scene
    scene.collection.objects.link(curveOBJ)
    bpy.data.collections[collection].objects.link(curveOBJ)
    #creating and assigning new material
    mat = bpy.data.materials.new("matBase")            # Create new material
    mat.diffuse_color = color                          # set diffuse color to our color
    mat.metallic = 1
    mat.specular_intensity = 0.125                     # specify specular intensity
    curveOBJ.active_material = mat                     # assign this material to our curveObject
    curveOBJ.material_slots[0].link = 'OBJECT'         # link material in slot 0 to object
    curveOBJ.material_slots[0].material = mat          # link material in slot 0 to our material
    return curveOBJ                                    # return reference to this curve object


def CreateStreamFromTextData(pack):
    lsPoints = []
    for d in pack:
        point = Vector((float(d[0]),float(d[1]),float(d[2])))# * SCALE_MULT
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

#--------------------------------------------------------------------------
#### Adjust the scene for tomography data ####
#--------------------------------------------------------------------------
#The units are not carried over correctly, so what has been at an x-position of 1000 micrometers would now be at 1000 m, which is out of bounds for the Blender viewer standard
#The next bit expands the viewer area

#bpy.context.scene.unit_settings.scale_length = 1e-05
#bpy.context.scene.unit_settings.length_unit = 'MICROMETERS'
#bpy.context.space_data.clip_end = 10000 * SCALE_MULT

for SCREEN_AREA in bpy.context.screen.areas:
    if SCREEN_AREA.type == 'VIEW_3D':
        break

SCREEN_AREA.spaces.active.clip_end = 10000 * SCALE_MULT

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

####Create a layer for the apodeme####
tendon_col = bpy.data.collections.new("Apodeme")
bpy.context.scene.collection.children.link(tendon_col)
#tendon_sel = bpy.context.view_layer.layer_collection.children[tendon_col.name]
#bpy.context.view_layer.active_layer_collection = tendon_sel

####Read and draw the apodeme####
p1,p2,p3,p4 = ReadApodemeData(FILE_MARKERS)

#data verts points in Blender
CreatePointAtLocation(p1)
CreatePointAtLocation(p2)
CreatePointAtLocation(p3)
CreatePointAtLocation(p4)

directionVector, v12mid, v34mid = GetApodemeDirection(p1,p2,p3,p4)
#apodeme - directional
CreateCurve(dataPoints = [v34mid,v12mid], thickness = SCALE_MULT, color = (0,255,0,255), use_cyclic = False, collection = "Apodeme")#thickness = 10 * SCALE_MULT
#normalized apodeme
normalApodeme = directionVector.normalized()
CreateCurve([Vector((0,0,0)),normalApodeme * 100 * SCALE_MULT], SCALE_MULT, (0,255,0,255), False, collection = "Apodeme")#thickness = 10 * SCALE_MULT

####Create layers for the fibers####
fibers_col = bpy.data.collections.new("Fibers")
bpy.context.scene.collection.children.link(fibers_col)
normalized_col = bpy.data.collections.new("Normalized")
bpy.context.scene.collection.children.link(normalized_col)
straight_col = bpy.data.collections.new("Straightened")
bpy.context.scene.collection.children.link(straight_col)

####Read and draw the fibers, calculate the angles####
#for each fiber:
filepath = bpy.data.filepath
directory = os.path.dirname(filepath)
fiberFilePath = os.path.join(directory,FILE_FIBERS)
allFiberlines = ReadStreamData(fiberFilePath)

rawDirections = []

for i in range(0, len(allFiberlines)):
    lines = allFiberlines[i]
    #create fiber from data
    fiberPoints, length = CreateStreamFromTextData(lines)
    #if we got enough points:
    if len(fiberPoints):
        #individual fiber - directional
        CreateCurve(fiberPoints, SCALE_MULT/5, (255,128,0,255), False, collection = "Fibers")
        fiberDirection = GetFiberDirection(fiberPoints)
        #compute angle
        angle = math.degrees(fiberDirection.angle(normalApodeme, Vector((0,0,0))))
        if angle >= 90:
            angle = abs(angle - 180)
            #append for output to *.csv
            rawDirections.append(angle)
            #create direction curve flipped
            CreateCurve([fiberPoints[0], fiberPoints[0]+fiberDirection*length], SCALE_MULT/5, (255,0,0,255), False, collection = "Straightened")
            #draw nomalized fiber at origin for debug and flipped:
            #CreateCurve([Vector((0,0,0)),-(fiberDirection * 100 * SCALE_MULT)], SCALE_MULT, (255,0,0,255), False, collection = "Normalized")
        else:
            #append for output to *.csv
            rawDirections.append(angle)
            #create direction curve
            CreateCurve([fiberPoints[0], fiberPoints[0]+fiberDirection*length], SCALE_MULT/5, (255,0,0,255), False, collection = "Straightened")
            #draw nomalized fiber at origin for debug:
            #CreateCurve([Vector((0,0,0)),fiberDirection * 100 * SCALE_MULT], SCALE_MULT, (255,0,0,255), False, collection = "Normalized")


#--------------------------------------------------------------------------
# Write attachment angles to one column - csv
#--------------------------------------------------------------------------
FILE_DIRECTIONS =  os.path.join(directory,"out-streams.csv")
strDirections=[str(s) for s in rawDirections]
with open(FILE_DIRECTIONS,'w') as f:
    f.writelines('\n'.join(strDirections))



#---------------------- QUICK PLOT --------------------------------
#pip3 install matplotlib

#plt.plot(rawDirections)
#plt.show()
#plt.savefig('out-directions.png')
