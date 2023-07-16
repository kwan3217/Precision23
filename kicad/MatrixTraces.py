"""
To run:

import sys
sys.path.append('/home/jeppesen/workspace/Precision23/kicad')
import CharlieplexTraces


"""

import pcbnew
import math
import numpy as np

# most queries start with a board
board = pcbnew.GetBoard()

#Natural board unit is nanometer, but I want things to be placed to the nearest mil
mil=25400
inch=1000*mil

#These are all in mils
centerX=3500
centerY=3500
diodeRad=1460
outerRingRad=1400
outerViaRad=(outerRingRad+diodeRad)/2
# From OSHPark design rule 6mil trace width
ringWidth=6
# From OSHPark design rule 10mil drill size
viaDrillDia=10
# From OSHPark design rule 5mil annular ring
viaAnnular=5
viaDia=viaDrillDia+viaAnnular*2
viaRad=viaDia/2
# From OSHPark design rule 6mil trace clearance. Add one mil for tolerance.
minSpacing=7
ringSpacing=math.ceil(viaRad)+minSpacing+ringWidth/2
print("Ring Spacing: %f"%ringSpacing)


#Ugly hack from https://electronics.stackexchange.com/q/437065
layertable = {}

numlayers=pcbnew.PCB_LAYER_ID_COUNT
for i in range(numlayers):
    name = board.GetLayerName(i)
    layertable[name]=i
print(layertable)


def polar(r,theta):
    x=int(centerX+r*np.sin(np.radians(theta)))
    y=int(centerY-r*np.cos(np.radians(theta)))
    return pcbnew.VECTOR2I(int(x*mil),int(y*mil))


def polar_slot(slot:int,m:int,i_ring:int):
    return polar(r=outerRingRad-i_ring*ringSpacing,theta=1.5*(slot*4+m))


def trace(signame:str,xy0:pcbnew.VECTOR2I,xy1:pcbnew.VECTOR2I,layer:str="F.Cu",width:int=6):
    net=board.GetNetsByName()[signame]
    track=pcbnew.PCB_TRACK(board)
    track.SetStart(xy0)
    track.SetEnd  (xy1)          
    track.SetWidth(width*mil)
    track.SetNetCode(net.GetNetCode())
    track.SetLayer(layertable[layer])
    #track.SetLocked(True)
    board.Add(track)


def trace_polar(signame:str,r0:int,theta0:int,r1:int,theta1:int,*args,**kwargs):
    trace(signame=signame,
          xy0=polar(r0,theta0),
          xy1=polar(r1,theta1),
          *args,**kwargs)


def trace_polarslot(signame:str,
                    slot0:int,m0:int,i_ring0:int,
                    slot1:int,m1:int,i_ring1:int,*args,**kwargs):
    trace(signame=signame,
          xy0=polar_slot(slot=slot0,m=m0,i_ring=i_ring0),
          xy1=polar_slot(slot=slot1,m=m1,i_ring=i_ring1),
          *args,**kwargs)


def via(signame:str,xy:pcbnew.VECTOR2I,layer0:str="F.Cu",layer1:str="B.Cu",drill:int=viaDrillDia,dia:int=viaDia):
    pvia=pcbnew.PCB_VIA(board)
    pvia.SetLayerPair(layertable[layer0],layertable[layer1])
    pvia.SetPosition(xy)
    net=board.GetNetsByName()[signame]
    pvia.SetNet(net)
    pvia.SetDrill(drill*mil)
    pvia.SetWidth(dia*mil)
    #pvia.SetLocked(True)
    board.Add(pvia)


def via_polar(signame:str,r:int,theta:int,*args,**kwargs):
    via(signame=signame,
        xy=polar(r,theta),
        *args,**kwargs)


def via_polarslot(signame:str,
                  slot:int,m:int,i_ring:int,
                  *args,**kwargs):
    via(signame=signame,
        xy=polar_slot(slot=slot,m=m,i_ring=i_ring),
        *args,**kwargs)


def place_diodes():
    for i_hand in range(2):
        for i_diode in range(60):
            modref="D%01d%02d"%(i_hand,i_diode)
            print(modref)
            mod=board.FindFootprintByReference(modref)
            #for pad in mod.Pads():
            #     print("pad {}({}) on {}({}) at {},{} shape {} size {},{}".format(pad.GetPadName(),
            #        pad.GetNet().GetNetname(),
            #        mod.GetReference(),
            #        mod.GetValue(),
            #        pad.GetPosition().x, pad.GetPosition().y,
            #        padshapes[pad.GetShape()],
            #        pad.GetSize().x, pad.GetSize().y
            #     ))
            theta=i_diode*6
            mod.SetPosition(polar(diodeRad,theta))
            if(mod.IsFlipped()!=(i_hand==1)):
                mod.SetLayerAndFlip(layertable["B.Cu"])
            mod.SetOrientation(pcbnew.EDA_ANGLE(-theta+180*i_hand,pcbnew.DEGREES_T))
    pcbnew.Refresh()


#place_diodes()


def erase_rings():
    nets=board.GetNetsByName()
    rlimit=int(outerRingRad-21.5*ringSpacing)
    hands=[f"{x} hand" for x in ["Hour","Minute"]]
    for i_hand,hand in enumerate(hands):
        Ps=[f"/{hand}/Px{i}" for i in range(10)]
        Qs=[f"/{hand}/Q{i}x" for i in range( 6)]
        for i_ring,signame in enumerate(Ps+Qs):
            net=nets[signame]
            print(f"Erasing net {signame}:")
            for i_track,track in enumerate(board.TracksInNet(net.GetNetCode())):
                 x0=track.GetStart().x/mil
                 x1=track.GetEnd  ().x/mil
                 y0=track.GetStart().y/mil
                 y1=track.GetEnd  ().y/mil
                 r0=np.sqrt((x0-centerX)**2+(y0-centerY)**2)
                 r1=np.sqrt((x1-centerX)**2+(y1-centerY)**2)
                 print(f"Checking track {i_track}, {r0=},{r1=},{rlimit=}")
                 if r0>rlimit or r1>rlimit:
                     board.Remove(track)
    pcbnew.Refresh()


