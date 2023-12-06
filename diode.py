import numpy as np


# All voltages are in Volts.
# All table voltages are in mA and all calculated
# currents will be displayed and plotted in mA.
# They may be converted to A at some point, but only
# for internal purposes.


class Diode:
    def __init__(self, *, MFRnum: str = None, DKnum: str = None,
                 VI: np.array=None,
                 VIfn:str=None,
                 nm: float=None,
                 If: float=None, Vf: float=None,
                 Ifmax: float = None, Vfmax: float = None,
                 mcd: float=None, hex: str=None):
        """
        :param MFRnum: Manufacturer part number
        :param DKnum:  Digikey number
        :param IV:     Current/voltage curve. In the form of an Nx2 numpy array,
                       column 0 is voltage in V, column 1 is current in mA. Stored
                       current will be in SI units (A).
        :param nm:     Nominal wavelength. Input is in nm, stored is in SI unit (m).
                       This is the "dominant" wavelength from the Kingbright datasheet
        :param If:     Nominal forward current. Input in mA, stored in SI units (A).
        :param Vf:     Nominal forward voltage, V.
        :param Ifmax:  Maximum forward current. Chosen from end of diode curve
                       or absolute maximum
        :param Vfmax:  Forward voltage at Ifmax
        :param mcd:    Nominal brightness at If. This is "Typ" from Kingbright datasheet.
        """
        self.MFRnum = MFRnum
        self.DKnum = DKnum
        if VIfn is not None:
            with open(VIfn,"rt") as inf:
                self.VI=[]
                header=inf.readline().strip().split(",")
                for line in inf:
                    parts=line.strip().split(",")
                    self.VI.append([float(parts[0]),float(parts[1])])
            self.VI=np.array(self.VI)
        else:
            self.VI = VI
        self.VI[:, 1] /= 1000.0  # convert mA to A
        if nm is None:
            self.lam=float('nan')
        else:
            self.lam = nm / 1e9  # convert nm to m
        if Ifmax is None:
            self.Ifmax = np.max(self.VI[:, 1])
            self.Vfmax = np.max(self.VI[:, 0])
        else:
            self.Ifmax = Ifmax / 1000.0
            self.Vfmax = Vfmax
        if If is None:
            self.If=self.Ifmax
            self.Vf=self.Vfmax
        else:
            self.If = If / 1000.0  # convert mA to A
            self.Vf = Vf
        if mcd is None:
            self.cd=float('nan')
        else:
            self.cd = mcd / 1000.0  # convert mcd to cd
        self.hex = hex

    def _mb(x0, y0, x1, y1):
        m = (y1 - y0) / (x1 - x0)
        b = y0 - m * x0
        return m, b

    def Iv(self, V):
        """
        Calculate current given voltage
        :param V: Voltage across diode in volts
        :return: Current in amps
        """
        for v0, i0, v1, i1 in zip(self.VI[:-1, 0], self.VI[:-1, 1], self.VI[1:, 0], self.VI[1:, 1]):
            if V >= v0 and V <= v1:
                t = (V - v0) / (v1 - v0)
                return i0 * (1 - t) + i1 * t
        return float('nan')

    def Vi(self, I):
        """
        Calculate voltage given current
        :param I: Current through diode in amps
        :return: Voltage across diode in volts
        """
        for v0, i0, v1, i1 in zip(self.VI[:-1, 0], self.VI[:-1, 1], self.VI[1:, 0], self.VI[1:, 1]):
            if I >= i0 and I <= i1:
                t = (I - i0) / (i1 - i0)
                return v0 * (1 - t) + v1 * t
        return float('nan')

    def Cdi(self, I):
        """
        Calculate brightness in cd given current.

        Assumes linear brightness/current relation.
        """
        return I / self.If * self.cd

    def Icd(self, cd):
        """
        Calculate current necessary to get given brightness
        """
        return cd / self.cd * self.If

    def Rivcc(self, I, Vcc):
        """
        Calculate resistance necessary to get given current and supply voltage
        """
        V = self.Vi(I)
        Vr = Vcc - V
        R = Vr / I
        return R

    def Rcdvcc(self, cd, Vcc):
        """
        Calculate resistance necessary to get given brightness and supply voltage
        """
        return self.Rivcc(self.Icd(cd), Vcc)


# This curve has been checked against several Kingbright blue LEDs.
# All checked LEDs use this curve.
BlueLEDCurve = np.array([[0.00, 0],
                         [2.28, 0],
                         [2.30, 0.2124],
                         [2.39, 0.2124],
                         [2.41, 0.2974],
                         [2.46, 0.2974],
                         [2.56, 0.7222],
                         [2.65, 1.7417],
                         [2.74, 3.4834],
                         [2.80, 4.8003],
                         [2.88, 6.8819],
                         [2.95, 8.5387],
                         [3.00, 10.1105],
                         [3.11, 13.254],
                         [3.18, 15.5905],
                         [3.26, 18.5641],
                         [3.30, 20.0000],
                         [3.45, 27.1453],
                         [3.51, 30.0000]])

