import sys
import time
import subprocess
import os

# Project Moonlight: The AI Adapter ("Qi")
# "The Mind directs the Body."

def build_moonbit_kernel():
    print("[Qi] Building MoonBit Kernel (Nervous System)...")
    core_path = os.path.join("..", "core")

    try:
        subprocess.run(
            ["moon", "build", "--target", "wasm"],
            cwd=core_path,
            check=True,
            capture_output=False
        )
        print("[Qi] Kernel Synapse Constructed.")
    except FileNotFoundError:
        print("[Qi] WARNING: 'moon' CLI not found. Skipping build step.")
        print("     Ensure 'core/target/wasm/release/build/lib/lib.wasm' exists.")
    except subprocess.CalledProcessError as e:
        print(f"[Qi] Kernel Build Failure: {e}")
        # We proceed, hoping an old kernel exists
    except Exception as e:
        print(f"[Qi] Build Error: {e}")

def ignite_kernel():
    print("[Qi] Igniting Moonlight Kernel (Rust Bridge)...")
    
    # In a real deployment, we would use shared_memory (shm) to pass tensors.
    # For this MVP, we orchestrate the process.
    
    rust_bridge_path = os.path.join("..", "bridge-rust")
    
    try:
        # Ignite the "Beast"
        # We use --release for speed, but --quiet to reduce noise
        # Using cargo run will compile if needed
        result = subprocess.run(
            ["cargo", "run", "--quiet"], 
            cwd=rust_bridge_path,
            check=True,
            capture_output=False # Let it stream towards stdout
        )
        print("[Qi] Kernel Cycle Complete.")
        
    except FileNotFoundError:
        print("[Qi] Error: Cargo not found. Is Rust installed?")
    except subprocess.CalledProcessError as e:
        print(f"[Qi] Kernel Failure: {e}")
        print("[Qi] Diagnosis: Did you build the MoonBit kernel? Is the Wasm file present?")

if __name__ == "__main__":
    print("Moonlight AI Adapter v2.0 (Kinetic)")
    print("Subject: Neuro-Symbolic Tensor Flow")
    
    # Simulated "Thought" -> Action
    start_time = time.time()

    # 1. Build Nervous System
    build_moonbit_kernel()

    # 2. Ignite Body
    ignite_kernel()

    end_time = time.time()
    
    print(f"[Qi] OODA Loop Time: {(end_time - start_time)*1000:.2f}ms")
