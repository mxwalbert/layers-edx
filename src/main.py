import copy
import time

import layers_edx.spectrum.spectrum_properties
from detector import detector
from layers_edx.spectrum.spectrum_properties import SpectrumProperties

# data paths
standards_path = "C:\\Users\\WolfMa\\Documents\\Dissertation\\Experimental\\EDX\\230125_CuAg_50W_5mubar\\standards\\"
measurements_path = "C:\\Users\\WolfMa\\Documents\\Dissertation\\Experimental\\EDX\\230125_CuAg_50W_5mubar\\spectra\\"

# file names
detector_name = "Octane Elect Plus 230118.xdet"
standard_names = {
    "Ag": "Ag std - Pure Silver.zstd",
    "Cu": "Cu std - Pure Copper.zstd",
    "O": "O std - Cu2O.zstd",
    "Si": "Si std - Pure Silicon.zstd"
}
measurement_names = ['1.msa', '70.msa']

# measurement conditions
BEAM_ENERGY = 20.  # keV
PROBE_CURRENT = 1.  # nA
LIVE_TIME = 20.  # s
WORKING_DISTANCE = 8.5  # mm

spec_prop = SpectrumProperties(
    detector=detector,
    beam_energy=BEAM_ENERGY,
    probe_current=PROBE_CURRENT,
    live_time=LIVE_TIME,
    working_distance=WORKING_DISTANCE
)


# calculates the point of symmetry (vertex) of a parabola which fits through the provided points
def calc_parabola_vertex(x, y):
    denom = (x[0] - x[1]) * (x[0] - x[2]) * (x[1] - x[2])
    A = (x[2] * (y[1] - y[0]) + x[1] * (y[0] - y[2]) + x[0] * (y[2] - y[1])) / denom
    B = (x[2] * x[2] * (y[0] - y[1]) + x[1] * x[1] * (y[2] - y[0]) + x[0] * x[0] * (y[1] - y[2])) / denom
    C = (x[1] * x[2] * (x[1] - x[2]) * y[0] + x[2] * x[0] * (x[2] - x[0]) * y[1] + x[0] * x[1] * (x[0] - x[1]) * y[
        2]) / denom
    xv = -B / (2 * A)
    yv = C - B * B / (4 * A)
    return xv, yv


# kratios of the model system
def calculate_kratios(kratios_exp, specimen_layers, standards_calc, detector=detector):
    specimen_calc = generate_spectrum(specimen_layers, detector)
    specimen_calc = ScriptableSpectrum(specimen_calc)
    props = specimen_layers.props
    specimen_calc.getProperties().addAll(props)
    kratios_calc = kratios(specimen_calc, standards_calc).unknown.kratios()
    deviation = []
    for transition_set in kratios_exp.getTransitions().iterator():
        deviation.append(kratios_calc.getKRatio(transition_set) - kratios_exp.getKRatio(transition_set))
    return kratios_calc, list_mean(deviation)


# PROCEDURE
# load standard bundles
standards_exp = {}
for element, standard_name in standard_names.items():
    standards_exp[epq.Element.byName(element)] = readSpectrum(standards_path + standard_name, det=detector)

# generate calculated standards
standards_calc = {}
for element in standards_exp:
    comp = epq.Composition([element], [1])
    standard_layers = Layers([{'comp': comp, 't': 1}], props)
    standards_calc[element] = generate_spectrum(standard_layers)
    standards_calc[element].getProperties().addAll(props)
    standards_calc[element].getProperties().setCompositionProperty(
        layers_edx.spectrum.spectrum_properties.SpectrumProperties.StandardComposition, comp)

# load measurement
measurement_name = measurement_names[1]
unk = readSpectrum(measurements_path + measurement_name)
unk.getProperties().setDetector(detector)

# compute optimal experimental k-ratios
kratios_exp = kratios(unk, standards_exp).unknown.kratios().optimalKRatioSet()

# initialize concentrations
# treat sample as homogenous specimen and compute the concentration using regular ZAF correction
quant0 = quantify(unk, standards_exp).unknown.composition()

# build specimen layers
film_comp = {epq.Element.byName(element): quant0.weightFraction(epq.Element.byName(element), True) for element in
             ['Ag', 'Cu']}
