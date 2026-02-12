.PHONY: all build run test clean check-env

# Project Moonlight: The Mechanic's Ear Build System
# "Speed is Safety."

PYTHON := python3
CARGO := cargo
MOON := moon

all: build

check-env:
	@which $(PYTHON) > /dev/null || (echo "Error: python3 not found"; exit 1)
	@which $(CARGO) > /dev/null || (echo "Error: cargo not found"; exit 1)
	@which $(MOON) > /dev/null || (echo "Error: moon not found"; exit 1)

build: check-env
	@echo "--- [1/3] Synthesizing MoonBit Kernel ---"
	$(PYTHON) scripts/synthesize_moonbit_kernel.py
	@echo "--- [2/3] Building MoonBit Core (Wasm) ---"
	cd core && $(MOON) build --target wasm
	@echo "--- [3/3] Building Rust Bridge ---"
	cd bridge-rust && $(CARGO) build --release

run: build
	@echo "--- [RUN] Igniting Moonlight Bridge ---"
	cd bridge-rust && $(CARGO) run --release --quiet

test: build
	@echo "--- [TEST] Running Integration Tests ---"
	$(PYTHON) tests/test_integration.py

clean:
	@echo "--- [CLEAN] Purging Artifacts ---"
	cd core && $(MOON) clean || true
	cd bridge-rust && $(CARGO) clean || true
	rm -rf core/target
	rm -rf __pycache__
	rm -rf bridge-python/__pycache__
	rm -rf tests/__pycache__
