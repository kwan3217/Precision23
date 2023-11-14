"""
To run:

import sys
sys.path.append('/home/jeppesen/workspace/Precision23/kicad')
import MatrixTraces

Script will always throw an exception before reaching the end,
either due to a bug or an intentional AssertionError. This keeps
the module from being properly imported, so it can be rerun
just by re-doing the import MatrixTraces.



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
centerXf=3500
centerXb=centerXf+4000
centerX=(centerXf,centerXb)
centerY=3500
flatDiodeRad=1460
domeDiodeRad=flatDiodeRad-10
outerRingRad=1400
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
outerViaRad=outerRingRad+ringSpacing
print("Ring Spacing: %f"%ringSpacing)

handnames=["Hour","Minute","Second","Third"]


#Ugly hack from https://electronics.stackexchange.com/q/437065
layertable = {}

numlayers=pcbnew.PCB_LAYER_ID_COUNT
for i in range(numlayers):
    name = board.GetLayerName(i)
    layertable[name]=i
print(layertable)


def polar(*,i_board:int,r:int,theta:float):
    """
    Calculate position from polar coordinates

    :param i_board: Front (0) or back (1) board. The front board has the hour
                    and minute hand, the back board has the second and third hand
    :param r: distance from center of board in mil. Strongly recommended to only use integral mils.
    :param theta: Azimuth, measured clockwise from straight up (12:00), in degrees. Fractional degrees allowed.
    :return: A VECTOR2I with x and y global coordinates (nanometers right of and below top-left corner of page)

    Note: All coordinates are converted to integer mils before being converted to kicad global coordinates
    """
    x=int(centerX[i_board]+r*np.sin(np.radians(theta)))
    y=int(centerY         -r*np.cos(np.radians(theta)))
    return pcbnew.VECTOR2I(int(x*mil),int(y*mil))


def polar_slot(*,i_board:int,slot:int,m:int,i_ring:int):
    """
    Calculate position from polar slot coordinates

    :param i_board: Front (0) or back (1) board. The front board has the hour
                    and minute hand, the back board has the second and third hand
    :param slot: Azimuth slot number, from 0 to 59. Each LED in each hand is one slot. Must be an integer
    :param m: Azimuth subslot number, with 4 subslots in each slot, IE a subslot is 1.5deg. Subslot 0 is 
              the center of the LED, +1 and +2 are clockwise, -1 is counterclockwise. Can use any
              float number, but [-1,0,1,2] are the most common.
    :param i_ring: Ring slot number. Outer complete ring is ring 0.
    :param theta: Azimuth, measured clockwise from straight up (12:00), in degrees. Fractional degrees allowed.
    :return: A VECTOR2I with x and y global coordinates (nanometers right of and below top-left corner of page)

    Note: All coordinates are converted to integer mils before being converted to kicad global coordinates
    """
    return polar(i_board=i_board,r=outerRingRad-i_ring*ringSpacing,theta=1.5*(slot*4+m))


def trace(*,signame:str,xy0:pcbnew.VECTOR2I,xy1:pcbnew.VECTOR2I,layer:str="F.Cu",width:int=6):
    """
    Create a trace

    :param signame: Signal name, must exactly match one of the signal names on the board
    :param xy0: end 0 of trace in kicad global coordinate vector
    :param xy1: end 1 of trace in kicad global coordinate vector
    :param layer: Layer to draw trace on, must match one of the copper layers
    :param width: Width of trace in mils
    """
    net=board.GetNetsByName()[signame]
    track=pcbnew.PCB_TRACK(board)
    track.SetStart(xy0)
    track.SetEnd  (xy1)          
    track.SetWidth(width*mil)
    track.SetNetCode(net.GetNetCode())
    track.SetLayer(layertable[layer])
    #track.SetLocked(True)
    board.Add(track)


def signame(*,i_board:int=None,i_hand:int=None,i_boardhand:int=None,tens:int='x',ones:int='x'):
    """
    Calculate a signal name from hand indexes

    :param i_board: Front (0) or back (1) board. Hour and minute are on front board, second and third on back.
    :param i_hand:  Front (0) or back (1) of board. Hour and second are front hands, minute and third are back.
    :param i_boardhand: 
    :param tens: Tens digit of signal slot. Either tens or ones must be passed, but not both.
    :param ones: Ones digit of signal slot
    """
    if i_boardhand is None:
        i_boardhand=i_board*2+i_hand
    return f"/{handnames[i_boardhand]} hand/{handnames[i_boardhand][0]}{tens}{ones}"


def trace_polar(*,i_hand:int,tens:int='x',ones:int='x',
                  r0:int,theta0:float,r1:int,theta1:float,**kwargs):
    """
    Create matching traces on both boards
    
    :param i_hand: Front (0) or back (1) hands. Hour and Second are front hands, Minute and Third are back.
    :param tens:   Tens digit of slot
    :param ones:   Ones digit of slot
    :param r0:     radius of end 0 in mils
    :param theta0: azimuth of end 0 in degrees, clockwise from 12:00
    :param r1:     radius of end 1 in mils
    :param theta1: azimuth of end 1
    :param kwargs: Other arguments passed through to trace()
    """
    for i_board in range(2):
        trace(signame=signame(i_board=i_board,i_hand=i_hand,tens=tens,ones=ones),
            xy0=polar(i_board=i_board,r=r0,theta=theta0),
            xy1=polar(i_board=i_board,r=r1,theta=theta1),
            **kwargs)


def trace_polarslot(*,i_hand:int,tens:int='x',ones:int='x',
                    slot0:int,m0:int,i_ring0:int,
                    slot1:int,m1:int,i_ring1:int,**kwargs):
    """
    Create matching traces on both boards using slot coordinates

    :param i_hand: Front (0) or back (1) hands
    :param tens:   Tens digit
    :param ones:   Ones digit
    :param slot0: Azimuth slot of end 0
    :param m0: Azimuth subslot of end 0
    :param i_ring0: Ring of end 0
    :param slot1: Azimuth slot of end 1
    :param m1: Azimuth subslot of end 1
    :param i_ring1: Ring slot of end 1
    :param kwargs: Other arguments passed through to trace()
    """
    for i_board in range(2):
        trace(signame=signame(i_board=i_board,i_hand=i_hand,tens=tens,ones=ones),
              xy0=polar_slot(i_board=i_board,slot=slot0,m=m0,i_ring=i_ring0),
              xy1=polar_slot(i_board=i_board,slot=slot1,m=m1,i_ring=i_ring1),
              **kwargs)


def via(*,signame:str,xy:pcbnew.VECTOR2I,layer0:str="F.Cu",layer1:str="B.Cu",drill:int=viaDrillDia,dia:int=viaDia):
    """
    Create a via

    :param signame: Signal name, must exactly match one of the signal names on the board
    :param xy: Location kicad global coordinate vector
    :param layer0: Layer to start on, must match one of the copper layers
    :param layer1: Layer to end on
    :param drill: Drill diameter in mils
    :param dia: Via diameter in mils
    """
    pvia=pcbnew.PCB_VIA(board)
    pvia.SetLayerPair(layertable[layer0],layertable[layer1])
    pvia.SetPosition(xy)
    net=board.GetNetsByName()[signame]
    pvia.SetNet(net)
    pvia.SetDrill(drill*mil)
    pvia.SetWidth(dia*mil)
    #pvia.SetLocked(True)
    board.Add(pvia)


def via_polar(*,i_hand:int,tens:int='x',ones:int='x',
              r:int,theta:int,**kwargs):
    """
    Create matching vias on both boards
    
    :param i_hand: Front (0) or back (1) hands. Hour and Second are front hands, Minute and Third are back.
    :param tens:   Tens digit of slot
    :param ones:   Ones digit of slot
    :param r:      Distance from center in mils
    :param theta:  azimuth in degrees, clockwise from 12:00
    :param kwargs: Other arguments passed through to via()
    """
    for i_board in range(2):
        via(signame=signame(i_board=i_board,i_hand=i_hand,tens=tens,ones=ones),
            xy=polar(i_board=i_board,r=r,theta=theta),
            **kwargs)


def via_polarslot(*,i_hand:int,tens:int='x',ones:int='x',
                  slot:int,m:int,i_ring:int,
                  **kwargs):
    """
    Create matching traces on both boards using slot coordinates

    :param i_hand: Front (0) or back (1) hands
    :param tens:   Tens digit
    :param ones:   Ones digit
    :param slot: Azimuth slot
    :param m: Azimuth subslot
    :param i_ring: Ring index
    :param kwargs: Other arguments passed through to via()
    """
    for i_board in range(2):
        via(signame=signame(i_board=i_board,i_hand=i_hand,tens=tens,ones=ones),
            xy=polar_slot(i_board=i_board,slot=slot,m=m,i_ring=i_ring),
            **kwargs)


def place_diodes():
    for i_hand,i_board,rad in zip(range(4),(0,0,1,1),(flatDiodeRad,domeDiodeRad,domeDiodeRad,domeDiodeRad)):
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
            mod.SetPosition(polar(i_board,rad,theta))
            if(mod.IsFlipped()!=(i_hand==1)):
                mod.SetLayerAndFlip(layertable["B.Cu"])
            mod.SetOrientation(pcbnew.EDA_ANGLE(-theta+180*i_hand,pcbnew.DEGREES_T))
    pcbnew.Refresh()


#place_diodes()
#raise AssertionError("Stop!")


def erase_rings():
    nets=board.GetNetsByName()
    rlimit=int(outerRingRad-23.1*ringSpacing)
    for i_boardhand in range(4):
        i_board=i_boardhand//2
        i_hand=i_boardhand%2
        Ps=[signame(i_boardhand=i_boardhand,ones=i) for i in range(10)]
        Qs=[signame(i_boardhand=i_boardhand,tens=i) for i in range( 6)]
        for this_signame in Ps+Qs:
            print(f"Erasing net {this_signame}:")
            net=nets[this_signame]
            for i_track,track in enumerate(board.TracksInNet(net.GetNetCode())):
                 x0=track.GetStart().x/mil
                 x1=track.GetEnd  ().x/mil
                 y0=track.GetStart().y/mil
                 y1=track.GetEnd  ().y/mil
                 r0=np.sqrt((x0-centerX[i_board])**2+(y0-centerY)**2)
                 r1=np.sqrt((x1-centerX[i_board])**2+(y1-centerY)**2)
                 print(f"Checking track {i_track}, {r0=},{r1=},{rlimit=}")
                 if r0>rlimit and r1>rlimit:
                     board.Remove(track)
    pcbnew.Refresh()


erase_rings()
#raise AssertionError("Stop!")

def arc(*,i_hand:int,tens:int='x',ones:int='x',
               i_ring:int,
               slot0:int=0,m0:int=0,
               slot1:int=0,m1:int=0,
               **kwargs):
    """
    Create matching arcs on both boards using slot coordinates

    :param i_hand: Front (0) or back (1) hands
    :param tens:   Tens digit
    :param ones:   Ones digit
    :param i_ring: Ring index
    :param slot0: Azimuth slot 0
    :param m0: Azimuth subslot 0
    :param slot1: Azimuth slot 1
    :param m1: Azimuth subslot 1
    :param kwargs: Other arguments passed through to trace()
    """
    # Do everything internally in subslots, since it's easier to iterate.
    # Even though subslots are conventionally [-1..2], they are unbounded.
    for m in range(slot0*4+m0,slot1*4+m1):
        trace_polarslot(i_hand=i_hand,tens=tens,ones=ones,
             slot0=0,m0=m  ,i_ring0=i_ring,
             slot1=0,m1=m+1,i_ring1=i_ring,
             **kwargs)


def rings():
    """
    Draw complete rings for each ones position on each hand (total of 20 rings)
    """
    for i_hand in range(2):
        for ones in range(10):
            arc(i_hand=i_hand,ones=ones,i_ring=i_hand*10+ones+2,m0=0,m1=240)
            pcbnew.Refresh()


rings()
#raise AssertionError("Stop!")


def arcs():
    """
    Draw partial rings for each tens position on each hand. Total of 12 arcs, but
    all 6 of each hand can go in the same ring, so only 2 rings total.
    """
    for i_hand in range(2):
        for tens in range(6):
            print(f"Laying arc {signame(i_hand=i_hand,i_board=0,tens=tens)} and {signame(i_hand=i_hand,i_board=1,tens=tens)}")
            dm=-1 if i_hand==1 else 2
            arc(i_hand=i_hand,tens=tens,
                slot0=tens*10,m0=dm,
                slot1=tens*10,m1=35+dm+1,i_ring=1-i_hand)
            pcbnew.Refresh()


arcs()
#raise AssertionError("Stop!")


def radial(*,i_hand:int,tens:int='x',ones:int='x',
             i_ring:int,theta:float,rad_ofs:int,theta_ofs:float):
    """
    Create matching radial traces on both boards. Each radial runs from 
    the appropriate ring to the diode pad. Front side LEDs 


    :param i_hand: Front (0) or back (1) hands
    :param tens:   Tens digit
    :param ones:   Ones digit
    :param i_ring: Ring index of inner end. All traces end near the diodes.
    :param kwargs: Other arguments passed through to trace()
    """
    ringRad=outerRingRad-(i_ring)*ringSpacing
    diodeRad=domeDiodeRad
    if i_hand==0:
       outerRad=outerViaRad
    else:
       outerRad=diodeRad
    # X0x from ring to inward of center of diode
    trace_polar(i_hand=i_hand,tens=tens,ones=ones,
       r0=ringRad,theta0=theta,
       r1=outerRad+rad_ofs,theta1=theta,layer="B.Cu")
    # Via at ring
    via_polar(i_hand=i_hand,tens=tens,ones=ones,
       r=ringRad,theta=theta)
    if i_hand==0:
        # Via at outer end of radial to front side
        via_polar(i_hand=i_hand,tens=tens,ones=ones,
          r=outerRad+rad_ofs,theta=theta)
        # Front-side trace from via to left pad
        trace_polar(i_hand=i_hand,tens=tens,ones=ones,
          r0=diodeRad        ,theta0=theta+theta_ofs,
          r1=outerRad+rad_ofs,theta1=theta          ,layer="F.Cu")


def radials():
    for i_slot in range(60):
        ones=i_slot%10
        tens=i_slot//10
        theta0=i_slot*6
        theta1=theta0+1.5
        theta2=theta1+1.5
        thetam=theta0-1.5
        i_ring0=2+ones
        i_ring1=12+ones
        i_ring2=1
        i_ringm=0
        radial(i_hand=0,tens=tens,i_ring=i_ring0,theta=theta0,rad_ofs=0                       ,theta_ofs=-1.2)
        radial(i_hand=1,tens=tens,i_ring=i_ring1,theta=theta1,rad_ofs=0                       ,theta_ofs= 0  )
        radial(i_hand=0,ones=ones,i_ring=i_ring2,theta=theta2,rad_ofs=flatDiodeRad-outerViaRad,theta_ofs=-1.5)
        radial(i_hand=1,ones=ones,i_ring=i_ringm,theta=thetam,rad_ofs=0                       ,theta_ofs= 0  )
        pcbnew.Refresh()


radials()
#raise AssertionError("Stop!")


def tap(*,i_hand:int,tens:int='x',ones:int='x',slot:int,m:int,hasvia:bool=False,layer:str="B.Cu"):
    """
    Create a pair of traces inward from rings so that they can join the internal circuitry.
    Tap positions must be chosen manually (in taps() below) but are then drawn automatically.
    
    :param i_hand:
    :param tens:
    :param ones:
    :param slot:
    :param m:
    :param hasvia: If True, draw a new via on the ring connecting the ring to the tap. If false, don't
                   draw one (because it's there already)
    """
    if tens=='x':
        i_ring=2+10*i_hand+ones
    else:
        i_ring=1-i_hand
    trace_polarslot(i_hand=i_hand,tens=tens,ones=ones,
                    slot0=slot,m0=m,i_ring0=i_ring,
                    slot1=slot,m1=m,i_ring1=22    ,layer=layer)
    if hasvia:
        via_polarslot(i_hand=i_hand,tens=tens,ones=ones,slot=slot,m=m,i_ring=i_ring)



def taps():
    tap(i_hand=0,ones=0,slot= 1,m=-1,hasvia=True)
    tap(i_hand=0,ones=1,slot= 0,m= 2,hasvia=True)
    tap(i_hand=0,ones=2,slot= 0,m= 0,hasvia=True)
    tap(i_hand=0,ones=3,slot= 0,m=-1,hasvia=True)
    tap(i_hand=0,ones=4,slot=59,m= 2,hasvia=True)
    tap(i_hand=0,ones=5,slot=59,m=-1,hasvia=True)
    tap(i_hand=0,ones=6,slot=58,m= 2,hasvia=True)
    tap(i_hand=0,ones=7,slot=58,m=-1,hasvia=True)
    tap(i_hand=0,ones=8,slot=57,m= 2,hasvia=True)
    tap(i_hand=0,ones=9,slot=57,m= 0,hasvia=True)
    tap(i_hand=1,ones=0,slot=30,m= 1)
    tap(i_hand=1,ones=1,slot=30,m= 0,hasvia=True)
    tap(i_hand=1,ones=2,slot=30,m=-1,hasvia=True)
    tap(i_hand=1,ones=3,slot=29,m= 2,hasvia=True)
    tap(i_hand=1,ones=4,slot=29,m= 0,hasvia=True)
    tap(i_hand=1,ones=5,slot=29,m=-1,hasvia=True)
    tap(i_hand=1,ones=6,slot=28,m= 2,hasvia=True)
    tap(i_hand=1,ones=7,slot=28,m= 0,hasvia=True)
    tap(i_hand=1,ones=8,slot=28,m=-1,hasvia=True)
    tap(i_hand=1,ones=9,slot=27,m= 2,hasvia=True)
    tap(i_hand=0,tens=0,slot= 3,m= 2,hasvia=False)

    tap(i_hand=1,tens=2,slot=27,m=-1,hasvia=False)
    via_polarslot(i_hand=1,tens=2,i_ring=22,slot=27,m=-1)
    arc(i_hand=1,tens=2,i_ring=22,slot0=27,m0=-1,slot1=32,m1=-2)

    tap(i_hand=1,tens=3,slot=31,m=-1,hasvia=False)

    tap(i_hand=1,tens=4,slot=40,m=-1,hasvia=False)
    arc(i_hand=1,tens=4,i_ring=22,slot1=39,m1= 1,slot0=31,m0=0,layer='B.Cu')
    trace_polarslot(i_hand=1,tens=4,i_ring0=23,slot0=40,m0=-2,i_ring1=22,slot1=40,m1=-1,layer='B.Cu')
    trace_polarslot(i_hand=1,tens=4,i_ring0=23,slot0=39,m0= 2,i_ring1=22,slot1=39,m1= 1,layer='B.Cu')

    tap(i_hand=0,tens=3,slot=39,m= 2,hasvia=False)

    tap(i_hand=0,tens=4,slot=49,m= 2,hasvia=False)
    via_polarslot(i_hand=0,tens=4,i_ring=22,slot=49,m=2)
    arc(i_hand=0,tens=4,i_ring=22,slot0=49,m0= 2,slot1=61,m1=-1)

    tap(i_hand=0,tens=5,slot=56,m= 2,hasvia=False)
    trace_polarslot(i_hand=1,tens=5,i_ring0=22,slot0=56,m0= 2,i_ring1=23,slot1=56,m1= 2,layer='B.Cu')
    via_polarslot(i_hand=0,tens=5,i_ring=23,slot=56,m=2)
    arc(i_hand=0,tens=5,i_ring=23,slot0=56,m0= 2,slot1=60,m1=2)

    tap(i_hand=0,tens=1,slot=10,m= 2,hasvia=False)
    via_polarslot(i_hand=0,tens=1,i_ring=22,slot=10,m=2)
    arc(i_hand=0,tens=1,i_ring=22,slot1=10,m1= 2,slot0=2,m0= 0)

    tap(i_hand=1,tens=1,slot=19,m=-1,hasvia=False)
    via_polarslot(i_hand=1,tens=1,i_ring=22,slot=19,m=-1)
    arc(i_hand=1,tens=1,i_ring=22,slot0=19,m0=-1,slot1=26,m1= 1)
    trace_polarslot(i_hand=1,tens=1,i_ring0=22,slot0=26,m0= 1,i_ring1=23,slot1=27,m1=-2)
    arc(i_hand=1,tens=1,i_ring=23,slot1=31,m1= 0,slot0=26,m0= 1)

    tap(i_hand=1,tens=5,slot=50,m=-1,hasvia=False)

    tap(i_hand=1,tens=0,slot= 9,m=-1,hasvia=False)

    tap(i_hand=1,tens=2,slot=20,m= 2,hasvia=False)
    pcbnew.Refresh()


taps()
raise AssertionError("Stop!")
        

def redraw():
    erase_rings()
    draw_rings()
    draw_radials()


place_diodes()
