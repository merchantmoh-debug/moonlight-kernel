# ==============================================================================
# Ark V4 Swarm Simulator (The Ocean)
# ==============================================================================
# "A million drops make an ocean."
#
# Simulates a Federated Learning round with Homomorphic Encryption (Mocked).
# ==============================================================================

import time
import random

class SovereignWorker:
    def __init__(self, id):
        self.id = f"Worker-{id:04d}"
        self.compute_power = random.uniform(0.5, 2.0) # TFLOPS
        self.status = "IDLE"

    def join_network(self):
        print(f"[{self.id}] Connecting to The Ocean via WebRTC...")
        time.sleep(0.05)
        self.status = "CONNECTED"

    def train(self, global_step):
        if self.status != "CONNECTED": return 0.0
        # Simulating Homomorphic Gradient Calculation
        loss = random.uniform(0.1, 0.5) / (global_step + 1)
        print(f"[{self.id}] Training Step {global_step} | Loss: {loss:.4f} | (Encrypted)")
        return loss

class TheOcean:
    def __init__(self, size=10):
        self.workers = [SovereignWorker(i) for i in range(size)]
        self.global_model_accuracy = 0.0

    def ignite(self):
        print("\n=== INITIATING MOONLIGHT V4 PROTOCOL ===")
        print(f"Swarm Size: {len(self.workers)} Devices")
        print("Encryption Scheme: CKKS (Simulated)")
        print("=======================================\n")

        # 1. Connect
        for w in self.workers:
            w.join_network()

        # 2. Train Loop
        for step in range(1, 4):
            print(f"\n--- Global Step {step} ---")
            total_loss = 0
            for w in self.workers:
                total_loss += w.train(step)
            
            avg_loss = total_loss / len(self.workers)
            self.global_model_accuracy += (1.0 / avg_loss) * 0.1
            print(f">>> CRITICAL: Aggregating Encrypted Gradients... Model Accuracy: {self.global_model_accuracy:.2f}%")
            time.sleep(0.5)

        print("\n=== PROTOCOL COMPLETE ===")
        print("The Swarm has learned.")

if __name__ == "__main__":
    ocean = TheOcean(size=5) # Simulate 5 nodes
    ocean.ignite()
