import pytest
import numpy as np
from layers_edx.detector.detector import DetectorProperties, DetectorPosition, EDSCalibration
from layers_edx.detector.eds_detector import EDSDetector
from layers_edx.quantification.quantify_spectrum.standard_spectrum import StandardSpectrum
from layers_edx.quantification.quantify_spectrum.reference_spectrum import ReferenceSpectrum
from layers_edx.quantification.quantify_spectrum.quantify_spectrum import QuantifySpectrum
from layers_edx.kratio import KRatioSet
from layers_edx.roi import RegionOfInterestSet, RegionOfInterest
from layers_edx.element import Element, Composition
from layers_edx.spectrum.base_spectrum import BaseSpectrum
from layers_edx.spectrum.spectrum_properties import SpectrumProperties
from layers_edx.xrt import XRayTransition
from layers_edx.units import ToSI


@pytest.fixture
def mock_element():
    return Element('Si')

@pytest.fixture
def mock_composition(mock_element):
    return Composition([mock_element], [1.0])

@pytest.fixture
def mock_xrt(mock_element):
    return XRayTransition(mock_element, 'KA1')

@pytest.fixture
def mock_beam_energy():
    return 15.

@pytest.fixture
def mock_spectrum_data():
    data = np.zeros(150)
    data[17] = 100.
    return data

@pytest.fixture
def mock_detector(mock_spectrum_data):
    det_prop = DetectorProperties(
        channel_count=mock_spectrum_data.shape[0],
        area=100.0,
        thickness=1.0
    )
    det_pos = DetectorPosition()
    det_cal = EDSCalibration(
        channel_width=100
    )
    return EDSDetector(
        properties=det_prop,
        position=det_pos,
        calibration=det_cal
    )

@pytest.fixture
def mock_spectrum_properties(mock_detector, mock_beam_energy):
    return SpectrumProperties(
        detector=mock_detector,
        beam_energy=mock_beam_energy
    )

@pytest.fixture
def mock_spectrum(mock_spectrum_properties, mock_spectrum_data):
    return BaseSpectrum(
        properties=mock_spectrum_properties,
        data=mock_spectrum_data
    )

@pytest.fixture
def mock_standard_spectrum(mock_element, mock_composition, mock_spectrum):
    return StandardSpectrum(mock_spectrum, mock_element, mock_composition)

@pytest.fixture
def mock_reference_spectrum(mock_spectrum, mock_composition):
    return ReferenceSpectrum(mock_spectrum, mock_composition)

def test_standard_spectrum_create_roi(mock_element, mock_standard_spectrum):
    roi_set = mock_standard_spectrum.create_element_roi_set(mock_element)
    assert isinstance(roi_set, RegionOfInterestSet)

def test_standard_spectrum_compute_intensities(mock_xrt, mock_standard_spectrum):
    roi = RegionOfInterest(mock_xrt)
    intensities = mock_standard_spectrum.compute_intensities(roi)
    assert intensities[mock_xrt] > 0.
