"""
Analyze IV curves for LEDs
"""
import re
from glob import glob
from os.path import basename

import numpy as np
from matplotlib import pyplot as plt


def main():
    colors=["Red1"]
    plotcolors={220.0:'r',100.0:'#804000',50:'k'}
    for color in colors:
        vcmds ={}
        vouts = {}
        vleds = {}
        Imas={}
        infns=glob(f"IV/*{color}*.csv")
        for infn in infns:
            with open(infn,"rt",errors='backslashreplace') as inf:
                oldcmd=None
                this_vouts=None
                this_vleds=None
                for line in inf:
                    line=line.strip()
                    match = re.match("(?P<dncmd>[-+]?[0-9]+),"
                                     "(?P<nsamples>[-+]?[0-9]+),"
                                     "(?P<dnins>[-+]?[0-9]+),"
                                     "(?P<dninss>[-+]?[0-9]+),"
                                     "(?P<dnouts>[-+]?[0-9]+),"
                                     "(?P<dnoutss>[-+]?[0-9]+),"
                                     "(?P<dnmids>[-+]?[0-9]+),"
                                     "(?P<dnmidss>[-+]?[0-9]+),"
                                     "(?P<dnbots>[-+]?[0-9]+),"
                                     "(?P<dnbotss>[-+]?[0-9]+),"
                                     "(?P<vcmd>[-+]?[0-9]+\.[0-9]+),"
                                     "(?P<vin>[-+]?[0-9]+\.[0-9]+),"
                                     "(?P<vout>[-+]?[0-9]+\.[0-9]+),"
                                     "(?P<vmid>[-+]?[0-9]+\.[0-9]+),"
                                     "(?P<vbot>[-+]?[0-9]+\.[0-9]+),"
                                     "(?P<R>[-+]?[0-9]+\.[0-9]+),"
                                     "(?P<Ima>[-+]?[0-9]+\.[0-9]+)"
                                     ,line)
                    if match is None:
                        continue
                    dncmd   =int(match.group("dncmd"))
                    nsamples=int(match.group("nsamples"))
                    dnins   =int(match.group("dnins"))
                    dninss  =int(match.group("dninss"))
                    dnouts  =int(match.group("dnouts"))
                    dnoutss =int(match.group("dnoutss"))
                    dnmids  =int(match.group("dnmids"))
                    dnmidss =int(match.group("dnmidss"))
                    dnbots  =int(match.group("dnbots"))
                    dnbotss =int(match.group("dnbotss"))
                    dnin_mu =float(dnins )/float(nsamples)
                    dnin_sig2=float(dninss)/float(nsamples)-dnin_mu**2
                    dnin_sig=np.sqrt(dnin_sig2)
                    dnout_mu=float(dnouts)/float(nsamples)
                    dnout_sig2=float(dnoutss)/float(nsamples)-dnout_mu**2
                    dnout_sig=np.sqrt(dnout_sig2)
                    dnmid_mu=float(dnmids)/float(nsamples)
                    dnmid_sig2=float(dnmidss)/float(nsamples)-dnmid_mu**2
                    dnmid_sig=np.sqrt(dnmid_sig2)
                    dnbot_mu=float(dnbots)/float(nsamples)
                    dnbot_sig2=float(dnbotss)/float(nsamples)-dnbot_mu**2
                    dnbot_sig=np.sqrt(dnbot_sig2)
                    R = float(match.group("R"))
                    vcmd=dncmd   *5.0/1024.0
                    vin =dnin_mu *5.0/1024.0
                    vout=dnout_mu *5.0/1024.0
                    vmid=dnmid_mu *5.0/1024.0
                    vbot=dnbot_mu *5.0/1024.0
                    vled=vmid-vbot
                    vr=vout-vmid
                    Ima=vr/R
                    if (R,nsamples) not in vcmds:
                        vcmds[(R,nsamples)]=[]
                        vouts[(R, nsamples)] = []
                        vleds[(R, nsamples)] = []
                        Imas[(R,nsamples)]=[]
                    vcmds[(R, nsamples)].append(vcmd)
                    vouts[(R, nsamples)].append(vout)
                    vleds[(R, nsamples)].append(vled)
                    Imas[(R, nsamples)].append(Ima)
        vcmds={k:np.array(v) for k,v in vcmds.items()}
        vouts={k:np.array(v) for k,v in vouts.items()}
        vleds={k:np.array(v) for k,v in vleds.items()}
        Imas={k:np.array(v) for k,v in Imas.items()}
        plt.figure("I vs V")
        for k in vcmds.keys():
            plt.plot(vleds[k],Imas[k],('--' if k[1]==1 else '-'),color=plotcolors[k[0]],label=str(k))
        plt.xlabel("Vled/V")
        plt.ylabel("Iled/mA")
        plt.title(basename(infn))
        plt.legend()
        plt.figure("V")
        for k in vcmds.keys():
            plt.plot(vcmds[k],vins[k],('--' if k[1]==1 else '-'),label="vled" str(k))
            plt.plot(vcmds[k],vouts[k],('--' if k[1]==1 else '-'),label="vled" str(k))
            plt.plot(vcmds[k],vleds[k],('--' if k[1]==1 else '-'),label="vled" str(k))
        plt.ylabel("Vled/V")
        plt.title(basename(infn))
        plt.legend()
        plt.figure("Vcmd vs Vout")
        plt.plot(range(6),range(6))
        for k in vcmds.keys():
            plt.plot(vcmds[k],vouts[k],('--' if k[1]==1 else '-'),color=plotcolors[k[0]],label=str(k))
        plt.xlabel("Vcmd/V")
        plt.ylabel("Vout/V")
        plt.title(basename(infn))
        plt.legend()
        plt.show()


if __name__=="__main__":
    main()