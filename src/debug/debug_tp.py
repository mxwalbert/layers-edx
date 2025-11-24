from layers_edx.material_properties.tp import TransitionProbabilities
from layers_edx.element import Element
from layers_edx.atomic_shell import AtomicShell

si = Element('Si')
print(f"Si in RADIATIVE: {si in TransitionProbabilities.Endlib1997.RADIATIVE}")
if si in TransitionProbabilities.Endlib1997.RADIATIVE:
    data = TransitionProbabilities.Endlib1997.RADIATIVE[si]
    print(f"Number of entries for Si: {len(data)}")
    k_shell = AtomicShell(si, 'K')
    print(f"K shell index: {k_shell.shell}")
    
    found_k = False
    for xrt, ionized, prob in data:
        if ionized == k_shell.shell:
            print(f"Found transition for K shell: {xrt.transition} prob={prob}")
            found_k = True
    
    if not found_k:
        print("No transitions found for K shell ionization.")
else:
    print("Si not found in RADIATIVE data.")
