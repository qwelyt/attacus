import build123d as bd

def pro_micro() -> bd.Part:
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