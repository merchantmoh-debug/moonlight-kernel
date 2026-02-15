.PHONY: all build run test clean check-env mock-build mock-test benchmark

# Project Moonlight: The Mechanic's Ear Build System
# "Speed is Safety."

PYTHON := python3

all: setup build

# Dependency Setup
setup:
	@echo "--- [SETUP] Installing Dependencies ---"
	$(PYTHON) -m pip install -r requirements.txt || echo "Warning: Pip install failed. Ensure 'rich' is installed."

# Standard Build (Delegates to Python Orchestrator)
build:
	$(PYTHON) bridge-python/moonlight.py build

# Mock Build (Forces Mock Kernel)
mock-build:
	$(PYTHON) bridge-python/moonlight.py build --mock

# Run the Bridge
run:
	$(PYTHON) bridge-python/moonlight.py run

# Run Tests
test:
	$(PYTHON) bridge-python/moonlight.py test

# Benchmark Performance
benchmark:
	$(PYTHON) bridge-python/moonlight.py benchmark

# Aliases for compatibility
mock-test: test

clean:
	@echo "--- [CLEAN] Purging Artifacts ---"
	cd core && moon clean || true
	cd bridge-rust && cargo clean || true
	cd core/mock_kernel && cargo clean || true
	rm -rf core/target
	rm -rf __pycache__
	rm -rf bridge-python/__pycache__
	rm -rf tests/__pycache__
