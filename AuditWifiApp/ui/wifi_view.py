"""WiFi view module.

This module defines the ``WifiView`` class responsible for building the
Tkinter interface dedicated to WiFi monitoring.
"""

from __future__ import annotations

import csv
import logging
import os
import tkinter as tk
from datetime import datetime
from tkinter import filedialog, messagebox, ttk
from typing import List, Any, Dict

try:
    import matplotlib
    matplotlib.use('TkAgg')  # Force TkAgg backend
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.backends._backend_tk import NavigationToolbar2Tk
    from matplotlib.figure import Figure
    MATPLOTLIB_AVAILABLE = True
    try:
        import mplcursors
        CURSORS_AVAILABLE = True
    except ImportError:
        CURSORS_AVAILABLE = False
except ImportError:  # pragma: no cover - optional dependency
    MATPLOTLIB_AVAILABLE = False
    CURSORS_AVAILABLE = False

import yaml
from heatmap_generator import generate_heatmap
from network_analyzer import NetworkAnalyzer
from network_scanner import scan_wifi
from wifi.wifi_collector import WifiSample

def _get_scan_wifi():
    """Return scan_wifi implementation, patched via runner when available."""
    try:  # pragma: no cover - runner may be importing
        from runner import scan_wifi as r_scan
        return r_scan
    except Exception:
        return scan_wifi

