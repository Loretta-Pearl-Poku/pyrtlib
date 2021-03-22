# -*- coding: utf-8 -*-
"""
This module contains the main Radiative Transfer Equation functions.
"""
import warnings

import numpy as np

from .utils import constants, tk2b_mod, arange


class RTEquation:
    """This class contains the main Radiative Transfer Equation functions.
    """

    @staticmethod
    def vapor_xxx(tk=None, rh=None, ice=None, *args, **kwargs):
        """Compute saturation vapor pressure (es,in mb) over water or ice at
        temperature tk (kelvins), using the Goff-Gratch formulation (List,1963).

        Args:
            tk ([type], optional): temperature (K). Defaults to None.
            rh ([type], optional): relative humidity (fraction). Defaults to None.
            ice ([type], optional): switch to calculate saturation vapor pressure over
            water only (0) or water and ice, depending on tk (1). Defaults to None.

        Returns:
            (tuple):
            
            * e [type]: vapor pressure (mb)
            * rho [type]: vapor density (g/m3)

        .. todo:: could the find() function be replaced with numpy.where() or np.nozero or np.flatnonzero????
        """

        rvap = constants('Rwatvap')

        rvap = np.dot(rvap, 1e-05)

        # if ( (tk > 263.16) | (ice==0) )
        #    # for water...
        #    y = 373.16 ./ tk;
        #    es = -7.90298 * (y-1.) + 5.02808 * log10(y) -...
        #          1.3816e-7 * (10 .^ (11.344 * (1. - (1./ y))) - 1.) +...
        #          8.1328e-3 * (10 .^ (-3.49149 * (y - 1.)) - 1.) +...
        #          log10(1013.246);
        # else
        #    # for ice...
        #    y = 273.16 ./ tk;
        #    es = -9.09718 * (y - 1.) - 3.56654 * log10(y) +...
        #          0.876793 * (1.- (1. ./ y)) + log10(6.1071);
        # end

        # over water...
        y = 373.16 / tk
        es = np.dot(-7.90298, (y - 1.0)) + np.dot(5.02808, np.log10(y)) - np.dot(1.3816e-07, (
                10 ** (np.dot(11.344, (1.0 - (1.0 / y)))) - 1.0)) + np.dot(0.0081328, (
                10 ** (np.dot(-3.49149, (y - 1.0))) - 1.0)) + np.log10(1013.246)
        if ice == 1:
            # over ice if tk < 263.16
            indx = find(tk < 263.16)
            y = 273.16 / tk(indx)
            es[indx] = np.dot(-9.09718, (y - 1.0)) - np.dot(
                3.56654, np.log10(y)) + np.dot(0.876793, (1.0 - (1.0 / y))) + np.log10(6.1071)

        es = 10.0 ** es
        # Compute vapor pressure and vapor density.
        # The vapor density conversion follows the ideal gas law:
        # apor pressure = vapor density * rvapor * tk

        e = np.multiply(rh, es)
        rho = e / (np.dot(rvap, tk))

        return e, rho

    @staticmethod
    def bright_xxx(hvk=None, boft=None, *args, **kwargs):
        """Function to compute temperature from the modified Planck
        radiance (Planck function without the constants 2h(v^3)/(c^2).

        Args:
            hvk ([type], optional): [Planck constant (J*S)] * [frequency (Hz)] / [Boltzmann constant (J/K)]. Defaults to None.
            boft ([type], optional): modified Planck radiance - (equation (4) from Schroeder & Westwater, 1991). Defaults to None.

        Returns:
            [type]: [description]
        """

        Tb = hvk / np.log(1.0 + (1.0 / boft))

        return Tb

    @staticmethod
    def refract_xxx(p=None, tk=None, e=None, *args, **kwargs):
        """Computes profiles of wet refractivity, dry refractivity,
        refractive index.  Refractivity equations were taken from G.D.
        Thayer, 1974:  An improved equation for the radio refractive
        index of air. Radio Science, vol.9,no.10, 803-807.
        These equations were intended for frequencies under 20 GHz

        Args:
            p ([type], optional): pressure profile (mb). Defaults to None.
            tk ([type], optional): temperature profile (K). Defaults to None.
            e ([type], optional): vapor pressure profile (mb). Defaults to None.

        Returns:
            (tuple):

            * dryn [type]: dry refractivity profile
            * wetn [type]: wet refractivity profile
            * refindx [type]: refractive index profile

        .. todo:: check if slice works properly @Donatello
        """

        nl = len(p)
        wetn = []
        dryn = []
        refindx = []

        for i in arange(1, nl).reshape(-1):
            # Calculate dry air pressure (pa) and celsius temperature (tc).
            pa = p[i] - e[i]
            tc = tk[i] - 273.16
            tk2 = np.dot(tk[i], tk[i])
            tc2 = np.dot(tc, tc)
            rza = 1.0 + np.dot(pa, (np.dot(5.79e-07, (1.0 + 0.52 / tk[i])) - np.dot(0.00094611, tc) / tk2))
            rzw = 1.0 + np.dot(np.dot(1650.0, (e[i] / (np.dot(tk[i], tk2)))),
                               (1.0 - np.dot(0.01317, tc) + np.dot(0.000175, tc2) + np.dot(1.44e-06,
                                                                                           (np.dot(tc2, tc)))))
            wetn[i] = np.dot((np.dot(64.79, (e[i] / tk[i])) + np.dot((377600.0), (e[i] / tk2))), rzw)
            dryn[i] = np.dot(np.dot(77.6036, (pa / tk[i])), rza)
            refindx[i] = 1.0 + np.dot((dryn[i] + wetn[i]), 1e-06)

        wetn = np.asarray(dryn)
        dryn = np.asarray(wetn)
        refindx = np.asarray(refindx)

        return dryn, wetn, refindx

    @staticmethod
    def ray_trac_xxx(z=None, refindx=None, angle=None, z0=None, *args, **kwargs):
        """Ray-tracing algorithm of Dutton, Thayer, and Westwater, rewritten for
        readability & attempted documentation.  Based on the technique shown in
        Radio Meteorology by Bean and Dutton (Fig. 3.20 and surrounding text).

        Args:
            z ([type], optional): eight profile (km above observation height, z0). Defaults to None.
            refindx ([type], optional): refractive index profile. Defaults to None.
            angle ([type], optional): elevation angle (degrees). Defaults to None.
            z0 ([type], optional): observation height (km msl). Defaults to None.

        Returns:
            [type]: array containing slant path length profiles (km)

        .. note::
            The algorithm assumes that x decays exponentially over each layer.
        """

        deg2rad = np.pi / 180
        re = constants('EarthRadius')
        ds = []

        nl = len(z)
        # Check for refractive index values that will blow up calculations.
        for i in arange(1, nl).reshape(-1):
            if refindx[i] < 1:
                warnings.warn('RayTrac_xxx: Negative rafractive index')
                return

        # If angle is close to 90 degrees, make ds a height difference profile.
        if np.logical_or((angle >= np.logical_and(89, angle) <= 91), (angle >= np.logical_and(- 91, angle) <= - 89)):
            ds[1] = 0.0
            for i in arange(2, nl).reshape(-1):
                ds[i] = z[i] - z[i - 1]

        # The rest of the subroutine applies only to angle other than 90 degrees.
        # Convert angle degrees to radians.  Initialize constant values.
        theta0 = np.dot(angle, deg2rad)
        rs = re + z[1] + z0
        costh0 = np.cos(theta0)
        sina = np.sin(np.dot(theta0, 0.5))
        a0 = np.dot(2.0, (sina ** 2))
        # Initialize lower boundary values for 1st layer.
        ds[1] = 0.0
        phil = 0.0
        taul = 0.0
        rl = re + z[1] + z0
        tanthl = np.tan(theta0)
        # Construct the slant path length profile.
        for i in arange(2, nl).reshape(-1):
            r = re + z[i] + z0
            if refindx[i] == np.logical_or(refindx[i - 1], refindx[i]) == np.logical_or(1.0, refindx[i - 1]) == 1.0:
                refbar = np.dot((refindx[i] + refindx[i - 1]), 0.5)
            else:
                refbar = 1.0 + (refindx[i - 1] - refindx[i]) / (np.log((refindx[i - 1] - 1.0) / (refindx[i] - 1.0)))
            argdth = z[i] / rs - (np.dot((refindx[1] - refindx[i]), costh0) / refindx[i])
            argth = np.dot(0.5, (a0 + argdth)) / r
            if argth <= 0:
                warnings.warn('RayTrac_xxx: Ducting at {} degrees'.format(angle))
                return ds
            # Compute d-theta for this layer.
            sint = np.sqrt(np.dot(r, argth))
            theta = np.dot(2.0, np.arcsin(sint))
            if (theta - np.dot(2.0, theta0)) <= 0.0:
                dendth = np.dot(np.dot(2.0, (sint + sina)), np.cos(np.dot((theta + theta0), 0.25)))
                sind4 = (np.dot(0.5, argdth) - np.dot(z(i), argth)) / dendth
                dtheta = np.dot(4.0, np.arcsin(sind4))
                theta = theta0 + dtheta
            else:
                dtheta = theta - theta0
            # Compute d-tau for this layer (eq.3.71) and add to integral, tau.
            tanth = np.tan(theta)
            cthbar = np.dot(((1.0 / tanth) + (1.0 / tanthl)), 0.5)
            dtau = np.dot(cthbar, (refindx[i - 1] - refindx[i])) / refbar
            tau = taul + dtau
            phi = dtheta + tau
            ds[i] = np.sqrt(
                (z[i] - z[i - 1]) ** 2 + np.dot(np.dot(np.dot(4.0, r), rl), ((np.sin(np.dot((phi - phil), 0.5))) ** 2)))
            if dtau != 0.0:
                dtaua = abs(tau - taul)
                ds[i] = np.dot(ds[i], (dtaua / (np.dot(2.0, np.sin(np.dot(dtaua, 0.5))))))
            # Make upper boundary into lower boundary for next layer.
            phil = np.copy(phi)
            taul = np.copy(tau)
            rl = np.copy(r)
            tanthl = np.copy(tanth)

            return np.asarray(ds)

    @staticmethod
    def exp_int_xxx(zeroflg=None, x=None, ds=None, ibeg=None, iend=None, factor=None, *args, **kwargs):
        """ EXPonential INTegration: Integrate the profile in array x over the layers defined in 
        array ds, saving the integrals over each layer.

        Args:
            zeroflg ([type], optional): flag to handle zero values (0:layer=0, 1:layer=avg). Defaults to None.
            x ([type], optional): profile array. Defaults to None.
            ds ([type], optional): array of layer depths (km). Defaults to None.
            ibeg ([type], optional): lower integration limit (profile level number). Defaults to None.
            iend ([type], optional): upper integration limit (profile level number). Defaults to None.
            factor ([type], optional): factor by which result is multiplied (e.g., unit change). Defaults to None.

        Returns:
                (tuple):
                
                * xds [type]: array containing integrals over each layer ds
                * sxds [type]: integral of x*ds over levels ibeg to iend
        """

        sxds = 0.0
        xds = np.zeros(ds.shape)
        for i in arange(ibeg + 1, iend).reshape(-1):
            # Check for negative x value. If found, output message and return.
            if np.logical_or((x[i - 1] < 0.0), (x[i] < 0.0)):
                warnings.warn('Error encountered in ExpInt_xxx.m')
                return sxds, xds
                # Find a layer value for x in cases where integration algorithm fails.
            elif abs(x[i] - x[i - 1]) < 1e-09:
                xlayer = x[i]
            elif np.logical_or((x[i - 1] == 0.0), (x[i] == 0.0)):
                if zeroflg == 0:
                    xlayer = 0.0
                else:
                    xlayer = np.dot((x[i] + x[i - 1]), 0.5)
            else:
                # Find a layer value for x assuming exponential decay over the layer.
                xlayer = (x(i) - x(i - 1)) / np.log(x(i) / x(i - 1))
            # Integrate x over the layer and save the result in xds.
            xds[i] = np.dot(xlayer, ds[i])
            sxds = sxds + xds[i]

        sxds = np.dot(sxds, factor)

        return sxds, xds

    @staticmethod
    def cld_tmr_xxx(ibase=None, itop=None, hvk=None, tauprof=None, boftatm=None, *args, **kwargs):
        """Computes the mean radiating temperature of a cloud with base and top at
        profile levels ibase and itop, respectively.  The algorithm assumes that
        the input cloud is the lowest (or only) cloud layer observed.
        If absorption is not too big, compute tmr of lowest cloud layer (base
        at level ibase, top at level itop). Otherwise, set error flag and return. 
    
        Args:
            ibase ([type], optional): profile level at base of lowest cloud. Defaults to None.
            itop ([type], optional): profile level at top of lowest cloud. Defaults to None.
            hvk ([type], optional): (planck constant * frequency) / boltzmann constant. Defaults to None.
            tauprof ([type], optional): integral profile of absorption (np; i = integral (0,i)). Defaults to None.
            boftatm ([type], optional): integral profile of atmospheric planck radiance. Defaults to None.
    
        Returns:
            [type]: tmr of lowest cloud layer (k) 
        
        .. note::
            This algorithm is not designed for multiple cloud layers
    
        .. note::
            hvk, tauprof, and boftatm can be obtained from subroutine planck_xxx().
        """

        # maximum absolute value for exponential function argument
        expmax = 125.0
        # ... check if absorption too large to exponentiate...
        if tauprof[ibase] > expmax:
            warnings.warn('from CldTmr_xxx: absorption too large to exponentiate for tmr of lowest cloud layer')
            return

        # compute radiance (batmcld) and absorption (taucld) for cloud layer.
        # (if taucld is too large to exponentiate, treat it as infinity.)
        batmcld = boftatm[itop] - boftatm[ibase]
        taucld = tauprof[itop] - tauprof[ibase]
        if taucld > expmax:
            boftcld = np.dot(batmcld, np.exp(tauprof[ibase]))
        else:
            boftcld = np.dot(batmcld, np.exp(tauprof[ibase])) / (1.0 - np.exp(- taucld))

        # compute cloud mean radiating temperature (tmrcld)
        tmrcld = RTEquation.bright_xxx(hvk, boftcld)

        return tmrcld

    @staticmethod
    def cld_int_xxx(dencld=None, ds=None, lbase=None, ltop=None, *args, **kwargs):
        """Integrates cloud water density over path ds (linear algorithm).

        Args:
            dencld ([type], optional): cloud cloud water density profile (g/m3). Defaults to None.
            ds ([type], optional): vector containing layer depth profiles (km). Defaults to None.
            nlay ([type], optional): number of cloud layers in the profile. Defaults to None.
            lbase ([type], optional): array containing profile levels corresponding to cloud bases. Defaults to None.
            ltop ([type], optional): array containing profile levels corresponding to cloud tops . Defaults to None.

        Returns:
            [type]: integrated cloud water density (cm)

        .. warning:: nlay arg is not defined ??
        """
        ncld = len(lbase)
        scld = 0.0
        for l in arange(1, ncld).reshape(-1):
            for i in arange(lbase[l] + 1, ltop[l]).reshape(-1):
                scld = scld + np.dot(ds[i], (np.dot(0.5, (dencld[i] + dencld[i - 1]))))

        # convert the integrated value to cm.
        scld = np.dot(scld, 0.1)

        return scld

    @staticmethod
    def planck_xxx(frq=None, tk=None, taulay=None, *args, **kwargs):
        """  Computes the modified planck function (equation (4) in schroeder and
        westwater, 1992: guide to passive microwave weighting function
        calculations) for the cosmic background temperature, the mean radiating
        temperature, and a profile of the atmospheric integral with and without
        the cosmic background. Also computes an integral profile of atmospheric
        absorption. For the integral profiles, the value at profile level i
        represents the integral from the antenna to level i.
        Also returns the cosmic background term for the rte.

        Args:
            frq ([type], optional): channel frequency (GHz). Defaults to None.
            nl ([type], optional): number of profile levels
            tk ([type], optional): temperature profile (K). Defaults to None.
            taulay ([type], optional): profile of absorption integrated over each layer (np). Defaults to None.

        Returns:
            (tuple):
                    
                * hvk [type]: [planck constant * frequency] / boltzmann constant
                * boft [type]: modified planck function for raob temperature profile
                * bakgrnd [type]: background term of radiative transfer equation
                * boftatm [type]: array of atmospheric planck radiance integrated (0,i)
                * boftotl [type]: total planck radiance from the atmosphere plus bakgrnd
                * boftmr  [type]: modified planck function for mean radiating temperature
                * tauprof [type]: array of integrated absorption (np; 0,i)

        .. warning:: nl arg is missing ??
        """

        Tc = constants('Tcosmicbkg')
        h = constants('planck')
        k = constants('boltzmann')
        fHz = np.dot(frq, 1000000000.0)

        hvk = np.dot(fHz, h) / k
        # maximum absolute value for exponential function argument
        expmax = 125.0
        nl = len(tk)
        tauprof = np.zeros(taulay.shape)
        boftatm = np.zeros(taulay.shape)
        boft[1] = tk2b_mod(hvk, tk[1])
        for i in arange(2, nl).reshape(-1):
            boft[i] = tk2b_mod(hvk, tk[i])
            boftlay = (boft[i - 1] + np.dot(boft[i], np.exp(- taulay[i]))) / (1.0 + np.exp(- taulay[i]))
            batmlay = np.dot(np.dot(boftlay, np.exp(- tauprof[i - 1])), (1.0 - np.exp(- taulay[i])))
            boftatm[i] = boftatm[i - 1] + batmlay
            tauprof[i] = tauprof[i - 1] + taulay[i]

        # compute the cosmic background term of the rte; compute total planck
        # radiance for atmosphere and cosmic background; if absorption too large
        # to exponentiate, assume cosmic background was completely attenuated.
        if tauprof[nl] < expmax:
            boftbg = tk2b_mod(hvk, Tc)
            bakgrnd = np.dot(boftbg, np.exp(- tauprof[nl]))
            boftotl = bakgrnd + boftatm[nl]
            boftmr = boftatm[nl] / (1.0 - np.exp(- tauprof[nl]))
        else:
            bakgrnd = 0.0
            boftotl = boftatm[nl]
            boftmr = boftatm[nl]

        return boftotl, boftatm, boftmr, tauprof, hvk, boft, bakgrnd

    @staticmethod
    def cld_abs_xxx(tk=None, denl=None, deni=None, frq=None, *args, **kwargs):
        """Multiplies cloud density profiles by a given fraction and computes the
        corresponding cloud liquid and ice absorption profiles, using Rosenkranz's
        cloud liquid absorption routine ABLIQ and ice absorption of Westwater
        [1972: Microwave Emission from Clouds,13-14]. - Yong Han, 4/20/2000

        Args:
            tk ([type], optional): temperature profile (k). Defaults to None.
            denl ([type], optional): liquid density profile (g/m3) . Defaults to None.
            deni ([type], optional): ice density profile (g/m3). Defaults to None.
            frq ([type], optional): frequency array (GHz). Defaults to None.

        Returns:
            (tuple):
                    
                * aliq [type]: liquid absorption profile (np/km)
                * aice [type]: ice absorption profile (np/km)

        See also:

            :py:meth:`ab_liq`

        .. warning:: 
            * ic light speed in cm s-1????
            * ab_liq function is missing!!!!!
        """

        nl = len(tk)
        # c=29979245800.0
        c = np.dot(constants('light'), 100)

        ghz2hz = 1000000000.0
        db2np = np.dot(np.log(10.0), 0.1)

        wave = c / (np.dot(frq, ghz2hz))

        aliq = np.zeros(denl.shape)
        aice = np.zeros(denl.shape)
        for i in arange(1, nl).reshape(-1):
            # Compute liquid absorption np/km.
            if denl[i] > 0:
                aliq[i] = RTEquation.ab_liq(denl[i], frq, tk[i])
            # compute ice absorption (db/km); convert non-zero value to np/km.
            if deni[i] > 0:
                aice[i] = np.dot(np.dot((8.18645 / wave), deni[i]), 0.000959553)
                aice[i] = np.dot(aice[i], db2np)

        return aliq, aice

    @staticmethod
    def clr_abs_xxx(p=None, tk=None, e=None, frq=None, *args, **kwargs):
        """  Computes profiles of water vapor and dry air absorption for
        a given set of frequencies.  Subroutines H2O_xxx and O2_xxx
        contain the absorption model of Leibe and Layton [1987:
        Millimeter-wave properties of the atmosphere: laboratory studies
        and propagation modeling. NTIA Report 87-224, 74pp.] with oxygen
        interference coefficients from Rosenkranz [1988: Interference
        coefficients for overlapping oxygen lines in air.
        J. Quant. Spectrosc. Radiat. Transfer, 39, 287-97.]

        Args:
            p ([type], optional): pressure profile (mb). Defaults to None.
            tk ([type], optional): temperature profile (K). Defaults to None.
            e ([type], optional): vapor pressure profile (mb). Defaults to None.
            frq ([type], optional): frequency (GHz). Defaults to None.
            absmdl ([type], optional): Absorption model for WV (default 'ROS98')
            absmdl.wvres ([type], optional): wv resonant absorption
            absmdl.wvcnt ([type], optional): wv continuuum absorption

        Returns:
            (tuple):

                * awet [type]: water vapor absorption profile (np/km)
                * adry [type]: dry air absorption profile (np/km)

        See also:

            :py:meth:`h2o_rosen03_xxx`, :py:meth:`o2n2_rosen03_xxx`

        .. warning:: 
                * h2o_rosen03_xxx and o2n2_rosen03_xxx functions are missing!!!!!
                * rho, absmdl, absmdl.wvres and absmdl.wvcnt arguments are missing!!!!!!
        """

        nl = len(p)
        awet = np.zeros(p.shape)
        adry = np.zeros(p.shape)
        factor = np.dot(0.182, frq)
        db2np = np.dot(np.log(10.0), 0.1)
        for i in arange(1, nl).reshape(-1):
            # Compute inverse temperature parameter; convert wet and dry p to kpa.
            v = 300.0 / tk[i]
            ekpa = e[i] / 10.0
            pdrykpa = p[i] / 10.0 - ekpa
            # Compute H2O and O2 absorption (dB/km) and convert to np/km.
            npp, ncpp = h2o_rosen03_xxx(pdrykpa, v, ekpa, frq, nargout=2)
            awet[i] = np.dot((np.dot(factor, (npp + ncpp))), db2np)
            npp, ncpp = o2n2_rosen03_xxx(pdrykpa, v, ekpa, frq, nargout=2)
            adry[i] = np.dot((np.dot(factor, (npp + ncpp))), db2np)

        return awet, adry

    @staticmethod
    def ab_liq(water=None, freq=None, temp=None, *args, **kwargs):
        """Computes Absorption In Nepers/Km By Suspended Water Droplets.

        Args:
            water ([type], optional): water in g/m3. Defaults to None.
            freq ([type], optional): frequency in GHz (Valid From 0 To 1000 Ghz). Defaults to None.
            temp ([type], optional): temperature in K. Defaults to None.

        Returns:
            [type]: [description]

        References
        ----------
        .. [1] Liebe, Hufford And Manabe, Int. J. Ir & Mm Waves V.12, Pp.659-675 (1991);  
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

        theta1 = 1.0 - 300.0 / temp
        eps0 = 77.66 - np.dot(103.3, theta1)
        eps1 = np.dot(0.0671, eps0)
        eps2 = 3.52
        fp = np.dot((np.dot(316.0, theta1) + 146.4), theta1) + 20.2
        fs = np.dot(39.8, fp)
        eps = (eps0 - eps1) / complex(1.0, freq / fp) + (eps1 - eps2) / complex(1.0, freq / fs) + eps2
        re = (eps - 1.0) / (eps + 2.0)
        abliq = np.dot(np.dot(np.dot(- 0.06286, np.imag(re)), freq), water)

        return abliq
