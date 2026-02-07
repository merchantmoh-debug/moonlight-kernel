import sys
import time
import subprocess
import os

# Project Moonlight: The AI Adapter ("Qi")
# "The Mind directs the Body."

def ignite_kernel():
    print("[Qi] Igniting Moonlight Kernel (Rust Bridge)...")
    
    # In a real deployment, we would use shared_memory (shm) to pass tensors.
    # For this MVP, we orchestrate the process.
    
    rust_bridge_path = os.path.join("..", "bridge-rust")
    
    try:
        # Ignite the "Beast"
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

if __name__ == "__main__":
    print("Moonlight AI Adapter v1.0")
    print("Subject: Neuro-Symbolic Tensor Flow")
    
    # Simulated "Thought" -> Action
    start_time = time.time()
    ignite_kernel()
    end_time = time.time()
    
    print(f"[Qi] OODA Loop Time: {(end_time - start_time)*1000:.2f}ms")
