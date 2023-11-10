# %%
from ocp_vscode import show, show_object, reset_show, set_port, set_defaults, get_defaults, Camera
set_port(3939)

import build123d as bd
import pro_micro_c
import diode_1n4148
import copy
w = 19.05
l = 19.05
cut_size = 14.07

def col(rows=3, cut=True):
    with bd.BuildSketch() as skt:
        with bd.GridLocations(w,l,1,rows):
            if cut:
                bd.Rectangle(cut_size,cut_size)
            else:
                bd.Rectangle(w,l)
    return skt.sketch

key_locs =  {
        3: [(0,0),(w,l/3), (w*2,l/1.4),(w*3,l/2),(w*4,l/3)],
        1: [((w*2.5, -w*1.7),0), ((w*3.7, -w*1.9),-20),((w*5, -w*2.2),-35)],
    }

def key_placement(cut=True):
    with bd.BuildSketch() as skt:
        with bd.Locations(*key_locs[3]):
            bd.add(col(rows=3,cut=cut))
        
        for i in key_locs[1]:
            bd.add(col(rows=1, cut=cut)
                .rotate(bd.Axis.Z, i[1])
                .move(bd.Location(i[0]))
            )
    print(skt.sketch.bounding_box().center())
    sbb = skt.sketch.bounding_box()
    centered = skt.sketch.translate((-(sbb.center().X),-(sbb.center().Y),0))
    print(skt.sketch.bounding_box().center())

    return skt
        
def outline():
    with bd.BuildSketch() as skt:
        bd.add(key_placement(cut=False))
        bd.offset(amount=7, kind=bd.Kind.INTERSECTION)
        bd.Rectangle(1,1) # Remove internal jibber-jabber
        vs = skt.vertices().sort_by(sort_by=bd.Axis.Y)
        with bd.BuildLine():
            bd.Polyline(
                vs[0].to_tuple(),
                vs[1].to_tuple(),
                vs[2].to_tuple(),
                close=True
            )
        bd.make_face()
        with bd.BuildLine():
            bd.Polyline(
                vs[5].to_tuple(),
                vs[10].to_tuple(),
                vs[16].to_tuple(),
                close=True
            )
        bd.make_face()
    return skt.sketch

def shape(angle: float = 40, space:float = 215):
    _outline = outline()
    with bd.BuildSketch() as ske:
        bd.add(_outline.rotate(bd.Axis.Z, -angle/2))
        bd.add(_outline
            .mirror(mirror_plane=bd.Plane.YZ)
            .rotate(bd.Axis.Z, angle/2)
            .move(bd.Location((space,0,0)))
            )
        vs = ske.vertices().sort_by(sort_by=bd.Axis.X)
        pts = []
        for idx,i in enumerate(vs):
            if idx in [14,23,18,19]:
                pts.append(i.to_tuple())
        with bd.BuildLine():
            bd.Polyline(*pts, close=True)
        #bd.make_face()
    sbb = ske.sketch.bounding_box()
    centered = ske.sketch.translate((-(sbb.center().X),-(sbb.center().Y),0))

    return centered


def attacus():
    angle = 40
    space = 215
    with bd.BuildSketch() as ske:
        bd.add(shape(angle, space))
        # Cuts the keys
        bd.add(key_placement(cut=True).sketch.rotate(bd.Axis.Z, -angle/2),mode=bd.Mode.SUBTRACT)
        bd.add(key_placement(cut=True).sketch.mirror(mirror_plane=bd.Plane.YZ)
            .rotate(bd.Axis.Z, angle/2)
            .move(bd.Location((space,0,0))),
            mode=bd.Mode.SUBTRACT
            )
    
    with bd.BuildPart() as prt:
        bd.add(ske)
        bd.extrude(amount=2)
    return prt.part



