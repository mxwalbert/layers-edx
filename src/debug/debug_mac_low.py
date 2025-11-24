from layers_edx.element import Element
from layers_edx.units import ToSI
from layers_edx.material_properties.mac import MassAbsorptionCoefficient

si = Element('Si')
energy = ToSI.kev(0.09) # 90 eV
print(f"Energy: {energy} J")

mac = MassAbsorptionCoefficient.compute(si, energy)
print(f"MAC(Si, 0.09 keV): {mac}")

energy_low = ToSI.ev(10.0)
mac_low = MassAbsorptionCoefficient.compute(si, energy_low)
print(f"MAC(Si, 10 eV): {mac_low}")
