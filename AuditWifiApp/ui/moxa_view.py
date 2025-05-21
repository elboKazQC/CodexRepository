"""Moxa view module.

Contains ``MoxaView`` responsible for displaying and analysing
Moxa logs in a dedicated Tkinter frame.
"""

from __future__ import annotations

import json
import os
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk

from config_manager import ConfigurationManager
from src.ai.simple_moxa_analyzer import analyze_moxa_logs


class MoxaView:
    """Tkinter view dedicated to Moxa log analysis."""

    def __init__(self, master: tk.Misc, config_dir: str, default_config: dict) -> None:
        """Create the view and load the latest configuration.

        Args:
            master: Parent widget hosting the frame.
            config_dir: Directory where configuration files are stored.
            default_config: Default configuration to use when none was saved.

        On initialization the previous config is loaded if present and all
        Tkinter widgets are prepared.
        """
        self.master = master
        self.frame = ttk.Frame(master)

        self.config_manager = ConfigurationManager(default_config)
        self.config_dir = config_dir
        os.makedirs(self.config_dir, exist_ok=True)
        self.last_config_file = os.path.join(self.config_dir, "last_moxa_config.json")
        if os.path.exists(self.last_config_file):
            try:
                with open(self.last_config_file, "r", encoding="utf-8") as f:
                    self.config_manager.config = json.load(f)
            except Exception:
                pass
        self.current_config = self.config_manager.get_config()
        self.example_log_path = os.path.join(
            os.path.dirname(__file__), "..", "config", "example_moxa_log.txt"
        )

        self.moxa_input: tk.Text
        self.moxa_config_text: scrolledtext.ScrolledText
        self.moxa_params_text: tk.Text
        self.moxa_results: tk.Text
        self.analyze_button: ttk.Button
        self.export_button: ttk.Button

        self.create_interface()

    # ------------------------------------------------------------------
    # Interface building
    # ------------------------------------------------------------------
    def create_interface(self) -> None:
        """Create widgets for Moxa log analysis using two columns."""
        # Split the view horizontally: left column for logs/results, right column
        # for configuration and actions. Panedwindow allows manual resizing.
        paned = ttk.Panedwindow(self.frame, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)

        left_pane = ttk.Frame(paned)
        right_pane = ttk.Frame(paned)
        paned.add(left_pane, weight=3)
        paned.add(right_pane, weight=2)

        # ----- Left column: logs to analyze and resulting report -----
        input_frame = ttk.LabelFrame(left_pane, text="Collez vos logs Moxa ici :", padding=10)
        input_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.moxa_input = tk.Text(input_frame, wrap=tk.WORD)
        input_scroll = ttk.Scrollbar(input_frame, command=self.moxa_input.yview)
        self.moxa_input.configure(yscrollcommand=input_scroll.set)
        self.moxa_input.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        input_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        results_frame = ttk.LabelFrame(left_pane, text="R\u00e9sultats de l'analyse :", padding=10)
        results_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.moxa_results = tk.Text(results_frame, wrap=tk.WORD)
        res_scroll = ttk.Scrollbar(results_frame, command=self.moxa_results.yview)
        self.moxa_results.configure(yscrollcommand=res_scroll.set)
        self.moxa_results.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        res_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # ----- Right column: configuration, parameters and action buttons -----
        cfg_frame = ttk.LabelFrame(right_pane, text="Configuration Moxa actuelle (JSON) :", padding=10)
        cfg_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        scrolled_cls = scrolledtext.ScrolledText
        if "PYTEST_CURRENT_TEST" in os.environ:
            scrolled_cls = tk.Text

        self.moxa_config_text = scrolled_cls(cfg_frame, height=8, wrap=tk.WORD)
        self.moxa_config_text.pack(fill=tk.BOTH, expand=True)
        self.moxa_config_text.insert('1.0', json.dumps(self.current_config, indent=2))
        self.setup_json_tags()
        self.highlight_json()

        params_frame = ttk.LabelFrame(right_pane, text="Param\u00e8tres suppl\u00e9mentaires :", padding=10)
        params_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        help_btn = ttk.Button(params_frame, text="\u2753", width=3, command=self.show_metrics_help)
        help_btn.pack(side=tk.RIGHT, padx=5)
        # Additional parameters from the user
        self.moxa_params_text = tk.Text(params_frame, height=8, wrap=tk.WORD)
        params_scroll = ttk.Scrollbar(params_frame, command=self.moxa_params_text.yview)
        self.moxa_params_text.configure(yscrollcommand=params_scroll.set)
        self.moxa_params_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        params_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        # Hint label for the parameters field
        ttk.Label(
            params_frame,
            text="Indiquez ici tout contexte supplémentaire",
        ).pack(anchor=tk.W, pady=(5, 0))

        cfg_btn_frame = ttk.Frame(right_pane)
        cfg_btn_frame.pack(pady=5)
        ttk.Button(cfg_btn_frame, text="Charger config", command=self.load_config).pack(side=tk.LEFT, padx=5)
        ttk.Button(cfg_btn_frame, text="\xc9diter config", command=self.edit_config).pack(side=tk.LEFT, padx=5)

        ttk.Button(cfg_btn_frame, text="Copier JSON", command=self.copy_json).pack(side=tk.LEFT, padx=5)
        ttk.Button(cfg_btn_frame, text="Exporter JSON", command=self.export_json).pack(side=tk.LEFT, padx=5)


        self.analyze_button = ttk.Button(right_pane, text="\U0001F50E Analyser les logs", command=self.analyze_moxa_logs)
        self.analyze_button.pack(pady=10)

        self.export_button = ttk.Button(right_pane, text="\U0001F4BE Exporter l'analyse", command=self.export_data, state=tk.DISABLED)
        self.export_button.pack(pady=5)

    # ------------------------------------------------------------------
    # Helper actions
    # ------------------------------------------------------------------
    def load_example_log(self) -> None:
        """Load example log file into the input text widget."""
        try:
            with open(self.example_log_path, "r", encoding="utf-8") as fh:
                content = fh.read()
        except Exception:
            messagebox.showerror("Erreur", "Impossible de charger l'exemple de log")
            return
        self.moxa_input.delete('1.0', tk.END)
        self.moxa_input.insert('1.0', content)

    def show_metrics_help(self) -> None:
        """Display a short help message about available metrics."""
        message = (
            "Collez vos journaux Moxa ici pour obtenir une analyse et des recommandations."
        )
        messagebox.showinfo("Aide", message)

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------
    def analyze_moxa_logs(self) -> None:
        """Analyse les logs Moxa coll\u00e9s via l'API OpenAI."""
        logs = self.moxa_input.get('1.0', tk.END).strip()
        if not logs:
            messagebox.showwarning("Analyse impossible", "Veuillez coller des logs Moxa \u00e0 analyser")
            return
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            messagebox.showerror("Cl\u00e9 API manquante", "La variable d'environnement OPENAI_API_KEY doit \u00eatre d\u00e9finie pour utiliser l'analyse OpenAI.")
            return
        self.moxa_results.delete('1.0', tk.END)
        self.moxa_results.insert('1.0', "\U0001F504 Analyse en cours avec OpenAI...\n\n")
        self.analyze_button.config(state=tk.DISABLED)
        self.moxa_results.update()
        try:
            config_text = self.moxa_config_text.get('1.0', tk.END).strip()
            if config_text:
                self.current_config = json.loads(config_text)
        except json.JSONDecodeError:
            messagebox.showerror("Configuration invalide", "La configuration Moxa n'est pas un JSON valide.")
            return
        params_text = self.moxa_params_text.get('1.0', tk.END).strip()
        analysis = analyze_moxa_logs(logs, self.current_config, params_text or None)
        if analysis:
            self.moxa_results.delete('1.0', tk.END)
            self.moxa_results.insert('end', "Analyse OpenAI des Logs Moxa\n\n", "title")
            self.format_and_display_ai_analysis(analysis)
            self.export_button.config(state=tk.NORMAL)
            messagebox.showinfo("Succ\u00e8s", "Analyse compl\u00e9t\u00e9e par OpenAI !")
            self.save_last_config()
        else:
            self.moxa_results.insert('1.0', "\u274C Aucun r\u00e9sultat d'analyse\n")
        self.analyze_button.config(state=tk.NORMAL)

    def format_and_display_ai_analysis(self, analysis: str) -> None:
        """Format OpenAI answer either as JSON or as plain text."""
        try:
            data = json.loads(analysis)
            self.display_structured_analysis(data)
        except json.JSONDecodeError:
            self.display_text_analysis(analysis)

    def display_structured_analysis(self, data: dict) -> None:
        """Display structured analysis returned by OpenAI."""
        if "score_global" in data:
            score = data["score_global"]
            self.moxa_results.insert('end', f"Score Global: {score}/100\n", "title")
            if score >= 70:
                self.moxa_results.insert('end', "\u2705 Configuration adapt\u00e9e\n\n", "success")
            elif score >= 50:
                self.moxa_results.insert('end', "\u26a0\ufe0f Am\u00e9liorations possibles\n\n", "warning")
            else:
                self.moxa_results.insert('end', "\u274C Optimisation n\u00e9cessaire\n\n", "alert")
        if "problemes" in data:
            self.moxa_results.insert('end', "Probl\u00e8mes D\u00e9tect\u00e9s:\n", "section")
            for prob in data["problemes"]:
                self.moxa_results.insert('end', f"\u2022 {prob}\n", "normal")
            self.moxa_results.insert('end', "\n")
        if "recommendations" in data:
            self.moxa_results.insert('end', "Recommandations:\n", "section")
            for rec in data["recommendations"]:
                if isinstance(rec, dict):
                    self.moxa_results.insert('end', f"\u2022 Probl\u00e8me: {rec.get('probleme', '')}\n", "normal")
                    self.moxa_results.insert('end', f"  Solution: {rec.get('solution', '')}\n\n", "normal")
                else:
                    self.moxa_results.insert('end', f"\u2022 {rec}\n", "normal")
            self.moxa_results.insert('end', "\n")
        if "analyse_detaillee" in data:
            self.moxa_results.insert('end', "Analyse D\u00e9taill\u00e9e:\n", "section")
            self.moxa_results.insert('end', f"{data['analyse_detaillee']}\n\n", "normal")
        if "conclusion" in data:
            self.moxa_results.insert('end', "Conclusion:\n", "section")
            self.moxa_results.insert('end', f"{data['conclusion']}\n", "normal")

    def display_text_analysis(self, text: str) -> None:
        """Display plain text analysis from OpenAI."""
        sections = text.split('\n\n')
        for section in sections:
            if section.strip():
                if any(keyword in section.lower() for keyword in ['probl\u00e8mes:', 'recommandations:', 'analyse:', 'conclusion:', 'impact:']):
                    self.moxa_results.insert('end', f"\n{section}\n", "section")
                else:
                    self.moxa_results.insert('end', f"{section}\n", "normal")
        self.moxa_results.see('1.0')

    def load_config(self) -> None:
        """Load a JSON configuration file."""
        filepath = filedialog.askopenfilename(initialdir=self.config_dir, filetypes=[("JSON", "*.json")], title="Charger une configuration")
        if filepath:
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    self.config_manager.config = json.load(f)
                self.current_config = self.config_manager.get_config()
                self.moxa_config_text.delete('1.0', tk.END)
                self.moxa_config_text.insert('1.0', json.dumps(self.current_config, indent=2))
                self.highlight_json()
                messagebox.showinfo("Configuration", f"Configuration charg\u00e9e depuis {filepath}")
            except Exception as e:
                messagebox.showerror("Erreur", f"Impossible de charger la configuration:\n{e}")

    def edit_config(self) -> None:
        """Open a dialog allowing edition of the current JSON configuration.

        Boolean options are displayed with checkboxes while numeric and string
        options keep text fields. A ``R\u00e9initialiser`` button restores default
        values.
        """

        dialog = tk.Toplevel(self.master)
        dialog.title("\xc9diter la configuration")

        str_entries: dict[str, tk.StringVar] = {}
        bool_entries: dict[str, tk.BooleanVar] = {}

        for row, (key, value) in enumerate(self.config_manager.get_config().items()):
            label = key.replace("_", " ").capitalize()
            ttk.Label(dialog, text=label).grid(row=row, column=0, sticky=tk.W, padx=5, pady=2)
            if isinstance(value, bool):
                var = tk.BooleanVar(value=value)
                ttk.Checkbutton(dialog, variable=var).grid(row=row, column=1, padx=5, pady=2, sticky=tk.W)
                bool_entries[key] = var
            else:
                var = tk.StringVar(value=str(value))
                ttk.Entry(dialog, textvariable=var, width=20).grid(row=row, column=1, padx=5, pady=2)
                str_entries[key] = var

        def reset() -> None:
            """Reset fields to the default configuration."""
            defaults = self.config_manager.default_config
            for key, val in defaults.items():
                if key in bool_entries:
                    bool_entries[key].set(bool(val))
                elif key in str_entries:
                    str_entries[key].set(str(val))

        def save() -> None:
            """Persist edited values and refresh the JSON display."""
            for k, v in str_entries.items():
                val = v.get()
                try:
                    parsed = int(val)
                except ValueError:
                    try:
                        parsed = float(val)
                    except ValueError:
                        parsed = val
                self.config_manager.update_config(k, parsed)
            for k, v in bool_entries.items():
                self.config_manager.update_config(k, bool(v.get()))

            self.current_config = self.config_manager.get_config()
            self.moxa_config_text.delete("1.0", tk.END)
            self.moxa_config_text.insert("1.0", json.dumps(self.current_config, indent=2))
            self.highlight_json()
            dialog.destroy()

        row = len(str_entries) + len(bool_entries)
        ttk.Button(dialog, text="R\u00e9initialiser", command=reset).grid(row=row, column=0, padx=5, pady=10)
        ttk.Button(dialog, text="OK", command=save).grid(row=row, column=1, padx=5, pady=10)
        ttk.Button(dialog, text="Annuler", command=dialog.destroy).grid(row=row, column=2, padx=5, pady=10)

    def save_last_config(self) -> None:
        """Save current configuration for later reuse."""
        try:
            with open(self.last_config_file, "w", encoding="utf-8") as f:
                json.dump(self.config_manager.get_config(), f, indent=2)
        except Exception:
            pass

    def setup_json_tags(self) -> None:
        """Configure tags for JSON highlighting."""
        self.moxa_config_text.tag_config("key", foreground="blue")
        self.moxa_config_text.tag_config("string", foreground="green")
        self.moxa_config_text.tag_config("number", foreground="purple")
        self.moxa_config_text.tag_config("bool", foreground="orange")

    def highlight_json(self) -> None:
        """Apply a minimal JSON coloration in the config text widget."""
        import re

        text = self.moxa_config_text.get("1.0", tk.END)
        if not isinstance(text, str):
            return
        for tag in ("key", "string", "number", "bool"):
            self.moxa_config_text.tag_remove(tag, "1.0", tk.END)
        for m in re.finditer(r'"[^"\n]*"(?=\s*:)', text):
            self.moxa_config_text.tag_add("key", f"1.0+{m.start()}c", f"1.0+{m.end()}c")
        for m in re.finditer(r'"[^"\n]*"', text):
            self.moxa_config_text.tag_add("string", f"1.0+{m.start()}c", f"1.0+{m.end()}c")
        for m in re.finditer(r'\b\d+(?:\.\d+)?\b', text):
            self.moxa_config_text.tag_add("number", f"1.0+{m.start()}c", f"1.0+{m.end()}c")
        for m in re.finditer(r'\b(?:true|false|null)\b', text, re.IGNORECASE):
            self.moxa_config_text.tag_add("bool", f"1.0+{m.start()}c", f"1.0+{m.end()}c")

    def copy_json(self) -> None:
        """Copy the configuration JSON to the clipboard."""
        text = json.dumps(self.config_manager.get_config(), indent=2)
        self.master.clipboard_clear()
        self.master.clipboard_append(text)
        messagebox.showinfo("Copie", "Configuration copi\u00e9e dans le presse-papiers")

    def export_json(self) -> None:
        """Save the configuration JSON to a file."""
        filepath = filedialog.asksaveasfilename(
            initialdir=self.config_dir,
            defaultextension=".json",
            filetypes=[("JSON", "*.json")],
            title="Exporter la configuration",
        )
        if filepath:
            try:
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(json.dumps(self.config_manager.get_config(), indent=2))
                messagebox.showinfo("Export", f"Configuration enregistr\u00e9e dans {filepath}")
            except Exception as e:
                messagebox.showerror("Erreur", f"Impossible d'exporter la configuration:\n{e}")

    def export_data(self) -> None:

        """Export current analysis results to a JSON or PDF file."""
        filepath = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("Fichiers JSON", "*.json"), ("Fichiers PDF", "*.pdf")],
            title="Exporter l'analyse",
        )
        if not filepath:
            return

        content = self.moxa_results.get("1.0", tk.END).strip()

        try:
            if filepath.lower().endswith(".pdf"):
                from matplotlib.backends.backend_pdf import PdfPages
                import matplotlib.pyplot as plt

                fig = plt.figure(figsize=(8.27, 11.69))
                plt.axis("off")
                fig.text(0.05, 0.95, content, va="top", wrap=True)
                with PdfPages(filepath) as pdf:
                    pdf.savefig(fig, bbox_inches="tight")
                plt.close(fig)
            else:
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump({"analysis": content}, f, indent=2, ensure_ascii=False)

            messagebox.showinfo("Export r\u00e9ussi", f"Les r\u00e9sultats ont \u00e9t\u00e9 export\u00e9s vers :\n{filepath}")
        except Exception as exc:  # pragma: no cover - best effort
            messagebox.showerror("Erreur", f"Impossible d'exporter les donn\u00e9es : {exc}")


