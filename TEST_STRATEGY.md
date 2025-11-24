# Test Strategy for `layers-edx`

## 1. Overview
`layers-edx` is a Python library for Electron Probe Quantification (EPQ) and EDX simulation, ported from the NIST EPQ library. The package involves complex physical calculations, data structures for materials and atomic properties, and algorithms for simulation and quantification.

This document outlines the strategy to ensure the correctness, reliability, and maintainability of the package through a comprehensive testing approach.

## 2. Current Status
- **Existing Tests**: There are currently 7 passing tests located in `test/test_quantification`.
- **Coverage**: The tests cover the `QuantifyModel`, `StandardModel`, `ReferenceModel`, `StandardSpectrum`, and `ReferenceSpectrum` classes.
- **Gaps**: The majority of the core modules (`element`, `layers`, `correction`, `simulation`, `detector`, `fitting`, etc.) are currently untested or only implicitly tested via the quantification tests.

## 3. Test Strategy

### 3.1 Unit Testing
The primary focus will be on high-coverage unit tests for individual components.

*   **Core Data Structures**:
    *   `Element`: Verify atomic properties (weight, number, symbol) against standard values. Test equality and hashing.
    *   `Composition`: Test creation from weight/atomic fractions, normalization, mixing elements, and conversion between weight and atomic fractions.
    *   `AtomicShell` & `XRayTransition`: Verify shell energies and transition weights.
    *   `Units`: Test conversion functions (eV to J, cm to m, etc.) in `units.py`.

*   **Physics Modules**:
    *   `Correction` (PAP, PhiRhoZ): Test the implementation of correction algorithms. Verify `chi`, `phi`, and `F` curves against known physical constraints or reference values.
    *   `Bremsstrahlung`: Test background generation algorithms.
    *   `MaterialProperties`: Test mass absorption coefficients and other material-specific properties.

*   **Simulation & Layers**:
    *   `Layer`: Test `Layer` properties, `ideal_intensities`, `upper_layer_absorption`, and `emitted_intensity`.
    *   `BasicSimulator`: Test the generation of emitted intensities from a composition.

*   **Spectrum & Detector**:
    *   `Detector`: Test `DetectorProperties`, `DetectorPosition`, and calibration logic.
    *   `Spectrum`: Test `BaseSpectrum` and its subclasses for data handling, channel manipulation, and property access.

*   **Fitting**:
    *   Test peak fitting algorithms and background subtraction.

### 3.2 Integration Testing
Integration tests will verify that components work together correctly.

*   **Simulation Pipeline**: Define a multi-layer sample -> Simulate Spectrum -> Verify output structure and basic physical sanity (e.g., peaks at correct energies).
*   **Quantification Pipeline**: Take a simulated spectrum (from known composition) -> Quantify it -> Verify that the calculated composition matches the input composition (within numerical tolerance).

### 3.3 Regression Testing
Since this is a port of NIST EPQ, we should aim to validate against the original library or established literature values where possible.

*   **Golden Data**: Create a set of "golden" inputs (compositions, beam energies) and expected outputs (k-ratios, concentrations) to ensure no regressions in physical accuracy.

## 4. Implementation Plan

We will implement tests in phases, prioritized by dependency order.

### Phase 1: Foundations
*   **Target**: `units.py`, `element.py`, `atomic_shell.py`, `xrt.py`, `composition.py` (inside `element.py`).
*   **Goal**: Ensure the basic building blocks are solid.

### Phase 2: Physics & Materials
*   **Target**: `material_properties/`, `correction/`, `bremsstrahlung.py`.
*   **Goal**: Validate the physical models.

### Phase 3: Simulation & Layers
*   **Target**: `layers.py`, `simulation.py`.
*   **Goal**: Test the layer interaction and intensity calculations.

### Phase 4: Spectrum & Detector
*   **Target**: `detector/`, `spectrum/`.
*   **Goal**: Ensure spectral data is handled correctly.

### Phase 5: Fitting & Quantification (Expansion)
*   **Target**: `fitting/`, `kratio.py`, `quantification/`.
*   **Goal**: Expand existing quantification tests and add fitting tests.

## 5. Tools & Conventions
*   **Runner**: `pytest`
*   **Coverage**: `pytest-cov` to track coverage.
*   **Structure**: Mirror the package structure in the `test` directory (e.g., `test/test_element.py`, `test/correction/test_pap.py`).
*   **Fixtures**: Use `conftest.py` for shared fixtures (e.g., common elements, detectors).
