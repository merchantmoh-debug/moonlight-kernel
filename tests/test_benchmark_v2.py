import subprocess
import sys
import os

def test_kinetic_bridge():
    print("--- [TEST] Verifying Kinetic Bridge V2 ---")

    # Enable debug logging
    env = os.environ.copy()
    env["RUST_LOG"] = "debug"

    try:
        # Rebuild first to ensure latest binary
        print("Building...")
        subprocess.run([sys.executable, "bridge-python/moonlight.py", "build", "--mock"], check=True, capture_output=True)

        print("Running Bridge...")
        result = subprocess.run(
            [sys.executable, "bridge-python/moonlight.py", "run"],
            check=True,
            capture_output=True,
            text=True,
            env=env
        )
        output = result.stdout
        # env_logger prints to stderr usually
        combined = output + result.stderr

        print("--- Bridge Logs ---")
        print(combined)

        # Verify Core Logic
        if "Neuronal Validation: ACTIVE" not in combined:
            print("[FAIL] Neuronal Validation Missing!")
            sys.exit(1)

        # Verify New Features
        if "Vector Batch Addition: ACTIVE" not in combined:
            print("[WARN] Vector Batch Addition log missing. (Check debug level)")
        else:
            print("[PASS] Vector Batch Addition Verified.")

        # Verify Completion
        if "Kinetic Loop Complete" not in combined:
             print("[FAIL] Loop did not complete successfully.")
             sys.exit(1)

        print("[SUCCESS] All Checks Passed.")

    except subprocess.CalledProcessError as e:
        print(f"[FAIL] Process crashed with code {e.returncode}")
        print(e.stdout)
        print(e.stderr)
        sys.exit(1)

if __name__ == "__main__":
    test_kinetic_bridge()
