import sys
import shutil
import time
import subprocess
import os
import argparse
import psutil
import random
import math
from rich.console import Console
from rich.panel import Panel
from rich.layout import Layout
from rich.live import Live
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich import box
from rich.text import Text
from rich.align import Align

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
        # Simulate Analysis
        self.entropy_level = random.uniform(0.1, 0.4)
        self.urgency_level = 0.9 if "kinetic" in context else 0.5
        self.threat_level = 0.05 # Low threat in controlled env

        return {
            "ENTROPY": self.entropy_level,
            "URGENCY": self.urgency_level,
            "THREAT": self.threat_level
        }

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
        console.print(Panel(Align.center(title), style="bold cyan", title="The Neuro-Symbolic Bridge (V2.0)"))

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
            while not progress.finished:
                progress.update(task1, advance=5)
                time.sleep(0.05)

        # Display Gate Status
        gate_table = Table(box=box.SIMPLE, show_header=False)
        gate_table.add_row("[bold]ENTROPY[/bold]", f"{metrics['ENTROPY']:.2f}", "[green]STABLE[/green]" if metrics['ENTROPY'] < 0.5 else "[red]CHAOS[/red]")
        gate_table.add_row("[bold]URGENCY[/bold]", f"{metrics['URGENCY']:.2f}", "[red]WAR SPEED[/red]" if metrics['URGENCY'] > 0.8 else "[blue]CRUISE[/blue]")
        console.print(Panel(gate_table, title="Virtual Nervous System", style="bold magenta"))

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

            # Dashboard State
            logs = []
            start_time = time.time()

            # Layout
            layout = Layout()
            layout.split_column(
                Layout(name="header", size=3),
                Layout(name="body", ratio=1),
                Layout(name="footer", size=3)
            )

            layout["header"].update(Panel(f"Moonlight Bridge (Kernel: {os.path.basename(final_kernel)})", style="bold cyan"))

            # HEADLESS CHECK: If not TTY, disable TUI to prevent pipe deadlock
            if sys.stdout.isatty():
                with Live(layout, console=console, refresh_per_second=10) as live:
                    while True:
                        output = process.stdout.readline()

                        if output == '' and process.poll() is not None:
                            break

                        if output:
                            line = output.strip()
                            if "Neuronal Validation: ACTIVE" in line:
                                logs.append("[bold green]✔ NEURONAL VALIDATION: ACTIVE[/bold green]")
                            elif "BENCHMARK" in line:
                                logs.append(f"[bold cyan]{line}[/bold cyan]")
                            elif "Validation FAILED" in line:
                                logs.append(f"[bold red]{line}[/bold red]")
                            elif "ERROR" in line:
                                logs.append(f"[bold red]{line}[/bold red]")
                            elif "[MODE: ZERO-COPY]" in line:
                                 logs.append(f"[bold magenta]{line}[/bold magenta]")
                            elif line:
                                clean_line = line.replace("INFO", "[blue]INFO[/blue]").replace("WARN", "[yellow]WARN[/yellow]")
                                logs.append(clean_line)

                            if len(logs) > 15:
                                logs.pop(0)

                        log_content = "\n".join(logs)
                        layout["body"].update(Panel(log_content, title="Kernel Log Stream", border_style="blue"))

                        cpu = psutil.cpu_percent()
                        ram = psutil.virtual_memory().percent
                        elapsed = int(time.time() - start_time)
                        pulse = "⚡" if int(time.time() * 2) % 2 == 0 else " "
                        stats = f"{pulse} CPU: {cpu}% | RAM: {ram}% | T+{elapsed}s | Mode: {'BENCH' if bench_mode else 'KINETIC'}"
                        layout["footer"].update(Panel(stats, title="System Telemetry", border_style="green"))
            else:
                # HEADLESS MODE (For Tests)
                while True:
                    output = process.stdout.readline()
                    if output == '' and process.poll() is not None:
                        break
                    if output:
                        print(output.strip())

            if process.returncode != 0:
                 err = process.stderr.read()
                 console.print(f"[bold red]Bridge Crash:[/bold red]\n{err}")
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
