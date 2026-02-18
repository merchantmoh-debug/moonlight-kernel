from rich.live import Live
from rich.layout import Layout
from rich.panel import Panel
from rich.align import Align
import psutil
import time
import threading
import re

class Dashboard:
    def __init__(self):
        self.layout = Layout()
        self.layout.split(
            Layout(name="header", size=3),
            Layout(name="main", ratio=1),
            Layout(name="logs", size=10)
        )
        self.layout["main"].split_row(
            Layout(name="cortex"),
            Layout(name="kinetic"),
        )

        self.vectors_sec = 0.0
        self.logs = []
        self.lock = threading.Lock()

    def update_logs(self, line):
        with self.lock:
            # Filter ansi codes if needed, but rich handles some.
            self.logs.append(line)
            if len(self.logs) > 8:
                self.logs.pop(0)

            if "BENCHMARK" in line:
                match = re.search(r"BENCHMARK:\s+([\d\.]+)", line)
                if match:
                    self.vectors_sec = float(match.group(1))

    def get_renderable(self):
        cpu = psutil.cpu_percent()
        mem = psutil.virtual_memory().percent

        self.layout["header"].update(Panel(Align.center("[bold white]MOONLIGHT KERNEL v2.2 - NEURO-SYMBOLIC DASHBOARD[/]"), style="on blue"))

        self.layout["cortex"].update(Panel(
            Align.center(f"[bold cyan]CPU: {cpu}%[/]\n[bold magenta]RAM: {mem}%[/]"),
            title="Cortex Status (Host)",
            border_style="cyan"
        ))

        with self.lock:
            vec_sec = self.vectors_sec
            log_text = "\n".join(self.logs)

        self.layout["kinetic"].update(Panel(
            Align.center(f"[bold green]{vec_sec:.2f}[/]\nvectors/sec"),
            title="Kinetic Output (Bridge)",
            border_style="green"
        ))

        self.layout["logs"].update(Panel(log_text, title="Nervous System Logs", border_style="white"))

        return self.layout

def run_monitor(process):
    dashboard = Dashboard()

    # Thread to read process output
    def reader():
        for line in process.stdout:
            if line:
                dashboard.update_logs(line.strip())

    t = threading.Thread(target=reader, daemon=True)
    t.start()

    with Live(dashboard.get_renderable(), refresh_per_second=4, screen=True) as live:
        try:
            while process.poll() is None:
                live.update(dashboard.get_renderable())
                time.sleep(0.1)
        except KeyboardInterrupt:
            process.terminate()
            pass
