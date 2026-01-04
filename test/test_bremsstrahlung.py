import math
from layers_edx.bremsstrahlung import Castellano2004aBremsstrahlung, Riveros1993
from layers_edx.element import Element, Composition
from layers_edx.units import ToSI


def test_riveros_compute():
    si = Element("Si")
    comp = Composition([si], [1.0])
    beam_energy = ToSI.kev(20.0)
    take_off_angle = math.radians(40.0)

    model = Riveros1993(comp, beam_energy, take_off_angle)

    # Compute at 10 keV
    intensity = model.compute(ToSI.kev(10.0))
    assert intensity > 0


def test_castellano_compute():
    si = Element("Si")
    comp = Composition([si], [1.0])
    beam_energy = ToSI.kev(20.0)
    take_off_angle = math.radians(40.0)

    model = Castellano2004aBremsstrahlung(comp, beam_energy, take_off_angle)

    # Compute at 10 keV
    intensity = model.compute(ToSI.kev(10.0))
    assert intensity > 0

    # Intensity should be zero above beam energy
    assert model.compute(ToSI.kev(21.0)) == 0.0

    # Intensity should be zero at very low energy (below 50 eV as per code)
    assert model.compute(ToSI.ev(10.0)) == 0.0
