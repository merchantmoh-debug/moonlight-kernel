import sys
import time
import subprocess
import os
import shutil

# Project Moonlight: The AI Adapter ("Qi")
# "The Mind directs the Body."

def check_dependencies():
    """Checks for necessary tools."""
    moon_path = shutil.which("moon")
    cargo_path = shutil.which("cargo")

    status = True
    if not moon_path:
        print("[Qi] WARNING: 'moon' CLI not found. MoonBit kernel synthesis/build disabled.")
        status = False

    if not cargo_path:
        print("[Qi] CRITICAL: 'cargo' not found. Rust bridge cannot run.")
        status = False

    return status

def build_moonbit_kernel():
    print("[Qi] Building MoonBit Kernel (Nervous System)...")
    core_path = os.path.join("..", "core")

    try:
        if shutil.which("moon"):
            subprocess.run(
                ["moon", "build", "--target", "wasm"],
                cwd=core_path,
                check=True,
                capture_output=False
            )
            print("[Qi] Kernel Synapse Constructed.")
        else:
            print("[Qi] Skipping build (toolchain missing). Verifying existing artifact...")
            # Check if artifact exists
            wasm_path = os.path.join(core_path, "target", "wasm", "release", "build", "lib", "lib.wasm")
            if os.path.exists(wasm_path):
                 print(f"[Qi] Found existing artifact: {wasm_path}")
            else:
                 print(f"[Qi] WARNING: No Wasm artifact found at {wasm_path}")
                 print("     If you are testing without 'moon', ensure a Mock Kernel is built.")

    except subprocess.CalledProcessError as e:
        print(f"[Qi] Kernel Build Failure: {e}")
    except Exception as e:
        print(f"[Qi] Build Error: {e}")

def ignite_kernel():
    print("[Qi] Igniting Moonlight Kernel (Rust Bridge)...")
    
    rust_bridge_path = os.path.join("..", "bridge-rust")
    
    try:
        # Ignite the "Beast"
        result = subprocess.run(
            ["cargo", "run", "--quiet"], 
            cwd=rust_bridge_path,
            check=True,
            capture_output=False
        )
        print("[Qi] Kernel Cycle Complete.")
        
    except FileNotFoundError:
        print("[Qi] Error: Cargo not found. Is Rust installed?")
    except subprocess.CalledProcessError as e:
        print(f"[Qi] Kernel Failure: {e}")
        print("[Qi] Diagnosis: The Rust bridge crashed. Check if the Wasm kernel is valid.")

if __name__ == "__main__":
    print("Moonlight AI Adapter v2.1 (Kinetic)")
    print("Subject: Neuro-Symbolic Tensor Flow")
    
    check_dependencies()

    # Simulated "Thought" -> Action
    start_time = time.time()

    # 1. Build Nervous System
    build_moonbit_kernel()

    # 2. Ignite Body
    ignite_kernel()

    end_time = time.time()
    
    print(f"[Qi] OODA Loop Time: {(end_time - start_time)*1000:.2f}ms")
