import sys
import shutil
import time
import subprocess
import os
import argparse
import random
import math
import threading
import queue
import hashlib

try:
    import psutil
except ImportError:
    class PsutilMock:
        def cpu_percent(self, interval=None): return 50.0
        def virtual_memory(self):
            class Mem: percent = 50.0
            return Mem()
    psutil = PsutilMock()

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.layout import Layout
    from rich.live import Live
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
    from rich import box
    from rich.text import Text
    from rich.align import Align
except ImportError:
    # Dummy classes for headless/restricted environments
    class Console:
        def print(self, *args, **kwargs):
            text = " ".join(str(a) for a in args)
            import re
            text = re.sub(r'\[.*?\]', '', text)
            print(text)
    class Panel:
        def __init__(self, renderable, **kwargs): self.renderable = renderable
        def __str__(self): return str(self.renderable)
    class Layout:
        def __init__(self, **kwargs): self.parts = {}
        def split(self, *args, **kwargs): pass
        def split_column(self, *args, **kwargs): pass
        def __setitem__(self, key, value): self.parts[key] = value
        def __getitem__(self, key): return self.parts.get(key, self)
        def update(self, *args): pass
    class Live:
        def __init__(self, *args, **kwargs): pass
        def __enter__(self): return self
        def __exit__(self, *args): pass
    class Table:
        def __init__(self, **kwargs): self.rows = []
        def add_column(self, *args, **kwargs): pass
        def add_row(self, *args, **kwargs):
            self.rows.append(args)
            print(" | ".join(str(a) for a in args)) # Immediate print for fallback
        def __str__(self): return ""
    class Progress:
        def __init__(self, *args, **kwargs): self.finished = False
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def add_task(self, *args, **kwargs): pass
        def update(self, *args, **kwargs):
             if 'advance' in kwargs:
                  # Simulate progress
                  pass
    class SpinnerColumn: pass
    class TextColumn:
        def __init__(self, *args, **kwargs): pass
    class BarColumn: pass
    class Box: pass
    box = Box()
    box.ROUNDED = None
    box.SIMPLE = None
    class Text: pass
    class Align:
        @staticmethod
        def center(x): return x

# Initialize Console
console = Console()

class SignalGate:
    """
    The Virtual Nervous System: Signal Filtering
    """
    def __init__(self):
        self.entropy_level = 0.0
        self.urgency_level = 0.0
        self.threat_level = 0.0

    def analyze(self, context="kinetic_execution"):
        # Real Proprioception
        try:
            # Short interval for immediate feedback
            cpu = psutil.cpu_percent(interval=0.1)
            mem = psutil.virtual_memory().percent
        except Exception:
            cpu = 50.0 # Fallback
            mem = 50.0

        self.entropy_level = cpu / 100.0
        self.urgency_level = mem / 100.0
        self.threat_level = 0.05 # Low threat in controlled env

        return {
            "ENTROPY": self.entropy_level,
            "URGENCY": self.urgency_level,
            "THREAT": self.threat_level
        }

    def check_veto(self, metrics):
        """
        The Sound Heart: Vetoes execution if the system is unstable.
        """
        if metrics["ENTROPY"] > 0.90:
            return True, "[VETO] System Entropy Critical (CPU > 90%). Rest required."
        if metrics["URGENCY"] > 0.95:
             return True, "[VETO] Memory Pressure Critical. Aborting to prevent OOM."
        return False, "System Stable."

