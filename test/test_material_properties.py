import pytest
import math
from layers_edx.material_properties.mac import MassAbsorptionCoefficient
from layers_edx.material_properties.mip import MeanIonizationPotential
from layers_edx.element import Element, Composition
from layers_edx.units import ToSI

def test_mac_element():
    si = Element('Si')
    energy = ToSI.kev(1.74) # Si Ka energy
    
    # MAC of Si for Si Ka should be significant
    mac = MassAbsorptionCoefficient.compute(si, energy)
    assert mac > 0
    
    # MAC decreases with energy (away from edges)
    mac_high = MassAbsorptionCoefficient.compute(si, ToSI.kev(10.0))
    assert mac > mac_high

def test_mac_composition():
    si = Element('Si')
    o = Element('O')
    sio2 = Composition([si, o], [1.0, 2.0], weight=False)
    energy = ToSI.kev(1.74)
    
    mac_sio2 = MassAbsorptionCoefficient.compute_composition(sio2, energy)
    mac_si = MassAbsorptionCoefficient.compute(si, energy)
    mac_o = MassAbsorptionCoefficient.compute(o, energy)
    
    # MAC of composition is weighted average
    w_si = sio2.weight_fractions[si]
    w_o = sio2.weight_fractions[o]
    expected = w_si * mac_si + w_o * mac_o
    
    assert mac_sio2 == pytest.approx(expected)

def test_mip_element():
    si = Element('Si')
    mip = MeanIonizationPotential.compute(si)
    assert mip > 0
    # MIP for Si (Z=14) is approx 173 eV
    assert mip == pytest.approx(ToSI.ev(173), rel=0.1)

def test_mip_composition():
    si = Element('Si')
    o = Element('O')
    sio2 = Composition([si, o], [1.0, 2.0], weight=False)
    
    mip = MeanIonizationPotential.compute_composition(sio2)
    assert mip > 0
    
    # Should be between MIP of Si and O
    mip_si = MeanIonizationPotential.compute(si)
    mip_o = MeanIonizationPotential.compute(o)
    
    assert min(mip_si, mip_o) < mip < max(mip_si, mip_o)
