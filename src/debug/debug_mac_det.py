from layers_edx.material_properties.mac import MassAbsorptionCoefficient
from layers_edx.element import Element
from layers_edx.units import ToSI
from layers_edx.detector.detector import EDSCalibration
from layers_edx.xrt import XRayTransition

si = Element('Si')
energy = ToSI.kev(1.74)
print(f"Energy: {energy} J")

mac = MassAbsorptionCoefficient.compute(si, energy)
print(f"MAC(Si, 1.74 keV): {mac}")

# Check Detector visibility logic
xrt = XRayTransition(si, 'KA1')
print(f"XRT Edge Energy: {xrt.edge_energy} J")
beam_energy = ToSI.kev(20.0)
print(f"Beam Energy: {beam_energy} J")
min_overvoltage = EDSCalibration.MIN_OVERVOLTAGE
print(f"Min Overvoltage: {min_overvoltage}")

threshold = beam_energy / min_overvoltage
print(f"Threshold (Beam/OV): {threshold} J")

if xrt.edge_energy < threshold:
    print("Condition (edge < threshold) is TRUE. is_visible returns FALSE.")
else:
    print("Condition (edge < threshold) is FALSE. is_visible returns TRUE (if loop passes).")