film_comp = epq.Composition(film_comp.keys(), list_normalize(film_comp.values()))
substrate_comp = {epq.Element.byName(element): quant0.weightFraction(epq.Element.byName(element), True) for element in
                  ['Si']}
substrate_comp = epq.Composition(substrate_comp.keys(), list_normalize(substrate_comp.values()))
specimen_layers = Layers([
    {'comp': film_comp, 't': 0.001, 'fixed': {'comp': False, 't': False}},
    {'comp': substrate_comp, 't': 1, 'fixed': {'comp': True, 't': True}}
], props)

# Initialize computation cycle
delta_c = {}
idx = 0

print("""
INPUT:
Composition (wt): %s
Composition (at): %s
Mass thickness (kg/m3): %.6f
""") % (specimen_layers.get_comp(0), specimen_layers.get_comp(0).stoichiometryString(), specimen_layers.get_t(0))

starttime = time.time()
# Computation cycle
while True:

    # Step1: obtain kratios and deviation of the current layer
    kratios_calc, delta_c[idx] = calculate_kratios(kratios_exp, specimen_layers, standards_calc)

    # Step2: update concentration and obtain thickness-related deviation
    for layer_idx in range(len(specimen_layers)):
        if not specimen_layers.get_fixed(layer_idx, 'comp'):
            new_comp = {}
            for element in specimen_layers.get_elements(layer_idx):
                optimal_transition = kratios_exp.optimalDatum(element)
                new_comp[element] = specimen_layers.get_weight_fraction(layer_idx, element)
                new_comp[element] *= kratios_exp.getKRatio(optimal_transition) / kratios_calc.getKRatio(
                    optimal_transition)
            specimen_layers.update_comp(layer_idx, new_comp)
    _, delta_t = calculate_kratios(kratios_exp, specimen_layers, standards_calc)

    # Step3: calculate kratios for slightly thicker and thinner films and obtain the new thickness
    new_t = {}
    specimen_layers_copy = copy.copy(specimen_layers)
    for layer_idx in range(len(specimen_layers) - 1):
        if not specimen_layers.get_fixed(layer_idx, 't'):
            t = specimen_layers.get_t(layer_idx)
            t_plus, t_minus = t * 11 / 10, t * 9 / 10
            specimen_layers_copy.update_t(layer_idx, t_plus)
            _, delta_plus = calculate_kratios(kratios_exp, specimen_layers_copy, standards_calc)
            specimen_layers_copy.update_t(layer_idx, t_minus)
            _, delta_minus = calculate_kratios(kratios_exp, specimen_layers_copy, standards_calc)
            new_t[layer_idx], _ = calc_parabola_vertex([t, t_plus, t_minus], [delta_t, delta_plus, delta_minus])
            if new_t[layer_idx] < 0:
                new_t[layer_idx] = t_minus
            specimen_layers_copy.update_t(layer_idx, new_t[layer_idx])

    # Step4: calculate the kratio deviation with the updated composition and thicknesses
    _, delta_ct = calculate_kratios(kratios_exp, specimen_layers_copy, standards_calc)

    # Step5: update the layer thicknesses of the original layers object
    for layer_idx in range(len(specimen_layers) - 1):
        t_final = (new_t[layer_idx] + specimen_layers.get_t(layer_idx)) / 2 if delta_ct > delta_c else new_t[layer_idx]
        specimen_layers.update_t(layer_idx, t_final)

    # Step 6: check if new iteration is needed
    c_diff = composition_difference(specimen_layers.get_comp(0), specimen_layers.get_comp_history(0))
    t_diff = (specimen_layers.get_t(0) - specimen_layers.get_t_history(0))
    print(c_diff, t_diff)
    if abs(list_max(c_diff.values())) < 1e-4 and abs(t_diff) < 1e-6:
        break
    idx += 1

print("""
RESULTS:
Composition (wt): %s
Composition (at): %s
Mass thickness (kg/m3): %.6f
""") % (specimen_layers.get_comp(0), specimen_layers.get_comp(0).stoichiometryString(), specimen_layers.get_t(0))
