import bisect
import math
from typing import Protocol
from layers_edx import read_csv, llf
from layers_edx.element import Element, Composition
from layers_edx.units import ToSI


class MassAbsorptionCoefficient:
    """
    Provides functionality to compute the mass absorption coefficient (MAC) for a given element
    or material composition at a specified photon energy.
    """

    class Algorithm(Protocol):
        """
        Protocol defining the interface for MAC computation algorithms.
        """

        @classmethod
        def compute(cls, element: Element, energy: float) -> float:
            """
            Method for computing the mass absorption coefficient for a single element at the given energy.

            Args:
                element (Element): The element for which the coefficient is computed.
                energy (float): The energy of the x-ray beam (J).

            Returns:
                float: The mass absorption coefficient (m^2/kg).
            """
            ...

    class Chantler2005(Algorithm):

        data: llf = [list(x) for x in zip(*read_csv('FFastMAC'))]
        ENERGY: llf = [[]] + [[ToSI.kev(value) for value in x[:x.index(0.0)]] for x in data[0::2]]
        MAC: llf = [[]] + [[ToSI.cm2pg(value) for value in x[:x.index(0.0)]] for x in data[1::2]]

        @classmethod
        def compute(cls, element: Element, energy: float) -> float:
            z = element.atomic_number
            energy_idx = bisect.bisect_left(cls.ENERGY[z], energy)
            if energy_idx == len(cls.ENERGY[z]):
                return 0.0
            le, ue = cls.ENERGY[z][energy_idx - 1], cls.ENERGY[z][energy_idx]
            lm, um = cls.MAC[z][energy_idx - 1], cls.MAC[z][energy_idx]
            try:
                return math.exp(math.log(lm) + (math.log(um / lm) * (math.log(energy / le) / math.log(ue / le))))
            except ValueError:
                return 0.0

    @classmethod
    def compute(cls, element: Element, energy: float) -> float:
        """
        Computes the mass absorption coefficient for the specified element at the specified energy.

        Args:
            element (Element): The element for which the mass absorption coefficient is to be calculated.
            energy (float): The energy of the x-ray beam (J).

        Returns:
            float: The mass absorption coefficient for the specified element at the given energy (m^2/kg).
                Returns NaN if no valid value is found.
        """
        for database in [cls.Chantler2005]:
            value = database.compute(element, energy)
            if value > 0.0:
                return value
        return float('nan')

    @classmethod
    def compute_composition(cls, composition: Composition, energy: float) -> float:
        """
        Calculates the mass absorption coefficient for the specified composition at the specified energy.

        Args:
            composition (Composition): The composition of elements with their weight fractions.
            energy (float): The energy of the x-ray beam in joules (J).

        Returns:
            float: The mass absorption coefficient for the given composition at the specified energy (m^2/kg).
        """
        return sum([cls.compute(elm, energy) * frac for elm, frac in composition.raw_weight_fractions.items()])
