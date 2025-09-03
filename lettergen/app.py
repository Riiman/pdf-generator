import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from typing import Dict, List

from .generator import (
    GenerationOptions,
    parse_template_fields,
    generate_bulk,
    generate_single,
)
from .utils import ensure_directory


class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("LetterGen - PDF & DOCX Generator")
        self.geometry("820x560")
        self.minsize(820, 560)

        self.template_path_var = tk.StringVar()
        self.data_path_var = tk.StringVar()
        self.output_dir_var = tk.StringVar()
        self.filename_field_var = tk.StringVar()
        self.concurrency_var = tk.IntVar(value=max(1, min(os.cpu_count() or 4, 8)))

        self.available_fields: List[str] = []

        self._build_ui()

    def _build_ui(self) -> None:
        pad = {"padx": 8, "pady": 6}

        frm = ttk.Frame(self)
        frm.pack(fill=tk.BOTH, expand=True)

        # Template
        row = 0
        ttk.Label(frm, text="Template (HTML)").grid(row=row, column=0, sticky=tk.W, **pad)
        ttk.Entry(frm, textvariable=self.template_path_var, width=80).grid(row=row, column=1, sticky=tk.EW, **pad)
        ttk.Button(frm, text="Browse", command=self._browse_template).grid(row=row, column=2, **pad)

        # Data
        row += 1
        ttk.Label(frm, text="Data (CSV/XLSX)").grid(row=row, column=0, sticky=tk.W, **pad)
        ttk.Entry(frm, textvariable=self.data_path_var, width=80).grid(row=row, column=1, sticky=tk.EW, **pad)
        ttk.Button(frm, text="Browse", command=self._browse_data).grid(row=row, column=2, **pad)

        # Output
        row += 1
        ttk.Label(frm, text="Output Folder").grid(row=row, column=0, sticky=tk.W, **pad)
        ttk.Entry(frm, textvariable=self.output_dir_var, width=80).grid(row=row, column=1, sticky=tk.EW, **pad)
        ttk.Button(frm, text="Browse", command=self._browse_output).grid(row=row, column=2, **pad)

        # Filename field
        row += 1
        ttk.Label(frm, text="Filename Field").grid(row=row, column=0, sticky=tk.W, **pad)
        self.filename_combo = ttk.Combobox(frm, textvariable=self.filename_field_var, values=self.available_fields, state="readonly")
        self.filename_combo.grid(row=row, column=1, sticky=tk.EW, **pad)
        ttk.Button(frm, text="Refresh Fields", command=self._refresh_fields).grid(row=row, column=2, **pad)

        # Concurrency
        row += 1
        ttk.Label(frm, text="Parallel Workers").grid(row=row, column=0, sticky=tk.W, **pad)
        ttk.Spinbox(frm, textvariable=self.concurrency_var, from_=1, to=max(1, (os.cpu_count() or 4) * 2), width=6).grid(row=row, column=1, sticky=tk.W, **pad)

        # Actions
        row += 1
        actions = ttk.Frame(frm)
        actions.grid(row=row, column=0, columnspan=3, sticky=tk.EW, **pad)
        ttk.Button(actions, text="Generate Batch", command=self._on_generate_batch).pack(side=tk.LEFT, padx=4)
        ttk.Button(actions, text="Generate One", command=self._on_generate_single).pack(side=tk.LEFT, padx=4)
        ttk.Button(actions, text="Open Output Folder", command=self._open_output).pack(side=tk.LEFT, padx=4)

        # Log
        row += 1
        ttk.Label(frm, text="Log").grid(row=row, column=0, sticky=tk.NW, **pad)
        self.log = tk.Text(frm, height=18)
        self.log.grid(row=row, column=1, columnspan=2, sticky=tk.NSEW, **pad)

        frm.columnconfigure(1, weight=1)
        frm.rowconfigure(row, weight=1)

    def _browse_template(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("HTML files", "*.html;*.htm"), ("All files", "*.*")])
        if path:
            self.template_path_var.set(path)
            self._refresh_fields()

    def _browse_data(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("Data files", "*.csv;*.xlsx;*.xls"), ("All files", "*.*")])
        if path:
            self.data_path_var.set(path)

    def _browse_output(self) -> None:
        path = filedialog.askdirectory()
        if path:
            self.output_dir_var.set(path)

    def _open_output(self) -> None:
        out = self.output_dir_var.get()
        if not out:
            messagebox.showinfo("Output", "Please select an output folder first.")
            return
        try:
            os.startfile(out)  # type: ignore[attr-defined]
        except Exception:
            messagebox.showerror("Error", f"Cannot open folder: {out}")

    def _refresh_fields(self) -> None:
        path = self.template_path_var.get()
        if not path or not os.path.isfile(path):
            return
        try:
            fields = parse_template_fields(path)
            self.available_fields = fields
            self.filename_combo["values"] = fields
            if fields and self.filename_field_var.get() not in fields:
                self.filename_field_var.set(fields[0])
            self._log(f"Detected fields: {', '.join(fields)}")
        except Exception as exc:
            messagebox.showerror("Template Error", str(exc))

    def _log(self, msg: str) -> None:
        self.log.insert(tk.END, msg + "\n")
        self.log.see(tk.END)

    def _collect_opts(self) -> GenerationOptions:
        out_dir = self.output_dir_var.get().strip() or str(Path.home() / "Documents" / "LetterGen")
        ensure_directory(out_dir)
        return GenerationOptions(
            output_dir=out_dir,
            filename_field=self.filename_field_var.get().strip() or "filename",
            concurrency=max(1, int(self.concurrency_var.get() or 1)),
        )

    def _on_generate_batch(self) -> None:
        template = self.template_path_var.get()
        data = self.data_path_var.get()
        if not template or not os.path.isfile(template):
            messagebox.showwarning("Missing", "Please choose a template HTML file.")
            return
        if not data or not os.path.isfile(data):
            messagebox.showwarning("Missing", "Please choose a data CSV/XLSX file.")
            return
        opts = self._collect_opts()
        self._log("Starting batch generation...")

        def worker():
            try:
                results = generate_bulk(template, data, opts)
                self._log(f"Done. Generated {len(results)} files (PDF+DOCX pairs).")
            except Exception as exc:
                messagebox.showerror("Error", str(exc))

        threading.Thread(target=worker, daemon=True).start()

    def _on_generate_single(self) -> None:
        template = self.template_path_var.get()
        if not template or not os.path.isfile(template):
            messagebox.showwarning("Missing", "Please choose a template HTML file.")
            return
        fields = self.available_fields or parse_template_fields(template)
        dialog = SingleDialog(self, fields)
        self.wait_window(dialog)
        if not dialog.ok:
            return
        row = dialog.values
        opts = self._collect_opts()

        self._log("Generating single letter...")

        def worker():
            try:
                generate_single(template, row, opts)
                self._log("Done. Generated PDF and DOCX.")
            except Exception as exc:
                messagebox.showerror("Error", str(exc))

        threading.Thread(target=worker, daemon=True).start()


class SingleDialog(tk.Toplevel):
    def __init__(self, master: tk.Tk, fields: List[str]) -> None:
        super().__init__(master)
        self.title("Enter Fields")
        self.ok = False
        self.values: Dict[str, str] = {}
        self.inputs: Dict[str, tk.Entry] = {}

        frm = ttk.Frame(self)
        frm.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        for i, field in enumerate(fields):
            ttk.Label(frm, text=field).grid(row=i, column=0, sticky=tk.W, pady=4)
            ent = ttk.Entry(frm, width=50)
            ent.grid(row=i, column=1, sticky=tk.EW, pady=4)
            self.inputs[field] = ent

        btns = ttk.Frame(frm)
        btns.grid(row=len(fields), column=0, columnspan=2, pady=10)
        ttk.Button(btns, text="OK", command=self._on_ok).pack(side=tk.LEFT, padx=6)
        ttk.Button(btns, text="Cancel", command=self.destroy).pack(side=tk.LEFT, padx=6)

        frm.columnconfigure(1, weight=1)

        self.grab_set()
        self.transient(master)

    def _on_ok(self) -> None:
        for key, ent in self.inputs.items():
            self.values[key] = ent.get()
        self.ok = True
        self.destroy()


def main() -> None:
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
