"""AMR monitoring view.

Provides a Tkinter interface to monitor multiple AMR IP addresses
using :class:`AmrPingMonitor`.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import scrolledtext, ttk
from datetime import datetime
import os

from amr_ping_monitor import AmrPingMonitor


class AmrMonitorView:
    """Tkinter view dedicated to AMR connectivity monitoring.

    Users can add or remove IP addresses and launch a ping monitor. Each
    address is listed with a coloured status indicating connectivity.
    """

    def __init__(self, master: tk.Misc) -> None:
        self.master = master
        self.frame = ttk.Frame(master)
        self.monitor: AmrPingMonitor | None = None

        self.ip_entry: ttk.Entry
        self.ip_listbox: ttk.Treeview
        self.log_text: scrolledtext.ScrolledText
        self.start_button: ttk.Button
        self.stop_button: ttk.Button

        self.create_interface()

    # ------------------------------------------------------------------
    # Interface creation
    # ------------------------------------------------------------------
    def create_interface(self) -> None:
        """Create widgets for AMR monitoring."""
        input_frame = ttk.LabelFrame(self.frame, text="Adresses IP des AMR", padding=5)
        input_frame.pack(fill=tk.X, padx=5, pady=5)

        self.ip_entry = ttk.Entry(input_frame)
        self.ip_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        add_button = ttk.Button(input_frame, text="Ajouter", command=self.add_ip)
        add_button.pack(side=tk.LEFT, padx=5)

        remove_button = ttk.Button(input_frame, text="Supprimer", command=self.remove_ip)
        remove_button.pack(side=tk.LEFT, padx=5)

        columns = ("ip",)
        self.ip_listbox = ttk.Treeview(
            self.frame,
            columns=columns,
            show="headings",
            selectmode="browse",
            height=4,
        )
        self.ip_listbox.heading("ip", text="Adresse IP")
        self.ip_listbox.column("ip", width=150)
        self.ip_listbox.pack(fill=tk.X, padx=5, pady=5)

        btn_frame = ttk.Frame(self.frame)
        btn_frame.pack(pady=5)

        self.start_button = ttk.Button(btn_frame, text="▶ Démarrer", command=self.start_monitoring)
        self.start_button.pack(side=tk.LEFT, padx=5)

        self.stop_button = ttk.Button(btn_frame, text="⏹ Arrêter", command=self.stop_monitoring, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)

        log_frame = ttk.LabelFrame(self.frame, text="Journal", padding=5)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        scrolled_cls = scrolledtext.ScrolledText
        if "PYTEST_CURRENT_TEST" in os.environ:
            scrolled_cls = tk.Text
        self.log_text = scrolled_cls(log_frame, state=tk.DISABLED, height=10)
        self.log_text.pack(fill=tk.BOTH, expand=True)

    # ------------------------------------------------------------------
    # Monitoring control
    # ------------------------------------------------------------------
    def start_monitoring(self) -> None:
        """Start ping monitoring for the listed IPs."""
        ips = [self.ip_listbox.item(i)["values"][0] for i in self.ip_listbox.get_children()]
        if not ips:
            return

        self.monitor = AmrPingMonitor(ips, callback=self._on_status_change)
        self.monitor.start()

        self.start_button.configure(state=tk.DISABLED)
        self.stop_button.configure(state=tk.NORMAL)
        self._append_log("Monitoring démarré.")

    def stop_monitoring(self) -> None:
        """Stop the ping monitoring."""
        if self.monitor:
            self.monitor.stop()
            self.monitor = None
        self.start_button.configure(state=tk.NORMAL)
        self.stop_button.configure(state=tk.DISABLED)
        self._append_log("Monitoring stoppé.")

    def add_ip(self) -> None:
        """Add an IP to the list and monitor if running."""
        ip = self.ip_entry.get().strip()
        if not ip:
            return
        self.ip_listbox.insert("", tk.END, values=(ip,))
        if self.monitor:
            self.monitor.add_ip(ip)
        self.ip_entry.delete(0, tk.END)

    def remove_ip(self) -> None:
        """Remove selected IPs from the list and monitor."""
        selection = self.ip_listbox.selection()
        for iid in selection:
            ip = self.ip_listbox.item(iid)["values"][0]
            self.ip_listbox.delete(iid)
            if self.monitor:
                self.monitor.remove_ip(ip)

    # ------------------------------------------------------------------
    # Callbacks and utilities
    # ------------------------------------------------------------------
    def _on_status_change(self, ip: str, reachable: bool) -> None:
        status = "OK" if reachable else "Perte de connexion"
        timestamp = datetime.now().strftime("%H:%M:%S")
        msg = f"{timestamp} - {ip} - {status}"
        color = "green" if reachable else "red"
        for iid in self.ip_listbox.get_children():
            if self.ip_listbox.item(iid)["values"][0] == ip:
                self.ip_listbox.item(iid, tags=(color,))
                self.ip_listbox.tag_configure("green", foreground="green")
                self.ip_listbox.tag_configure("red", foreground="red")
                break
        self.frame.after(0, self._append_log, msg)

    def _append_log(self, message: str) -> None:
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.configure(state=tk.DISABLED)
        self.log_text.see(tk.END)
