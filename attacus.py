# %%
from ocp_vscode import show, show_object, reset_show, set_port, set_defaults, get_defaults, Camera
set_port(3939)
set_defaults(
    reset_camera=Camera.KEEP
    ,measure_tools=True
    )

import build123d as bd
import pro_micro_c
import diode_1n4148
import copy, itertools, functools
from typing import TypeVar
T = TypeVar('T')
#%%
w = 19.05
l = 19.05
cut_size = 14.07
key_locs =  {
        3: [(0,0),(w,l/3), (w*2,l/1.4),(w*3,l/2),(w*4,l/3)],
        1: [((w*2.5, -w*1.7),0), ((w*3.7, -w*1.9),-20),((w*5, -w*2.2),-35)],
    }

cherry_switch = bd.import_step("cherry_mx.stp").rotate(bd.Axis.X, 90).move(bd.Location((0,-2,2.2)))
keycap = bd.import_step("DSA_1u.step").rotate(bd.Axis.X, 90).move(bd.Location((0,0,8.7)))
dil_socket = bd.import_step("DIL_socket_24pins.step")
promicro = pro_micro_c.pro_micro().rotate(bd.Axis.Z, 180).move(bd.Location((0,18,1)))
diode = diode_1n4148.diode_1n4148(leg_diameter=1).rotate(bd.Axis.X, 90)
#%%
def col(thing, rows:int=3):
    _locations = bd.GridLocations(w,l,1,rows)
    cluster = [copy.copy(thing).locate(loc) for loc in _locations]
    return cluster

def key_locations_half(thing:T)->T:
    col_three = col(thing, rows=3)
    col_one = col(thing, rows=1)
    three_col = None
    one_col = None
    t = None
    if isinstance(thing, bd.Sketch):
        three_col = bd.Sketch()+col_three
        one_col = bd.Sketch()+col_one
        t = bd.Sketch()
    elif isinstance(thing, bd.Part):
        three_col = bd.Part()+col_three
        one_col = bd.Part()+col_one
        t = bd.Part()
    elif isinstance(thing, bd.Compound):
        three_col = bd.Compound()+col_three
        one_col = bd.Compound()+col_one
        t = bd.Compound()
    threes = [copy.copy(three_col).locate(bd.Location(loc)) for loc in key_locs[3]]
    ones = [copy.copy(one_col).rotate(bd.Axis.Z,loc[1]).locate(bd.Location(loc[0])) for loc in key_locs[1]]

    return t+threes+ones

def key_locations(thing,space=220):
    kp = key_locations_half(thing).rotate(bd.Axis.Z, -20)
    kpbb = kp.bounding_box().size
    kpm = kp.mirror(mirror_plane=bd.Plane.YZ).translate((space,0,0))
    return kp+kpm

def outline():
    kl = key_locations(bd.Rectangle(w,l))
    with bd.BuildSketch() as skt:
        bd.add(kl)
        bd.offset(amount=7, kind=bd.Kind.INTERSECTION, mode=bd.Mode.ADD)

    vertecies = skt.vertices().sort_by(bd.Axis.Y)
    pts = [vertecies[i] for i in [0,1,2,3,22,23]]
    wires = [bd.Line(pair[0], pair[1]) for pair in itertools.combinations(pts,2)]
    skt=skt.sketch+bd.make_hull(wires)
    return skt

def plate(thickness=2):
    ol = outline()
    with bd.BuildSketch() as cross:
        bd.add(bd.Rectangle(cut_size+2,4))
        bd.add(bd.Rectangle(4, cut_size+2))
        bd.add(bd.Rectangle(cut_size, cut_size))

    with bd.BuildPart() as prt:
        with bd.BuildSketch():
            bd.add(ol)
            bd.add(key_locations(cross.sketch), mode=bd.Mode.SUBTRACT)
        bd.extrude(amount=thickness-1)
        with bd.BuildSketch(bd.Location((0,0,prt.part.bounding_box().size.Z))):
            bd.add(ol)
            bd.add(key_locations(bd.Rectangle(cut_size, cut_size)), mode=bd.Mode.SUBTRACT)
        bd.extrude(amount=1)
    return prt.part

