# -*- coding: utf-8 -*-
"""
This class contains the absorption model used in pyrtlib.
"""

import types
from typing import Tuple, Union

import numpy as np

from .utils import dilec12, dcerror


class AbsModel(object):
    """This is an abstraction class to define the absorption model.
    """

    def __init__(self):
        self._model = ''
        """Model used to compute absorption"""

    @property
    def model(self) -> str:
        return self._model

    @model.setter
    def model(self, model: str) -> None:
        if model and isinstance(model, str):
            self._model = model
        else:
            raise ValueError("Please enter a valid absorption model")


class LiqAbsModel(AbsModel):
    """This class contains the absorption model used in pyrtlib.
    """

    @staticmethod
    def liquid_water_absorption(water: np.ndarray, freq: np.ndarray, temp: np.ndarray) -> np.ndarray:
        """Computes Absorption In Nepers/Km By Suspended Water Droplets.

        Args:
            water (np.ndarray): water in g/m3. Defaults to None.
            freq (np.ndarray): frequency in GHz (Valid From 0 To 1000 Ghz). Defaults to None.
            temp (np.ndarray): temperature in K. Defaults to None.

        Returns:
            np.ndarray: [description]

        References
        ----------
        .. [1] Liebe, Hufford And Manabe, Int. J. Ir & Mm Waves V.12, Pp.659-675 (1991).
        .. [2] Liebe Et Al, Agard Conf. Proc. 542, May 1993.

        .. note::
            Revision history:

            * Pwr 8/3/92   Original Version
            * Pwr 12/14/98 Temp. Dependence Of Eps2 Eliminated To Agree With Mpm93 

        .. warning:: conversion of complex() function is missing
        """
        if water <= 0:
            abliq = 0
            return abliq

        if LiqAbsModel.model in ['rose03', 'rose98']:
            theta1 = 1.0 - 300.0 / temp
            eps0 = 77.66 - np.dot(103.3, theta1)
            eps1 = np.dot(0.0671, eps0)
            eps2 = 3.52
            fp = np.dot((np.dot(316.0, theta1) + 146.4), theta1) + 20.2
            fs = np.dot(39.8, fp)
            eps = (eps0 - eps1) / np.complex(1.0, freq / fp) + (eps1 - eps2) / complex(1.0, freq / fs) + eps2
        elif LiqAbsModel.model in ['rose17', 'rose16', 'rose19', 'rose19sd']:
            eps = dilec12(freq, temp)
        else:
            raise ValueError('[AbsLiq] No model available with this name: {} . Sorry...'.format(LiqAbsModel.model))

        re = (eps - 1.0) / (eps + 2.0)

        abliq = -0.06286 * np.imag(re) * freq * water

        return abliq


class N2AbsModel(AbsModel):
    """This class contains the absorption model used in pyrtlib.
    """

    @staticmethod
    def n2_absorption(t: np.ndarray, p: np.ndarray, f: np.ndarray) -> np.ndarray:
        """Collision-Induced Power Absorption Coefficient (Neper/Km) in air
        with modification of 1.34 to account for O2-O2 and O2-N2 collisions, as calculated by [3]

        5/22/02, 4/14/05 P.Rosenkranz

        Copyright (c) 2002 Massachusetts Institute of Technology

        Args:
            t ([type], optional): Temperature (K). Defaults to None.
            p ([type], optional): Dry Air Pressure (Mb). Defaults to None.
            f ([type], optional): Frequency (Ghz)(Valid 0-2000 Ghz). Defaults to None.

        Returns:
            [type]: [description]

        References
        ----------
        .. [1] See eq. 2.6 in Thermal Microwave Radiation - Applications for Remote Sensing (C. Maetzler, ed.) London, IET, 2006.
        .. [2] Borysow, A, and L. Frommhold, Astrophysical Journal, v.311, pp.1043-1057 (1986)
        .. [3] J.Boissoles, C.Boulet, R.H.Tipping, A.Brown, and Q.Ma, J. Quant. Spectros. Radiat. Trans. v.82, 505-516 (2003).
        """

        th = 300.0 / t
        fdepen = 0.5 + 0.5 / (1.0 + (f / 450.0) ** 2)
        if N2AbsModel.model in ['rose16', 'rose17', 'rose18', 'rose19', 'rose19sd']:
            l, m, n = 6.5e-14, 3.6, 1.34
        elif N2AbsModel.model in ['rose20', 'rose20sd']:
            l, m, n = 9.95e-14, 3.22, 1
        elif N2AbsModel.model == 'rose03':
            l, m, n = 6.5e-14, 3.6, 1.29
        elif N2AbsModel.model in ['rose98']:
            l, m, n = 6.4e-14, 3.55, 1
            fdepen = 1
        else:
            raise ValueError('[AbsN2] No model available with this name: {} . Sorry...'.format(AbsModel.model))

        bf = l * fdepen * p * p * f * f * th ** m

        abs_n2 = n * bf

        return abs_n2


