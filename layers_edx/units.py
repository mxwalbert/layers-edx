from __future__ import annotations

from scipy.constants import physical_constants


class PhysicalConstants:
    ElementaryCharge: float = physical_constants["elementary charge"][0]
    AMU: float = physical_constants["unified atomic mass unit"][0]
    BohrRadius: float = physical_constants["Bohr radius"][0]
    ElectronRestMass: float = physical_constants["electron mass energy equivalent"][0]


class ToSI:
    @classmethod
    def compute(cls, value: float, factor: float) -> float:
        return value * factor

    @classmethod
    def ev(cls, value: float) -> float:
        """Electronvolt."""
        return cls.compute(value, PhysicalConstants.ElementaryCharge)

    @classmethod
    def kev(cls, value: float) -> float:
        """Kilo-electronvolt."""
        return cls.compute(value, 1e3 * PhysicalConstants.ElementaryCharge)

    @classmethod
    def cm(cls, value: float) -> float:
        """Centimeter."""
        return cls.compute(value, 1e-2)

    @classmethod
    def cm2(cls, value: float) -> float:
        """Centimeter squared."""
        return cls.compute(value, 1e-4)

    @classmethod
    def mm(cls, value: float) -> float:
        """Millimeter."""
        return cls.compute(value, 1e-3)

    @classmethod
    def mm2(cls, value: float) -> float:
        """Millimeter squared."""
        return cls.compute(value, 1e-6)

    @classmethod
    def um(cls, value: float) -> float:
        """Micrometer."""
        return cls.compute(value, 1e-6)

    @classmethod
    def nm(cls, value: float) -> float:
        """Nanometer."""
        return cls.compute(value, 1e-9)

    @classmethod
    def cm2pg(cls, value: float) -> float:
        """Centimeter squared per gram."""
        return cls.compute(value, 1e-1)

    @classmethod
    def gpcm2(cls, value: float) -> float:
        """Grams per centimeter squared."""
        return cls.compute(value, 1e1)

    @classmethod
    def gpcm3(cls, value: float) -> float:
        """Grams per centimeter cubed."""
        return cls.compute(value, 1e3)

    @classmethod
    def gpcm2kev(cls, value: float) -> float:
        """Grams per centimeter squared kilo-electronvolt."""
        return cls.compute(value, 1e-2 / PhysicalConstants.ElementaryCharge)

    @classmethod
    def amu(cls, value: float) -> float:
        """Unified atomic mass unit."""
        return cls.compute(value, PhysicalConstants.AMU)


class FromSI(ToSI):
    @classmethod
    def compute(cls, value: float, factor: float) -> float:
        return value / factor
