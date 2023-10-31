# %%
from ocp_vscode import show, show_object, reset_show, set_port, set_defaults, get_defaults, Camera
set_port(3939)

import build123d as bd
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

def shape(cut=True):
    with bd.BuildSketch() as skt:
        with bd.Locations(*key_locs[3]):
            bd.add(col(rows=3,cut=cut))
        
        for i in key_locs[1]:
            bd.add(col(rows=1, cut=cut)
                .rotate(bd.Axis.Z, i[1])
                .move(bd.Location(i[0]))
            )

    return skt
        


def key_placements():
    with bd.BuildSketch() as skt:
        bd.add(shape(cut=True))
        # bd.make_hull(skt.edges())
        # bd.fillet(skt.vertices(), radius=1.5)
    return skt.sketch

def outline():
    with bd.BuildSketch() as skt:
        bd.add(shape(cut=False))
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

def bf():
    skt = outline()
    angle = 40
    space = skt.bounding_box().size.X*1.6
    with bd.BuildSketch() as ske:
        bd.add(skt.rotate(bd.Axis.Z, -angle/2))
        bd.add(skt
            .mirror(mirror_plane=bd.Plane.YZ)
            .rotate(bd.Axis.Z, angle/2)
            .move(bd.Location((space,0,0)))
            )

    return ske.sketch

