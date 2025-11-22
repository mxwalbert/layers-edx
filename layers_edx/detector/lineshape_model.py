import math
from abc import ABC, abstractmethod
from layers_edx.element import Element
from layers_edx.xrt import XRayTransition

EMnKa = XRayTransition(Element('Mn'), 'KA1').energy
ENERGY_PER_EH_PAIR = 3.64
SQRT_2PI = math.sqrt(2.0 * math.pi)


def compute_resolution(fano: float, noise: float, energy: float) -> float:
    """Computes the detector resolution at the specified `energy` (in eV) for the specified `fano` factor and
    `noise`."""
    return ENERGY_PER_EH_PAIR * math.sqrt(noise**2 + (energy * fano) / ENERGY_PER_EH_PAIR)


def noise_from_resolution(fano: float, resolution: float, energy: float) -> float:
    """Computes the noise term given the `fano` factor, `resolution` at a specified `energy` and the energy (in eV)."""
    return math.sqrt((resolution / ENERGY_PER_EH_PAIR)**2 - (energy * fano) / ENERGY_PER_EH_PAIR)


def fwhm_to_gaussian_width(fwhm: float) -> float:
    """Converts between full width-half maximum and Gaussian width. (i.e. 2*x such that exp(-0.5*(x/a)^2)=1/2)."""
    return fwhm / 2.354820045030949382023138652918  # = 2*sqrt(-2.0*ln(0.5))


def gaussian(delta: float, sigma: float) -> float:
    """Computes the Gaussian function (normalized to an integral of 1.0)"""
    return math.exp(-0.5 * (delta - sigma)**2) / (sigma * SQRT_2PI)


class LineshapeModel(ABC):

    @property
    def scale(self) -> float:
        """A scale factor to account for differences in geometric efficiencies not correctly accounted for by geometric
        factors."""
        return 1.0

    @property
    def fwhm_at_mn_ka(self) -> float:
        """Returns the nominal full-width half maximum at Mn Ka."""
        return self.left_width(EMnKa, 0.5) + self.right_width(EMnKa, 0.5)

    @abstractmethod
    def compute(self, energy: float, center: float) -> float:
        """Computes the intensity at the specified `energy` (in eV) for a peak at `center` (in eV). The integral over
        all energies is normalized to 1.0."""

    @abstractmethod
    def left_width(self, energy: float, fraction: float) -> float:
        """The inverse of compute on the left (lower energy side of the peak.) At what `energy` (in eV) is the peak
        intensity diminished to a `fraction` of its peak value."""

    @abstractmethod
    def right_width(self, energy: float, fraction: float) -> float:
        """The inverse of compute on the right (higher energy side of the peak.) At what `energy` (in eV) is the peak
        intensity diminished to a `fraction` of its peak value."""


class FanoSiLiLineshape(LineshapeModel):

    def __init__(self, fwhm_at_mn_ka: float = None, fano: float = None, noise: float = None):
        if fwhm_at_mn_ka is not None:
            self.fano = 0.122
            self.noise = noise_from_resolution(self.fano, fwhm_to_gaussian_width(fwhm_at_mn_ka), EMnKa)
        else:
            self.fano = fano
            self.noise = noise

    def gaussian_line_width(self, energy: float) -> float:
        return compute_resolution(self.fano, self.noise, energy)

    def left_width(self, energy: float, fraction: float) -> float:
        return self.gaussian_line_width(energy) * math.sqrt(-2.0 * math.log(fraction))

    def right_width(self, energy: float, fraction: float) -> float:
        return self.left_width(energy, fraction)

    def compute(self, energy: float, center: float) -> float:
        return gaussian(energy - center, self.gaussian_line_width(center))