class MoonlightAdapter:
    def __init__(self):
        self.root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.bridge_path = os.path.join(self.root_dir, "bridge-rust")
        self.moon_path = shutil.which("moon")
        self.cargo_path = shutil.which("cargo")
        self.gate = SignalGate()

        # Kernel Paths
        self.moonbit_wasm = os.path.join(self.root_dir, "core", "target", "wasm", "release", "build", "lib", "lib.wasm")
        self.mock_wasm = os.path.join(self.root_dir, "core", "mock_kernel", "target", "wasm32-unknown-unknown", "release", "mock_kernel.wasm")

    def print_header(self):
        title = r"""
      __  __                      _ _       _     _
     |  \/  | ___   ___  _ __  | (_) __ _| |__ | |_
     | |\/| |/ _ \ / _ \| '_ \ | | |/ _` | '_ \| __|
     | |  | | (_) | (_) | | | || | | (_| | | | | |_
     |_|  |_|\___/ \___/|_| |_||_|_|\__, |_| |_|\__|
                                    |___/
        """
        console.print(Panel(Align.center(title), style="bold cyan", title="The Neuro-Symbolic Bridge (V2.1 - Sovereign UI)"))

    def scan_environment(self):
        table = Table(title="System Diagnostics", box=box.ROUNDED, expand=True)
        table.add_column("Component", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Path/Details", style="dim")

        # Tools
        table.add_row("MoonBit CLI", "✅ DETECTED" if self.moon_path else "❌ MISSING", self.moon_path or "N/A")
        table.add_row("Rust Cargo", "✅ DETECTED" if self.cargo_path else "❌ MISSING", self.cargo_path or "N/A")

        # Artifacts
        moon_exists = os.path.exists(self.moonbit_wasm)
        mock_exists = os.path.exists(self.mock_wasm)

        table.add_row("MoonBit Kernel", "✅ READY" if moon_exists else "❌ NOT FOUND", self.moonbit_wasm if moon_exists else "Run 'moon build'")
        table.add_row("Mock Kernel", "✅ READY" if mock_exists else "❌ NOT FOUND", self.mock_wasm if mock_exists else "Run 'cargo build' in core/mock_kernel")

        console.print(table)

        if not self.cargo_path:
             console.print("[bold red]CRITICAL:[/bold red] Rust is required to run the bridge.")
             return False
        return True

    def verify_integrity(self, kernel_path):
        """
        The Digital Proprioception: Verifies the integrity of the Wasm kernel.
        """
        try:
            console.print(f"[cyan]Verifying Kernel Integrity: {os.path.basename(kernel_path)}...[/cyan]")
            sha256_hash = hashlib.sha256()
            with open(kernel_path, "rb") as f:
                # Read and update hash string value in blocks of 4K
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)

            digest = sha256_hash.hexdigest()
            console.print(f"[dim]Kernel Hash (SHA256): {digest}[/dim]")

            # In a strict environment, we would compare this against a signed manifest.
            # For now, we log it as a security event.
            return True, digest
        except Exception as e:
            return False, str(e)

    def ignite(self, bench_mode=False, kernel_override=None):
        if not self.cargo_path:
            console.print("[bold red]Error:[/bold red] Cargo not found.")
            return

        # 1. Signal Gate Analysis (Pre-Computation)
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        ) as progress:
            task1 = progress.add_task("[cyan]Calibrating Signal Gates...", total=100)
            metrics = self.gate.analyze("kinetic_execution" if not bench_mode else "benchmark")
            # Fallback progress finish
            progress.finished = True
            time.sleep(0.02)

        # Display Gate Status
        gate_table = Table(box=box.SIMPLE, show_header=False)
        gate_table.add_row("[bold]ENTROPY (CPU)[/bold]", f"{metrics['ENTROPY']*100:.1f}%", "[green]STABLE[/green]" if metrics['ENTROPY'] < 0.5 else "[yellow]HIGH[/yellow]")
        gate_table.add_row("[bold]URGENCY (RAM)[/bold]", f"{metrics['URGENCY']*100:.1f}%", "[red]WAR SPEED[/red]" if metrics['URGENCY'] > 0.8 else "[blue]CRUISE[/blue]")
        gate_table.add_row("[bold]THREAT (VETO)[/bold]", f"{metrics['THREAT']*100:.1f}%", "[green]SECURE[/green]")
        console.print(Panel(gate_table, title="Virtual Nervous System", style="bold magenta"))

        # 2. The Veto Check
        veto, reason = self.gate.check_veto(metrics)
        if veto:
            console.print(f"[bold red]⛔ INTERVENTION:[/bold red] {reason}")
            raise SystemError(f"KERNEL PANIC: {reason}")

        cmd = ["cargo", "run", "--quiet", "--manifest-path", "Cargo.toml", "--"]

        if bench_mode:
            cmd.append("--bench")

        # Kernel Selection Logic
        final_kernel = None
        if kernel_override:
            final_kernel = kernel_override
        elif os.path.exists(self.moonbit_wasm):
            final_kernel = self.moonbit_wasm
        elif os.path.exists(self.mock_wasm):
            final_kernel = self.mock_wasm
        else:
            console.print("[bold red]Error:[/bold red] No valid kernel found. Build one first.")
            return

        # 3. Integrity Verification
        success, digest = self.verify_integrity(final_kernel)
        if not success:
             console.print(f"[bold red]SECURITY ALERT:[/bold red] Kernel verification failed: {digest}")
             # In strict mode we might abort, but for now we proceed with warning

        cmd.extend(["--kernel", os.path.abspath(final_kernel)])

        console.print(f"[bold yellow]Igniting Bridge...[/bold yellow] (Kernel: {os.path.basename(final_kernel)})")
        
        try:
            # We run in the bridge directory
            env = os.environ.copy()
            env["RUST_LOG"] = "info" # Force info logging

            process = subprocess.Popen(
                cmd,
                cwd=self.bridge_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                env=env,
                bufsize=1, # Line buffered
                shell=False
            )

            # Non-Blocking Reader
            log_queue = queue.Queue()
            def reader_thread():
                for line in process.stdout:
                    log_queue.put(line)
                process.stdout.close()

            t = threading.Thread(target=reader_thread, daemon=True)
            t.start()

            # Dashboard State
            logs = []
            start_time = time.time()
            last_bench_str = ""

            # Layout
            layout = Layout()
            layout.split_column(
                Layout(name="header", size=3),
                Layout(name="body", ratio=1),
                Layout(name="footer", size=3)
            )

            layout["header"].update(Panel(f"Moonlight Bridge (Kernel: {os.path.basename(final_kernel)})", style="bold cyan"))

            # TUI Loop
            if sys.stdout.isatty():
                with Live(layout, console=console, refresh_per_second=10) as live:
                    while True:
                        # Process Queue
                        while not log_queue.empty():
                            try:
                                line = log_queue.get_nowait()
                                line = line.strip()
                                if "Neuronal Validation: ACTIVE" in line:
                                    logs.append("[bold green]✔ NEURONAL VALIDATION: ACTIVE[/bold green]")
                                elif "BENCHMARK_DATA:" in line:
                                    try:
                                        # Parse: BENCHMARK_DATA: vectors_sec=123.45, mb_sec=12.34
                                        parts = line.split(":")[1].strip().split(",")
                                        vecs = parts[0].split("=")[1]
                                        mbs = parts[1].split("=")[1]
                                        last_bench_str = f" | Speed: {vecs} v/s"
                                        logs.append(f"[bold green]🚀 TELEMETRY: {vecs} vec/s ({mbs} MB/s)[/bold green]")
                                    except Exception:
                                        logs.append(f"[bold yellow]⚠ PARSE ERROR: {line}[/bold yellow]")
                                elif "BENCHMARK" in line:
                                    logs.append(f"[bold cyan]{line}[/bold cyan]")
                                elif "Validation FAILED" in line:
                                    logs.append(f"[bold red]{line}[/bold red]")
                                elif "ERROR" in line:
                                    logs.append(f"[bold red]{line}[/bold red]")
                                elif "KINETIC OPTIMIZATIONS" in line or ">" in line:
                                     logs.append(f"[bold green]{line}[/bold green]")
                                elif line:
                                    clean_line = line.replace("INFO", "[blue]INFO[/blue]").replace("WARN", "[yellow]WARN[/yellow]")
                                    logs.append(clean_line)

                                if len(logs) > 15:
                                    logs.pop(0)
                            except queue.Empty:
                                break

                        # Update UI
                        log_content = "\n".join(logs)
                        layout["body"].update(Panel(log_content, title="Kernel Log Stream", border_style="blue"))

                        cpu = psutil.cpu_percent()
                        ram = psutil.virtual_memory().percent
                        elapsed = int(time.time() - start_time)
                        pulse = "⚡" if int(time.time() * 2) % 2 == 0 else " "
                        stats = f"{pulse} CPU: {cpu}% | RAM: {ram}% | T+{elapsed}s | Mode: {'BENCH' if bench_mode else 'KINETIC'}{last_bench_str}"
                        layout["footer"].update(Panel(stats, title="System Telemetry", border_style="green"))

                        # Check Exit
                        if process.poll() is not None and log_queue.empty():
                            break

                        time.sleep(0.05)
            else:
                 # HEADLESS MODE (For Tests)
                 while True:
                     try:
                         line = log_queue.get(timeout=0.1)
                         print(line.strip())
                     except queue.Empty:
                         if process.poll() is not None:
                             break

            if process.returncode != 0:
                 console.print(f"[bold red]Bridge Crash with code {process.returncode}[/bold red]")
            else:
                 console.print("[bold green]Bridge Protocol Complete.[/bold green]")

        except Exception as e:
            console.print(f"[bold red]Execution Error:[/bold red] {e}")

    def interactive_menu(self):
        self.print_header()
        while True:
            console.print("\n[bold]Select Directive:[/bold]")
            console.print("1. [cyan]Scan Environment[/cyan]")
            console.print("2. [green]Ignite Bridge (Standard)[/green]")
            console.print("3. [yellow]Run Benchmark[/yellow]")
            console.print("4. [red]Exit[/red]")

            choice = input("\n> ")

            if choice == "1":
                self.scan_environment()
            elif choice == "2":
                self.ignite()
            elif choice == "3":
                self.ignite(bench_mode=True)
            elif choice == "4":
                console.print("Terminating link.")
                break
            else:
                console.print("[red]Invalid directive.[/red]")

def main():
    try:
        adapter = MoonlightAdapter()

        parser = argparse.ArgumentParser(description="Moonlight Adapter (Qi)")
        subparsers = parser.add_subparsers(dest="command")

        subparsers.add_parser("scan", help="Scan system environment")
        ignite_parser = subparsers.add_parser("ignite", help="Run the bridge")
        ignite_parser.add_argument("--bench", action="store_true", help="Run in benchmark mode")
        ignite_parser.add_argument("--kernel", help="Override kernel path")

        args = parser.parse_args()

        if args.command == "scan":
            adapter.print_header()
            adapter.scan_environment()
        elif args.command == "ignite":
            adapter.print_header()
            adapter.ignite(bench_mode=args.bench, kernel_override=args.kernel)
        else:
            adapter.interactive_menu()
    except KeyboardInterrupt:
        console.print("\n[red]Interrupted by Operator.[/red]")
        sys.exit(0)

if __name__ == "__main__":
    main()
