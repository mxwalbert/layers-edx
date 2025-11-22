import math
from layers_edx.correction import PhiRhoZ
from layers_edx.atomic_shell import AtomicShell
from layers_edx.element import Composition
from layers_edx.material_properties.bf import BackscatterFactor
from layers_edx.material_properties.ics import ProportionalIonizationCrossSection
from layers_edx.material_properties.mac import MassAbsorptionCoefficient
from layers_edx.material_properties.si import SurfaceIonization
from layers_edx.material_properties.sp import StoppingPower
from layers_edx.material_properties.er import ElectronRange
from layers_edx.spectrum.spectrum_properties import SpectrumProperties
from layers_edx.units import FromSI, ToSI
from layers_edx.xrt import XRayTransition


class PAP(PhiRhoZ):
    """Implements the PAP algorithm as described in Pouchou & Pichoir in Electron Probe Quantitation."""

    mac = MassAbsorptionCoefficient
    bf = BackscatterFactor
    si = SurfaceIonization
    sp = StoppingPower
    pics = ProportionalIonizationCrossSection
    er = ElectronRange

    def __init__(self, composition: Composition, shell: AtomicShell, properties: SpectrumProperties):
        super().__init__(composition, shell, properties)

        f = (self.bf.compute(composition, shell, self.beam_energy) * FromSI.gpcm2kev(self.sp.compute_inv(composition, shell, self.beam_energy)) / self.pics.compute_family(shell, self.beam_energy))
        self.f = f

        phi0 = self.si.compute(composition, shell, self.beam_energy)
        self.phi0 = phi0

        u0 = self.beam_energy / shell.edge_energy

        z_bar = composition.mean_atomic_number
        z_bar_n = self.log_mean_atomic_number
        beta = 40.0 / z_bar
        q0 = 1.0 - (0.535 * math.exp(-math.pow(21.0 / z_bar_n, 1.2))) - (2.5e-4 * math.pow(z_bar_n / 20.0, 3.5))
        q = q0 + ((1.0 - q0) * math.exp((1.0 - u0) / beta))
        d = 1.0 + (1.0 / math.pow(u0, math.pow(z_bar, 0.45)))

        rx = q * d * FromSI.gpcm2(self.er.compute(composition, shell, self.beam_energy))
        self.rx = rx

        g1 = 0.11 + (0.41 * math.exp(-math.pow(z_bar / 12.75, 0.75)))
        g2 = 1.0 - math.exp(-math.pow(u0 - 1.0, 0.35) / 1.19)
        g3 = 1.0 - math.exp(((0.5 - u0) * math.pow(z_bar, 0.4)) / 4.0)

        rm = g1 * g2 * g3 * rx
        self.rm = rm

        tt = f - ((phi0 * rx) / 3.0)
        dr = rx - rm
        d = dr * tt * ((dr * f) - (phi0 * rx * (rm + (rx / 3.0))))

        if d > 0.0:
            rc = 1.5 * ((tt / phi0) - (math.sqrt(d) / (phi0 * dr)))
        else:
            rm = (rx * (f - ((phi0 * rx) / 3.0))) / (f + (phi0 * rx))
            rc = (3.0 * rm * (f + (phi0 * rx))) / (2.0 * phi0 * rx)
        self.rc = rc

        self.a1 = phi0 / ((rm * (rc + rx)) - (rx * rc))
        self.a2 = (self.a1 * (rc - rm)) / (rc - rx)

    @property
    def mean_atomic_number(self) -> float:
        return sum([f * math.sqrt(e.atomic_number) for e, f in self.composition.weight_fractions.items()]) ** 2

    @property
    def log_mean_atomic_number(self) -> float:
        return math.exp(sum([f * math.log(e.atomic_number) for e, f in self.composition.weight_fractions.items()]))

    def compute_za_correction(self, xrt: XRayTransition) -> float:
        chi = FromSI.cm2pg(self.chi(xrt))
        chi2 = chi * chi
        f1 = (self.a1 / chi) * (((((self.rc - self.rm) * (self.rx - self.rc - (2.0 / chi))) - (2.0 / chi2)) * math.exp(-chi * self.rc)) - ((self.rc - self.rm) * self.rx) + (self.rm * (self.rc - (2.0 / chi))) + (2.0 / chi2))
        f2 = (self.a2 / chi) * (((self.rx - self.rc) * (self.rx - self.rc - (2.0 / chi))) + (2.0 / chi2)) * math.exp(-chi * self.rx)
        return ToSI.gpcm2(f1 + f2)

    def compute_curve(self, rho_z: float) -> float:
        if rho_z <= 0.0:
            return 0.0
        rho_z = FromSI.gpcm2(rho_z)
        if rho_z < self.rc:
            b1 = self.phi0 - (self.a1 * self.rm * self.rm)
            return self.a1 * (rho_z - self.rm) ** 2 + b1
        elif rho_z < self.rx:
            return self.a2 * (rho_z - self.rx) ** 2
        return 0.0
