from ocp_vscode import show, show_object, reset_show, set_port, set_defaults, get_defaults, Camera
set_port(3939)

import build123d as bd
import functools
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

def butterfly():
    # _outline = outline()
    with bd.BuildSketch() as skt:
        bd.add(outline())
        bd.add(shape(cut=True),mode=bd.Mode.SUBTRACT)
    skt = skt.sketch
    angle = 30
    with bd.BuildSketch() as ske:
        bd.add(skt.rotate(bd.Axis.Z, -angle/2))
        bd.add(skt
            .mirror(mirror_plane=bd.Plane.YZ)
            .rotate(bd.Axis.Z, angle/2)
            .move(bd.Location((skt.bounding_box().size.X*2,0,0)))
            )
    return ske.sketch

part = butterfly()
#left = shape().rotate(bd.Axis.Z, -15)
vs = part.vertices().sort_by(sort_by=bd.Axis.Y)

#part = shape()
# a = [bd.Text(idx).move(i.to_tuple()) for i in vs]
# for idx,i in enumerate(vs):
#     print(idx, i)
numbers = [bd.Text(str(idx), font_size=5).move(bd.Location(i.to_tuple())) for idx,i in enumerate(vs)]


show(
    part,
    numbers,
    # key_placements(),
    # _outline.rotate(bd.Axis.Z, -15),
    reset_camera=Camera.KEEP
)