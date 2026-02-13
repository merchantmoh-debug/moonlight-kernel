.PHONY: all build run test clean check-env mock-build mock-test

# Project Moonlight: The Mechanic's Ear Build System
# "Speed is Safety."

PYTHON := python3
CARGO := cargo
MOON := moon

all: build

check-env:
	@which $(PYTHON) > /dev/null || (echo "Error: python3 not found. Please install Python." && exit 1)
	@which $(CARGO) > /dev/null || (echo "Error: cargo not found. Please install Rust." && exit 1)
	@which $(MOON) > /dev/null || (echo "Error: moon not found. Consider using 'make mock-build' if you lack the MoonBit toolchain." && exit 1)

# Standard Build (Requires MoonBit)
build: check-env
	@echo "--- [1/3] Synthesizing MoonBit Kernel ---"
	$(PYTHON) scripts/synthesize_moonbit_kernel.py
	@echo "--- [2/3] Building MoonBit Core (Wasm) ---"
	cd core && $(MOON) build --target wasm
	@echo "--- [3/3] Building Rust Bridge ---"
	cd bridge-rust && $(CARGO) build --release

# Mock Build (Requires only Rust)
mock-build:
	@echo "--- [MOCK] building Rust-based Mock Kernel ---"
	@which $(CARGO) > /dev/null || (echo "Error: cargo not found." && exit 1)
	cd core/mock_kernel && $(CARGO) build --target wasm32-unknown-unknown --release
	@echo "--- [MOCK] Deploying Artifact ---"
	mkdir -p core/target/wasm/release/build/lib/
	cp core/mock_kernel/target/wasm32-unknown-unknown/release/mock_kernel.wasm core/target/wasm/release/build/lib/lib.wasm
	@echo "--- [MOCK] Building Rust Bridge ---"
	cd bridge-rust && $(CARGO) build --release

run: build
	@echo "--- [RUN] Igniting Moonlight Bridge ---"
	cd bridge-rust && $(CARGO) run --release --quiet

test: build
	@echo "--- [TEST] Running Integration Tests ---"
	$(PYTHON) tests/test_integration.py

mock-test: mock-build
	@echo "--- [TEST] Running Integration Tests (Mock Kernel) ---"
	$(PYTHON) tests/test_integration.py

clean:
	@echo "--- [CLEAN] Purging Artifacts ---"
	cd core && $(MOON) clean || true
	cd bridge-rust && $(CARGO) clean || true
	cd core/mock_kernel && $(CARGO) clean || true
	rm -rf core/target
	rm -rf __pycache__
	rm -rf bridge-python/__pycache__
	rm -rf tests/__pycache__
