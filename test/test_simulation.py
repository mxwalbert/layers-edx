import pytest
from layers_edx.simulation import BasicSimulator
from layers_edx.xrt import XRayTransition

def test_basic_simulator_emitted(mock_composition, mock_spectrum_properties):
    sim = BasicSimulator(mock_composition, mock_spectrum_properties)
    intensities = sim.emitted_intensities
    
    assert len(intensities) > 0
    
    # Check for Si Ka
    si = mock_composition.elements[0]
    ka1 = XRayTransition(si, 'KA1')
    
    # It might not be exactly KA1 key if transition probabilities use different keys or if it's not in the top list?
    # But BasicSimulator iterates over shells and their transitions.
    
    # Let's check if any Si K line is present
    found = False
    for xrt, intensity in intensities.items():
        if xrt.element == si and xrt.destination.name == 'K':
            assert intensity > 0
            found = True
    assert found

def test_basic_simulator_measured(mock_composition, mock_spectrum_properties):
    sim = BasicSimulator(mock_composition, mock_spectrum_properties)
    intensities = sim.measured_intensities
    
    assert len(intensities) > 0
    
    # Measured intensities should be less than emitted due to solid angle (scale factor)
    # scale = 1 / (4 pi r^2)
    # r (sample_distance) default is 1.0 cm? Need to check SpectrumProperties default.
    
    emitted = sim.emitted_intensities
    
    for xrt, intensity in intensities.items():
        assert intensity > 0
        assert intensity < emitted[xrt]