class H2OAbsModel(AbsModel):
    """This class contains the absorption model used in pyrtlib.
    """

    def __init__(self):
        super(H2OAbsModel, self).__init__()

    @property
    def h2oll(self) -> types.MethodType:
        return self._h2oll

    @h2oll.setter
    def h2oll(self, h2oll) -> None:
        if h2oll and isinstance(h2oll, types.MethodType):
            self._h2oll = h2oll
        else:
            raise ValueError("Please enter a valid absorption model")

    def h2o_rosen19_sd(self, pdrykpa: np.ndarray, vx: np.ndarray, ekpa: np.ndarray, frq: np.ndarray) -> Union[
        Tuple[np.ndarray, np.ndarray], None]:
        """Compute absorption coefficients in atmosphere due to water vapor
        this version should not be used with a line list older than june 2018,
        nor the new list with an older version of this subroutine.
        Line parameters will be read from file h2o_list.asc; intensities
        should include the isotope abundance factors.
        this version uses a line-shape cutoff.

        Args:
            pdrykpa ([type], optional): [description]. Defaults to none.
            vx ([type], optional): [description]. Defaults to none.
            ekpa ([type], optional): [description]. Defaults to none.
            frq ([type], optional): [description]. Defaults to none.

        Returns:
            [type]: [description]

        References
        ----------
        .. [1] Rosenkranz, P.W.: Line-By-Line Microwave Radiative Transfer (Non-Scattering), Remote Sens. Code Library, Doi:10.21982/M81013, 2017

        Example
        -------

        .. code-block:: python

            import numpy as np
            from pyrtlib.rte import RTEquation
            from pyrtlib.absmodel import H2OAbsModel, AbsModel
            from pyrtlib.atmp import AtmosphericProfiles as atmp
            from pyrtlib.utils import ppmv2gkg, mr2rh, import_lineshape

            z, p, d, tk, md = atmp.gl_atm(atmp.TROPICAL)
            frq = np.arange(20, 201, 1)
            ice = 0
            gkg = ppmv2gkg(md[:, atmp.H2O], atmp.H2O)
            rh = mr2rh(p, tk, gkg)[0] / 100

            e, rho = RTEquation.vapor(tk, rh, ice)

            AbsModel.model = 'rose16'
            H2OAbsModel.h2oll = import_lineshape('h2oll_{}'.format('rose16'))
            for i in range(0, len(z)):
                v = 300.0 / tk[i]
                ekpa = e[i] / 10.0
                pdrykpa = p[i] / 10.0 - ekpa
                for j in range(0, len(frq)):
                    _, _ = H2OAbsModel().h2o_rosen19_sd(pdrykpa, v, ekpa, frq[j])

        """
        # nico: the best-fit voigt are given in koshelev et al. 2018, table 2 (rad,
        # mhz/torr). these correspond to w3(1) and ws(1) in h2o_list_r18 (mhz/mb)

        # cyh ***********************************************
        db2np = np.log(10.0) * 0.1
        rvap = (0.01 * 8.31451) / 18.01528
        factor = 0.182 * frq
        t = 300.0 / vx
        p = (pdrykpa + ekpa) * 10.0
        rho = ekpa * 10.0 / (rvap * t)
        f = frq
        # cyh ***********************************************

        if rho.any() <= 0.0:
            # abh2o = 0.0
            # npp = 0
            # ncpp = 0
            return

        pvap = (rho * t) / 216.68
        if H2OAbsModel.model in ['rose03', 'rose16', 'rose17', 'rose98']:
            pvap = (rho * t) / 217.0
        pda = p - pvap
        if H2OAbsModel.model in ['rose03', 'rose16', 'rose98']:
            den = 3.335e+16 * rho
        else:
            den = 3.344e+16 * rho
        # continuum terms
        ti = self.h2oll.reftcon / t
        # xcf and xcs include 3 for conv. to density & stimulated emission
        if H2OAbsModel.model in ['rose03', 'rose98']:
            con = (5.43e-10 * pda * ti ** 3 + 1.8e-08 * pvap * ti ** 7.5) * pvap * f * f
        else:
            con = (self.h2oll.cf * pda * ti ** self.h2oll.xcf + self.h2oll.cs * pvap * ti ** self.h2oll.xcs) * pvap * f * f
        # nico 2019/03/18 *********************************************************
        # add resonances
        nlines = len(self.h2oll.fl)
        ti = self.h2oll.reftline / t
        df = np.zeros((2, 1))

        if H2OAbsModel.model.startswith(('rose19sd', 'rose20sd')):
            tiln = np.log(ti)
            ti2 = np.exp(2.5 * tiln)
            summ = 0.0
            for i in range(0, nlines):
                width0 = self.h2oll.w0[i] * pda * ti ** self.h2oll.x[i] + self.h2oll.w0s[i] * pvap * ti ** \
                         self.h2oll.xs[i]
                width2 = self.h2oll.w2[i] * pda + self.h2oll.w2s[i] * pvap

                shiftf = self.h2oll.sh[i] * pda * (1. - self.h2oll.aair[i] * tiln) * ti ** self.h2oll.xh[i]
                shifts = self.h2oll.shs[i] * pvap * (1. - self.h2oll.aself[i] * tiln) * ti ** self.h2oll.xhs[i]
                shift = shiftf + shifts
                # nico: thus using the best-fit voigt (shift instead of shift0 and shift2)
                wsq = width0 ** 2
                s = self.h2oll.s1[i] * ti2 * np.exp(self.h2oll.b2[i] * (1. - ti))
                df[0] = f - self.h2oll.fl[i] - shift
                df[1] = f + self.h2oll.fl[i] + shift
                base = width0 / (562500.0 + wsq)
                res = 0.0
                for j in range(0, 2):
                    # if(i.eq.1 .and. j.eq.1 .and. abs(df(j)).lt.10.*width0) then
                    # WIDTH2>0.0 & J==1 & abs(DF(J)) < 10*WIDTH0
                    # width2 > 0 and j == 1 and abs(df[j]) < np.dot(10, width0)
                    if width2 > 0 and j == 0 and np.abs(df[j]) < (10 * width0):
                        # speed-dependent resonant shape factor
                        # double complex dcerror,xc,xrt,pxw,a
                        xc = np.complex((width0 - np.dot(1.5, width2)), df[j]) / width2
                        if H2OAbsModel.model == 'rose20sd':
                            if i == 1:
                                delta2 = (self.h2oll.d2air * pda) + (self.h2oll.d2self * pvap)
                            else:
                                delta2 = 0.0
                            xc = np.complex((width0 - np.dot(1.5, width2)), df[j] + np.dot(1.5, delta2)) / np.complex(width2, -delta2)
                        
                        xrt = np.sqrt(xc)

                        pxw = 1.77245385090551603 * xrt * dcerror(-np.imag(xrt), np.real(xrt))
                        sd = 2.0 * (1.0 - pxw) / (width2 if H2OAbsModel.model != 'rose20sd' else np.complex(width2, -delta2))
                        res += np.real(sd) - base
                    else:
                        if np.abs(df[j]) < 750.0:
                            res += width0 / (df[j] ** 2 + wsq) - base

                summ += s * res * (f / self.h2oll.fl[i]) ** 2
        elif H2OAbsModel.model in ['rose16', 'rose03', 'rose17', 'rose98']:
            ti2 = ti ** 2.5
            summ = 0.0
            for i in range(0, nlines):
                widthf = self.h2oll.w0[i] * pda * ti ** self.h2oll.x[i]
                widths = self.h2oll.w0s[i] * pvap * ti ** self.h2oll.xs[i]
                width = widthf + widths
                if H2OAbsModel.model == 'rose98':
                    shift = 0.0
                else:
                    shift = self.h2oll.sr[i] * (width if H2OAbsModel.model == 'rose03' else widthf)
                wsq = width ** 2
                s = self.h2oll.s1[i] * ti2 * np.exp(self.h2oll.b2[i] * (1.0 - ti))
                df[0] = f - self.h2oll.fl[i] - shift
                df[1] = f + self.h2oll.fl[i] + shift
                # use clough's definition of local line contribution
                base = width / (562500.0 + wsq)
                # do for positive and negative resonances
                res = 0.0
                for j in range(0, 2):
                    if np.abs(df[j]) <= 750.0:
                        res += width / (df[j] ** 2 + wsq) - base
                summ += s * res * (f / self.h2oll.fl[i]) ** 2
        elif H2OAbsModel.model in ['rose19', 'rose20']:
            tiln = np.log(ti)
            ti2 = np.exp(2.5 * tiln)
            summ = 0.0
            for i in range(0, nlines):
                widthf = self.h2oll.w0[i] * pda * ti ** self.h2oll.x[i]
                widths = self.h2oll.w0s[i] * pvap * ti ** self.h2oll.xs[i]
                width = widthf + widths
                shiftf = self.h2oll.sh[i] * pda * (1. - self.h2oll.aair[i] * tiln) * ti ** self.h2oll.xh[i]
                shifts = self.h2oll.shs[i] * pvap * (1. - self.h2oll.aself[i] * tiln) * ti ** self.h2oll.xhs[i]
                shift = shiftf + shifts
                wsq = width ** 2
                s = self.h2oll.s1[i] * ti2 * np.exp(self.h2oll.b2[i] * (1. - ti))
                df[0] = f - self.h2oll.fl[i] - shift
                df[1] = f + self.h2oll.fl[i] + shift
                base = width / (562500.0 + wsq)
                res = 0.0
                for j in range(0, 2):
                    if np.abs(df[j]) < 750.0:
                        res += width / (df[j] ** 2 + wsq) - base
                summ += s * res * (f / self.h2oll.fl[i]) ** 2
        elif H2OAbsModel.model == 'rose18':
            ti2 = ti ** 2.5
            summ = 0.0
            for i in range(0, nlines):
                widthf = self.h2oll.w0[i] * pda * ti ** self.h2oll.x[i]
                widths = self.h2oll.w0s[i] * pvap * ti ** self.h2oll.xs[i]
                width = widthf + widths
                shiftf = self.h2oll.sh[i] * pda * ti ** self.h2oll.xh[i]
                shifts = self.h2oll.shs[i] * pvap * ti ** self.h2oll.xhs[i]
                shift = shiftf + shifts
                wsq = width ** 2
                s = self.h2oll.s1[i] * ti2 * np.exp(self.h2oll.b2[i] * (1. - ti))
                df[0] = f - self.h2oll.fl[i] - shift
                df[1] = f + self.h2oll.fl[i] + shift
                base = width / (562500.0 + wsq)
                res = 0.0
                for j in range(0, 2):
                    if np.abs(df[j]) < 750.0:
                        res += width / (df[j] ** 2 + wsq) - base
                summ += s * res * (f / self.h2oll.fl[i]) ** 2
        # nico 2019/03/18 *********************************************************
        # cyh **************************************************************
        # separate the following original equ. into line and continuum
        # terms, and change the units from np/km to ppm
        # abh2o = .3183e-4*den*sum + con

        npp = (3.183e-05 * den * summ / db2np) / factor
        ncpp = (con / db2np) / factor
        # cyh *************************************************************

        return npp, ncpp


