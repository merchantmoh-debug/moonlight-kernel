import subprocess
import os
import sys
import re

def test_integration():
    print("[TEST] Starting Integration Test (Kinetic Validation)...")

    # Path to bridge-rust
    bridge_rust = os.path.join(os.path.dirname(__file__), "..", "bridge-rust")

    # Run cargo run
    try:
        # Build first (in case it wasn't built)
        # We assume `cargo build` is needed or handled by `run`.
        result = subprocess.run(
            ["cargo", "run", "--release", "--quiet"],
            cwd=bridge_rust,
            check=True,
            capture_output=True,
            text=True
        )
        output = result.stdout

        # Verification Logic
        # 1. Check for basic validation signal
        expected_phrase = "Neuronal Validation: ACTIVE"
        count = output.count(expected_phrase)

        # New expectation: At least 5 validation cycles (due to batching, count might be higher)
        if count < 5:
            print(f"[TEST] FAILURE: Expected at least 5 validation cycles, found {count}.")
            print("Full Output:")
            print(output)
            sys.exit(1)

        # 2. Check for Numerical Correctness (High Resolution Audit)
        # Expected: [Vec3] Output: (157, 157, 157)
        # Regex to find: [Vec3] Output: \((\d+), (\d+), (\d+)\)
        match = re.search(r"Output: \((\d+), (\d+), (\d+)\)", output)
        if match:
            x, y, z = int(match.group(1)), int(match.group(2)), int(match.group(3))
            print(f"[TEST] Found Output Vector: ({x}, {y}, {z})")

            # Allow tolerance +/- 2
            expected = 157
            if abs(x - expected) <= 2 and abs(y - expected) <= 2 and abs(z - expected) <= 2:
                print(f"[TEST] SUCCESS: Numerical Verification PASSED. (Target: {expected}, Got: {x})")
                print(f"[TEST] Total Validations: {count}")
                sys.exit(0)
            else:
                print(f"[TEST] FAILURE: Numerical Verification FAILED. Expected ~{expected}, Got ({x}, {y}, {z})")
                sys.exit(1)
        else:
            print("[TEST] FAILURE: Could not find numerical output in log.")
            print("Full Output:")
            print(output)
            sys.exit(1)

    except subprocess.CalledProcessError as e:
        print(f"[TEST] FAILURE: Cargo run failed with code {e.returncode}")
        print(e.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"[TEST] FAILURE: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_integration()
