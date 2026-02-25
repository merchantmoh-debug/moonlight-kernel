from rich.live import Live
from rich.layout import Layout
from rich.panel import Panel
from rich.align import Align
from rich.table import Table
from rich.console import Group
from rich.text import Text
import time
import threading
import re
import math

class Dashboard:
    def __init__(self, gate=None):
        self.gate = gate
        self.layout = Layout()
        self.layout.split(
            Layout(name="header", size=3),
            Layout(name="body", ratio=1),
            Layout(name="footer", size=3)
        )
        self.layout["body"].split_row(
            Layout(name="left", ratio=1),
            Layout(name="right", ratio=2),
        )
        self.layout["left"].split_column(
            Layout(name="cortex", ratio=1),
            Layout(name="signals", ratio=1),
        )
        self.layout["right"].split_column(
            Layout(name="kinetic", size=6),
            Layout(name="logs", ratio=1)
        )

        self.vectors_sec = 0.0
        self.mb_sec = 0.0
        self.logs = []
        self.throughput_history = [0.0] * 60
        self.lock = threading.Lock()
        self.start_time = time.time()
        self.mode = "Standard"

    def update_logs(self, line):
        with self.lock:
            # Parse metrics
            if "BENCHMARK_DATA:" in line:
                try:
                    parts = line.split(":")[1].strip().split(",")
                    vecs = float(parts[0].split("=")[1])
                    mbs = float(parts[1].split("=")[1])
                    self.vectors_sec = vecs
                    self.mb_sec = mbs
                    self.throughput_history.append(vecs)
                    if len(self.throughput_history) > 60:
                        self.throughput_history.pop(0)
                except:
                    pass

            # Clean log line
            clean_line = line
            if "INFO" in line: clean_line = line.replace("INFO", "[blue]INFO[/blue]")
            elif "WARN" in line: clean_line = line.replace("WARN", "[yellow]WARN[/yellow]")
            elif "ERROR" in line: clean_line = line.replace("ERROR", "[red]ERROR[/red]")
            elif "BENCHMARK" in line: clean_line = f"[bold cyan]{line}[/bold cyan]"
            elif "Validation: ACTIVE" in line: clean_line = f"[bold green]{line}[/bold green]"

            self.logs.append(clean_line)
            if len(self.logs) > 20:
                self.logs.pop(0)

    def generate_sparkline(self, data):
        # Simple text sparkline
        if not data: return ""
        chars = "  ▂▃▄▅▆▇█"
        max_val = max(data) if max(data) > 0 else 1
        return "".join([chars[int(v / max_val * 8)] for v in data])

    def get_renderable(self):
        # 1. Header
        elapsed = int(time.time() - self.start_time)
        pulse = "⚡" if int(time.time() * 2) % 2 == 0 else " "
        header_text = f"[bold white]MOONLIGHT KERNEL v2.3[/] | [cyan]{self.mode}[/] | T+{elapsed}s {pulse}"
        self.layout["header"].update(Panel(Align.center(header_text), style="on blue"))

        # 2. Cortex Status (Host)
        metrics = {"ENTROPY": 0.0, "URGENCY": 0.0, "THREAT": 0.0}
        if self.gate:
            metrics = self.gate.analyze() # Non-blocking analysis

        cpu_val = metrics["ENTROPY"] * 100
        mem_val = metrics["URGENCY"] * 100

        cortex_table = Table.grid(padding=1)
        cortex_table.add_column(style="bold cyan", justify="right")
        cortex_table.add_column(style="white")
        cortex_table.add_row("CPU Entropy:", f"{cpu_val:.1f}%")
        cortex_table.add_row("RAM Urgency:", f"{mem_val:.1f}%")
        cortex_table.add_row("Threat Lvl:", f"{metrics['THREAT']*100:.0f}%")

        self.layout["cortex"].update(Panel(
            Align.center(cortex_table, vertical="middle"),
            title="[bold]Cortex (Host)[/bold]",
            border_style="cyan"
        ))

        # 3. Signal Gate Status
        gate_status = "[green]SOUND[/green]"
        if cpu_val > 90 or mem_val > 90: gate_status = "[red]CRITICAL[/red]"
        elif cpu_val > 80: gate_status = "[yellow]STRESSED[/yellow]"

        signal_text = f"\n[bold]System State:[/bold]\n{gate_status}\n\n[dim]Veto Power Active[/dim]"
        self.layout["signals"].update(Panel(
            Align.center(signal_text, vertical="middle"),
            title="[bold]Nervous System[/bold]",
            border_style="magenta"
        ))

        # 4. Kinetic Output
        with self.lock:
            vec_sec = self.vectors_sec
            mb_sec = self.mb_sec
            sparkline = self.generate_sparkline(self.throughput_history)
            log_text = "\n".join(self.logs)

        kinetic_panel = Group(
            Align.center(f"[bold green]{vec_sec:,.0f}[/bold green] vec/s"),
            Align.center(f"[dim]{mb_sec:.2f} MB/s[/dim]"),
            Align.center(f"[{sparkline}]", vertical="bottom")
        )

        self.layout["kinetic"].update(Panel(
            kinetic_panel,
            title="[bold]Kinetic Bridge (Output)[/bold]",
            border_style="green"
        ))

        # 5. Logs
        self.layout["logs"].update(Panel(
            log_text,
            title="[bold]Neural Log Stream[/bold]",
            border_style="white"
        ))

        # 6. Footer
        footer_text = "[dim]Ark Omega-Point v112.0 | Native Mode Optimized (f32+Canary)[/dim]"
        self.layout["footer"].update(Panel(Align.center(footer_text), style="dim"))

        return self.layout
