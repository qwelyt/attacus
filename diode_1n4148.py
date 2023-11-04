import build123d as bd

def diode_1n4148(bent=True) -> bd.Part:
    if bent:
        with bd.BuildPart() as prt:
            bd.Cylinder(radius=1.6/2, height=3.9)
            bd.fillet(prt.edges(), radius=0.2)
            l = bd.Cylinder(radius=0.55/2, height=3.9+2*2)
            ends = l.faces().sort_by(bd.Axis.Z)
            with bd.Locations(
                ends[0].center().to_tuple(),
                ends[-1].center().to_tuple()
                ):
                bd.Sphere(radius=0.55/2)
            with bd.BuildSketch(bd.Plane.XZ):
                with bd.GridLocations(0, l.bounding_box().size.Z, 1, 2):
                    bd.Circle(radius=0.55/2)
            bd.extrude(amount=5)
        
        return prt.part
    else:
        with bd.BuildPart() as prt:
            bd.Cylinder(radius=1.6/2, height=3.9)
            bd.fillet(prt.edges(), radius=0.2)
            bd.Cylinder(radius=0.55/2, height=26*2+3.9)
        
        return prt.part