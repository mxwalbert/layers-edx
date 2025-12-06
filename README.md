# layers-edx

A Python port of the [NIST EPQ (Electron Probe Quantification) library](https://github.com/usnistgov/EPQ) for X-ray microanalysis and electron probe quantification.

## Features

- **Element Properties**: Atomic weights, ionization potentials, and shell structures
- **X-ray Transitions**: Energy levels, weights, and transition probabilities
- **Material Properties**: Mass absorption coefficients (MAC), mean ionization potentials (MIP)
- **EPQ Cross-Validation**: Tests validate against original Java EPQ library

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/mxwalbert/layers-edx.git
cd layers-edx

# Create and activate virtual environment
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# Linux/Mac:
source .venv/bin/activate

# Install the package
pip install -e .
```

### Basic Usage

```python
from layers_edx.element import Element
from layers_edx.xrt import XRayTransition, XRayTransitionSet

# Get element properties
si = Element('Si')
print(f"Atomic weight: {si.atomic_weight}")
print(f"Atomic number: {si.atomic_number}")

# Get X-ray transitions
ka1 = XRayTransition(si, 'KA1')
print(f"Si Kα1 energy: {ka1.energy_ev:.2f} eV")
print(f"Si Kα1 weight: {ka1.weight:.4f}")

# Get all K-shell transitions
k_transitions = XRayTransitionSet(si, 'K')
for xrt in k_transitions:
    print(f"{xrt.name}: {xrt.energy_ev:.2f} eV")
```

## References

- [NIST EPQ Library (Java)](https://github.com/usnistgov/EPQ)
- [DTSA-II Software](https://www.cstl.nist.gov/div837/Division%20Programs/MML/Microanalysis/DTSA-II.html)

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for setup instructions and guidelines.

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

This Python implementation is derived from the [NIST EPQ library](https://github.com/usnistgov/EPQ), which is in the public domain pursuant to Title 17 Section 105 of the United States Code. See the [NOTICE](NOTICE) file for attribution details.

## Support

If you encounter problems with the software, please:
1. Check existing [Issues](https://github.com/mxwalbert/layers-edx/issues)
2. Open a new issue with details about your problem
3. Include your OS, Python version and other details about your environment
