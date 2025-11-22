import math
from typing import Protocol
from layers_edx import read_csv
from layers_edx.element import Element, Composition
from layers_edx.units import ToSI


class MeanIonizationPotential:
    """
    Provides algorithms to compute the mean ionization potential (MIP) of elements and compositions.

    The mean ionization potential is an effective average energy (J) required to ionize atoms in a material.
    """

    class Algorithm(Protocol):
        """
        Protocol defining the interface for MIP computation algorithms.
        """

        @classmethod
        def compute(cls, element: Element) -> float:
            """
            Method for computing the mean ionization potential for the specified element.

            Args:
                element (Element): The element of interest.

            Returns:
                float: The mean ionization potential (J).
            """
            ...

    class Berger83(Algorithm):

        MIP = read_csv('BergerSeltzer83', value_offset=1, row_offset=1, conversion=lambda x: ToSI.ev(x))

        @classmethod
        def compute(cls, element: Element) -> float:
            z = element.atomic_number
            if z >= len(cls.MIP):
                return 0.0
            return cls.MIP[z][0]

    @classmethod
    def compute(cls, element: Element) -> float:
        """
        Computes the mean ionization potential of an element using the default algorithm (Berger83).

        Args:
            element (Element): The element whose mean ionization potential is to be computed.

        Returns:
            float: The mean ionization potential (J). Returns NaN if no value is available.
        """
        for database in [cls.Berger83]:
            value = database.compute(element)
            if value > 0.0:
                return value
        return float('nan')

    @classmethod
    def compute_composition(cls, composition: Composition) -> float:
        """
        Computes the effective mean ionization potential for a compound or mixture.

        Args:
            composition (Composition): The composition containing weight fractions of elements.

        Returns:
            float: The effective mean ionization potential (J).
        """
        m = 0.0
        ln_j = 0.0
        for element in composition.elements:
            cz_a = composition.weight_fractions[element] * element.atomic_number / element.atomic_weight
            m += cz_a
            ln_j += cz_a * math.log(cls.compute(element))
        return math.exp(ln_j / m)
