import subprocess
import os
import sys

def test_integration():
    print("[TEST] Starting Integration Test...")

    # Path to bridge-rust
    bridge_rust = os.path.join(os.path.dirname(__file__), "..", "bridge-rust")

    # Run cargo run
    try:
        result = subprocess.run(
            ["cargo", "run", "--release", "--quiet"],
            cwd=bridge_rust,
            check=True,
            capture_output=True,
            text=True
        )
        output = result.stdout
        # print("[TEST] Rust Bridge Output:\n", output)

        # Verification Logic
        # We expect 5 cycles.
        # "Kernel Processed: 3 bytes"
        expected_phrase = "Neuronal Validation: ACTIVE"
        count = output.count(expected_phrase)

        if count == 5:
            print(f"[TEST] SUCCESS: Found {count} validation cycles.")
            sys.exit(0)
        else:
            print(f"[TEST] FAILURE: Expected 5 validation cycles, found {count}.")
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
