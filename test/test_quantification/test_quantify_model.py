import pytest
from layers_edx.quantification.quantify_model.standard_model import StandardModel
from layers_edx.quantification.quantify_model.reference_model import ReferenceModel
from layers_edx.quantification.quantify_model.quantify_model import QuantifyModel
from layers_edx.kratio import KRatioSet
from layers_edx.roi import RegionOfInterestSet, RegionOfInterest
from layers_edx.element import Element, Composition
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
def mock_model(mock_xrt):
    return {mock_xrt: 100.0}

@pytest.fixture
def mock_beam_energy():
    return ToSI.kev(15)

@pytest.fixture
def mock_standard_model(mock_element, mock_composition, mock_model, mock_beam_energy):
    return StandardModel(mock_model, mock_beam_energy, mock_element, mock_composition)

@pytest.fixture
def mock_reference_model(mock_composition, mock_model):
    return ReferenceModel(mock_model, mock_composition)

def test_standard_model_create_roi(mock_element, mock_standard_model):
    roi_set = mock_standard_model.create_element_roi_set(mock_element)
    assert isinstance(roi_set, RegionOfInterestSet)

def test_standard_model_compute_intensities(mock_xrt, mock_standard_model):
    roi = RegionOfInterest(mock_xrt)
    intensities = mock_standard_model.compute_intensities(roi)
    assert intensities[mock_xrt] == 100.0

def test_reference_model(mock_xrt, mock_reference_model):
    assert mock_reference_model.model[mock_xrt] == 100.0

@pytest.fixture
def mock_quantify_model(mock_element, mock_standard_model, mock_beam_energy):
    standards = {mock_element: mock_standard_model}
    return QuantifyModel(mock_beam_energy, standards)

def test_quantify_model_create_reference(mock_quantify_model, mock_standard_model):
    reference = mock_quantify_model.create_reference(mock_standard_model)
    assert isinstance(reference, ReferenceModel)

def test_quantify_model_compute(mock_xrt, mock_quantify_model):
    unknown = {mock_xrt: 200.0}
    k_ratio_set = mock_quantify_model.compute(unknown)
    assert isinstance(k_ratio_set, KRatioSet)
