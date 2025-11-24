from layers_edx.element import Element, Material
from layers_edx.units import ToSI
from layers_edx.detector.detector import DetectorProperties, EDSCalibration
import numpy as np
import math
from layers_edx.material_properties.mac import MassAbsorptionCoefficient

dp = DetectorProperties(1024, 10.0, 0.0) # area 10 mm2, thickness 0.0 mm?
# Wait, thickness default is 1.0 in class definition, but here I passed 0.0 as 3rd arg!
# DetectorProperties(channel_count, area, thickness, ...)
# I passed 0.0 for thickness!

print(f"Thickness passed: 0.0")

dp_default = DetectorProperties()
print(f"Default thickness: {dp_default.thickness}")

# If thickness is 0, active_mt is 0.
# result *= 1 - exp(0) = 1 - 1 = 0.
# Efficiency is 0.

print("Found the issue: I initialized DetectorProperties with thickness=0.0 in the test fixture!")