class O2AbsModel(AbsModel):
    """This class contains the absorption model used in pyrtlib.
    """

    def __init__(self):
        super(O2AbsModel, self).__init__()

    @property
    def o2ll(self) -> types.MethodType:
        return self._o2ll

    @o2ll.setter
    def o2ll(self, o2ll) -> None:
        if o2ll and isinstance(o2ll, types.MethodType):
            self._o2ll = o2ll
        else:
            raise ValueError("Please enter a valid absorption model")

    def o2abs_rosen18(self, pdrykpa: float, vx: float, ekpa: float, frq: float) -> Tuple[np.ndarray, np.ndarray]:
        """Returns power absorption coefficient due to oxygen in air,
        in nepers/km.  Multiply o2abs by 4.343 to convert to db/km.

        History:

        * 5/1/95  P. Rosenkranz
        * 11/5/97  P. Rosenkranz - 1- line modification.
        * 12/16/98 pwr - updated submm freq's and intensities from HITRAN96
        * 8/21/02  pwr - revised width at 425
        * 3/20/03  pwr - 1- line mixing and width revised
        * 9/29/04  pwr - new widths and mixing, using HITRAN intensities for all lines
        * 6/12/06  pwr - chg. T dependence of 1- line to 0.8
        * 10/14/08 pwr - moved isotope abundance back into intensities; added selected O16O18 lines.
        * 5/30/09  pwr - remove common block, add weak lines.
        * 12/18/14 pwr - adjust line broadening due to water vapor.

        Args:
            pdrykpa ([type], optional): [description]. Defaults to None.
            vx ([type], optional): [description]. Defaults to None.
            ekpa ([type], optional): [description]. Defaults to None.
            frq ([type], optional): [description]. Defaults to None.

        Returns:
            np.ndarray: [description]
            np.ndarray: [description]

        References
        ----------
        .. [1] P.W. Rosenkranz, CHAP. 2 in ATMOSPHERIC REMOTE SENSING BY MICROWAVE RADIOMETRY (M.A. Janssen, ed., 1993) (http://hdl.handle.net/1721.1/68611).
        .. [3] G.Yu. Golubiatnikov & A.F. Krupnov, J. Mol. Spect. v.217, pp.282-287 (2003).
        .. [4] M.Yu. Tretyakov et al, J. Mol. Spect. v.223, pp.31-38 (2004).
        .. [5] M.Yu. Tretyakov et al, J. Mol. Spect. v.231, pp.1-14 (2005).
        .. [6] B.J. Drouin, JQSRT v.105, pp.450-458 (2007).
        .. [7] D.S. Makarov et al, J. Mol. Spect. v.252, pp.242-243 (2008).
        .. [8] M.A. Koshelev et al, JQSRT, in press (2015). line intensities from HITRAN2004. non-resonant intensity from JPL catalog.

        .. note::
            * The mm line-width and mixing coefficients are from Tretyakov et al submm line-widths from Golubiatnikov & Krupnov (except 234 GHz from Drouin)
            * The same temperature dependence (X) is used for submillimeter line widths as in the 60 GHz band: (1/T)**X

        .. note::
            Nico: the only differences wrt to o2n2_rosen17_xxx are:

            * PRESWV = VAPDEN*TEMP/217. -> PRESWV = VAPDEN*TEMP/216.68 - this is now consistent with h2o
            * ABSN2_ros16(TEMP,PRES,FREQ) -> ABSN2_ros18(TEMP,PRESDA,FREQ) - since absn2.f takes in input P = DRY AIR PRESSURE (MB)
            * ABSN2 is now external
            * The continuum term is summed BEFORE O2ABS = max(O2ABS,0.)
        """

        # cyh*** add the following lines *************************
        db2np = np.log(10.0) * 0.1
        rvap = (0.01 * 8.31451) / 18.01528
        factor = 0.182 * frq
        temp = 300.0 / vx
        pres = (pdrykpa + ekpa) * 10.0
        vapden = ekpa * 10.0 / (rvap * temp)
        freq = frq
        # cyh*****************************************************

        th = 300.0 / temp
        th1 = th - 1.0
        b = th ** self.o2ll.x
        preswv = (vapden * temp) / 216.68
        presda = pres - preswv
        den = 0.001 * (presda * b + 1.2 * preswv * th)
        dfnr = self.o2ll.wb300 * den

        # nico intensities of the non-resonant transitions for o16-o16 and o16-o18, from jpl's line compilation
        # 1.571e-17 (o16-o16) + 1.3e-19 (o16-o18) = 1.584e-17
        # 1.584e-17*freq*freq*dfnr/(th*(freq*freq + dfnr*dfnr))
        summ = 1.584e-17 * freq * freq * dfnr / (th * (freq * freq + dfnr * dfnr))
        # cyh **************************************************************

        nlines = len(self.o2ll.f)
        for k in range(0, nlines):
            df = self.o2ll.w300[k] * den
            fcen = self.o2ll.f[k]
            y = den * (self.o2ll.y300[k] + self.o2ll.v[k] * th1)
            strr = self.o2ll.s300[k] * np.exp(-self.o2ll.be[k] * th1)
            sf1 = (df + (freq - fcen) * y) / ((freq - fcen) ** 2 + df * df)
            sf2 = (df - (freq + fcen) * y) / ((freq + fcen) ** 2 + df * df)
            summ += strr * (sf1 + sf2) * (freq / self.o2ll.f[k]) ** 2

        # o2abs = .5034e12*sum*presda*th^3/3.14159;
        # .20946e-4/(3.14159*1.38065e-19*300) = 1.6097e11
        # nico the following computes n/pi*sum*th^2 (see notes)
        # nico n/pi = a/(pi*k*t_0) * pda * th
        # nico a/(pi*k*t_0) = 0.20946/(3.14159*1.38065e-23*300) = 1.6097e19  - then it needs a factor 1e-8 to accont
        # for units conversion (pa->hpa, hz->ghz, m->km)
        # nico pa2hpa=1e-2; hz2ghz=1e-9; m2cm=1e2; m2km=1e-3; pa2hpa^-1 * hz2ghz * m2cm^-2 * m2km^-1 = 1e-8
        # nico th^3 = th(from ideal gas law 2.13) * th(from the mw approx of stimulated emission 2.16 vs. 2.14) *
        # th(from the partition sum 2.20)

        o2abs = 1.6097e+11 * summ * presda * th ** 3
        o2abs = np.maximum(o2abs, 0.0)
        # cyh *** ********************************************************
        # separate the equ. into line and continuum
        # terms, and change the units from np/km to ppm

        # nico intensities of the non-resonant transitions for o16-o16 and o16-o18, from jpl's line compilation
        # 1.571e-17 (o16-o16) + 1.3e-19 (o16-o18) = 1.584e-17

        ncpp = 1.584e-17 * freq * freq * dfnr / (th * (freq * freq + dfnr * dfnr))
        # 20946e-4/(3.14159*1.38065e-19*300) = 1.6097e11
        # nico a/(pi*k*t_0) = 0.20946/(3.14159*1.38065e-23*300) = 1.6097e19  - then it needs a factor 1e-8 to accont
        # for units conversion (pa->hpa, hz->ghz)
        # nico pa2hpa=1e-2; hz2ghz=1e-9; m2cm=1e2; m2km=1e-3; pa2hpa^-1 * hz2ghz * m2cm^-2 * m2km^-1 = 1e-8
        # nico th^3 = th(from ideal gas law 2.13) * th(from the mw approx of stimulated emission 2.16 vs. 2.14)
        # * th(from the partition sum 2.20)
        ncpp = 1.6097e+11 * ncpp * presda * th ** 3

        # change the units from np/km to ppm
        npp = (o2abs / db2np) / factor

        ncpp = (ncpp / db2np) / factor
        # cyh ************************************************************

        return npp, ncpp

    def o2abs_rosen19(self, pdrykpa: float, vx: float, ekpa: float, frq: float) -> Tuple[np.ndarray, np.ndarray]:
        """Returns power absorption coefficient due to oxygen in air,
        in nepers/km. multiply o2abs2 by 4.343 to convert to db/km.

        History:

        * 5/1/95  P. Rosenkranz
        * 11/5/97  P. Rosenkranz - 1- line modification.
        * 12/16/98 pwr - updated submm freq's and intensities from HITRAN96
        * 8/21/02  pwr - revised width at 425
        * 3/20/03  pwr - 1- line mixing and width revised
        * 9/29/04  pwr - new widths and mixing, using HITRAN intensities for all lines
        * 6/12/06  pwr - chg. T dependence of 1- line to 0.8
        * 10/14/08 pwr - moved isotope abundance back into intensities, added selected O16O18 lines.
        * 5/30/09  pwr - remove common block, add weak lines.
        * 12/18/14 pwr - adjust line broadening due to water vapor.
        * 9/29/18  pwr - 2nd-order line mixing
        * 8/20/19  pwr - adjust intensities according to Koshelev meas.

        Args:
            pdrykpa ([type], optional): [description]. Defaults to None.
            vx ([type], optional): [description]. Defaults to None.
            ekpa ([type], optional): [description]. Defaults to None.
            frq ([type], optional): [description]. Defaults to None.

        Returns:
            [type]: [description]

        References
        ----------
        .. [1] P.W. Rosenkranz, CHAP. 2 and appendix, in ATMOSPHERIC REMOTE SENSING BY MICROWAVE RADIOMETRY (M.A. Janssen, ed., 1993)(http://hdl.handle.net/1721.1/68611).
        .. [2] G.Yu. Golubiatnikov & A.F. Krupnov, J. Mol. Spect. v.217, pp.282-287 (2003).
        .. [3] M.Yu. Tretyakov et al, J. Mol. Spect. v.223, pp.31-38 (2004).
        .. [4] M.Yu. Tretyakov et al, J. Mol. Spect. v.231, pp.1-14 (2005).
        .. [5] B.J. Drouin, JQSRT v.105, pp.450-458 (2007).
        .. [6] D.S. Makarov et al, J. Mol. Spect. v.252, pp.242-243 (2008).
        .. [7] D.S. Makarov et al, JQSRT v.112, pp.1420-1428 (2011).
        .. [8] M.A. Koshelev et al, JQSRT, v.154, pp.24-27 (2015).
        .. [9] M.A. Koshelev et al, JQSRT, v.169, pp.91-95 (2016).
        .. [10] M.A. Koshelev et al, JQSRT, v.196, pp.78?86 (2017).
        .. [11] D.S. Makarov et al, JQSRT v.243 (March 2020) doi:10.1016/j.jqsrt.2019.106798

        Line intensities from HITRAN2004.
        Non-resonant intensity from JPL catalog.

        .. note::
         1. The mm line-width coefficients are from Tretyakov et al 2005,
            Makarov et al 2008, and Koshelev et al 2016;
            submm line-widths from Golubiatnikov & Krupnov, except 234-GHz line width from Drouin.
            Mixing coeff. from Makarov's 2018 revision.
         2. The same temperature dependence (X) is used for submillimeter
            line widths as in the 60 GHz band: (1/T)**X (Koshelev et al 2016)
         3. The sign of DNU in the shape factor is corrected.
        """

        # *** add the following lines *************************
        db2np = np.log(10.0) * 0.1
        rvap = (0.01 * 8.314510) / 18.01528
        factor = 0.182 * frq
        temp = 300.0 / vx
        pres = (pdrykpa + ekpa) * 10.0
        vapden = (ekpa * 10.0) / (rvap * temp)
        freq = frq
        # *****************************************************

        th = 300.0 / temp
        th1 = th - 1.0
        b = th ** self.o2ll.x
        preswv = vapden * temp / 216.68
        if O2AbsModel.model in ['rose03', 'rose16', 'rose17', 'rose18', 'rose98']:
            preswv = vapden * temp / 217.0
        presda = pres - preswv
        den = 0.001 * (presda * b + 1.2 * preswv * th)
        if O2AbsModel.model in ['rose03', 'rose16', 'rose98']:
            den = 0.001 * (presda * b + 1.1 * preswv * th)
        if O2AbsModel.model == 'rose03':
            dens = 0.001 * (presda * th ** 0.9 + 1.1 * preswv * th)
        if O2AbsModel.model == 'rose98':
            dens = 0.001 * (presda + 1.1 * preswv) * th
        dfnr = self.o2ll.wb300 * den
        pe2 = den * den

        # nico intensities of the non-resonant transitions for o16-o16 and o16-o18, from jpl's line compilation
        # 1.571e-17 (o16-o16) + 1.3e-19 (o16-o18) = 1.584e-17
        summ = 1.584e-17 * freq * freq * dfnr / (th * (freq * freq + dfnr * dfnr))
        if O2AbsModel.model in ['rose03', 'rose16', 'rose17', 'rose18', 'rose98']:
            summ = 0.0
        nlines = len(self.o2ll.f)
        if O2AbsModel.model in ['rose03', 'rose98']:
            for k in range(0, nlines):
                if k == 0:
                    df = self.o2ll.w300[0] * dens
                else:
                    df = self.o2ll.w300[k] * den
                y = 0.001 * pres * b * (self.o2ll.y300[k] + self.o2ll.v[k] * th1)
                strr = self.o2ll.s300[k] * np.exp(-self.o2ll.be[k] * th1)
                sf1 = (df + (freq - self.o2ll.f[k]) * y) / ((freq - self.o2ll.f[k]) ** 2 + df * df)
                sf2 = (df - (freq + self.o2ll.f[k]) * y) / ((freq + self.o2ll.f[k]) ** 2 + df * df)
                summ += strr * (sf1 + sf2) * (freq / self.o2ll.f[k]) ** 2
        elif O2AbsModel.model in ['rose17', 'rose18']:
            for k in range(0, nlines):
                df = self.o2ll.w300[k] * den
                fcen = self.o2ll.f[k]
                y = den * (self.o2ll.y300[k] + self.o2ll.v[k] * th1)
                strr = self.o2ll.s300[k] * np.exp(-self.o2ll.be[k] * th1)
                sf1 = (df + (freq - fcen) * y) / ((freq - self.o2ll.f[k]) ** 2 + df * df)
                sf2 = (df - (freq + fcen) * y) / ((freq + self.o2ll.f[k]) ** 2 + df * df)
                summ += strr * (sf1 + sf2) * (freq / self.o2ll.f[k]) ** 2
        else:
            for k in range(0, nlines):
                df = self.o2ll.w300[k] * den
                y = den * (self.o2ll.y0[k] + self.o2ll.y1[k] * th1)
                dnu = pe2 * (self.o2ll.dnu0[k] + self.o2ll.dnu1[k] * th1)
                strr = self.o2ll.s300[k] * np.exp(-self.o2ll.be[k] * th1)
                del1 = freq - self.o2ll.f[k] - dnu
                del2 = freq + self.o2ll.f[k] + dnu
                gfac = 1. + pe2 * (self.o2ll.g0[k] + self.o2ll.g1[k] * th1)
                d1 = del1 * del1 + df * df
                d2 = del2 * del2 + df * df
                sf1 = (df * gfac + del1 * y) / d1
                sf2 = (df * gfac - del2 * y) / d2
                summ += strr * (sf1 + sf2) * (freq / self.o2ll.f[k]) ** 2

        o2abs = 1.6097e+11 * summ * presda * th ** 3
        if O2AbsModel.model in ['rose03', 'rose98']:
            o2abs = 5.034e+11 * summ * presda * th ** 3 / 3.14159
        # o2abs = 1.004 * np.maximum(o2abs, 0.0)
        if O2AbsModel.model != 'rose98':
            o2abs = np.maximum(o2abs, 0.0)
        if O2AbsModel.model in ['rose20', 'rose20sd']:
            o2abs = 1.004 * np.maximum(o2abs, 0.0)

        # *** ********************************************************
        # separate the equ. into line and continuum
        # terms, and change the units from np/km to ppm

        # nico intensities of the non-resonant transitions for o16-o16 and o16-o18, from jpl's line compilation
        # 1.571e-17 (o16-o16) + 1.3e-19 (o16-o18) = 1.584e-17

        ncpp = 1.584e-17 * freq * freq * dfnr / (th * (freq * freq + dfnr * dfnr))
        #  .20946e-4/(3.14159*1.38065e-19*300) = 1.6097e11
        # nico a/(pi*k*t_0) = 0.20946/(3.14159*1.38065e-23*300) = 1.6097e19  - then it needs a factor 1e-8 to accont
        # for units conversion (pa->hpa, hz->ghz)
        # nico pa2hpa=1e-2; hz2ghz=1e-9; m2cm=1e2; m2km=1e-3; pa2hpa^-1 * hz2ghz * m2cm^-2 * m2km^-1 = 1e-8
        # nico th^3 = th(from ideal gas law 2.13) * th(from the mw approx of stimulated emission 2.16 vs. 2.14) *
        # th(from the partition sum 2.20)
        if O2AbsModel.model in ['rose03', 'rose98']:
            ncpp = 1.6e-17 * freq * freq * dfnr / (th * (freq * freq + dfnr * dfnr))
            ncpp *= 5.034e+11 * presda * th ** 3 / 3.14159
        else:
            ncpp *= 1.6097e11 * presda * th ** 3  # nico: n/pi*sum0
        if O2AbsModel.model in ['rose03', 'rose16', 'rose17', 'rose18', 'rose98']:
            ncpp += N2AbsModel.n2_absorption(temp, pres, freq)
        # change the units from np/km to ppm
        npp = (o2abs / db2np) / factor
        ncpp = (ncpp / db2np) / factor
        # ************************************************************

        return npp, ncpp
