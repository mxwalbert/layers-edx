import pytest
from layers_edx.units import ToSI, FromSI, PhysicalConstants


def test_physical_constants():
    assert PhysicalConstants.ElementaryCharge > 0
    assert PhysicalConstants.AMU > 0
    assert PhysicalConstants.BohrRadius > 0
    assert PhysicalConstants.ElectronRestMass > 0


def test_to_si_energy():
    # 1 eV = 1.602e-19 J
    assert ToSI.ev(1.0) == pytest.approx(PhysicalConstants.ElementaryCharge)
    assert ToSI.kev(1.0) == pytest.approx(1000 * PhysicalConstants.ElementaryCharge)


def test_to_si_length():
    assert ToSI.cm(1.0) == 0.01
    assert ToSI.mm(1.0) == 0.001
    assert ToSI.um(1.0) == 1e-6
    assert ToSI.nm(1.0) == 1e-9


def test_to_si_area():
    assert ToSI.cm2(1.0) == 1e-4
    assert ToSI.mm2(1.0) == 1e-6


def test_to_si_mass():
    assert ToSI.amu(1.0) == pytest.approx(PhysicalConstants.AMU)


def test_to_si_density():
    # 1 g/cm^3 = 1000 kg/m^3
    assert ToSI.gpcm3(1.0) == 1000.0


def test_from_si_energy():
    joules = PhysicalConstants.ElementaryCharge
    assert FromSI.ev(joules) == pytest.approx(1.0)
    assert FromSI.kev(joules * 1000) == pytest.approx(1.0)


def test_from_si_length():
    assert FromSI.cm(0.01) == pytest.approx(1.0)
    assert FromSI.um(1e-6) == pytest.approx(1.0)
    assert FromSI.nm(1e-9) == pytest.approx(1.0)
