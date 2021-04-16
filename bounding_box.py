import bpy
from bpy.props import *
from mathutils import *
from math import *   
from bpy.types import Operator    
from bpy.types import PropertyGroup

###
   
class functions():
    
    def getobjectBounds(ob):
    
        obminx = ob.bound_box[0][0]+ob.location.x
        obminy = ob.bound_box[0][1]+ob.location.y
        obminz = ob.bound_box[0][2]+ob.location.z
    
        obmaxx = ob.bound_box[7][0]+ob.location.x
        obmaxy = ob.bound_box[7][1]+ob.location.y
        obmaxz = ob.bound_box[7][2]+ob.location.z
    
        for vertex in ob.bound_box[:]:
    
            x = vertex[0]+ob.location.x
            y = vertex[1]+ob.location.y
            z = vertex[2]+ob.location.z
# if other vertex locations are smaller, update object minimum     
            if x <= obminx:
                obminx = x
            if y <= obminy:
                obminy = y
            if z <= obminz:
                obminz = z
# if other vertex locations are larger, update object maximum   
            if x >= obmaxx:
                obmaxx = x
            if y >= obmaxy:
                obmaxy = y
            if z >= obmaxz:
                obmaxz = z
    
        boundsmin = [obminx,obminy,obminz]
        boundsmax = [obmaxx,obmaxy,obmaxz] 
        bounds = [boundsmin,boundsmax] 
        return bounds

scd1 = [0,0,0,0]
   
def scenedim1():
    
    
    global scd1
    
    minx = 0
    miny = 0
    minz = 0
    
    maxx = 0
    maxy = 0
    maxz = 0
      
    c1=0
    
    for o1 in bpy.context.selected_objects:
    
        if o1.name=="Camera" or o1.name=="Empty":
            pass
    
        else:
            
            bounds = functions.getobjectBounds(o1)
            oxmin = bounds[0][0]
            oxmax = bounds[1][0]
    
            oymin = bounds[0][1]
            oymax = bounds[1][1]
        
            ozmin = bounds[0][2]
            ozmax = bounds[1][2]
    
            if  c1 == 0 :
                minx = oxmin
                miny = oymin
                minz = ozmin
    
                maxx = oxmax
                maxy = oymax
                maxz = ozmax
    
         # min 
    
            if oxmin <= minx:
                minx = oxmin
    
            if oymin <= miny:
                miny = oymin
    
            if ozmin <= minz:
                minz = ozmin
    
        # max 
    
            if oxmax >= maxx:
                maxx = oxmax
    
            if oymax >= maxy:
                maxy = oymax
    
            if ozmax >= maxz:
                maxz = ozmax
    
        c1+=1
        
    locx=(maxx+minx)/2
    locy=(maxy+miny)/2
    locz=(maxz+minz)/2    
    widhtx=(maxx-minx)   
    widhty=(maxy-miny)  
    widhtz=(maxz-minz)
    
    scd = [locx, locy, locz, widhtx ,widhty ,widhtz ,len(bpy.context.selected_objects)]    

    return scd
    
#scd = scenedim1()

#bpy.ops.mesh.primitive_uv_sphere_add(radius=1, enter_editmode=False, align='WORLD', location=((maxx-minx),(maxy-miny),(maxz-minz)), scale=(scd1[0], scd1[1], scd1[2]))
#bpy.ops.mesh.primitive_cube_add(size=2, enter_editmode=False, align='WORLD', location=(scd[0], scd[1], scd[2]), scale=(scd[3], scd[4], scd[5]))
#print(scd[:])

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
    bpy.context.object.modifiers["Shrinkwrap"].offset = size
    bpy.ops.object.modifier_apply(modifier="Subdivision")
    bpy.ops.object.modifier_apply(modifier="Shrinkwrap")
    # Calculate Object Volume by calculating mass with density of 1
    bpy.ops.rigidbody.objects_add(type='ACTIVE')
    bpy.ops.rigidbody.mass_calculate(material='Custom')
    vol = bpy.context.object.rigid_body.mass

    return vol

vol1 = CalcVolume('Source', 'Mesh', 0.1)
print(vol1)