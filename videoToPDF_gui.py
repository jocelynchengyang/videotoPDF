#!/usr/bin/env python3
"""
Simple GUI for videoToPDF.py

A thin Tkinter front-end around SlideCapture:
  - pick capture settings and a source window (or full screen)
  - Start / Stop the capture without using Ctrl+C
  - watch progress in a log pane
  - the PDF is written when you press Stop

Run:
    source .venv/bin/activate
    python3 videoToPDF_gui.py
"""

import os
import queue
import sys
import threading
import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk

from videoToPDF import SlideCapture


class _QueueWriter:
    """File-like object that forwards writes to a queue for the GUI to drain."""

    def __init__(self, q):
        self._q = q

    def write(self, text):
        if text:
            self._q.put(text)

    def flush(self):
        pass


class SlideCaptureGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("videoToPDF — Slide Capture")
        self.root.minsize(560, 520)

        self.capturer = None
        self.capture_thread = None
        self.log_queue = queue.Queue()
        self._stdout_backup = None
        self.windows = []  # list of {"label", "region"} from SlideCapture.list_windows()

        self._build_widgets()
        self.refresh_windows()
        self._drain_log()

    # ------------------------------------------------------------------ UI
    def _build_widgets(self):
        pad = {"padx": 8, "pady": 4}
        frm = ttk.Frame(self.root, padding=10)
        frm.pack(fill="both", expand=True)

        # Sensitivity
        ttk.Label(frm, text="Sensitivity (0.02–0.10):").grid(row=0, column=0, sticky="w", **pad)
        self.sensitivity_var = tk.DoubleVar(value=0.05)
        ttk.Spinbox(
            frm, from_=0.01, to=0.30, increment=0.01, width=8,
            textvariable=self.sensitivity_var, format="%.2f",
        ).grid(row=0, column=1, sticky="w", **pad)
        ttk.Label(frm, text="lower = more sensitive").grid(row=0, column=2, sticky="w", **pad)

        # Check interval
        ttk.Label(frm, text="Check interval (seconds):").grid(row=1, column=0, sticky="w", **pad)
        self.interval_var = tk.DoubleVar(value=1.0)
        ttk.Spinbox(
            frm, from_=0.2, to=10.0, increment=0.1, width=8,
            textvariable=self.interval_var, format="%.1f",
        ).grid(row=1, column=1, sticky="w", **pad)

        # Capture mode
        ttk.Label(frm, text="Capture mode:").grid(row=2, column=0, sticky="w", **pad)
        self.mode_var = tk.StringVar(value="first")
        mode_frame = ttk.Frame(frm)
        mode_frame.grid(row=2, column=1, columnspan=2, sticky="w", **pad)
        ttk.Radiobutton(mode_frame, text="first (on change)", value="first",
                        variable=self.mode_var).pack(side="left")
        ttk.Radiobutton(mode_frame, text="last (when stable)", value="last",
                        variable=self.mode_var).pack(side="left", padx=(12, 0))

        # Source window
        ttk.Label(frm, text="Capture source:").grid(row=3, column=0, sticky="w", **pad)
        self.source_var = tk.StringVar()
        self.source_combo = ttk.Combobox(frm, textvariable=self.source_var,
                                         state="readonly", width=44)
        self.source_combo.grid(row=3, column=1, columnspan=2, sticky="we", **pad)
        ttk.Button(frm, text="Refresh windows", command=self.refresh_windows).grid(
            row=4, column=1, columnspan=2, sticky="w", **pad)

        # Start / Stop
        btn_frame = ttk.Frame(frm)
        btn_frame.grid(row=5, column=0, columnspan=3, sticky="we", pady=(10, 4))
        self.start_btn = ttk.Button(btn_frame, text="Start capture", command=self.start_capture)
        self.start_btn.pack(side="left", padx=4)
        self.stop_btn = ttk.Button(btn_frame, text="Stop & save PDF",
                                   command=self.stop_capture, state="disabled")
        self.stop_btn.pack(side="left", padx=4)

        # Status
        self.status_var = tk.StringVar(value="Idle.")
        ttk.Label(frm, textvariable=self.status_var, foreground="#0a7").grid(
            row=6, column=0, columnspan=3, sticky="w", **pad)

        # Log
        self.log = scrolledtext.ScrolledText(frm, height=14, wrap="word", state="disabled")
        self.log.grid(row=7, column=0, columnspan=3, sticky="nsew", **pad)

        frm.columnconfigure(2, weight=1)
        frm.rowconfigure(7, weight=1)

    # ------------------------------------------------------------- helpers
    def _log(self, text):
        self.log.configure(state="normal")
        self.log.insert("end", text)
        self.log.see("end")
        self.log.configure(state="disabled")

    def _drain_log(self):
        try:
            while True:
                self._log(self.log_queue.get_nowait())
        except queue.Empty:
            pass

        if self.capturer is not None and self.capturer.is_capturing:
            self.status_var.set(f"Capturing…  {len(self.capturer.slides)} slide(s) so far")

        self.root.after(200, self._drain_log)

    def refresh_windows(self):
        probe = SlideCapture()
        self.windows = probe.list_windows()
        labels = ["Full screen"] + [w["label"] for w in self.windows]
        self.source_combo.configure(values=labels)
        if not self.source_var.get() or self.source_var.get() not in labels:
            self.source_combo.current(0)

    # -------------------------------------------------------------- actions
    def start_capture(self):
        if self.capture_thread and self.capture_thread.is_alive():
            return

        try:
            sensitivity = float(self.sensitivity_var.get())
            interval = float(self.interval_var.get())
        except (tk.TclError, ValueError):
            messagebox.showerror("Invalid input", "Sensitivity and interval must be numbers.")
            return

        self.capturer = SlideCapture(
            sensitivity=sensitivity,
            check_interval=interval,
            capture_mode=self.mode_var.get(),
        )

        idx = self.source_combo.current()
        if idx <= 0:
            region = self.capturer.get_full_screen_region()
        else:
            region = self.windows[idx - 1]["region"]

        # Route SlideCapture's print() output into the log pane.
        self._stdout_backup = sys.stdout
        sys.stdout = _QueueWriter(self.log_queue)

        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self.status_var.set("Capturing…")

        self.capture_thread = threading.Thread(
            target=self._run_capture, args=(region,), daemon=True
        )
        self.capture_thread.start()

    def _run_capture(self, region):
        try:
            self.capturer.start_capture(region=region)
        except Exception as e:  # noqa: BLE001 - surface anything to the log
            self.log_queue.put(f"\nError during capture: {e}\n")
        finally:
            self.root.after(0, self._on_capture_finished)

    def stop_capture(self):
        if self.capturer is not None:
            self.status_var.set("Stopping — building PDF…")
            self.stop_btn.configure(state="disabled")
            self.capturer.stop()

    def _on_capture_finished(self):
        if self._stdout_backup is not None:
            sys.stdout = self._stdout_backup
            self._stdout_backup = None

        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")

        count = len(self.capturer.slides) if self.capturer else 0
        if count and getattr(self.capturer, "session_timestamp", None):
            pdf = os.path.join(
                self.capturer.output_dir,
                f"slides_{self.capturer.session_timestamp}.pdf",
            )
            self.status_var.set(f"Done — {count} slide(s). Saved: {pdf}")
        else:
            self.status_var.set("Stopped — no slides captured.")

    def on_close(self):
        if self.capturer is not None and self.capturer.is_capturing:
            if not messagebox.askyesno("Quit", "Capture is running. Stop and quit?"):
                return
            self.capturer.stop()
        self.root.destroy()


def main():
    root = tk.Tk()
    app = SlideCaptureGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()


if __name__ == "__main__":
    main()