def top_case(thickness:float=4.0, height:float=20.0, lip_height:float=4):
    ol = outline()
    _lip=6
    _chamfer_amount = 5
    _cable_space = 10
    with bd.BuildPart() as prt:
        with bd.BuildSketch() as skt:
            bd.add(ol)
            bd.offset(amount=thickness, kind=bd.Kind.INTERSECTION)
        bd.extrude(amount=height)

        top = prt.faces().sort_by(bd.Axis.Z)[-1]

        with bd.BuildSketch():
            bd.add(ol)
            bd.offset(amount=1, kind=bd.Kind.INTERSECTION)
        bd.extrude(amount=(height-thickness-lip_height),mode=bd.Mode.SUBTRACT)

        with bd.BuildSketch(bd.Plane(top.location)):
            bd.add(ol)
            bd.offset(amount=-_lip, kind=bd.Kind.INTERSECTION)
        bd.extrude(amount=-height,mode=bd.Mode.SUBTRACT)
        
        top_outer_edges = prt.faces().sort_by(bd.Axis.Z)[-1].outer_wire().edges()
        bd.chamfer(top_outer_edges, length=_chamfer_amount)
        
        top_outer_edges = prt.faces().sort_by(bd.Axis.Z)[-1].outer_wire().edges()
        bd.fillet(top_outer_edges, 2)

        with bd.BuildSketch(bd.Plane(top.location)):
            with bd.Locations(top.center()):
                bd.Rectangle(_cable_space,80)
        bd.extrude(amount=-(_chamfer_amount),mode=bd.Mode.SUBTRACT)


    return prt.part

def bottom_case(thickness:float=4.0, height:float=4.0):
    ol = outline()
    with bd.BuildPart() as prt:
        with bd.BuildSketch():
            bd.add(ol)
            bd.offset(amount=thickness, kind=bd.Kind.INTERSECTION)
        bd.extrude(amount=height/2)
        with bd.BuildSketch():
            bd.add(ol)
            # bd.offset(amount=-2, kind=bd.Kind.INTERSECTION)
            bd.offset(amount=-6, kind=bd.Kind.INTERSECTION, mode=bd.Mode.SUBTRACT)
        bd.extrude(amount=height)
    return prt.part

def diodes(alt=1,rows=3,groups=6):
    dbb = diode.bounding_box().size
    if alt==1:
        grid1 = bd.GridLocations(dbb.X+1, (dbb.Y)*1.5, 5,2)
        grid2 = bd.GridLocations(dbb.X+1, (dbb.Y)*2, 5,1)
        grid3 = bd.GridLocations(dbb.X+1, (dbb.Y)*2, 3,1)
        diode_group1 = bd.Part()+[copy.copy(diode).locate(loc) for loc in grid1]
        diode_group2 = bd.Part()+[copy.copy(diode).locate(loc) for loc in grid2]
        diode_group3 = bd.Part()+[copy.copy(diode).locate(loc) for loc in grid3]
        return (diode_group1
                +diode_group2.translate(((dbb.X+1)/2,0,0))
                +diode_group3.translate(((dbb.X+1)/2,-dbb.Y*1.5,0))
        )
    elif alt==2:
        grid = bd.GridLocations(dbb.X+1, dbb.Y+1, 5,4)
        return bd.Part()+[copy.copy(diode).locate(loc) for loc in grid]
    elif alt==3:
        grid = bd.GridLocations(dbb.X+1, dbb.Y+1, 1,3)
        group = bd.Part()+[copy.copy(diode).locate(loc) for loc in grid]
        dds = [copy.copy(group).locate(bd.Location(((dbb.X+1)*i, -1*i, 0))) for i in range(5)]
        return bd.Part()+dds
    elif alt==4:
        grid = bd.GridLocations(dbb.X+1, dbb.Y+1, 1,5)
        group = bd.Part()+[copy.copy(diode).locate(loc) for loc in grid]
        dds = [copy.copy(group).locate(bd.Location(((dbb.X+1)*i, -1*i, 0))) for i in range(3)]
        return bd.Part()+dds
    elif alt==5:
        polar = bd.PolarLocations(dbb.Y*0.55, 5, 0)
        group = bd.Part()+[copy.copy(diode.rotate(bd.Axis.Z, 90)).locate(loc) for loc in polar]
        return group
    elif alt==6:
        dide = diode.rotate(bd.Axis.Z, 90)
        dbb = dide.bounding_box().size
        grid = bd.GridLocations(dbb.X+1, (dbb.Y+1)*rows, 1,groups)
        group = bd.Part()+[copy.copy(dide).locate(loc) for loc in grid]
        dds = [copy.copy(group).locate(bd.Location((1*i, (dbb.Y+1)*i, 0))) for i in range(rows)]
        return bd.Part()+dds
