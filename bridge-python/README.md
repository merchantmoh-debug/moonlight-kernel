# Moonlight Bridge: Python ("Qi")

## Overview
The Python Bridge serves as the "Qi" (Life Force/Signal) of the Moonlight architecture. It represents the "Brain" in the Brain-Body-Nervous System triad.

## Responsibility
- **Orchestration:** Commands the Rust host to initialize.
- **Signal Generation:** (Future) Provides high-level tensor definitions and operations to be executed by the kinetic core.
- **Observation:** Monitors the output of the Rust bridge.

## Structure
- `adapter.py`: A legacy wrapper script used to invoke the build and run process via Python `subprocess`.

## Usage
It is recommended to use the root `Makefile` to interact with this component.

```bash
cd ..
make test
```
