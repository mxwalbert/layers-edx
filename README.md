# layers-edx

A Python port of parts of the [NIST EPQ (Electron Probe Quantification) library](https://github.com/usnistgov/EPQ) for X-ray microanalysis and electron probe quantification.

## Features

- **Element Properties**: Atomic weights, ionization potentials, and shell structures
- **X-ray Transitions**: Energy levels, weights, and transition probabilities
- **Material Properties**: Mass absorption coefficients (MAC), mean ionization potentials (MIP)
- **EPQ Cross-Validation**: Tests validate against original Java EPQ library

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/layers-edx.git
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

## Development

### Prerequisites

For EPQ cross-validation testing, you'll need:
- **Java 21+** - [Download from Adoptium](https://adoptium.net/)
- **Apache Maven** - [Download from maven.apache.org](https://maven.apache.org/download.cgi)

### Setup for Contributors

```bash
# Install development dependencies
pip install -e ".[dev]"

# Set up EPQ library for cross-validation tests (Windows)
.\scripts\setup_epq.ps1

# Run tests
pytest
```

For detailed setup instructions, see [CONTRIBUTING.md](CONTRIBUTING.md).

## Project Structure

```
layers-edx/
├── layers_edx/          # Main Python package
│   ├── element.py       # Element properties
│   ├── xrt.py          # X-ray transitions
│   ├── units.py        # Unit conversions
│   └── ...
├── test/               # Test suite with EPQ validation
├── scripts/            # Setup and utility scripts
└── src/                # Example scripts
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=layers_edx

# Run only EPQ cross-validation tests
pytest -m epq
```

## Cross-Validation with EPQ

This project validates its Python implementation against the original NIST EPQ Java library. The test suite includes:

- **X-ray Transitions** (`test_xrt`): Validates transition energies and weights
- **Mass Absorption Coefficients** (`test_mac`): Validates MAC calculations
- **Mean Ionization Potentials** (`test_mip`): Validates MIP calculations

See [EPQ_API_REFERENCE.md](EPQ_API_REFERENCE.md) for detailed API mapping.

## References

- [NIST EPQ Library (Java)](https://github.com/usnistgov/EPQ)
- [DTSA-II Software](https://www.cstl.nist.gov/div837/Division%20Programs/MML/Microanalysis/DTSA-II.html)

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for setup instructions and guidelines.

## License

This project follows the NIST EPQ library's public domain status pursuant to Title 17 Section 105 of the United States Code.

## Acknowledgments

This project is based on the NIST EPQ library developed by the National Institute of Standards and Technology (NIST).
