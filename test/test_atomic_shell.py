import pytest
from layers_edx.atomic_shell import AtomicShell
from layers_edx.element import Element

def test_atomic_shell_creation():
    si = Element('Si')
    k_shell = AtomicShell(si, 'K')
    
    assert k_shell.name == 'K'
    assert k_shell.shell == 0
    assert k_shell.element == si

def test_atomic_shell_properties():
    si = Element('Si')
    k_shell = AtomicShell(si, 'K')
    
    assert k_shell.capacity == 2
    assert k_shell.family == 0 # K family
    assert k_shell.principal_quantum_number == 1
    
    l3_shell = AtomicShell(si, 'LIII')
    assert l3_shell.capacity == 4
    assert l3_shell.principal_quantum_number == 2

def test_atomic_shell_energy():
    si = Element('Si')
    k_shell = AtomicShell(si, 'K')
    
    # Si K edge is approx 1.839 keV
    from layers_edx.units import ToSI
    assert k_shell.edge_energy > ToSI.ev(1000) # eV
    assert k_shell.edge_energy < ToSI.ev(2000) # eV

def test_atomic_shell_exists():
    h = Element('H')
    k_shell = AtomicShell(h, 'K')
    assert k_shell.exists
    
    # H does not have L shells populated in ground state usually, but edge energy might be defined?
    # Actually exists checks energy > 0.
    
    # Let's check a high shell for a light element
    m_shell = AtomicShell(h, 'MIII')
    assert not m_shell.exists or m_shell.edge_energy == 0

def test_angular_momentum():
    si = Element('Si')
    k = AtomicShell(si, 'K')
    assert k.orbital_angular_momentum == 0
    
    l3 = AtomicShell(si, 'LIII')
    assert l3.orbital_angular_momentum == 1
