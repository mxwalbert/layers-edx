import math
from layers_edx.correction import PhiRhoZ
from layers_edx.atomic_shell import AtomicShell
from layers_edx.element import Composition
from layers_edx.material_properties.bf import BackscatterFactor
from layers_edx.material_properties.ics import ProportionalIonizationCrossSection
from layers_edx.material_properties.si import SurfaceIonization
from layers_edx.material_properties.sp import StoppingPower
from layers_edx.spectrum.spectrum_properties import SpectrumProperties
from layers_edx.units import FromSI, ToSI
from layers_edx.xrt import XRayTransition


class XPP(PhiRhoZ):
    """
    Implements the XPP algorithm as described in
    Pouchou & Pichoir in Electron Probe Quantitation.
    """

    bf = BackscatterFactor
    si = SurfaceIonization
    sp = StoppingPower
    pics = ProportionalIonizationCrossSection

    def __init__(
        self,
        composition: Composition,
        shell: AtomicShell,
        properties: SpectrumProperties,
    ):
        super().__init__(composition, shell, properties)
        f = (
            self.bf.compute(self.composition, self.shell, self.beam_energy)
            * FromSI.gpcm2kev(
                self.sp.compute_inv(self.composition, self.shell, self.beam_energy)
            )
            / self.pics.compute_family(shell, self.beam_energy)
        )
        phi0 = self.si.compute(self.composition, self.shell, self.beam_energy)
        mean_zb = self.mean_atomic_number
        u0 = self.beam_energy / self.shell.edge_energy
        x = 1.0 + (1.3 * math.log(mean_zb))
        y = 0.2 + (mean_zb / 200.0)
        r_bar = f / (
            1.0
            + (
                (x * math.log(1.0 + (y * (1.0 - math.pow(u0, -0.42)))))
                / math.log(1.0 + y)
            )
        )
        if f / r_bar < phi0:
            r_bar = f / phi0
        g = (
            0.22
            * math.log(4.0 * mean_zb)
            * (1.0 - (2.0 * math.exp((mean_zb * (1.0 - u0)) / 15.0)))
        )
        h = 1.0 - ((10.0 * (1.0 - (1.0 / (1.0 + (u0 / 10.0))))) / (mean_zb * mean_zb))
        gh4 = g * h**4
        little_b = (
            math.sqrt(2.0) * (1.0 + math.sqrt(1.0 - ((r_bar * phi0) / f)))
        ) / r_bar
        limit = 0.9 * little_b * r_bar**2 * (little_b - ((2.0 * phi0) / f))
        gh4 = limit if gh4 > limit else gh4
        p = (gh4 * f) / r_bar**2
        little_a = (p + (little_b * ((2.0 * phi0) - (little_b * f)))) / (
            (little_b * f * (2.0 - (little_b * r_bar))) - phi0
        )
        eps = (little_a - little_b) / little_b
        if abs(eps) < 1e-6:
            eps = 1e-6
            little_a = little_b * (1.0 + eps)
        big_b = (
            (little_b**2 * f * (1.0 + eps)) - p - (phi0 * little_b * (2.0 + eps))
        ) / eps
        big_a = ((((big_b / little_b) + phi0) - (little_b * f)) * (1 + eps)) / eps
        self.f = f
        self.phi0 = phi0
        self.little_b = little_b
        self.little_a = little_a
        self.eps = eps
        self.big_b = big_b
        self.big_a = big_a

    @property
    def mean_atomic_number(self) -> float:
        return (
            sum(
                [
                    f * math.sqrt(e.atomic_number)
                    for e, f in self.composition.weight_fractions.items()
                ]
            )
            ** 2
        )

    def compute_za_correction(self, xrt: XRayTransition) -> float:
        chi = FromSI.cm2pg(self.chi(xrt))
        return ToSI.gpcm2(
            (
                (self.phi0 + (self.big_b / (self.little_b + chi)))
                - (
                    (self.big_a * self.little_a * self.eps)
                    / ((self.little_b * (1.0 + self.eps)) + chi)
                )
            )
            / (self.little_b + chi)
        )

    def generated(self, xrt: XRayTransition) -> float:
        return ToSI.gpcm2(self.f)

    def compute_curve(self, rho_z: float) -> float:
        if rho_z <= 0.0:
            return 0.0
        rho_z = FromSI.gpcm2(rho_z)
        return (self.big_a * math.exp(-self.little_a * rho_z)) + (
            (((self.big_b * rho_z) + self.phi0) - self.big_a)
            * math.exp(-self.little_b * rho_z)
        )
