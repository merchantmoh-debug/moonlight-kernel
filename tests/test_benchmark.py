import subprocess
import os
import sys
import unittest
import re

class TestBenchmark(unittest.TestCase):
    def test_benchmark_mode(self):
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        adapter_path = os.path.join(root_dir, "bridge-python", "adapter.py")
        env = os.environ.copy()
        # Add bridge-python to PYTHONPATH so imports work
        env["PYTHONPATH"] = os.path.join(root_dir, "bridge-python")

        print(f"Running benchmark via {adapter_path}...")

        try:
            # Run ignite --bench
            # Note: We rely on cargo run being available and compiled
            result = subprocess.run(
                [sys.executable, adapter_path, "ignite", "--bench"],
                capture_output=True,
                text=True,
                timeout=120, # Increased timeout just in case of slow compilation
                env=env
            )

            output = result.stdout

            # Check for return code
            if result.returncode != 0:
                print("STDOUT:", output)
                print("STDERR:", result.stderr)
                self.fail(f"Benchmark process exited with code {result.returncode}")

            # Check for benchmark data
            self.assertIn("BENCHMARK_DATA:", output, "Benchmark data missing from output")

            found = False
            # Extract and parse
            for line in output.splitlines():
                clean_line = re.sub(r'\x1b\[[0-9;]*m', '', line)
                if "BENCHMARK_DATA:" in clean_line:
                    try:
                        parts = clean_line.split("BENCHMARK_DATA:")[1].strip().split(",")
                        vecs_sec = float(parts[0].split("=")[1])
                        mb_sec = float(parts[1].split("=")[1])

                        print(f"\n[BENCHMARK RESULT] Vectors/sec: {vecs_sec:,.2f} | MB/s: {mb_sec:.2f}")

                        # Assertion: Throughput > 1000 (Very safe baseline to ensure it ran)
                        self.assertGreater(vecs_sec, 1000.0, "Throughput too low! optimization failed?")
                        found = True
                        break
                    except Exception as e:
                        print(f"Parse Error on line '{clean_line}': {e}")

            self.assertTrue(found, "Could not parse BENCHMARK_DATA line")

        except subprocess.TimeoutExpired:
            self.fail("Benchmark timed out")

if __name__ == "__main__":
    unittest.main()