erase_rings()
#raise AssertionError("Stop!")


def draw_rings():
    hands=[f"{x} hand" for x in ["Hour","Minute"]]
    for i_hand,hand in enumerate(hands):
        Ps=[f"/{hand}/Px{i}" for i in range(10)]
        for i_ring,signame in enumerate(Ps):
            for m in range(240):
                trace_polarslot(signame=signame,
                     slot0=0,m0=m  ,i_ring0=i_hand*10+i_ring+2,
                     slot1=0,m1=m+1,i_ring1=i_hand*10+i_ring+2,
                     layer="F.Cu",width=6)
            pcbnew.Refresh()


draw_rings()


def draw_arcs():
    hands=[f"{x} hand" for x in ["Hour","Minute"]]
    for i_hand,hand in enumerate(hands):
        Qs=[f"/{hand}/Q{i}x" for i in range(6)]
        for i_arc,signame in enumerate(Qs):
            print(signame)
            for i_theta in range(36):
                dm=-1 if i_hand==0 else 2
                trace_polarslot(signame=signame,
                    slot0=i_arc*10,m0=i_theta+dm  ,i_ring0=i_hand,
                    slot1=i_arc*10,m1=i_theta+dm+1,i_ring1=i_hand,
                    layer="F.Cu",width=6)
            pcbnew.Refresh()


draw_arcs()


def draw_radials():
    def draw_radial(i_hand,i_ring,theta,rad_ofs,theta_ofs,signame):
        ringRad=outerRingRad-(i_ring)*ringSpacing
        if i_hand==0:
           outerRad=outerViaRad
        else:
           outerRad=diodeRad
        trace_polar(signame=signame,
           r0=ringRad,theta0=theta,
           r1=outerRad+rad_ofs,theta1=theta,layer="B.Cu")
        via_polar(signame=signame,
           r=ringRad,theta=theta)
        if i_hand==0:
            via_polar(signame=signame,
              r=outerRad+rad_ofs,theta=theta)
            trace_polar(signame=signame,
              r0=diodeRad        ,theta0=theta+theta_ofs,
              r1=outerRad+rad_ofs,theta1=theta          ,layer="F.Cu")
    for i_diode in range(60):
        theta0=i_diode*6
        theta1=theta0+1.5
        theta2=theta1+1.5
        thetam=theta0-1.5
        i_ring0=2+i_diode%10
        i_ring1=12+i_diode%10
        i_ring2=1
        i_ringm=0
        draw_radial(0,i_ring0,theta0,0,-1.2,f"/Hour hand/Px{i_diode%10}")
        draw_radial(1,i_ring1,theta1,0,0,f"/Minute hand/Px{i_diode%10}")
        draw_radial(0,i_ring2,theta2,diodeRad-outerViaRad,-1.5,f"/Hour hand/Q{i_diode//10}x")
        draw_radial(1,i_ringm,thetam,0,0,f"/Minute hand/Q{i_diode//10}x")
    pcbnew.Refresh()


draw_radials()


def draw_tap(sighand:int,sigx:int,slot:int,m:int,hasvia:bool=False):
    signame="/"+["Hour","Minute"][sighand]+f" hand/Px{sigx}"
    i_ring=2+10*sighand+sigx
    trace_polarslot(signame,
                    slot0=slot,m0=m,i_ring0=i_ring,
                    slot1=slot,m1=m,i_ring1=22    ,layer="B.Cu" if not(sighand==1 and sigx==9) else "F.Cu")
    if hasvia:
        via_polarslot(signame,slot=slot,m=m,i_ring=i_ring)


def draw_taps():
    draw_tap(0,0,slot= 1,m=-1,hasvia=True)
    draw_tap(0,1,slot= 0,m= 2,hasvia=True)
    draw_tap(0,2,slot= 0,m= 0,hasvia=True)
    draw_tap(0,3,slot= 0,m=-1,hasvia=True)
    draw_tap(0,4,slot=59,m= 2,hasvia=True)
    draw_tap(0,5,slot=59,m=-1,hasvia=True)
    draw_tap(0,6,slot=58,m= 2,hasvia=True)
    draw_tap(0,7,slot=58,m=-1,hasvia=True)
    draw_tap(0,8,slot=57,m= 2,hasvia=True)
    draw_tap(0,9,slot=57,m= 0,hasvia=True)
    draw_tap(1,0,slot=30,m= 1,hasvia=False)
    draw_tap(1,1,slot=30,m= 0,hasvia=True)
    draw_tap(1,2,slot=30,m=-1,hasvia=True)
    draw_tap(1,3,slot=29,m= 2,hasvia=True)
    draw_tap(1,4,slot=29,m= 0,hasvia=True)
    draw_tap(1,5,slot=29,m=-1,hasvia=True)
    draw_tap(1,6,slot=28,m= 2,hasvia=True)
    draw_tap(1,7,slot=28,m= 0,hasvia=True)
    draw_tap(1,8,slot=28,m=-1,hasvia=True)
    draw_tap(1,9,slot=27,m= 2,hasvia=False)
    pcbnew.Refresh()


draw_taps()
raise AssertionError("Stop!")
        

def redraw():
    erase_rings()
    draw_rings()
    draw_radials()


place_diodes()
