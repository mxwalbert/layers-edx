import pytest
from layers_edx.correction.pap import PAP
from layers_edx.correction.xpp import XPP
from layers_edx.element import Element, Composition
from layers_edx.atomic_shell import AtomicShell
from layers_edx.xrt import XRayTransition
from layers_edx.spectrum.spectrum_properties import SpectrumProperties
from layers_edx.detector.eds_detector import (
    EDSDetector,
    DetectorProperties,
    DetectorPosition,
    EDSCalibration,
)
from layers_edx.units import ToSI


@pytest.fixture
def mock_spectrum_properties() -> SpectrumProperties:
    # Minimal setup for SpectrumProperties
    det_prop = DetectorProperties(1024, 10.0, 1.0)  # channel_count, area, thickness
    det_pos = DetectorPosition()
    det_cal = EDSCalibration(10.0)  # channel_width
    detector = EDSDetector(det_prop, det_pos, det_cal)

    beam_energy = 20.0  # keV
    return SpectrumProperties(detector, beam_energy)


def test_pap_correction(mock_spectrum_properties: SpectrumProperties):
    si = Element("Si")
    comp = Composition([si], [1.0])
    shell = AtomicShell(si, "K")

    pap = PAP(comp, shell, mock_spectrum_properties)

    # Test curve
    rho_z = ToSI.gpcm2(100e-6)  # some depth
    assert pap.compute_curve(rho_z) >= 0

    # Test ZA correction
    xrt = XRayTransition(si, "KA1")
    za = pap.compute_za_correction(xrt)
    assert za > 0


def test_xpp_correction(mock_spectrum_properties: SpectrumProperties):
    si = Element("Si")
    comp = Composition([si], [1.0])
    shell = AtomicShell(si, "K")

    xpp = XPP(comp, shell, mock_spectrum_properties)

    # Test curve
    rho_z = ToSI.gpcm2(100e-6)
    assert xpp.compute_curve(rho_z) >= 0

    # Test ZA correction
    xrt = XRayTransition(si, "KA1")
    za = xpp.compute_za_correction(xrt)
    assert za > 0
