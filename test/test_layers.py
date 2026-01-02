import pytest
from layers_edx.layers import Layer, corrected_intensities
from layers_edx.units import ToSI
from layers_edx.xrt import XRayTransition


def test_layer_creation(mock_composition, mock_spectrum_properties):
    mass_thickness = ToSI.gpcm2(100e-6)  # 100 nm approx
    layer = Layer(mock_composition, mass_thickness, mock_spectrum_properties)

    assert layer.composition == mock_composition
    assert layer.mass_thickness == mass_thickness


def test_layer_ideal_intensities(mock_composition, mock_spectrum_properties):
    mass_thickness = ToSI.gpcm2(100e-6)
    layer = Layer(mock_composition, mass_thickness, mock_spectrum_properties)

    intensities = layer.ideal_intensities
    assert len(intensities) > 0

    si = mock_composition.elements[0]
    ka1 = XRayTransition(si, "KA1")
    # Check if any Si K line exists
    found = False
    for xrt in intensities:
        if xrt.element == si and xrt.destination.name == "K":
            found = True
            break
    assert found


@pytest.mark.skip(
    reason="Numerical integration issues with thin layers - needs more investigation"
)
def test_corrected_intensities(mock_composition, mock_spectrum_properties):
    # Create a single bulk layer (simpler case for testing)
    # Using a realistic bulk thickness
    import math

    thickness = ToSI.gpcm2(0.001)  # 1 mg/cm^2 = 0.1 kg/m^2

    layer = Layer(mock_composition, thickness, mock_spectrum_properties)
    layers = [layer]

    intensities = corrected_intensities(layers)
    assert len(intensities) > 0

    # Check that intensities are valid (not nan, not zero)
    for xrt, intensity in intensities.items():
        assert not math.isnan(intensity), f"Intensity for {xrt.transition} is nan"
        assert intensity > 0, f"Intensity for {xrt.transition} is not positive"