BlueFrontAPT1608GBC_D = Diode(MFRnum='APG1608QBC/D',
                              DKnum='754-1351-1-ND',
                              VI=BlueLEDCurve,
                              nm=465,
                              If=20, Vf=3.3,
                              mcd=100,
                              hex='#0000ff'
                              )

Blue = BlueFrontAPT1608GBC_D

GreenLEDCurve = np.array([[0.00, 0.0],
                          [2.33, 0.0],
                          [2.38, 0.1258],
                          [2.44, 0.4530],
                          [2.49, 0.6292],
                          [2.59, 1.3087],
                          [2.64, 1.8876],
                          [2.69, 2.6112],
                          [2.77, 3.8192],
                          [2.83, 4.9014],
                          [2.95, 8.2173],
                          [2.98, 9.1233],
                          [3.01, 9.9476],
                          [3.04, 10.9417],
                          [3.07, 11.9295],
                          [3.15, 14.9245],
                          [3.20, 16.6611],
                          [3.30, 20.0]])

GreenSideAPDA1806ZGCK = Diode(MFRnum='APDA1806ZGCK',
                              DKnum='754-2334-1-ND',
                              VI=GreenLEDCurve,
                              nm=525,
                              If=20, Vf=3.3,
                              mcd=3200,
                              hex="#00C000")

Green = GreenSideAPDA1806ZGCK

YellowLEDCurve=np.array([[0.00, 0],
                         [1.75, 0],
                         [1.78, 0.4404],
                         [1.81, 0.9438],
                         [1.86, 2.6846],
                         [1.88, 3.7122],
                         [1.89, 4.7819],
                         [1.93, 8.5361],
                         [1.96,11.8498],
                         [1.98,15.3943],
                         [2.00,20.0   ],
                         [2.04,29.8029]])

YellowSideAPDA1806SYCK = Diode(MFRnum='APDA1806SYCK',
                              DKnum='754-2331-1-ND',
                              VI=YellowLEDCurve,
                              nm=590,
                              If=20, Vf=2.0,
                              mcd=1100,
                              hex="#00C000")

Yellow=YellowSideAPDA1806SYCK


RedLEDCurve=np.array([[0.00, 0.0],
                      [1.81, 0.0],
                      [1.86, 0.6586],
                      [1.90, 1.3103],
                      [1.98, 3.496 ],
                      [2.05, 6.5844],
                      [2.10, 9.8195],
                      [2.16,14.8606],
                      [2.18,17.381 ],
                      [2.20,20.0   ],
                      [2.23,25.1519],
                      [2.25,30.0]])

RedSideAPDA1806SECK_J3_PRV = Diode(MFRnum='APDA1806SECK/J3-PRV',
                              DKnum='754-2329-1-ND',
                              VI=RedLEDCurve,
                              nm=625,
                              If=20, Vf=2.2,
                              mcd=7800,
                              hex="#00C000")

Red=RedSideAPDA1806SECK_J3_PRV

WhiteBrandXLED = Diode(VIfn='White BrandX LED Measured.csv')
White=WhiteBrandXLED

Vcc=5.0
Rw=White.Rivcc(White.If,Vcc)
print(f"{Vcc=},{White.If=},{Rw=}")


Vcc=3.3
Rlo=25 #Resistance of gate at low output
Rhi=25 #Resistance of gate at high output
Vrr=Vcc
Vgg=Vcc
Vyy=Vcc

for i in range(3):

    Rg = 50
    Vg = Green.Vi(Green.If)
    Vlo=Rlo*Green.If
    Vhi=Vcc-Rhi*Green.If
    Vgg=Vhi-Vlo
    print(f"mcdgreen={Green.cd*1000:.0f}mcd,Igreen={Green.If*1000:.1f}mA,{Rg=:.1f}R,{Vg=:.3f}V,{Vhi=:.3f}V,{Vlo=:.3f}V,{Vgg=:.3f}V")

    Cdy=Yellow.cd
    Iy = Yellow.Icd(Cdy)
    Ry = Yellow.Rivcc(Iy, Vcc)
    Vy = Yellow.Vi(Iy)
    Vlo=Rlo*Iy
    Vhi=Vcc-Rhi*Iy
    Vyy=Vhi-Vlo
    print(f"mcdyellow={Cdy*1000:.0f}mcd,Iyellow={Iy*1000:.1f}mA,{Ry=:.1f}R,{Vy=:.3f}V,{Vhi=:.3f}V,{Vlo=:.3f}V,{Vyy=:.3f}V")

    Cdr=Red.cd
    Ir = Red.Icd(Cdr)
    Rr = Red.Rivcc(Ir, Vcc)-Rlo-Rhi
    Vr = Red.Vi(Ir)
    Vlo=Rlo*Ir
    Vhi=Vcc-Rhi*Ir
    Vrr=Vhi-Vlo
    print(f"mcdred={Cdr*1000:.0f}mcd,Ired={Ir*1000:.1f}mA,{Rr=:.1f}R,{Vr=:.3f}V,{Vhi=:.3f}V,{Vlo=:.3f}V,{Vrr=:.3f}V")