def butterfly():
    # _outline = outline()
    skt = outline()
    angle = 40
    space = skt.bounding_box().size.X*1.6
    with bd.BuildSketch() as ske:
        bd.add(skt.rotate(bd.Axis.Z, -angle/2))
        bd.add(skt
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
        bd.make_face()
        bd.add(shape(cut=True).sketch.rotate(bd.Axis.Z, -angle/2),mode=bd.Mode.SUBTRACT)
        bd.add(shape(cut=True).sketch
            .mirror(mirror_plane=bd.Plane.YZ)
            .rotate(bd.Axis.Z, angle/2)
            .move(bd.Location((space,0,0))),
            mode=bd.Mode.SUBTRACT
            )
    
    with bd.BuildPart() as prt:
        bd.add(ske)
        bd.extrude(amount=2)
    return prt.part

def pro_micro():
    pcb_l = 34.9
    pcb_w = 18
    def port():
        with bd.BuildPart() as _port:
            with bd.BuildSketch():
                bd.Rectangle(9,7.35)
            bd.extrude(amount=3.25)
            bd.fillet(_port.edges().filter_by(bd.Axis.Y), 1)
            front = _port.faces().sort_by(bd.Axis.Y)[0]
            bd.offset(amount=-0.2, openings=front)
            
            with bd.BuildSketch(front):
                bd.Rectangle(7,0.5)
            bd.extrude(until=bd.Until.FIRST)
        return _port.part
    
    def components():
        with bd.BuildPart() as _componenets:
            with bd.BuildSketch() as chip:
                with bd.Locations((0,4.36)):
                    bd.Rectangle(7.5,7.5)
            bd.extrude(amount=1)

            with bd.BuildSketch() as diods_beside_port:
                with bd.Locations((0,-pcb_l/2+2)):
                    with bd.GridLocations(12,1,2,1):
                        bd.Rectangle(1,1.8)
            bd.extrude(amount=0.5)

            with bd.BuildSketch() as first_block_behind_port:
                with bd.Locations((0,-pcb_l/2+7.5+1.5)):
                    bd.Rectangle(9.25, 3.4)
            bd.extrude(amount=1.25)

            with bd.BuildSketch() as second_block_behind_port:
                with bd.Locations((0,-pcb_l/2+7.5+1.5+3.4+0.5)):
                    bd.Rectangle(11.45, 3.3)
            bd.extrude(amount=2)

            with bd.BuildSketch() as block_in_the_back:
                with bd.Locations((0,pcb_l/2.5)):
                    bd.Rectangle(11.45, 4)
            bd.extrude(amount=1)
        return _componenets.part

    with bd.BuildPart() as prt:
        with bd.BuildSketch():
            bd.Rectangle(pcb_w, pcb_l)
            with bd.Locations((0,2.24)):
                with bd.GridLocations(pcb_w-2, 2.54, 2, 12):
                    bd.Circle(radius=0.5, mode=bd.Mode.SUBTRACT)
        pcb = bd.extrude(amount=1.5)
        bd.add(port().move(bd.Location((0,-pcb_l/2+3,1.5))))
        bd.add(components().move(bd.Location((0,0,1.5))))

    return prt.part

def diode_1n4148(bent=True):
    if bent:
        with bd.BuildPart() as prt:
            bd.Cylinder(radius=1.6/2, height=3.9)
            bd.fillet(prt.edges(), radius=0.2)
            l = bd.Cylinder(radius=0.55/2, height=3.9+3*2)
            ends = l.faces().sort_by(bd.Axis.Z)
            with bd.Locations(
                ends[0].center().to_tuple(),
                ends[-1].center().to_tuple()
                ):
                bd.Sphere(radius=0.55/2)
            with bd.BuildSketch(bd.Plane.XZ):
                with bd.GridLocations(0, 3.9+3*2, 1, 2):
                    bd.Circle(radius=0.55/2)
            bd.extrude(amount=3)
        
        return prt.part
    else:
        with bd.BuildPart() as prt:
            bd.Cylinder(radius=1.6/2, height=3.9)
            bd.fillet(prt.edges(), radius=0.2)
            bd.Cylinder(radius=0.55/2, height=26*2+3.9)
        
        return prt.part

part = butterfly()
# part = bf()
# vs = part.vertices().sort_by(sort_by=bd.Axis.X)

#part = shape()
# a = [bd.Text(idx).move(i.to_tuple()) for i in vs]
# for idx,i in enumerate(vs):
    # print(idx, i)
# numbers = [bd.Text(str(idx), font_size=5).move(bd.Location(i.to_tuple())) for idx,i in enumerate(vs)]
pm = pro_micro().rotate(bd.Axis.Z, 180).move(bd.Location(part.bounding_box().center().to_tuple())*bd.Location((0,18,1)))
diode = diode_1n4148().rotate(bd.Axis.X, 90).rotate(bd.Axis.Z, 90)

# locs = bd.GridLocations(
#     diode.bounding_box().size.X+1,
#     diode.bounding_box().size.Y+2,
#     12,
#     3
#     )
# diodes = [copy.copy(diode).locate(loc) for loc in locs]
locs = bd.GridLocations(2,diode.bounding_box().size.Y+1,1,5)
locs_groups = bd.GridLocations(0, (diode.bounding_box().size.Y+1)*5, 1, 3)
diodes = []
diodes2 = []
diodes_long = []
for gidx,gloc in enumerate(locs_groups):
    for idx,loc in enumerate(locs):
        diodes.append(copy.copy(diode).locate(loc*bd.Location((idx,0,0))*gloc))
        diodes2.append(copy.copy(diode).locate(loc*bd.Location((-idx,0,0))*gloc))
        if gidx < 1 and idx < 3:
            diodes_long.append(copy.copy(diode).rotate(bd.Axis.Z, 90).locate(loc*bd.Location((idx*3,0,0))*gloc))

ds = bd.Part(children=diodes)
dsm = bd.Part(children=diodes2)
dsl = (bd.Part(children=diodes_long)).rotate(bd.Axis.Z, 90)
# ds = bd.Part(children=diodes
# %%

ddr = diode.rotate(bd.Axis.Z, 75)
locs = bd.GridLocations(
    ddr.bounding_box().size.X+1,
    ddr.bounding_box().size.Y-3,
    5,
    3
)
dd = [copy.copy(ddr).locate(loc) for loc in locs]
ddp = bd.Part(children=dd).rotate(bd.Axis.Z, 20)


show(
    part,
    # numbers,
    pm,
    ddp.locate(pm.location*bd.Location((0,-40,1))),
    # ds.locate(pm.location*bd.Location((0,-38,1))),
    # ds.locate(pm.location*bd.Location((-20,-30,1))),
    # dsm.locate(pm.location*bd.Location((20,-30,1))),
    # dsl.locate(pm.location*bd.Location((0,-15,1))),
    # copy.copy(dsl).locate(pm.location*bd.Location((0,-30,1))),
    # ds.locate(pm.location*bd.Location((13,-30,1))),
    # dsm.locate(pm.location*bd.Location((-13,-30,1))),
    # diodes2,
    # numbers,
    reset_camera=Camera.KEEP
)
# pm.export_step(__file__.replace(".py","_promicro.step"))
# part.export_stl(__file__.replace(".py",".stl"))
# %%
