from layers_edx.element import Element, Composition
from layers_edx.atomic_shell import AtomicShell
from layers_edx.units import ToSI
from layers_edx.material_properties.bf import BackscatterFactor
from layers_edx.material_properties.er import ElectronRange
from layers_edx.material_properties.si import SurfaceIonization
from layers_edx.material_properties.sp import StoppingPower
from layers_edx.material_properties.ics import ProportionalIonizationCrossSection
from layers_edx.correction.pap import PAP
from layers_edx.spectrum.spectrum_properties import SpectrumProperties
from layers_edx.detector.eds_detector import EDSDetector, DetectorProperties, DetectorPosition, EDSCalibration

si = Element('Si')
comp = Composition([si], [1.0])
shell = AtomicShell(si, 'K')
beam_energy = ToSI.kev(20.0)

print(f"Beam Energy: {beam_energy}")

bf = BackscatterFactor.compute(comp, shell, beam_energy)
print(f"BackscatterFactor: {bf}")

er = ElectronRange.compute(comp, shell, beam_energy)
print(f"ElectronRange: {er}")

si_val = SurfaceIonization.compute(comp, shell, beam_energy)
print(f"SurfaceIonization: {si_val}")

sp = StoppingPower.compute_inv(comp, shell, beam_energy)
print(f"StoppingPower (inv): {sp}")

pics = ProportionalIonizationCrossSection.compute_family(shell, beam_energy)
print(f"PICS: {pics}")

# Setup PAP
det_prop = DetectorProperties(1024, 10.0, 0.0)
det_pos = DetectorPosition()
det_cal = EDSCalibration(10.0)
detector = EDSDetector(det_prop, det_pos, det_cal)
props = SpectrumProperties(detector, 20.0)

pap = PAP(comp, shell, props)
print(f"PAP f: {pap.f}")
print(f"PAP phi0: {pap.phi0}")
print(f"PAP rx: {pap.rx}")
print(f"PAP rm: {pap.rm}")
print(f"PAP rc: {pap.rc}")

rho_z = ToSI.gpcm2(100e-6) # 100 um Si ~ 0.023 g/cm2 -> 0.23 kg/m2
print(f"rho_z: {rho_z}")
curve = pap.compute_curve(rho_z)
print(f"Curve at rho_z: {curve}")

# Check efficiency
eff = detector.efficiency
print(f"Efficiency shape: {eff.shape}")
print(f"Max efficiency: {eff.max()}")
print(f"Min efficiency: {eff.min()}")