class WifiView:
    """Tkinter view dedicated to WiFi collection and visualisation."""

    STATS_LABELS = {
        'signal': {'text': "Signal : -- dBm", 'color': 'gray'},
        'quality': {'text': "Qualité : --%", 'color': 'gray'},
        'tx': {'text': "TX : -- Mbps", 'color': 'gray'},
        'rx': {'text': "RX : -- Mbps", 'color': 'gray'}
    }

    def __init__(self, master: tk.Misc, analyzer: NetworkAnalyzer) -> None:
        # Initialize instance variables
        self.master = master
        self.analyzer = analyzer
        self.frame = ttk.Frame(master)

        # Initialize data structures
        self.samples: List[WifiSample] = []
        self.scan_results: List[dict] = []

        # Initialize UI variables
        self.scan_filter_var = tk.StringVar()        # Initialize matplotlib components
        if MATPLOTLIB_AVAILABLE:
            # Use seaborn-v0_8 style instead of deprecated 'seaborn'
            plt.style.use('seaborn-v0_8')  # Set style before creating figure
            self.fig = Figure(figsize=(10, 6), dpi=100, constrained_layout=False)  # Changed to False to allow manual adjustments
        else:
            self.fig = None

        self.canvas: Any = None
        self.toolbar: Any = None
        self.ax1: Any = None
        self.ax2: Any = None
        self.signal_line: Any = None
        self.quality_line: Any = None

        # Configuration settings
        self.update_interval = 1000  # ms
        self.max_samples = 100
        self.config_dir = os.path.join(os.path.dirname(__file__), "..", "config")
        self._sort_column = "ssid"
        self._sort_reverse = False

        # Set up UI
        self._setup_styles()
        self.create_interface()
        if MATPLOTLIB_AVAILABLE:
            self._setup_graphs()


    def update_data(self) -> None:
        """Public wrapper to update graphs and labels."""
        self._update_data()

    def update_status(self) -> None:
        """Public wrapper to refresh status display."""
        self._update_stats()

    def update_stats(self) -> None:
        """Backward compatibility wrapper for old tests."""

        self._update_stats()

    def _setup_styles(self) -> None:
        """Configure basic ttk styles for the view."""
        if "PYTEST_CURRENT_TEST" in os.environ:
            return
        try:
            style = ttk.Style()
            style.configure("Title.TLabel", font=("Helvetica", 14, "bold"))
            style.configure("Alert.TLabel", foreground="red", font=("Helvetica", 12))
            style.configure("Stats.TLabel", font=("Helvetica", 10))
            style.configure("Analyze.TButton", font=("Helvetica", 12), padding=10)
            style.configure("Journal.TLabelframe", background="#f0f0f0")
            style.configure(
                "Journal.TLabelframe.Label",
                background="#f0f0f0",
                foreground="red",
            )
        except Exception as e:
            logging.error(f"Error setting up styles: {e}")

    def create_interface(self) -> None:
        """Create all widgets used in the WiFi tab."""
        try:
            # Configure grid weights for proper resizing
            self.frame.columnconfigure(0, weight=0)  # Control panel (fixed width)
            self.frame.columnconfigure(1, weight=3)  # Visualization area
            self.frame.columnconfigure(2, weight=1)  # Journal
            self.frame.rowconfigure(0, weight=1)     # Make the main row expandable

            # Control panel creation with fixed width
            self.control_frame = ttk.LabelFrame(self.frame, text="Contrôles", padding=10, width=250)
            self._place(self.control_frame, row=0, column=0, sticky="nsew", padx=5, pady=5)
            self.control_frame.grid_propagate(False)  # Maintain fixed width            # Configure the control frame to use grid
            self.control_frame.columnconfigure(0, weight=1)

            # Row counter for grid placement
            row = 0

            # Control buttons using grid instead of pack
            self.start_button = ttk.Button(
                self.control_frame,
                text="▶ Démarrer l'analyse",
                command=self.start_collection,
                style="success.TButton"
            )
            self._place(self.start_button, row=row, column=0, sticky="ew", pady=5)
            row += 1

            self.stop_button = ttk.Button(
                self.control_frame,
                text="⏹ Arrêter l'analyse",
                command=self.stop_collection,
                state=tk.DISABLED,
                style="danger.TButton"
            )
            self._place(self.stop_button, row=row, column=0, sticky="ew", pady=5)
            row += 1

            self.scan_button = ttk.Button(
                self.control_frame,
                text="🔍 Scanner",
                command=self.scan_nearby_aps,
                style="info.TButton"
            )
            self._place(self.scan_button, row=row, column=0, sticky="ew", pady=5)
            row += 1

            self.export_scan_button = ttk.Button(
                self.control_frame,
                text="📃 Exporter le scan",
                command=self.export_scan_results,
                state=tk.DISABLED,
                style="info.TButton"
            )
            self._place(self.export_scan_button, row=row, column=0, sticky="ew", pady=5)
            row += 1            # Stats panel
            self.stats_panel = ttk.LabelFrame(
                self.control_frame,
                text="Statistiques",
                padding=5
            )
            self._place(self.stats_panel, row=row, column=0, sticky="ew", pady=10)
            row += 1

            # Configure stats panel to use grid
            self.stats_panel.columnconfigure(0, weight=1)

            # Statistics labels using grid
            stats_row = 0

            self.signal_label = ttk.Label(
                self.stats_panel,
                text=self.STATS_LABELS['signal']['text'],
                style="Stats.TLabel",
                foreground=self.STATS_LABELS['signal']['color']
            )
            self._place(self.signal_label, row=stats_row, column=0, sticky="ew", pady=2)
            stats_row += 1

            self.quality_label = ttk.Label(
                self.stats_panel,
                text=self.STATS_LABELS['quality']['text'],
                style="Stats.TLabel",
                foreground=self.STATS_LABELS['quality']['color']
            )
            self._place(self.quality_label, row=stats_row, column=0, sticky="ew", pady=2)
            stats_row += 1

            self.tx_label = ttk.Label(
                self.stats_panel,
                text=self.STATS_LABELS['tx']['text'],
                style="Stats.TLabel",
                foreground=self.STATS_LABELS['tx']['color']
            )
            self._place(self.tx_label, row=stats_row, column=0, sticky="ew", pady=2)
            stats_row += 1

            self.rx_label = ttk.Label(
                self.stats_panel,
                text=self.STATS_LABELS['rx']['text'],
                style="Stats.TLabel",
                foreground=self.STATS_LABELS['rx']['color']
            )
            self._place(self.rx_label, row=stats_row, column=0, sticky="ew", pady=2)
            stats_row += 1

            # Visualization area
            self._create_visualization_area()

            # Create alerts panel
            self._create_alerts_panel()

        except Exception as e:
            logging.error(f"Error creating interface: {e}")
            raise

    def _create_visualization_area(self) -> None:
        """Create the visualization area with scan tree and plots."""
        # Visualization frame with weight
        self.viz_frame = ttk.Frame(self.frame)
        self._place(self.viz_frame, row=0, column=1, sticky="nsew", padx=5, pady=5)

        # Configure visualization frame grid
        self.viz_frame.columnconfigure(0, weight=1)
        self.viz_frame.rowconfigure(0, weight=0)  # Scan area (fixed height)
        self.viz_frame.rowconfigure(1, weight=1)  # Plot area (expandable)

        # Scan frame with fixed height
        self.scan_frame = ttk.LabelFrame(
            self.viz_frame,
            text="Réseaux détectés",
            padding=5,
            height=200
        )
        self._place(self.scan_frame, row=0, column=0, sticky="ew", padx=5, pady=5)
        self.scan_frame.grid_propagate(False)  # Maintain fixed height
        self.scan_frame.columnconfigure(0, weight=1)

        # Entry for filtering scan results by SSID
        entry = ttk.Entry(
            self.scan_frame,
            textvariable=self.scan_filter_var
        )
        self._place(entry, row=0, column=0, sticky="ew", padx=5, pady=5)

        self.scan_filter_var.trace_add("write", lambda *_: self._refresh_scan_tree())

        # Scan tree
        scan_frame_inner = ttk.Frame(self.scan_frame)
        self._place(scan_frame_inner, row=1, column=0, sticky="nsew", padx=5, pady=5)
        scan_frame_inner.columnconfigure(0, weight=1)
        scan_frame_inner.rowconfigure(0, weight=1)

        columns = ("ssid", "signal", "channel", "band")
        self.scan_tree = ttk.Treeview(
            scan_frame_inner,
            columns=columns,
            show="headings",
            height=8
        )
        for col, title in zip(columns, ["SSID", "Signal (dBm)", "Canal", "Bande"]):
            self.scan_tree.heading(col, text=title, command=lambda c=col: self._on_heading_click(c))
            self.scan_tree.column(col, width=100)

        # Add scrollbar to scan tree
        command = getattr(self.scan_tree, "yview", lambda *a, **k: None)
        scan_scroll = ttk.Scrollbar(scan_frame_inner, orient="vertical", command=command)
        if hasattr(self.scan_tree, "configure"):
            self.scan_tree.configure(yscrollcommand=scan_scroll.set)

        self._place(self.scan_tree, row=0, column=0, sticky="nsew")
        self._place(scan_scroll, row=0, column=1, sticky="ns")

        if MATPLOTLIB_AVAILABLE:
            # Plot frame
            self.plot_frame = ttk.LabelFrame(
                self.viz_frame,
                text="Visualisation du signal",
                padding=5
            )
            self._place(self.plot_frame, row=1, column=0, sticky="nsew", padx=5, pady=5)

            # Configure plot frame grid to expand properly
            self.plot_frame.columnconfigure(0, weight=1)
            self.plot_frame.rowconfigure(0, weight=1)  # Graph area
            self.plot_frame.rowconfigure(1, weight=0)  # Toolbar

    def _create_alerts_panel(self) -> None:
        """Create the alerts panel."""
        self.alerts_frame = ttk.LabelFrame(
            self.frame,
            text="\U0001F534 Journal",
            padding=5,
            style="Journal.TLabelframe",
        )
        self._place(self.alerts_frame, row=0, column=2, sticky="ns", padx=5, pady=5)        # Create a frame to hold the text and scrollbar using grid
        text_container = ttk.Frame(self.alerts_frame)
        self._place(text_container, row=0, column=0, sticky="nsew", padx=2, pady=2)

        # Configure the grid for text_container
        text_container.columnconfigure(0, weight=1)  # Text area
        text_container.columnconfigure(1, weight=0)  # Scrollbar
        text_container.rowconfigure(0, weight=1)

        self.wifi_alert_text = tk.Text(
            text_container,
            height=4,
            wrap=tk.WORD
        )
        wifi_scroll = ttk.Scrollbar(
            text_container,
            command=self.wifi_alert_text.yview
        )
        self.wifi_alert_text.configure(yscrollcommand=wifi_scroll.set)
        self._place(self.wifi_alert_text, row=0, column=0, sticky="nsew")
        self._place(wifi_scroll, row=0, column=1, sticky="ns")

        # Make sure the alerts_frame can expand
        self.alerts_frame.columnconfigure(0, weight=1)
        self.alerts_frame.rowconfigure(0, weight=1)

    def _setup_graphs(self) -> None:
        """Initialize matplotlib figures and enable interactive cursors."""
        if not MATPLOTLIB_AVAILABLE or not self.fig:
            logging.warning("Matplotlib not available or figure not initialized")
            return

        try:
            # Configure figure layout
            self.fig.subplots_adjust(left=0.1, right=0.95, bottom=0.1, top=0.95, hspace=0.3)

            # Signal strength subplot
            self.ax1 = self.fig.add_subplot(211)
            self.ax1.set_title("Force du signal WiFi", pad=10)
            self.ax1.set_ylabel("Signal (dBm)")
            self.ax1.set_xlabel("Échantillons")
            self.ax1.grid(True, linestyle='--', alpha=0.7)
            self.signal_line, = self.ax1.plot([], [], 'b-', label="Signal", linewidth=2)
            self.ax1.set_ylim(-90, -30)
            self.ax1.legend(loc='upper right')

            # Quality subplot
            self.ax2 = self.fig.add_subplot(212)
            self.ax2.set_title("Qualité de la connexion", pad=10)
            self.ax2.set_ylabel("Qualité (%)")
            self.ax2.set_xlabel("Échantillons")
            self.ax2.grid(True, linestyle='--', alpha=0.7)
            self.quality_line, = self.ax2.plot([], [], 'g-', label="Qualité", linewidth=2)
            self.ax2.set_ylim(0, 100)
            self.ax2.legend(loc='upper right')

            if "PYTEST_CURRENT_TEST" in os.environ:
                return

            # Create and configure canvas in plot frame with proper expansion
            self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
            canvas_widget = self.canvas.get_tk_widget()
            self._place(canvas_widget, row=0, column=0, sticky="nsew", padx=5, pady=5)            # Add toolbar below the plot
            self.toolbar = NavigationToolbar2Tk(self.canvas, self.plot_frame, pack_toolbar=False)
            self._place(self.toolbar, row=1, column=0, sticky="ew")

            # Enable interactive cursors if available
            if CURSORS_AVAILABLE and self.signal_line and self.quality_line:
                mplcursors.cursor([self.signal_line, self.quality_line], hover=True)

            # Initial draw
            self.canvas.draw()

        except Exception as e:
            logging.error(f"Error setting up graphs: {e}")
            self.canvas = None  # Disable graphing on error

    def _update_plots(self) -> None:
        """Update plot data and redraw."""
        if not MATPLOTLIB_AVAILABLE or not self.samples or not self.canvas:
            return

        if not hasattr(self, 'signal_line') or not hasattr(self, 'quality_line'):
            return

        try:
            # Lock to prevent concurrent updates
            if hasattr(self.canvas, '_tkcanvas'):
                self.canvas._tkcanvas.config(cursor="watch")

            # Extract data points
            signals = [-s.signal_strength for s in self.samples]
            qualities = [s.quality for s in self.samples]
            x_data = list(range(len(signals)))

            # Update signal plot
            self.signal_line.set_data(x_data, signals)
            self.ax1.set_xlim(0, max(len(signals), 10))  # Minimum width
            self.ax1.relim()
            self.ax1.autoscale_view(scalex=False)  # Only autoscale y-axis

            # Update quality plot
            self.quality_line.set_data(x_data, qualities)
            self.ax2.set_xlim(0, max(len(qualities), 10))  # Minimum width
            self.ax2.relim()
            self.ax2.autoscale_view(scalex=False)  # Only autoscale y-axis

            # Redraw the plots
            self.canvas.draw_idle()  # Use draw_idle instead of draw for better performance

            # Restore cursor
            if hasattr(self.canvas, '_tkcanvas'):
                self.canvas._tkcanvas.config(cursor="")

        except Exception as e:
            logging.error(f"Error updating plots: {e}")
            if hasattr(self.canvas, '_tkcanvas'):
                self.canvas._tkcanvas.config(cursor="")

    def _update_data(self) -> None:
        """Update displayed data."""
        try:
            # Get latest sample via collector helper
            collector = getattr(self.analyzer, 'wifi_collector', None)
            if collector:
                # Actively request a new sample from the collector
                if getattr(collector, 'is_collecting', False):
                    sample = collector.collect_sample()
                else:
                    sample = collector.get_latest_sample()

                if sample is not None:
                    self.samples.append(sample)
                    if len(self.samples) > self.max_samples:
                        self.samples.pop(0)

            # Update stats first as they're simpler
            self._update_stats()

            # Update plots if available
            if MATPLOTLIB_AVAILABLE and self.canvas:
                self._update_plots()

            # Schedule next update if collection is active and window exists
            if (hasattr(self, 'stop_button') and
                self.stop_button.winfo_exists() and
                self.stop_button.cget('state') == tk.NORMAL):
                self.frame.after(self.update_interval, self._update_data)

        except Exception as e:
            logging.error(f"Error updating data: {e}")
            # Try to schedule next update even if this one failed
            if (hasattr(self, 'stop_button') and
                self.stop_button.winfo_exists() and
                self.stop_button.cget('state') == tk.NORMAL):
                self.frame.after(self.update_interval, self._update_data)

    def _update_stats(self) -> None:
        """Update statistics display."""
        if not self.samples:
            return

        try:
            # Calculate statistics
            signals = [-s.signal_strength for s in self.samples[-10:]]
            qualities = [s.quality for s in self.samples[-10:]]

            avg_signal = sum(signals) / len(signals)
            avg_quality = sum(qualities) / len(qualities)

            # Color coding function for signal strength
            def col_sig(s):
                if s > -50: return "green"
                if s > -70: return "orange"
                return "red"

            # Update labels
            if hasattr(self, 'signal_label'):
                self.signal_label.config(
                    text=f"Signal : {avg_signal:.1f} dBm",
                    foreground=col_sig(avg_signal)
                )

            if hasattr(self, 'quality_label'):
                self.quality_label.config(
                    text=f"Qualité : {avg_quality:.1f}%",
                    foreground="green" if avg_quality > 50 else "red"
                )


            # Display TX/RX rates from the latest sample when available
            last_sample = self.samples[-1]
            if hasattr(self, 'tx_label'):
                self.tx_label.config(text=f"TX : {last_sample.transmit_rate}")

            if hasattr(self, 'rx_label'):
                self.rx_label.config(text=f"RX : {last_sample.receive_rate}")


        except Exception as e:
            logging.error(f"Error updating stats: {e}")

    def _log_event(self, message: str) -> None:
        """Add a message to the event log."""
        try:
            current_time = datetime.now().strftime("%H:%M:%S")
            self.wifi_alert_text.insert('1.0', f"{current_time} - {message}\n")
        except Exception as e:
            logging.error(f"Error logging event: {e}")

    def start_collection(self) -> None:
        """Start WiFi data collection."""
        try:
            # Refresh available networks before starting collection
            try:
                self.scan_nearby_aps()
            except Exception:
                pass

            self.analyzer.start_wifi_collection()
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self._log_event("Démarrage de la collecte WiFi")
            self.samples.clear()  # Reset samples for new collection
            self._update_data()  # Start data updates
        except Exception as e:
            logging.error(f"Error starting collection: {e}")
            messagebox.showerror("Erreur", f"Erreur au démarrage de la collecte : {e}")

    def stop_collection(self) -> None:
        """Stop WiFi data collection."""
        try:
            self.analyzer.stop_wifi_collection()
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            self._log_event("Arrêt de la collecte WiFi")
        except Exception as e:
            logging.error(f"Error stopping collection: {e}")
            messagebox.showerror("Erreur", f"Erreur à l'arrêt de la collecte : {e}")

    def scan_nearby_aps(self) -> None:
        """Scan for nearby access points."""
        try:
            # Get the scan function
            scan_wifi = _get_scan_wifi()

            # Perform scan
            self.scan_results = scan_wifi()
            self._refresh_scan_tree()

            # Enable export if we have results
            if self.scan_results:
                self.export_scan_button.config(state=tk.NORMAL)
                self._log_event(f"Scan terminé : {len(self.scan_results)} réseaux trouvés")
            else:
                self._log_event("Scan terminé : aucun réseau trouvé")

        except Exception as e:
            logging.error(f"Error scanning APs: {e}")
            messagebox.showerror("Erreur", f"Erreur lors du scan : {e}")

    def _refresh_scan_tree(self) -> None:
        """Update the scan results treeview."""
        try:
            # Clear existing items
            for row in self.scan_tree.get_children():
                self.scan_tree.delete(row)

            # Get filter text
            term = self.scan_filter_var.get().lower()

            # Add filtered results
            for ap in self.scan_results:
                if term and term not in ap.get("ssid", "").lower():
                    continue
                self.scan_tree.insert(
                    "",
                    "end",
                    values=(
                        ap.get("ssid", ""),
                        ap.get("signal", ""),
                        ap.get("channel", ""),
                        ap.get("frequency", "")
                    )
                )
        except Exception as e:
            logging.error(f"Error refreshing scan tree: {e}")

    def _on_heading_click(self, col: str) -> None:
        """Handle column header clicks for sorting."""
        try:
            # Toggle sort direction if same column
            if col == self._sort_column:
                self._sort_reverse = not self._sort_reverse
            else:
                self._sort_column = col
                self._sort_reverse = False

            # Get and sort all items
            try:
                children = self.scan_tree.get_children('')
            except TypeError:
                children = self.scan_tree.get_children()

            if hasattr(self.scan_tree, "set"):
                items = [(self.scan_tree.set(item, col), item) for item in children]
            else:
                col_index = {"ssid": 0, "signal": 1, "channel": 2, "band": 3}.get(col, 0)
                items = [(
                    self.scan_tree.item(item)["values"][col_index],
                    item,
                ) for item in children]
            items.sort(reverse=self._sort_reverse)

            # Rearrange items in sorted positions
            if hasattr(self.scan_tree, "move"):
                for index, (_, item_id) in enumerate(items):
                    self.scan_tree.move(item_id, '', index)
            else:
                # Fallback used in tests with DummyTreeview
                ordered = [self.scan_results[int(i) - 1] for _, i in items]
                self.scan_results = ordered
                self._refresh_scan_tree()

        except Exception as e:
            logging.error(f"Error sorting column: {e}")

    def export_scan_results(self) -> None:
        """Export scan results to CSV."""
        try:
            if not self.scan_results:
                messagebox.showwarning(
                    "Export",
                    "Aucun résultat de scan à exporter"
                )
                return

            filename = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                initialdir=os.path.expanduser("~"),
                title="Exporter les résultats du scan"
            )

            if not filename:
                return

            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["SSID", "Signal(dBm)", "Canal", "Bande"])
                for ap in self.scan_results:
                    writer.writerow([
                        ap.get("ssid", ""),
                        ap.get("signal", ""),
                        ap.get("channel", ""),
                        ap.get("frequency", "")
                    ])

            self._log_event(f"Résultats exportés vers {filename}")

        except Exception as e:
            logging.error(f"Error exporting scan results: {e}")
            messagebox.showerror("Erreur", f"Erreur lors de l'export : {e}")
