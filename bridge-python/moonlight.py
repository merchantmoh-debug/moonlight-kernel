#!/usr/bin/env python3
import argparse
import sys
import shutil
import subprocess
import os

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn
except ImportError:
    class Console:
        def print(self, *args, **kwargs):
            text = " ".join(str(a) for a in args)
            import re
            text = re.sub(r'\[.*?\]', '', text)
            print(text)
    class Panel:
        def __init__(self, renderable, **kwargs): self.renderable = renderable
        def __str__(self): return str(self.renderable)
    class Progress:
        def __init__(self, *args, **kwargs): pass
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def add_task(self, *args, **kwargs): pass
    class SpinnerColumn: pass
    class TextColumn:
        def __init__(self, *args, **kwargs): pass

# Ensure local imports work
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Unified Adapter
try:
    from adapter import MoonlightAdapter
except ImportError:
    print("CRITICAL: Adapter module missing. Run from repository root.")
    sys.exit(1)

console = Console()

def print_header(mode="NEUTRAL"):
    color = "green" if mode == "KINETIC" else "blue"
    console.print(Panel(f"[bold {color}]MOONLIGHT KERNEL v2.2 (KINETIC EDITION)[/]", subtitle="The Neuro-Symbolic Polyglot Bridge"))

def run_command(cmd, cwd=None, description="Executing"):
    """Executes a shell command with visual feedback."""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        progress.add_task(description=description, total=None)
        try:
            result = subprocess.run(
                cmd,
                cwd=cwd,
                check=True,
                capture_output=True,
                text=True,
                shell=False
            )
            return result.stdout
        except subprocess.CalledProcessError as e:
            console.print(f"[bold red]ERROR in '{description}':[/]")
            console.print(e.stderr)
            sys.exit(1)

def build_kernel(mock_mode=False):
    """Builds the Wasm Kernel and Rust Bridge."""
    console.print("[bold]Phase 1: Synthesis & Compilation[/]")

    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    if mock_mode:
        console.print("[yellow]Building MOCK KERNEL (Rust implementation of MoonBit logic)...[/]")
        run_command(
            ["cargo", "build", "--target", "wasm32-unknown-unknown", "--release"],
            cwd=os.path.join(root_dir, "core", "mock_kernel"),
            description="Compiling Mock Kernel (Wasm)"
        )

        # Deploy Artifact
        target_dir = os.path.join(root_dir, "core", "target", "wasm", "release", "build", "lib")
        os.makedirs(target_dir, exist_ok=True)
        shutil.copy(
            os.path.join(root_dir, "core", "mock_kernel", "target", "wasm32-unknown-unknown", "release", "mock_kernel.wasm"),
            os.path.join(target_dir, "lib.wasm")
        )
        console.print("[green]Mock Kernel Deployed.[/]")
    else:
        # Real build (if moon exists)
        console.print("[cyan]Synthesizing MoonBit Kernel...[/]")
        run_command(
            [sys.executable, "scripts/synthesize_moonbit_kernel.py"],
            cwd=root_dir,
            description="Synthesizing Logic"
        )
        console.print("[cyan]Compiling MoonBit Core...[/]")
        run_command(
            ["moon", "build", "--target", "wasm"],
            cwd=os.path.join(root_dir, "core"),
            description="Compiling MoonBit"
        )

    console.print("[bold]Phase 2: Bridge Construction[/]")
    run_command(
        ["cargo", "build", "--release"],
        cwd=os.path.join(root_dir, "bridge-rust"),
        description="Compiling Rust Host"
    )
    console.print("[bold green]Build Complete.[/]")

def run_tests():
    """Runs the integration test suite."""
    console.print("[bold]Phase 4: Verification[/]")
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    try:
        run_command(
            [sys.executable, "tests/test_integration.py"],
            cwd=root_dir,
            description="Running Integration Tests"
        )
        console.print("[bold green]All Tests Passed.[/]")
    except Exception as e:
         console.print("[bold red]Tests Failed.[/]")
         sys.exit(1)

def main():
    print_header("KINETIC")
    adapter = MoonlightAdapter()

    parser = argparse.ArgumentParser(description="Moonlight CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    build_parser = subparsers.add_parser("build", help="Build the kernel and bridge")
    build_parser.add_argument("--mock", action="store_true", help="Force mock kernel build")

    subparsers.add_parser("run", help="Run the bridge")
    subparsers.add_parser("monitor", help="Run Kinetic Dashboard")
    subparsers.add_parser("benchmark", help="Run performance benchmarks")
    subparsers.add_parser("test", help="Run tests")

    args = parser.parse_args()

    # Step 0: Proprioception (Unified)
    adapter.scan_environment()

    if args.command == "build":
        has_moon = bool(shutil.which("moon"))
        mock_mode = args.mock or (not has_moon)
        build_kernel(mock_mode=mock_mode)

    elif args.command == "run":
        adapter.ignite(bench_mode=False)

    elif args.command == "monitor":
        # Monitor is now same as run in adapter (it has built-in TUI)
        adapter.ignite(bench_mode=False)

    elif args.command == "benchmark":
        adapter.ignite(bench_mode=True)

    elif args.command == "test":
        # Check artifact
        if not os.path.exists("core/target/wasm/release/build/lib/lib.wasm"):
             console.print("[yellow]Artifact missing. Building Mock Kernel first...[/]")
             build_kernel(mock_mode=True)
        run_tests()

if __name__ == "__main__":
    main()