part = attacus()
# numbers = [bd.Text(str(idx), font_size=5).move(bd.Location(i.to_tuple())) for idx,i in enumerate(vs)]
# %%
# numbers = [bd.Text(str(idx), font_size=5).move(bd.Location(i.to_tuple())) for idx,i in enumerate(vs)]
pm = pro_micro_c.pro_micro().rotate(bd.Axis.Z, 180).move(bd.Location(part.bounding_box().center().to_tuple())*bd.Location((0,18,1)))
diode = diode_1n4148.diode_1n4148().rotate(bd.Axis.X, 90).rotate(bd.Axis.Z, 90)
# %%
doidr = diode.rotate(bd.Axis.Z, 90)
dbb = doidr.bounding_box().size
locs = bd.GridLocations(
    dbb.X*2,
    dbb.Y*1.5,
    5,
    2
    )
locs2 = bd.GridLocations(
    dbb.X*2,
    dbb.Y*1.1,
    5,
    1
    )
locs3 = bd.GridLocations(
    dbb.X*2,
    dbb.Y*1.1,
    3,
    1
    )
pmbb = pm.bounding_box().size
diode_group1 = bd.Part()+[copy.copy(doidr).locate(loc) for loc in locs]
diode_group2 = bd.Part()+[copy.copy(doidr).locate(loc) for loc in locs2]
diode_group3 = bd.Part()+[copy.copy(doidr).locate(loc) for loc in locs3]

diodes = (diode_group1 
    + diode_group2.locate(bd.Location((dbb.X,0,0))) 
    + diode_group3.locate(bd.Location((-dbb.X,-dbb.Y*1.5,0))) 
)
diodes_left = (diodes
    .rotate(bd.Axis.Z, -20)
    .locate(pm.location*bd.Location((-pmbb.X-2,-pmbb.Y+6,1)))
)
diodes_right = (bd.mirror(diodes, bd.Plane.XZ)
    .rotate(bd.Axis.Z, 180+20)
    .locate(pm.location*bd.Location((pmbb.X+2,-pmbb.Y+6,1)))
)

show(
    part,
    # numbers,
    pm,
    diodes_left,
    diodes_right,
    reset_camera=Camera.KEEP
)
# %%
with bd.BuildPart() as top_case:
    with bd.BuildSketch() as sk:
        bd.add(shape(40,215))
        bd.offset(amount=4, kind=bd.Kind.INTERSECTION)
    bd.extrude(amount=15)

    tcbb = top_case.part.bounding_box()
    z_offset = tcbb.size.Z

    with bd.BuildSketch() as sk:
        bd.add(shape(40,215))
        bd.offset(amount=1, kind=bd.Kind.INTERSECTION)
    bd.extrude(amount=(z_offset-3), mode=bd.Mode.SUBTRACT)

    with bd.BuildSketch() as sk:
        bd.add(shape(40,215))
        bd.offset(amount=-4, kind=bd.Kind.INTERSECTION)
    bd.extrude(amount=(z_offset), mode=bd.Mode.SUBTRACT)

    y2 = tcbb.size.Y/4
    tcc = bd.Location(tcbb.center())*bd.Location((0,y2,z_offset/2))
    with bd.Locations(tcc):
        bd.Box(20,20,10,mode=bd.Mode.SUBTRACT)

with bd.BuildPart() as bottom_case:
    with bd.BuildSketch() as sk:
        bd.add(shape(40,215))
        bd.offset(amount=4, kind=bd.Kind.INTERSECTION)
    bd.extrude(amount=2)
    with bd.BuildSketch() as sk:
        bd.add(shape(40,215))
        bd.offset(amount=0, kind=bd.Kind.INTERSECTION)
    bd.extrude(amount=4)

htc = bd.split(top_case.part, bd.Plane.YZ)

show(
    part.translate((0,0,9)),
    top_case,
    # htc,
    pm.translate((0,0,9)),
    bottom_case.part.translate((0,0,-4)),
    #prt2,
    #sk,
    # bd.Rectangle(140,140).translate((35,-25,0)),
    reset_camera=Camera.KEEP
)
# pm.export_step(__file__.replace(".py","_promicro.step"))
# part.export_stl(__file__.replace(".py",".stl"))


