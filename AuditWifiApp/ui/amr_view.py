"""AMR monitoring view.

Provides a Tkinter interface to monitor multiple AMR IP addresses
using :class:`AmrPingMonitor`.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import scrolledtext, ttk
from datetime import datetime

from typing import Dict, List

import os

from amr_ping_monitor import AmrPingMonitor


class AmrMonitorView:
    """Tkinter view dedicated to AMR connectivity monitoring."""

    def __init__(self, master: tk.Misc) -> None:
        self.master = master
        self.frame = ttk.Frame(master)
        self.monitor: AmrPingMonitor | None = None


        self.ip_entry_var = tk.StringVar()
        self.rows: Dict[str, ttk.Frame] = {}

        self.ip_input: ttk.Entry

        self.log_text: scrolledtext.ScrolledText
        self.start_button: ttk.Button
        self.stop_button: ttk.Button

        self.create_interface()

    # ------------------------------------------------------------------
    # Interface creation
    # ------------------------------------------------------------------
    def create_interface(self) -> None:
        """Create widgets for AMR monitoring."""

        input_frame = ttk.LabelFrame(self.frame, text="Ajouter une adresse IP", padding=5)
        input_frame.pack(fill=tk.X, padx=5, pady=5)

        self.ip_input = ttk.Entry(input_frame, textvariable=self.ip_entry_var)
        self.ip_input.pack(side=tk.LEFT, fill=tk.X, expand=True)
        add_button = ttk.Button(input_frame, text="Ajouter", command=self.add_ip)
        add_button.pack(side=tk.LEFT, padx=5)

        self.list_frame = ttk.Frame(self.frame)
        self.list_frame.pack(fill=tk.X, padx=5, pady=5)


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

    # IP management
    # ------------------------------------------------------------------
    def add_ip(self) -> None:
        """Add the IP from the entry field to the list."""
        ip = self.ip_entry_var.get().strip()
        if not ip or ip in self.rows:
            return
        row = ttk.Frame(self.list_frame, name=ip)
        canvas = tk.Canvas(row, width=16, height=16, highlightthickness=0)
        canvas.create_oval(2, 2, 14, 14, fill="gray")
        canvas.pack(side=tk.LEFT, padx=2)
        ttk.Label(row, text=ip, width=15).pack(side=tk.LEFT, padx=2)
        remove_btn = ttk.Button(row, text="✖", width=3, command=lambda ip=ip: self.remove_ip(ip))
        remove_btn.pack(side=tk.LEFT)
        row.pack(fill=tk.X, pady=2)
        self.rows[ip] = (row, canvas)
        self.ip_entry_var.set("")
        if self.monitor:
            self.monitor.add_ip(ip)

    def remove_ip(self, ip: str) -> None:
        """Remove an IP address from the list."""
        entry = self.rows.pop(ip, None)
        if entry:
            frame, _canvas = entry
            frame.destroy()
        if self.monitor:
            self.monitor.remove_ip(ip)

    # ------------------------------------------------------------------

    # Monitoring control
    # ------------------------------------------------------------------
    def start_monitoring(self) -> None:
        """Start ping monitoring for the listed IPs."""

        ips = list(self.rows.keys())

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

    # ------------------------------------------------------------------
    # Callbacks and utilities
    # ------------------------------------------------------------------
    def _on_status_change(self, ip: str, reachable: bool) -> None:
        status = "OK" if reachable else "Perte de connexion"
        timestamp = datetime.now().strftime("%H:%M:%S")
        msg = f"{timestamp} - {ip} - {status}"

        self.frame.after(0, self._update_row_status, ip, reachable)
        self.frame.after(0, self._append_log, msg)

    def _update_row_status(self, ip: str, reachable: bool) -> None:
        entry = self.rows.get(ip)
        if not entry:
            return
        color = "green" if reachable else "red"
        _frame, canvas = entry
        canvas.itemconfigure(1, fill=color)


    def _append_log(self, message: str) -> None:
        self.log_text.configure(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.configure(state=tk.DISABLED)
        self.log_text.see(tk.END)
