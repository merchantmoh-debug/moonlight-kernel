import sys
import shutil
import time
import subprocess
import os
import argparse
from rich.console import Console
from rich.panel import Panel
from rich.layout import Layout
from rich.live import Live
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import box
from rich.text import Text

# Initialize Console
console = Console()

class MoonlightAdapter:
    def __init__(self):
        self.root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.bridge_path = os.path.join(self.root_dir, "bridge-rust")
        self.moon_path = shutil.which("moon")
        self.cargo_path = shutil.which("cargo")

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
        console.print(Panel(title, style="bold cyan", title="The Neuro-Symbolic Bridge"))

    def scan_environment(self):
        table = Table(title="System Diagnostics", box=box.ROUNDED)
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

        # Pass absolute path to avoid CWD confusion
        cmd.extend(["--kernel", os.path.abspath(final_kernel)])

        console.print(f"[bold yellow]Igniting Bridge...[/bold yellow] (Kernel: {os.path.basename(final_kernel)})")
        
        try:
            # We run in the bridge directory so cargo works naturally
            process = subprocess.Popen(
                cmd,
                cwd=self.bridge_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # Stream Output
            with Live(console=console, refresh_per_second=10) as live:
                while True:
                    output = process.stdout.readline()
                    if output == '' and process.poll() is not None:
                        break
                    if output:
                        if "Neuronal Validation: ACTIVE" in output:
                            console.print("[bold green]✔ NEURONAL VALIDATION: ACTIVE[/bold green]")
                        elif "BENCHMARK" in output:
                            console.print(f"[bold cyan]{output.strip()}[/bold cyan]")
                        elif "CSV" in output:
                            pass # suppress raw csv
                        else:
                            console.print(output.strip(), style="dim")

            if process.returncode != 0:
                 err = process.stderr.read()
                 console.print(f"[bold red]Bridge Crash:[/bold red]\n{err}")

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

if __name__ == "__main__":
    main()