#%%
with bd.BuildPart() as rods:
    with bd.BuildSketch():
        with bd.Locations((0,2.24)):
            with bd.GridLocations(16, 2.54, 2, 12):
                bd.Circle(radius=1/2)
    bd.extrude(amount=20)
        
rods = rods.part.locate(bd.Location(promicro.center())).move(bd.Location((0,-2.54*2,-10)))
# show(
#     promicro
#     #,dil_socket
#     ,rods
#     ,reset_camera=Camera.KEEP
# )
# %%
tc = top_case()
tcbb = tc.bounding_box().size
bc = bottom_case()
plt = plate().move(bd.Location((0,0,tcbb.Z-8-2)))
dids = diodes(6)
dids2 = dids.mirror(bd.Plane.YZ)
#%%
caps = key_locations(keycap)
switches = key_locations(cherry_switch)
#%%
pltbb = plt.bounding_box().size
cntr = bd.Location(plt.center())
pm = (promicro
        .locate(cntr)
        .move(bd.Location((0,-15,pltbb.Z/2)))
    )
pmbb = pm.bounding_box().size
#%%
diodes_left = dids.locate(cntr).move( bd.Location((-pmbb.X-1,-12,pltbb.Z)))
diodes_right =dids2.locate(cntr).move(bd.Location((pmbb.X+1,-12,pltbb.Z)))
pm_pins = rods.locate(bd.Location(pm.center())).move(bd.Location((0,-2.54*2,-10)))
#%%
plt_with_holes = plt-diodes_left-diodes_right-pm_pins
#%%
show(
    #bc.translate((0,0,-2))
    plt_with_holes#.split(bd.Plane(bd.Plane.X))
    #, tc
    #, switches.translate((0,-1,plt.location.position.Z+pltbb.Z))
    #, caps.translate((0,0,plt.location.position.Z+pltbb.Z+cherry_switch.bounding_box().size.Z/3+0.5))
    ,pm
    # ,dil_socket.locate(bd.Location(pm.center()))
    ,diodes_left
    ,diodes_right
    ,reset_camera=Camera.KEEP
)
#%%
plt_with_holes.export_stl(__file__.replace(".py","_plate.stl"))
#%%
tc.export_stl(__file__.replace(".py","_top_case.stl"))
bc.export_stl(__file__.replace(".py","_bottom_case.stl"))
#%%

plate_right = bd.split(plt_with_holes, bd.Plane.YZ.offset(plt_with_holes.center().X), keep=bd.Keep.TOP)
plate_left = bd.split(plt_with_holes, bd.Plane.YZ.offset(plt_with_holes.center().X), keep=bd.Keep.BOTTOM)
show(
    #bd.split(plt_with_holes, bd.Plane(plt_with_holes.faces().sort_by(bd.Axis.X)[-1]))#.offset(plt_with_holes.bounding_box().size.X/2))
    #plt_with_holes
    plate_right
    ,plate_left
    ,bone
    ,reset_camera=Camera.KEEP

)

#%%
with bd.BuildPart() as bone_part:
    with bd.BuildSketch() as bone:
        with bd.BuildLine() as ln:
            bd.Polyline(
                (0,0)
                ,(0,2)
                ,(-2,2)
                ,(-4,4)
                ,(-8,4)
                ,(-8,0)
                ,close=True
            )
            bd.mirror(ln.line, about=bd.Plane.YZ)
        bd.make_face()
        bd.mirror(bone.sketch, about=bd.Plane.XZ)
    bd.extrude(amount=2)
#%%
e = plate_left.edges().sort_by(bd.Axis.X)[-1]
print(plt_with_holes.center())
show(
    bone_part.part.translate(plt_with_holes.center()).translate((0,10,0))
    ,bone_part.part.translate(plt_with_holes.center()).translate((0,-50,0))
    ,plate_left
    ,reset_camera=Camera.KEEP

)
#%%
bx = bd.extrude(bd.Rectangle(15,20), amount=2).locate(bd.Location((-15/2,0,0)))-bd.offset(bone_part.part, amount=0.1)
show(
    #bone_part,
    bx#.translate((-15/2,0,0))
)
#%%
import os
print(os.getcwd())
bx.export_stl(os.getcwd()+"/joinery_plate.stl")
bone_part.part.export_stl(os.getcwd()+"/joinery_joint.stl")