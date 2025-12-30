import math
from abc import ABC, abstractmethod
from layers_edx.element import Composition, Element
from layers_edx.units import FromSI, ToSI
from layers_edx.detector.eds_detector import EDSDetector
from layers_edx.spectrum.base_spectrum import BaseSpectrum
from layers_edx.material_properties.mac import MassAbsorptionCoefficient
from layers_edx.roi import RegionOfInterestSet
from layers_edx.xrt import XRayTransitionSet
from layers_edx.material_properties.mip import MeanIonizationPotential


class BremsstrahlungAnalytic(ABC):
    def __init__(
        self, composition: Composition, beam_energy: float, take_off_angle: float
    ):
        """Initializes the algorithm.

        :param composition: A Composition object.
        :param beam_energy: The excitation energy in J.
        :param take_off_angle: The take-off angle of the detector in rad.
        """
        self.composition = composition
        self.mac = MassAbsorptionCoefficient()
        self.e0_keV = FromSI.kev(beam_energy)
        self.take_off_angle = take_off_angle

    @abstractmethod
    def compute(self, energy: float) -> float:
        """
        Computes the emitted bremsstrahlung intensity at the specified photon `energy`.

        :param energy: The photon energy in J.
        """

    def to_detector(self, detector: EDSDetector, flux: float):
        """
        Compute the bremsstrahlung spectrum as measured by the specified `detector`
        at the specified beam `flux` (nA*s).
        """
        f = detector.calibration.channel_width / 10.0
        for channel in range(detector.properties.channel_count):
            energy = ToSI.ev(detector.spectrum.average_energy_from_channel(channel))
            detector.add_event(energy, max(0.0, self.compute(energy)) * flux * f)

    def fit_background(
        self,
        detector: EDSDetector,
        spectrum: BaseSpectrum,
        intervals: list[tuple[int, int]],
    ):
        spectrum.apply_zero_peak_discriminator()
        detector.reset()
        self.to_detector(detector, 1.0)
        brems = detector.scaled_spectrum(1.0)
        ss, sb = 0.0, 0.0
        for ii in intervals:
            for channel in range(*ii):
                s = spectrum.counts(channel)
                b = brems.counts(channel)
                if s > 0.0:
                    ss += s
                    sb += b
        return brems.copy().scale(ss / sb)

    def fit_background_composition(
        self, detector: EDSDetector, spectrum: BaseSpectrum, composition: Composition
    ):
        """
        Automatically select intervals based on the specified composition
        and then fit a background to the specified spectrum.
        """
        spectrum.apply_zero_peak_discriminator()
        dlm = detector.calibration.model
        e0 = ToSI.kev(self.e0_keV)
        first_ch = spectrum.smallest_nonzero_channel
        e_min = ToSI.ev(min(100.0, spectrum.min_energy_from_channel(first_ch)))
        roi_set = RegionOfInterestSet(dlm, 0.001, 0.0, 0.0)
        for element in composition.elements:
            roi_set.add_xrt_set(XRayTransitionSet(element, e_min, e0))

        tmp: list[tuple[int, int]] = []
        min_ch = spectrum.channel_from_energy(FromSI.ev(e_min))
        for roi in roi_set.rois:
            max_ch = spectrum.channel_from_energy(FromSI.ev(roi.low_energy))
            if max_ch > min_ch:
                tmp.append((min_ch, max_ch))
            min_ch = spectrum.channel_from_energy(FromSI.ev(roi.high_energy))
        max_ch = spectrum.channel_from_energy(FromSI.ev(e0))
        tmp.append((min_ch, max_ch))

        intervals: list[tuple[int, int]] = []
        if first_ch < spectrum.channel_count // 10:
            intervals.append((first_ch, first_ch + 4))
        width = 20
        for i in range(8):
            if len(intervals) > 4:
                break
            j = 2 * i if i < 4 else 2 * i + 1
            min_ch = spectrum.channel_from_energy(j * 2000.0)
            max_ch = spectrum.bound(spectrum.channel_from_energy((j + 1) * 2000.0))
            if (
                ToSI.ev(spectrum.max_energy_from_channel(min_ch)) > e0
                or min_ch >= spectrum.channel_count
            ):
                break
            best = None
            for ii in tmp:
                if ii[1] > min_ch and ii[0] < max_ch:
                    start = max(ii[0], min_ch)
                    end = min(ii[1], max_ch)
                    if best is None or end - start > best[1] - best[0]:
                        best = (start, end)
            if best is not None:
                if best[1] - best[0] > width:
                    a = sum(best) // 2
                    best = (a - (width // 2), a + (width // 2))
                intervals.append(best)

        self.fit_background(detector, spectrum, intervals)


class Riveros1993:
    @staticmethod
    def elastic_x_sec(z: int, e0k: float) -> float:
        zz = float(z)
        aa = 3.4e-3 * math.pow(zz, 0.67) / e0k
        mc2 = 511.0
        return (
            5.21e-21
            * ((zz / e0k) * (zz / e0k))
            * (4 * math.pi / (aa * (1.0 + aa)))
            * math.pow(((e0k + mc2) / (e0k + 2.0 * mc2)), 2)
        )

    @classmethod
    def elastic_fraction(cls, elm: Element, comp: Composition, e0k: float) -> float:
        density = sum(
            [
                comp.atomic_fractions[el] * cls.elastic_x_sec(el.atomic_number, e0k)
                for el in comp.elements
            ]
        )
        return (
            comp.atomic_fractions[elm]
            * cls.elastic_x_sec(elm.atomic_number, e0k)
            / density
        )

    @classmethod
    def compute_etam(cls, comp: Composition, e0k: float) -> float:
        return sum([cls.elastic_fraction(elm, comp, e0k) for elm in comp.elements])

    def __init__(
        self, composition: Composition, beam_energy: float, take_off_angle: float
    ):
        self.composition = composition
        self.beam_energy = beam_energy
        self.take_off_angle = take_off_angle
        self.etam = self.compute_etam(composition, FromSI.kev(beam_energy))

    def alphaz(self, elm: Element, eck: float) -> float:
        e0k = FromSI.kev(self.beam_energy)
        j = ToSI.kev(MeanIonizationPotential.Berger83.compute(elm))
        return (
            (2.14e5 * math.pow(elm.atomic_number, 1.16))
            / (elm.atomic_weight * math.pow(e0k, 1.25))
            * math.sqrt(math.log(1.166 * e0k / j) / (e0k - eck))
        )

    def betaz(self, elm: Element, eck: float) -> float:
        e0k = FromSI.kev(self.beam_energy)
        return (1.1e5 * math.pow(elm.atomic_number, 1.5)) / (
            (e0k - eck) * elm.atomic_weight
        )

    def chi(self, e: float):
        return MassAbsorptionCoefficient.compute_composition(
            self.composition, e
        ) / math.sin(self.take_off_angle)

    def compute(self, e: float) -> float:
        ek = FromSI.kev(e)
        u0 = self.beam_energy / e
        comp = self.composition
        phi0 = 1.0 + (self.etam * u0 * math.log(u0)) / (u0 - 1.0)
        gamma = (1.0 + self.etam) * (u0 * math.log(u0)) / (u0 - 1.0)
        alpha = sum([f * self.alphaz(e, ek) for e, f in comp.weight_fractions.items()])
        beta = sum([f * self.betaz(e, ek) for e, f in comp.weight_fractions.items()])
        xm = FromSI.cm2pg(self.chi(e))
        ff = xm / (2.0 * alpha)
        gg = (beta + xm) / (2.0 * alpha)
        if gg < 22.3:
            fchi = (
                math.sqrt(math.pi)
                * (
                    math.exp(ff * ff) * gamma * alpha * (1.0 - math.erf(ff))
                    - math.exp(gg * gg) * (gamma - phi0) * alpha * (1.0 - math.erf(gg))
                )
            ) / (2.0 * alpha * alpha)
            f = (
                math.sqrt(math.pi)
                * (gamma - math.exp(gg * gg) * (gamma - phi0) * math.erfc(gg))
            ) / (2.0 * alpha)
        else:
            fchi = 0.0
            f = 1.0
        return fchi / f


class Castellano2004aBremsstrahlung(BremsstrahlungAnalytic):
    def compute(self, energy: float) -> float:
        result = 0.0
        ekev = FromSI.kev(energy)
        if 0.05 < ekev < self.e0_keV:
            for element, af in self.composition.atomic_fractions.items():
                z = element.atomic_number
                result += (
                    af
                    * math.sqrt(z)
                    * (self.e0_keV - ekev)
                    / ekev
                    * (
                        -73.90
                        - 1.2446 * ekev
                        + 36.502 * math.log(z)
                        + (148.5 * math.pow(self.e0_keV, 0.1239) / z)
                        * (1.0 + (-0.006624 + 0.0002906 * self.e0_keV) * z / ekev)
                    )
                )
            result *= Riveros1993(
                self.composition, ToSI.kev(self.e0_keV), self.take_off_angle
            ).compute(energy)
        return result
