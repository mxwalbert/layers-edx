from __future__ import annotations
from typing import Tuple
from layers_edx import BASE_PATH


def get_physical_constant(name: str, unit: bool = False) -> float | Tuple[float, str] | None:
    with open(f'{BASE_PATH}/resources/CODATA2018.txt') as file:
        for line in file.readlines():
            if name == line[:len(name)]:
                value = float(line[60:].split('  ')[0].replace('...', '').replace(' ', ''))
                return (value, line[110:].replace('\n', '')) if unit else value


class PhysicalConstants:

    ElementaryCharge: float = get_physical_constant('elementary charge')
    AMU: float = get_physical_constant('unified atomic mass unit')
    BohrRadius: float = get_physical_constant('Bohr radius')
    ElectronRestMass: float = get_physical_constant('electron mass energy equivalent')


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
