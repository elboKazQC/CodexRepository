"""WiFi view module.

This module defines the ``WifiView`` class responsible for building the
Tkinter interface dedicated to WiFi monitoring. It mirrors the logic
initially present in ``runner.py`` but is isolated for clarity.
"""

from __future__ import annotations

import csv
import logging
import os
import tkinter as tk
from datetime import datetime
from tkinter import filedialog, messagebox, ttk
from typing import List

try:
    import mplcursors
except Exception:  # pragma: no cover - optional dependency
    mplcursors = None

try:
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure
    MATPLOTLIB_AVAILABLE = True
except ImportError:  # pragma: no cover - optional dependency
    MATPLOTLIB_AVAILABLE = False
    FigureCanvasTkAgg = None  # type: ignore
    Figure = None  # type: ignore
import yaml

from heatmap_generator import generate_heatmap
from network_analyzer import NetworkAnalyzer
from network_scanner import scan_wifi as _scan_wifi

def _get_scan_wifi():
    """Return scan_wifi implementation, patched via runner when available."""
    try:  # pragma: no cover - runner may be importing
        from runner import scan_wifi as r_scan
        return r_scan
    except Exception:
        return _scan_wifi
from wifi.wifi_collector import WifiSample


class WifiView:
    """Tkinter view dedicated to WiFi collection and visualisation."""

    def __init__(self, master: tk.Misc, analyzer: NetworkAnalyzer) -> None:
        self.master = master
        self.analyzer = analyzer
        self.frame = ttk.Frame(master)

        self.samples: List[WifiSample] = []
        self.scan_results: List[dict] = []

        self.start_button: ttk.Button
        self.stop_button: ttk.Button
        self.scan_button: ttk.Button
        self.export_scan_button: ttk.Button

        self.signal_label: ttk.Label
        self.quality_label: ttk.Label
        self.tx_label: ttk.Label
        self.rx_label: ttk.Label
        self.stats_panel: ttk.LabelFrame

        self.wifi_alert_text: tk.Text
        self.scan_tree: ttk.Treeview
        self.viz_frame: ttk.Frame
        self.alerts_frame: ttk.Frame
        self.canvas: FigureCanvasTkAgg

        self.update_interval = 1000  # ms
        self.max_samples = 100
        self.config_dir = os.path.join(os.path.dirname(__file__), "..", "config")

        self.setup_style()
        self.create_interface()
        if MATPLOTLIB_AVAILABLE:
            self.setup_graphs()

    # ------------------------------------------------------------------
    # Interface creation
    # ------------------------------------------------------------------
    def setup_style(self) -> None:
        """Configure basic ttk styles for the view."""
        if "PYTEST_CURRENT_TEST" in os.environ:
            return
        try:
            style = ttk.Style()
            style.configure("Title.TLabel", font=("Helvetica", 14, "bold"))
            style.configure("Alert.TLabel", foreground="red", font=("Helvetica", 12))
            style.configure("Stats.TLabel", font=("Helvetica", 10))
            style.configure("Analyze.TButton", font=("Helvetica", 12), padding=10)
            # Custom style for the journal area on the right
            style.configure("Journal.TLabelframe", background="#f0f0f0")
            style.configure(
                "Journal.TLabelframe.Label",
                background="#f0f0f0",
                foreground="red",
            )
        except Exception:
            pass

    def create_interface(self) -> None:

        """Create all widgets used in the WiFi tab."""
        # Layout uses a grid with a journal area on the right
        self.frame.columnconfigure(1, weight=1)


        self.control_frame = ttk.LabelFrame(self.frame, text="Contr\u00f4les", padding=10)
        self.control_frame.grid(row=0, column=0, sticky="ns", padx=5, pady=5)

        self.start_button = ttk.Button(self.control_frame, text="\u25B6 D\u00e9marrer l'analyse", command=self.start_collection)
        self.start_button.pack(fill=tk.X, pady=5)

        self.stop_button = ttk.Button(self.control_frame, text="\u23F9 Arr\u00eater l'analyse", command=self.stop_collection, state=tk.DISABLED)
        self.stop_button.pack(fill=tk.X, pady=5)

        self.scan_button = ttk.Button(self.control_frame, text="\U0001F50D Scanner", command=self.scan_nearby_aps)
        self.scan_button.pack(fill=tk.X, pady=5)

        self.export_scan_button = ttk.Button(self.control_frame, text="\U0001F4C3 Exporter le scan", command=self.export_scan_results, state=tk.DISABLED)
        self.export_scan_button.pack(fill=tk.X, pady=5)


        self.viz_frame = ttk.Frame(self.frame)
        self.viz_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)


        self.scan_frame = ttk.LabelFrame(self.viz_frame, text="R\u00e9seaux d\u00e9tect\u00e9s", padding=5)
        self.scan_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)


        # Entry for filtering scan results by SSID
        self.scan_filter_var = tk.StringVar()
        self.scan_filter_var.trace_add("write", lambda *_: self._refresh_scan_tree())
        ttk.Entry(self.scan_frame, textvariable=self.scan_filter_var).pack(fill=tk.X)


        columns = ("ssid", "signal", "channel", "band")
        self.scan_tree = ttk.Treeview(self.scan_frame, columns=columns, show="headings", height=8)
        for col, title in zip(columns, ["SSID", "Signal (dBm)", "Canal", "Bande"]):
            self.scan_tree.heading(col, text=title, command=lambda c=col: self._on_heading_click(c))
            self.scan_tree.column(col, width=100)
        self.scan_tree.pack(fill=tk.BOTH, expand=True)

        self._sort_column = "ssid"
        self._sort_reverse = False


        self.alerts_frame = ttk.LabelFrame(
            self.frame,
            text="\U0001F534 Journal",
            padding=5,
            style="Journal.TLabelframe",
        )
        self.alerts_frame.grid(row=0, column=2, sticky="ns", padx=5, pady=5)


        self.wifi_alert_text = tk.Text(self.alerts_frame, height=4, wrap=tk.WORD)
        wifi_scroll = ttk.Scrollbar(self.alerts_frame, command=self.wifi_alert_text.yview)
        self.wifi_alert_text.configure(yscrollcommand=wifi_scroll.set)
        self.wifi_alert_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        wifi_scroll.pack(side=tk.RIGHT, fill=tk.Y)

    def setup_graphs(self) -> None:
        """Initialise matplotlib figures and enable interactive cursors."""
        if not MATPLOTLIB_AVAILABLE:
            return
        self.fig = Figure(figsize=(10, 6))
        self.fig.subplots_adjust(hspace=0.3)

        self.ax1 = self.fig.add_subplot(211)
        self.ax1.set_title("Force du signal WiFi")
        self.ax1.set_ylabel("Signal (dBm)")
        self.ax1.grid(True)
        self.signal_line, = self.ax1.plot([], [], 'b-', label="Signal")
        self.ax1.set_ylim(-90, -30)
        self.ax1.legend()

        self.ax2 = self.fig.add_subplot(212)
        self.ax2.set_title("Qualit\u00e9 de la connexion")
        self.ax2.set_ylabel("Qualit\u00e9 (%)")
        self.ax2.grid(True)
        self.quality_line, = self.ax2.plot([], [], 'g-', label="Qualit\u00e9")
        self.ax2.set_ylim(0, 100)
        self.ax2.legend()

        # Skip canvas creation when running under pytest to avoid Tk errors
        if "PYTEST_CURRENT_TEST" in os.environ:
            return

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.viz_frame)
        # Place the canvas in the grid so it expands with the window
        self.canvas.get_tk_widget().grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

        if mplcursors:
            mplcursors.cursor(self.ax1.lines, hover=True)
            mplcursors.cursor(self.ax2.lines, hover=True)

    # ------------------------------------------------------------------
    # WiFi actions
    # ------------------------------------------------------------------
    def start_collection(self) -> None:
        """Start WiFi collection and graph updates."""
        if self.analyzer.start_analysis():
            self.samples = []
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.update_data()
            self.update_status("Collection en cours...")
            self.scan_nearby_aps()

    def stop_collection(self) -> None:
        """Stop ongoing WiFi collection."""
        self.analyzer.stop_analysis()
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.update_status("Collection arr\u00eat\u00e9e")

    def scan_nearby_aps(self) -> None:
        """Scan and display nearby WiFi access points."""
        scan_fn = _get_scan_wifi()
        results = scan_fn()
        self.scan_results = results
        self._refresh_scan_tree()
        if results:
            self.export_scan_button.config(state=tk.NORMAL)

    def _on_heading_click(self, column: str) -> None:
        """Handle column header click to sort results."""
        if self._sort_column == column:
            self._sort_reverse = not self._sort_reverse
        else:
            self._sort_column = column
            self._sort_reverse = False
        self._refresh_scan_tree()

    def _refresh_scan_tree(self) -> None:
        """Refresh the Treeview according to filter and sort settings."""
        for row in self.scan_tree.get_children():
            self.scan_tree.delete(row)
        term = self.scan_filter_var.get().lower()
        filtered = [ap for ap in self.scan_results if term in ap.get("ssid", "").lower()]
        sorted_results = sorted(filtered, key=lambda x: x.get(self._sort_column, ""), reverse=self._sort_reverse)
        for ap in sorted_results:
            self.scan_tree.insert("", "end", values=(ap.get("ssid", ""), ap.get("signal", ""), ap.get("channel", ""), ap.get("frequency", "")))

    def export_scan_results(self) -> None:
        """Export scan results to a CSV file."""
        if not self.scan_results:
            messagebox.showinfo("Export", "Aucun r\u00e9sultat \u00e0 exporter")
            return
        filepath = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("Fichiers CSV", "*.csv")], title="Exporter le scan")
        if filepath:
            with open(filepath, "w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["SSID", "Signal(dBm)", "Canal", "Bande"])
                for ap in self.scan_results:
                    writer.writerow([ap.get("ssid", ""), ap.get("signal", ""), ap.get("channel", ""), ap.get("frequency", "")])
            messagebox.showinfo("Export", f"R\u00e9sultats export\u00e9s vers {filepath}")

    def open_fullscreen(self) -> None:
        """Display the current figure in a new fullscreen window."""
        if not MATPLOTLIB_AVAILABLE:
            return
        window = tk.Toplevel(self.master)
        window.title("Visualisation WiFi")
        canvas = FigureCanvasTkAgg(self.fig, master=window)
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        window.state("zoomed")

    def update_data(self) -> None:
        """Fetch samples and refresh graphs periodically."""
        if not self.analyzer.is_collecting:
            return
        sample = self.analyzer.wifi_collector.collect_sample()
        if sample:
            self.samples.append(sample)
            self.update_display()
            self.update_stats()
            self.check_wifi_issues(sample)
        self.master.after(self.update_interval, self.update_data)

    # ------------------------------------------------------------------
    # Helpers for displaying metrics
    # ------------------------------------------------------------------
    def check_wifi_issues(self, sample: WifiSample) -> None:
        """Detect potential WiFi issues and display alerts."""
        alerts = []
        if sample.signal_strength < -80:
            alerts.append(f"\ud83d\udd34 Signal CRITIQUE : {sample.signal_strength} dBm")
        elif sample.signal_strength < -70:
            alerts.append(f"\u26a0\ufe0f Signal faible : {sample.signal_strength} dBm")
        if sample.quality < 20:
            alerts.append(f"\ud83d\udd34 Qualit\u00e9 CRITIQUE : {sample.quality}%")
        elif sample.quality < 40:
            alerts.append(f"\u26a0\ufe0f Qualit\u00e9 faible : {sample.quality}%")
        try:
            tx_rate = int(sample.raw_data.get('TransmitRate', '0 Mbps').split()[0])
            rx_rate = int(sample.raw_data.get('ReceiveRate', '0 Mbps').split()[0])
            if min(tx_rate, rx_rate) < 24:
                alerts.append(f"\u26a0\ufe0f D\u00e9bit insuffisant :\n   TX: {tx_rate} Mbps, RX: {rx_rate} Mbps")
        except (ValueError, IndexError, KeyError):
            pass
        if alerts:
            msg = f"Position au {datetime.now().strftime('%H:%M:%S')} :\n" + "\n".join(alerts)
            self.wifi_alert_text.delete('1.0', tk.END)
            self.wifi_alert_text.insert('1.0', msg)

    def update_display(self) -> None:
        """Refresh matplotlib graphs with latest samples."""
        if not MATPLOTLIB_AVAILABLE or not self.samples:
            return
        signals = [s.signal_strength for s in self.samples[-self.max_samples:]]
        qualities = [s.quality for s in self.samples[-self.max_samples:]]
        if MATPLOTLIB_AVAILABLE:
            self.signal_line.set_data(range(len(signals)), signals)
            self.quality_line.set_data(range(len(qualities)), qualities)
            self.ax1.set_xlim(0, len(signals))
            self.ax2.set_xlim(0, len(qualities))
            self.canvas.draw()

    def update_stats(self) -> None:
        """Update statistics labels with averaged values and colours."""
        if not self.samples:
            return

        current_sample = self.samples[-1]
        signal_values = [s.signal_strength for s in self.samples[-20:]]
        quality_values = [s.quality for s in self.samples[-20:]]

        avg_signal = sum(signal_values) / len(signal_values)
        avg_quality = sum(quality_values) / len(quality_values)

        def col_sig(val: float) -> str:
            return "green" if val > -60 else ("orange" if val > -70 else "red")

        def col_qual(val: float) -> str:
            return "green" if val > 70 else ("orange" if val > 40 else "red")

        def col_rate(val: int) -> str:
            return "green" if val >= 50 else ("orange" if val >= 24 else "red")

        self.signal_label.config(text=f"Signal : {avg_signal:.1f} dBm", foreground=col_sig(avg_signal))
        self.quality_label.config(text=f"Qualit\u00e9 : {avg_quality:.1f}%", foreground=col_qual(avg_quality))
        try:
            tx_rate = int(current_sample.raw_data.get('TransmitRate', '0 Mbps').split()[0])
            rx_rate = int(current_sample.raw_data.get('ReceiveRate', '0 Mbps').split()[0])
            rate_col = col_rate(min(tx_rate, rx_rate))
            self.tx_label.config(text=f"TX : {tx_rate} Mbps", foreground=rate_col)
            self.rx_label.config(text=f"RX : {rx_rate} Mbps", foreground=rate_col)
        except (ValueError, IndexError, KeyError):
            self.tx_label.config(text="TX : N/A", foreground="red")
            self.rx_label.config(text="RX : N/A", foreground="red")

    def export_data(self) -> None:
        """Export full network analysis report to disk."""
        filepath = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("Fichiers JSON", "*.json")], title="Exporter l'analyse")
        if not filepath:
            return
        self.analyzer.export_data(filepath)
        messagebox.showinfo("Export r\u00e9ussi", f"Les donn\u00e9es ont \u00e9t\u00e9 export\u00e9es vers :\n{filepath}")
        try:
            tag_map_path = os.path.join(self.config_dir, "tag_map.yaml")
            tag_map = {}
            if os.path.exists(tag_map_path):
                with open(tag_map_path, "r", encoding="utf-8") as fh:
                    tag_map = yaml.safe_load(fh) or {}
            records = self.analyzer.wifi_collector.records
            if records:
                fig = generate_heatmap(records, tag_map=tag_map)
                heatmap_file = os.path.splitext(filepath)[0] + "_heatmap.png"
                fig.savefig(heatmap_file)
        except Exception as exc:  # pragma: no cover - best effort
            logging.getLogger(__name__).warning("Failed to generate heatmap: %s", exc)

    # ------------------------------------------------------------------
    # Utility helpers
    # ------------------------------------------------------------------
    def update_status(self, message: str) -> None:
        """Insert a status message in the alert area."""
        current_time = datetime.now().strftime("%H:%M:%S")
        self.wifi_alert_text.insert('1.0', f"{current_time} - {message}\n")

    def show_error(self, message: str) -> None:
        """Display an error message box."""
        messagebox.showerror("Erreur", message)
        self.update_status(f"ERREUR: {message}")
