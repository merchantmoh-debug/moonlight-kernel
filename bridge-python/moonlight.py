#!/usr/bin/env python3
import argparse
import sys
import shutil
import subprocess
import time
import os
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

# Ensure local imports work
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

console = Console()

# --- FRAMEWORK ZERO: THE SOUND HEART ---
# "Speed is Safety."

def print_header(mode="NEUTRAL"):
    color = "green" if mode == "KINETIC" else "blue"
    console.print(Panel(f"[bold {color}]MOONLIGHT KERNEL v2.2 (KINETIC EDITION)[/]", subtitle="The Neuro-Symbolic Polyglot Bridge"))

def check_env():
    """Proprioception: Sense the environment."""
    table = Table(title="System Proprioception")
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="green")

    tools = {
        "moon": shutil.which("moon"),
        "cargo": shutil.which("cargo"),
        "rustc": shutil.which("rustc"),
        "python3": shutil.which("python3")
    }

    all_good = True
    has_moon = bool(tools["moon"])

    for tool, path in tools.items():
        status = "[bold green]ACTIVE[/]" if path else "[bold red]MISSING[/]"
        if not path and tool != "moon":
            all_good = False
        table.add_row(tool, status)

    console.print(table)

    if not has_moon:
        console.print("[yellow]WARNING: 'moon' CLI missing. Operating in MOCK KERNEL mode.[/]")

    if not all_good:
        console.print("[bold red]CRITICAL: Essential tools missing. Aborting.[/]")
        sys.exit(1)

    return has_moon

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
                text=True
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

def run_bridge(bench=False, iterations=None):
    """Ignites the bridge."""
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    bridge_dir = os.path.join(root_dir, "bridge-rust")

    cmd = ["cargo", "run", "--release", "--quiet", "--"]
    if bench:
        cmd.append("--bench")
    if iterations:
        cmd.extend([str(iterations)])

    console.print(f"[bold]Phase 3: Ignition ({'Benchmark' if bench else 'Kinetic Run'})[/]")

    # We stream output for run mode
    process = subprocess.Popen(
        cmd,
        cwd=bridge_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, # Merge stderr into stdout to prevent deadlock
        text=True,
        bufsize=1,
        universal_newlines=True
    )

    # Simple output streaming
    for line in process.stdout:
        line = line.strip()
        if "BENCHMARK" in line:
            console.print(f"[bold cyan]{line}[/]")
        elif "ERROR" in line:
            console.print(f"[bold red]{line}[/]")
        elif "Active" in line or "Connected" in line:
            console.print(f"[green]{line}[/]")
        else:
            console.print(line)

    process.wait()
    if process.returncode != 0:
        console.print(f"[bold red]Bridge Failed with code {process.returncode}[/]")
        console.print(process.stderr.read())
        sys.exit(process.returncode)

def run_monitor_cmd():
    """Ignites the bridge and connects the dashboard."""
    console.print("[bold]Phase 4: Neuro-Symbolic Connection[/]")
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    bridge_dir = os.path.join(root_dir, "bridge-rust")

    # Run in benchmark mode for continuous output (high iteration count in bench mode)
    cmd = ["cargo", "run", "--release", "--quiet", "--", "--bench"]

    process = subprocess.Popen(
        cmd,
        cwd=bridge_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
        universal_newlines=True
    )

    try:
        from dashboard import run_monitor
        run_monitor(process)
    except ImportError:
        console.print("[red]Dashboard module failed to load. Streaming raw output...[/]")
        for line in process.stdout:
            print(line, end="")

def run_tests():
    """Runs the integration test suite."""
    console.print("[bold]Phase 4: Verification[/]")
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Reuse existing test script but wrap it
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

    parser = argparse.ArgumentParser(description="Moonlight CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Build Command
    build_parser = subparsers.add_parser("build", help="Build the kernel and bridge")
    build_parser.add_argument("--mock", action="store_true", help="Force mock kernel build")

    # Run Command
    run_parser = subparsers.add_parser("run", help="Run the bridge")

    # Monitor Command
    monitor_parser = subparsers.add_parser("monitor", help="Run Kinetic Dashboard")

    # Test Command
    test_parser = subparsers.add_parser("test", help="Run tests")

    # Benchmark Command
    bench_parser = subparsers.add_parser("benchmark", help="Run performance benchmarks")

    args = parser.parse_args()

    # Step 0: Proprioception
    has_moon = check_env()

    # Signal Gate (Mock Entropy Check)
    # console.print("[dim]Signal Entropy: LOW | Urgency: HIGH[/]")

    if args.command == "build":
        # Auto-detect mock mode if moon is missing
        mock_mode = args.mock or (not has_moon)
        build_kernel(mock_mode=mock_mode)

    elif args.command == "run":
        run_bridge()

    elif args.command == "monitor":
        run_monitor_cmd()

    elif args.command == "benchmark":
        run_bridge(bench=True)

    elif args.command == "test":
        # Ensure build exists first? No, assume user built or let makefile handle it.
        # But we can try to build mock if needed.
        if not os.path.exists("core/target/wasm/release/build/lib/lib.wasm"):
             console.print("[yellow]Artifact missing. Building Mock Kernel first...[/]")
             build_kernel(mock_mode=True)
        run_tests()

if __name__ == "__main__":
    main()
