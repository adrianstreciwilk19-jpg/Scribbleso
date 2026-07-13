import html
import os
import re
import sys
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, ttk


DEFAULT_FONT_SIZE = 11
DESCRIPTION_FONT_SIZE = 9
ANONYMIZE_PATTERN = re.compile(
    r"""
    (?P<email>\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b)
    |
    (?P<address>
        (?<!\w)
        (?:
            (?i:ul\.?|ulica|al\.?|aleja|pl\.?|plac|os\.?|osiedle|rondo|rynek)\s+
            [A-Za-zĄĆĘŁŃÓŚŹŻąćęłńóśźż0-9.'-]+
            (?:\s+[A-Za-zĄĆĘŁŃÓŚŹŻąćęłńóśźż0-9.'-]+){0,5}
            \s+\d+[A-Za-z]?(?:[/-]\d+[A-Za-z]?)?
            (?:\s*,?\s*\d{2}-\d{3}\s+
                [A-Za-zĄĆĘŁŃÓŚŹŻąćęłńóśźż.'-]+
                (?:\s+[A-Za-zĄĆĘŁŃÓŚŹŻąćęłńóśźż.'-]+){0,3}
            )?
            |
            [A-ZĄĆĘŁŃÓŚŹŻ][A-Za-zĄĆĘŁŃÓŚŹŻąćęłńóśźż.'-]+
            (?:\s+[A-ZĄĆĘŁŃÓŚŹŻ][A-Za-zĄĆĘŁŃÓŚŹŻąćęłńóśźż.'-]+){0,4}
            \s+\d+[A-Za-z]?(?:[/-]\d+[A-Za-z]?)?
            \s*,?\s*\d{2}-\d{3}\s+
            [A-ZĄĆĘŁŃÓŚŹŻ][A-Za-zĄĆĘŁŃÓŚŹŻąćęłńóśźż.'-]+
            (?:\s+[A-ZĄĆĘŁŃÓŚŹŻ][A-Za-zĄĆĘŁŃÓŚŹŻąćęłńóśźż.'-]+){0,3}
        )
        (?!\w)
    )
    |
    (?P<number_sequence>(?<!\w)\+?\d(?:[\s.-]?\d){6,}(?!\w))
    |
    (?P<identifier>
        (?<!\w)
        (?:
            (?=[A-Za-z0-9._/-]*\d)(?=[A-Za-z0-9._/-]*[._/-])
            [A-Za-z0-9]+(?:[._/-][A-Za-z0-9]+)+
            |
            (?=(?:[A-Za-z0-9]*\d){3,})(?=[A-Za-z0-9]*[A-Za-z])
            [A-Za-z0-9]{4,}
            |
            \d{3,}
        )
        (?!\w)
    )
    |
    (?P<person>
        (?<!\w)
        [A-ZĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż]{2,}(?:-[A-ZĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż]{2,})?
        \s+
        [A-ZĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż]{2,}(?:-[A-ZĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż]{2,})?
        (?:\s+[A-ZĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż]{2,}(?:-[A-ZĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż]{2,})?)?
        (?!\w)
    )
    """,
    re.VERBOSE,
)
PROTECTED_REFERENCE_PATTERN = re.compile(
    r"""
    (?<!\w)
    (?:
        (?i:(?:RZ|Z|R)-\d+-\d{2,4})
        |
        (?i:ZU\d+)
    )
    (?!\w)
    """,
    re.VERBOSE,
)
STATIC_OUTPUT_LABELS = {
    "Opis Zgłoszenia:",
    "Komentarz dla użytkownika:",
    "Komentarz techniczny:",
    "[OPIS]",
    "[SQL]",
}
PERSON_FALSE_POSITIVE_WORDS = {
    "adres",
    "aplikacja",
    "błąd",
    "cnk",
    "dane",
    "data",
    "email",
    "komentarz",
    "konto",
    "mail",
    "microsoft",
    "numer",
    "odpowiedź",
    "opis",
    "problem",
    "sql",
    "system",
    "techniczny",
    "telefon",
    "tytuł",
    "użytkownika",
    "windows",
    "word",
    "zgłoszenia",
}
THEME_PALETTES = {
    "light": {
        "accent": "#2563eb",
        "accent_active": "#1d4ed8",
        "bg": "#e8eef6",
        "border": "#cbd5e1",
        "button": "#e2e8f0",
        "button_active": "#cbd5e1",
        "error": "#b91c1c",
        "input_bg": "#ffffff",
        "input_fg": "#111827",
        "muted": "#64748b",
        "panel": "#ffffff",
        "select_bg": "#bfdbfe",
        "select_fg": "#0f172a",
        "success": "#047857",
        "text": "#111827",
    },
    "dark": {
        "accent": "#38bdf8",
        "accent_active": "#0ea5e9",
        "bg": "#0f172a",
        "border": "#334155",
        "button": "#263449",
        "button_active": "#334155",
        "error": "#fca5a5",
        "input_bg": "#0b1220",
        "input_fg": "#e5e7eb",
        "muted": "#94a3b8",
        "panel": "#111827",
        "select_bg": "#075985",
        "select_fg": "#f8fafc",
        "success": "#6ee7b7",
        "text": "#e5e7eb",
    },
}


def px_font(size_px, family="Segoe UI"):
    # Tkinter interprets negative font sizes as pixels.
    return (family, -size_px)


class ScribblesoApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Opis zadań pod AI")
        self.geometry("1040x720")
        self.minsize(900, 620)

        self.theme_mode = tk.StringVar(value="Jasny")
        self.palette = THEME_PALETTES["light"]
        self.anonymize_enabled = tk.BooleanVar(value=True)
        self.sql_enabled = tk.BooleanVar(value=False)
        self.cnk_enabled = tk.BooleanVar(value=False)
        self.cnk_count = tk.IntVar(value=1)
        self.cnk_items = []
        self.output_file_path = tk.StringVar(value="")
        self.file_status = tk.StringVar(value="")

        self._configure_style()
        self._build_layout()
        self._bind_updates()
        self._update_preview()

    def _configure_style(self):
        palette = self.palette
        self.configure(bg=palette["bg"])

        style = ttk.Style(self)
        self.style = style
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure("TFrame", background=palette["bg"])
        style.configure("Panel.TFrame", background=palette["panel"], relief="flat")
        style.configure(
            "TLabel",
            background=palette["bg"],
            foreground=palette["text"],
            font=px_font(DEFAULT_FONT_SIZE),
        )
        style.configure(
            "Panel.TLabel",
            background=palette["panel"],
            foreground=palette["text"],
            font=px_font(DEFAULT_FONT_SIZE),
        )
        style.configure(
            "Heading.TLabel",
            background=palette["panel"],
            foreground=palette["text"],
            font=("Segoe UI", -16, "bold"),
        )
        style.configure(
            "Muted.Panel.TLabel",
            background=palette["panel"],
            foreground=palette["muted"],
            font=px_font(10),
        )
        style.configure(
            "TButton",
            background=palette["button"],
            bordercolor=palette["border"],
            focusthickness=1,
            focuscolor=palette["accent"],
            foreground=palette["text"],
            font=px_font(DEFAULT_FONT_SIZE),
            padding=(12, 8),
        )
        style.map(
            "TButton",
            background=[
                ("disabled", palette["button"]),
                ("active", palette["button_active"]),
            ],
            foreground=[("disabled", palette["muted"])],
        )
        style.configure(
            "Accent.TButton",
            background=palette["accent"],
            bordercolor=palette["accent"],
            foreground="#ffffff",
            font=px_font(DEFAULT_FONT_SIZE),
            padding=(12, 8),
        )
        style.map(
            "Accent.TButton",
            background=[
                ("disabled", palette["button"]),
                ("active", palette["accent_active"]),
            ],
            foreground=[("disabled", palette["muted"])],
        )
        style.configure(
            "TCheckbutton",
            background=palette["panel"],
            foreground=palette["text"],
            font=px_font(DEFAULT_FONT_SIZE),
        )
        style.map(
            "TCheckbutton",
            background=[("active", palette["panel"])],
            foreground=[("disabled", palette["muted"])],
        )
        style.configure(
            "TEntry",
            bordercolor=palette["border"],
            fieldbackground=palette["input_bg"],
            foreground=palette["input_fg"],
            insertcolor=palette["text"],
            padding=(8, 6),
        )
        style.configure(
            "TSpinbox",
            arrowsize=12,
            bordercolor=palette["border"],
            fieldbackground=palette["input_bg"],
            foreground=palette["input_fg"],
            insertcolor=palette["text"],
            padding=(6, 5),
        )
        style.configure(
            "TCombobox",
            arrowcolor=palette["text"],
            bordercolor=palette["border"],
            fieldbackground=palette["input_bg"],
            foreground=palette["input_fg"],
            padding=(8, 5),
        )
        style.map(
            "TCombobox",
            fieldbackground=[("readonly", palette["input_bg"])],
            foreground=[("readonly", palette["input_fg"])],
            selectbackground=[("readonly", palette["input_bg"])],
            selectforeground=[("readonly", palette["input_fg"])],
        )
        style.configure(
            "Status.TLabel",
            background=palette["panel"],
            foreground=palette["muted"],
            font=px_font(10),
        )

    def _change_theme(self, _event=None):
        self.palette = (
            THEME_PALETTES["dark"]
            if self.theme_mode.get() == "Ciemny"
            else THEME_PALETTES["light"]
        )
        self._configure_style()
        self._apply_theme_to_widgets()

    def _apply_theme_to_widgets(self):
        self._apply_theme_to_widget_tree(self)
        self.preview_text.tag_configure("default", font=px_font(DEFAULT_FONT_SIZE))
        self.preview_text.tag_configure("title", font=px_font(DEFAULT_FONT_SIZE))
        self.preview_text.tag_configure("description", font=px_font(DESCRIPTION_FONT_SIZE))

    def _apply_theme_to_widget_tree(self, widget):
        palette = self.palette

        if isinstance(widget, tk.Canvas):
            widget.configure(
                bg=palette["panel"],
                highlightbackground=palette["border"],
                highlightcolor=palette["accent"],
            )
        elif isinstance(widget, tk.Text):
            widget.configure(
                bg=palette["input_bg"],
                fg=palette["input_fg"],
                highlightbackground=palette["border"],
                highlightcolor=palette["accent"],
                insertbackground=palette["text"],
                selectbackground=palette["select_bg"],
                selectforeground=palette["select_fg"],
            )

        for child in widget.winfo_children():
            self._apply_theme_to_widget_tree(child)

    def _build_layout(self):
        root = ttk.Frame(self, padding=18)
        root.grid(row=0, column=0, sticky="nsew")

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        root.columnconfigure(0, weight=1, uniform="columns")
        root.columnconfigure(1, weight=1, uniform="columns")
        root.rowconfigure(0, weight=1)

        form_shell = ttk.Frame(root, style="Panel.TFrame")
        form_shell.grid(row=0, column=0, sticky="nsew", padx=(0, 9))
        form_shell.columnconfigure(0, weight=1)
        form_shell.rowconfigure(0, weight=1)

        self.form_canvas = tk.Canvas(
            form_shell,
            bg=self.palette["panel"],
            highlightthickness=1,
            highlightbackground=self.palette["border"],
        )
        self.form_canvas.grid(row=0, column=0, sticky="nsew")

        form_scrollbar = ttk.Scrollbar(form_shell, orient="vertical", command=self.form_canvas.yview)
        form_scrollbar.grid(row=0, column=1, sticky="ns")
        self.form_canvas.configure(yscrollcommand=form_scrollbar.set)

        form_panel = ttk.Frame(self.form_canvas, style="Panel.TFrame", padding=18)
        self.form_canvas_window = self.form_canvas.create_window(
            (0, 0), window=form_panel, anchor="nw"
        )
        form_panel.bind("<Configure>", self._update_form_scrollregion)
        self.form_canvas.bind("<Configure>", self._resize_form_panel)
        self._bind_form_mousewheel()
        form_panel.columnconfigure(0, weight=1)

        form_header = ttk.Frame(form_panel, style="Panel.TFrame")
        form_header.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        form_header.columnconfigure(0, weight=1)

        ttk.Label(form_header, text="Dane zgłoszenia", style="Heading.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Button(form_header, text="Wyczyść", command=self.clear_form).grid(
            row=0, column=1, sticky="e"
        )

        options_frame = ttk.Frame(form_panel, style="Panel.TFrame")
        options_frame.grid(row=1, column=0, sticky="ew", pady=(0, 14))

        self.anonymize_checkbox = ttk.Checkbutton(
            options_frame,
            text="Anonimizuj",
            variable=self.anonymize_enabled,
            command=self._update_preview,
        )
        self.anonymize_checkbox.grid(row=0, column=0, sticky="w", padx=(0, 18))

        self.sql_checkbox = ttk.Checkbutton(
            options_frame,
            text="SQL",
            variable=self.sql_enabled,
            command=self._toggle_sql_input,
        )
        self.sql_checkbox.grid(row=0, column=1, sticky="w", padx=(0, 18))

        self.cnk_checkbox = ttk.Checkbutton(
            options_frame,
            text="CNK",
            variable=self.cnk_enabled,
            command=self._toggle_cnk_input,
        )
        self.cnk_checkbox.grid(row=0, column=2, sticky="w")

        self.cnk_controls = ttk.Frame(options_frame, style="Panel.TFrame")
        self.cnk_controls.grid(row=1, column=0, columnspan=3, sticky="ew", pady=(8, 0))
        self.cnk_controls.columnconfigure(2, weight=1)

        ttk.Label(self.cnk_controls, text="Liczba par CNK:", style="Panel.TLabel").grid(
            row=0, column=0, sticky="w", padx=(0, 8)
        )
        self.cnk_count_spinbox = ttk.Spinbox(
            self.cnk_controls,
            from_=1,
            to=20,
            width=5,
            textvariable=self.cnk_count,
            command=self._sync_cnk_fields,
        )
        self.cnk_count_spinbox.grid(row=0, column=1, sticky="w")
        self.cnk_controls.grid_remove()

        ttk.Label(form_panel, text="Tytuł", style="Panel.TLabel").grid(row=2, column=0, sticky="w")
        self.title_entry = ttk.Entry(form_panel, font=px_font(DEFAULT_FONT_SIZE))
        self.title_entry.grid(row=3, column=0, sticky="ew", pady=(5, 12))

        ttk.Label(form_panel, text="Opis Zgłoszenia:", style="Panel.TLabel").grid(
            row=4, column=0, sticky="nw"
        )
        self.description_text = self._make_text(form_panel, height=5, font_size=DESCRIPTION_FONT_SIZE)
        self.description_text.grid(row=5, column=0, sticky="nsew", pady=(5, 12))

        ttk.Label(form_panel, text="Komentarz dla użytkownika:", style="Panel.TLabel").grid(
            row=6, column=0, sticky="nw"
        )
        self.user_comment_text = self._make_text(form_panel, height=5)
        self.user_comment_text.grid(row=7, column=0, sticky="nsew", pady=(5, 12))

        ttk.Label(form_panel, text="Komentarz techniczny:", style="Panel.TLabel").grid(
            row=8, column=0, sticky="nw"
        )
        self.technical_comment_text = self._make_text(form_panel, height=5)
        self.technical_comment_text.grid(row=9, column=0, sticky="nsew", pady=(5, 10))

        self.sql_text = self._make_text(form_panel, height=4)

        self.cnk_frame = ttk.Frame(form_panel, style="Panel.TFrame")
        self.cnk_frame.columnconfigure(0, weight=1)

        self.cnk_fields_frame = ttk.Frame(self.cnk_frame, style="Panel.TFrame")
        self.cnk_fields_frame.grid(row=0, column=0, sticky="ew")
        self.cnk_fields_frame.columnconfigure(0, weight=1)

        preview_panel = ttk.Frame(root, style="Panel.TFrame", padding=18)
        preview_panel.grid(row=0, column=1, sticky="nsew", padx=(9, 0))
        preview_panel.columnconfigure(0, weight=1)
        preview_panel.rowconfigure(2, weight=1)

        header = ttk.Frame(preview_panel, style="Panel.TFrame")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        header.columnconfigure(0, weight=1)

        ttk.Label(header, text="Wynik", style="Heading.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(header, text="Motyw", style="Muted.Panel.TLabel").grid(
            row=0, column=1, sticky="e", padx=(0, 8)
        )
        self.theme_combobox = ttk.Combobox(
            header,
            textvariable=self.theme_mode,
            values=("Jasny", "Ciemny"),
            state="readonly",
            width=8,
        )
        self.theme_combobox.grid(row=0, column=2, sticky="e", padx=(0, 10))
        self.theme_combobox.bind("<<ComboboxSelected>>", self._change_theme)

        self.copy_button = ttk.Button(
            header, text="Kopiuj", command=self.copy_result, style="Accent.TButton"
        )
        self.copy_button.grid(row=0, column=3, sticky="e")

        file_panel = ttk.Frame(preview_panel, style="Panel.TFrame")
        file_panel.grid(row=1, column=0, sticky="ew", pady=(0, 12))
        file_panel.columnconfigure(1, weight=1)

        ttk.Label(file_panel, text="Plik:", style="Panel.TLabel").grid(
            row=0, column=0, sticky="w", padx=(0, 8)
        )
        self.output_file_entry = ttk.Entry(
            file_panel,
            textvariable=self.output_file_path,
            font=px_font(DEFAULT_FONT_SIZE),
        )
        self.output_file_entry.grid(row=0, column=1, sticky="ew", padx=(0, 8))
        ttk.Button(file_panel, text="Wybierz", command=self.choose_output_file).grid(
            row=0, column=2, sticky="e", padx=(0, 8)
        )
        self.append_file_button = ttk.Button(
            file_panel,
            text="Dopisz",
            command=self.append_result_to_file,
            style="Accent.TButton",
        )
        self.append_file_button.grid(row=0, column=3, sticky="e")

        self.file_status_label = ttk.Label(
            file_panel, textvariable=self.file_status, style="Status.TLabel"
        )
        self.file_status_label.grid(row=1, column=1, columnspan=3, sticky="w", pady=(5, 0))

        preview_frame = ttk.Frame(preview_panel, style="Panel.TFrame")
        preview_frame.grid(row=2, column=0, sticky="nsew")
        preview_frame.columnconfigure(0, weight=1)
        preview_frame.rowconfigure(0, weight=1)

        self.preview_text = tk.Text(
            preview_frame,
            wrap="word",
            font=px_font(DEFAULT_FONT_SIZE),
            bg=self.palette["input_bg"],
            fg=self.palette["input_fg"],
            relief="solid",
            borderwidth=1,
            highlightbackground=self.palette["border"],
            highlightcolor=self.palette["accent"],
            insertbackground=self.palette["text"],
            padx=12,
            pady=12,
            selectbackground=self.palette["select_bg"],
            selectforeground=self.palette["select_fg"],
            undo=False,
        )
        self.preview_text.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(preview_frame, orient="vertical", command=self.preview_text.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.preview_text.configure(yscrollcommand=scrollbar.set)

        self.preview_text.tag_configure("default", font=px_font(DEFAULT_FONT_SIZE))
        self.preview_text.tag_configure("title", font=px_font(DEFAULT_FONT_SIZE))
        self.preview_text.tag_configure("description", font=px_font(DESCRIPTION_FONT_SIZE))
        self.preview_text.configure(state="disabled")

    def _make_text(self, parent, height, font_size=DEFAULT_FONT_SIZE):
        frame = ttk.Frame(parent, style="Panel.TFrame")
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)

        text = tk.Text(
            frame,
            height=height,
            wrap="word",
            font=px_font(font_size),
            bg=self.palette["input_bg"],
            fg=self.palette["input_fg"],
            relief="solid",
            borderwidth=1,
            highlightbackground=self.palette["border"],
            highlightcolor=self.palette["accent"],
            padx=8,
            pady=7,
            insertbackground=self.palette["text"],
            selectbackground=self.palette["select_bg"],
            selectforeground=self.palette["select_fg"],
        )
        text.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=text.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        text.configure(yscrollcommand=scrollbar.set)

        return frame

    def _update_form_scrollregion(self, _event=None):
        self.form_canvas.configure(scrollregion=self.form_canvas.bbox("all"))

    def _resize_form_panel(self, event):
        self.form_canvas.itemconfigure(self.form_canvas_window, width=event.width)

    def _bind_form_mousewheel(self):
        self.bind_all("<MouseWheel>", self._on_form_mousewheel, add="+")
        self.bind_all("<Button-4>", self._on_form_mousewheel, add="+")
        self.bind_all("<Button-5>", self._on_form_mousewheel, add="+")

    def _on_form_mousewheel(self, event):
        widget = self.winfo_containing(event.x_root, event.y_root)
        if not self._is_widget_inside(widget, self.form_canvas):
            return None

        if self._is_widget_inside(widget, self.preview_text) or isinstance(widget, tk.Text):
            return None

        units = self._mousewheel_units(event)
        if units:
            self.form_canvas.yview_scroll(units, "units")
            return "break"
        return None

    def _is_widget_inside(self, widget, parent):
        while widget is not None:
            if widget == parent:
                return True
            widget = widget.master
        return False

    def _mousewheel_units(self, event):
        if getattr(event, "num", None) == 4:
            return -3
        if getattr(event, "num", None) == 5:
            return 3

        delta = getattr(event, "delta", 0)
        if not delta:
            return 0

        steps = int(delta / 120)
        if steps == 0:
            steps = 1 if delta > 0 else -1
        return -steps * 3

    def _bind_updates(self):
        self.title_entry.bind("<KeyRelease>", lambda _event: self._update_preview())
        self.cnk_count_spinbox.bind(
            "<KeyRelease>", lambda _event: self.after_idle(self._sync_cnk_fields)
        )
        self.cnk_count_spinbox.bind("<FocusOut>", lambda _event: self._sync_cnk_fields())
        self.cnk_count_spinbox.bind("<Return>", lambda _event: self._sync_cnk_fields())

        for widget in self._input_text_widgets():
            self._bind_text_updates(widget)

    def _bind_text_updates(self, widget):
        widget.bind("<KeyRelease>", lambda _event: self._update_preview())
        widget.bind("<<Paste>>", lambda _event: self.after_idle(self._update_preview))
        widget.bind("<<Cut>>", lambda _event: self.after_idle(self._update_preview))

    def _input_text_widgets(self):
        return [
            self._text_from_frame(self.description_text),
            self._text_from_frame(self.user_comment_text),
            self._text_from_frame(self.technical_comment_text),
            self._text_from_frame(self.sql_text),
        ]

    def _text_from_frame(self, frame):
        for child in frame.winfo_children():
            if isinstance(child, tk.Text):
                return child
        raise RuntimeError("Nie znaleziono pola tekstowego.")

    def clear_form(self):
        self.title_entry.delete(0, "end")
        for frame in (
            self.description_text,
            self.user_comment_text,
            self.technical_comment_text,
            self.sql_text,
        ):
            self._clear_text_frame(frame)

        self.sql_enabled.set(False)
        self.sql_text.grid_remove()

        self.cnk_enabled.set(False)
        self.cnk_count.set(1)
        self._sync_cnk_fields()
        for item in self.cnk_items:
            self._clear_text_frame(item["comment_text"])
            self._clear_text_frame(item["response_text"])
        self.cnk_controls.grid_remove()
        self.cnk_frame.grid_remove()

        self.file_status.set("")
        self._reset_copy_button()
        self.after_idle(self._update_form_scrollregion)
        self._update_preview()

    def _clear_text_frame(self, frame):
        self._text_from_frame(frame).delete("1.0", "end")

    def _toggle_sql_input(self):
        if self.sql_enabled.get():
            self.sql_text.grid(row=10, column=0, sticky="nsew", pady=(0, 12))
        else:
            self.sql_text.grid_remove()
        self.after_idle(self._update_form_scrollregion)
        self._update_preview()

    def _toggle_cnk_input(self):
        if self.cnk_enabled.get():
            self.cnk_controls.grid()
            self.cnk_frame.grid(row=11, column=0, sticky="ew", pady=(0, 12))
            self._sync_cnk_fields()
            return
        else:
            self.cnk_controls.grid_remove()
            self.cnk_frame.grid_remove()
            self.after_idle(self._update_form_scrollregion)
        self._update_preview()

    def _sync_cnk_fields(self):
        count = self._get_cnk_count()

        while len(self.cnk_items) < count:
            self.cnk_items.append(self._make_cnk_item(len(self.cnk_items) + 1))

        while len(self.cnk_items) > count:
            item = self.cnk_items.pop()
            item["frame"].destroy()

        self._reindex_cnk_items()
        self.after_idle(self._update_form_scrollregion)
        self._update_preview()

    def _get_cnk_count(self):
        try:
            current_count = self.cnk_count.get()
            invalid_count = False
        except tk.TclError:
            current_count = 1
            invalid_count = True

        count = current_count
        count = max(1, min(20, count))
        if invalid_count or current_count != count:
            self.cnk_count.set(count)
        return count

    def _make_cnk_item(self, index):
        item_frame = ttk.Frame(self.cnk_fields_frame, style="Panel.TFrame")
        item_frame.columnconfigure(0, weight=1)

        comment_label = ttk.Label(
            item_frame, text=f"Komentarz na CNK {index}:", style="Panel.TLabel"
        )
        comment_label.grid(row=0, column=0, sticky="nw")
        comment_text = self._make_text(item_frame, height=4)
        comment_text.grid(row=1, column=0, sticky="nsew", pady=(5, 10))

        response_label = ttk.Label(
            item_frame, text=f"Odpowiedź Użytkownika {index}:", style="Panel.TLabel"
        )
        response_label.grid(row=2, column=0, sticky="nw")
        response_text = self._make_text(item_frame, height=4)
        response_text.grid(row=3, column=0, sticky="nsew", pady=(5, 12))

        self._bind_text_updates(self._text_from_frame(comment_text))
        self._bind_text_updates(self._text_from_frame(response_text))

        return {
            "frame": item_frame,
            "comment_label": comment_label,
            "comment_text": comment_text,
            "response_label": response_label,
            "response_text": response_text,
        }

    def _reindex_cnk_items(self):
        for index, item in enumerate(self.cnk_items, start=1):
            item["frame"].grid(row=index - 1, column=0, sticky="ew")
            item["comment_label"].configure(text=f"Komentarz na CNK {index}:")
            item["response_label"].configure(text=f"Odpowiedź Użytkownika {index}:")

    def _get_text(self, frame):
        return self._text_from_frame(frame).get("1.0", "end-1c").strip()

    def _append_block(self, sections, lines):
        if sections:
            sections.append(("default", ""))
        sections.extend(lines)

    def _build_sections(self):
        title = self.title_entry.get().strip()
        description = self._get_text(self.description_text)
        user_comment = self._get_text(self.user_comment_text)
        technical_comment = self._get_text(self.technical_comment_text)
        sql = self._get_text(self.sql_text) if self.sql_enabled.get() else ""

        sections = []
        if title:
            sections.append(("title", title))

        if description:
            self._append_block(
                sections,
                [
                    ("default", "Opis Zgłoszenia:"),
                    ("description", description),
                ],
            )

        if user_comment:
            self._append_block(
                sections,
                [
                    ("default", "Komentarz dla użytkownika:"),
                    ("default", user_comment),
                ],
            )

        if technical_comment:
            self._append_block(
                sections,
                [
                    ("default", "Komentarz techniczny:"),
                    ("default", "[OPIS]"),
                    ("default", technical_comment),
                ],
            )

        if sql:
            self._append_block(
                sections,
                [
                    ("default", "[SQL]"),
                    ("default", sql),
                ],
            )

        if self.cnk_enabled.get():
            for index, item in enumerate(self.cnk_items, start=1):
                cnk_comment = self._get_text(item["comment_text"])
                user_response = self._get_text(item["response_text"])

                if cnk_comment:
                    self._append_block(
                        sections,
                        [
                            ("default", f"Komentarz na CNK {index}:"),
                            ("default", cnk_comment),
                        ],
                    )

                if user_response:
                    self._append_block(
                        sections,
                        [
                            ("default", f"Odpowiedź Użytkownika {index}:"),
                            ("default", user_response),
                        ],
                    )

        if self.anonymize_enabled.get():
            return self._anonymize_sections(sections)

        return sections

    def _anonymize_sections(self, sections):
        replacements = {}
        counters = {"ADRES": 0, "EMAIL": 0, "ID": 0, "KLIENT": 0}
        protected_values = {}

        def replacement(match):
            kind = self._anonymized_match_kind(match)
            value = match.group(0)
            if kind == "KLIENT" and self._is_false_positive_person(value):
                return value

            key = (kind, value)

            if key not in replacements:
                counters[kind] += 1
                replacements[key] = f"[{kind}_{counters[kind]}]"

            return replacements[key]

        def anonymize_text(text):
            protected_text = self._protect_references(text, protected_values)
            anonymized_text = ANONYMIZE_PATTERN.sub(replacement, protected_text)
            return self._restore_references(anonymized_text, protected_values)

        return [
            (
                tag,
                anonymize_text(text)
                if self._should_anonymize_text(tag, text)
                else text,
            )
            for tag, text in sections
        ]

    def _protect_references(self, text, protected_values):
        protected_text = PROTECTED_REFERENCE_PATTERN.sub(
            lambda match: self._store_protected_value(match.group(0), protected_values),
            text,
        )
        return re.sub(
            r"(?<!\d)\d{8}(?!\d)",
            lambda match: (
                self._store_protected_value(match.group(0), protected_values)
                if self._is_yyyymmdd_date(match.group(0))
                else match.group(0)
            ),
            protected_text,
        )

    def _store_protected_value(self, value, protected_values):
        token = f"__SCRIBBLESO_KEEP_{len(protected_values)}__"
        protected_values[token] = value
        return token

    def _is_yyyymmdd_date(self, value):
        try:
            datetime.strptime(value, "%Y%m%d")
        except ValueError:
            return False
        return True

    def _restore_references(self, text, protected_values):
        for token, value in protected_values.items():
            text = text.replace(token, value)
        return text

    def _anonymized_match_kind(self, match):
        if match.group("address"):
            return "ADRES"
        if match.group("email"):
            return "EMAIL"
        if match.group("person"):
            return "KLIENT"
        return "ID"

    def _should_anonymize_text(self, tag, text):
        if tag == "title":
            return False

        if not text or text in STATIC_OUTPUT_LABELS:
            return False

        return not re.fullmatch(r"(Komentarz na CNK|Odpowiedź Użytkownika) \d+:", text)

    def _is_false_positive_person(self, value):
        words = re.split(r"[\s-]+", value.casefold())
        return any(word in PERSON_FALSE_POSITIVE_WORDS for word in words)

    def _update_preview(self):
        sections = self._build_sections()

        self.preview_text.configure(state="normal")
        self.preview_text.delete("1.0", "end")

        for index, (tag, text) in enumerate(sections):
            if index > 0:
                self.preview_text.insert("end", "\n")
            self.preview_text.insert("end", text, tag)

        self.preview_text.configure(state="disabled")

    def copy_result(self):
        sections = self._build_sections()
        plain_text = self._plain_text(sections)
        html_text = self._html_text(sections)

        try:
            self._copy_html_to_clipboard(html_text, plain_text)
        except Exception:
            self.clipboard_clear()
            self.clipboard_append(plain_text)
            self.update_idletasks()

        self._show_copy_feedback()

    def _show_copy_feedback(self):
        self.copy_button.configure(text="Skopiowano", state="disabled")
        self.after(3000, self._reset_copy_button)

    def _reset_copy_button(self):
        self.copy_button.configure(text="Kopiuj", state="normal")

    def choose_output_file(self):
        path = filedialog.asksaveasfilename(
            title="Wybierz plik do dopisywania",
            defaultextension=".txt",
            filetypes=[
                ("Pliki tekstowe i Word", "*.txt *.docx"),
                ("Pliki tekstowe", "*.txt"),
                ("Dokumenty Word", "*.docx"),
                ("Wszystkie pliki", "*.*"),
            ],
            confirmoverwrite=False,
        )
        if path:
            self.output_file_path.set(path)
            self.file_status.set("")

    def append_result_to_file(self):
        sections = self._build_sections()
        plain_text = self._plain_text(sections).strip()
        if not plain_text:
            self._show_file_status("Brak wyniku do dopisania.", success=False)
            return

        path_text = self.output_file_path.get().strip()
        if not path_text:
            self._show_file_status("Najpierw wybierz plik .txt albo .docx.", success=False)
            return

        path = Path(path_text)
        suffix = path.suffix.lower()

        try:
            if suffix == ".txt":
                self._append_to_txt(path, plain_text)
            elif suffix == ".docx":
                self._append_to_docx(path, sections)
            else:
                self._show_file_status("Obsługiwane są tylko pliki .txt i .docx.", success=False)
                return
        except Exception as exc:
            self._show_file_status(f"Nie udało się dopisać: {exc}", success=False)
            return

        self._show_file_status("Dopisano wynik do pliku.", success=True)

    def _append_to_txt(self, path, plain_text):
        try:
            content, encoding = self._read_text_file(path)
        except OSError:
            self._append_to_open_txt(path, plain_text, "utf-8")
            return

        content = content.rstrip()
        new_content = plain_text if not content else f"{content}\n\n\n{plain_text}"
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            path.write_text(new_content, encoding=encoding)
        except OSError:
            self._append_to_open_txt(path, plain_text, encoding)

    def _append_to_open_txt(self, path, plain_text, encoding):
        separator = "" if not path.exists() or path.stat().st_size == 0 else "\n\n\n"
        with path.open("a", encoding=encoding, newline="") as file:
            file.write(f"{separator}{plain_text}")

    def _read_text_file(self, path):
        if not path.exists():
            return "", "utf-8"

        data = path.read_bytes()
        if data.startswith(b"\xef\xbb\xbf"):
            return data.decode("utf-8-sig"), "utf-8-sig"

        for encoding in ("utf-8", "cp1250", "cp1252"):
            try:
                return data.decode(encoding), encoding
            except UnicodeDecodeError:
                pass

        return data.decode("utf-8", errors="replace"), "utf-8"

    def _append_to_docx(self, path, sections):
        try:
            self._append_to_docx_file(path, sections)
        except OSError as exc:
            if self._append_to_open_word_document(path, sections):
                return
            raise exc

    def _append_to_docx_file(self, path, sections):
        from docx import Document
        from docx.shared import Pt

        path.parent.mkdir(parents=True, exist_ok=True)
        document = Document(path) if path.exists() else Document()

        if self._docx_has_text(document):
            self._trim_docx_trailing_empty_paragraphs(document)
            document.add_paragraph()
            document.add_paragraph()
        elif len(document.paragraphs) == 1 and not document.paragraphs[0].text.strip():
            self._remove_docx_paragraph(document.paragraphs[0])

        for tag, text in sections:
            size = DESCRIPTION_FONT_SIZE if tag == "description" else DEFAULT_FONT_SIZE
            if not text:
                document.add_paragraph()
                continue

            for line in text.split("\n"):
                paragraph = (
                    document.add_paragraph(style="Heading 1")
                    if tag == "title"
                    else document.add_paragraph()
                )
                run = paragraph.add_run(line)
                if tag != "title":
                    run.font.name = "Segoe UI"
                    run.font.size = Pt(size)

        document.save(path)

    def _append_to_open_word_document(self, path, sections):
        try:
            import pythoncom
            import win32com.client
        except ImportError:
            return False

        pythoncom.CoInitialize()
        try:
            try:
                word = win32com.client.GetActiveObject("Word.Application")
            except Exception:
                return False

            document = self._find_open_word_document(word, path)
            if document is None:
                return False

            document.Activate()
            self._append_sections_to_word_document(document, sections)
            document.Save()
            return True
        finally:
            pythoncom.CoUninitialize()

    def _find_open_word_document(self, word, path):
        target_path = self._normalized_path(path)
        for document in word.Documents:
            try:
                if self._normalized_path(document.FullName) == target_path:
                    return document
            except Exception:
                pass
        return None

    def _normalized_path(self, path):
        return os.path.normcase(os.path.abspath(str(path)))

    def _append_sections_to_word_document(self, document, sections):
        if self._word_document_has_text(document):
            self._trim_word_trailing_empty_paragraphs(document)
            self._append_word_paragraph(document, "")
            self._append_word_paragraph(document, "")

        for tag, text in sections:
            size = DESCRIPTION_FONT_SIZE if tag == "description" else DEFAULT_FONT_SIZE
            if not text:
                self._append_word_paragraph(document, "")
                continue

            for line in text.split("\n"):
                self._append_word_paragraph(document, line, tag=tag, size=size)

    def _append_word_paragraph(self, document, text, tag="default", size=DEFAULT_FONT_SIZE):
        wd_style_normal = -1
        wd_style_heading_1 = -2
        end = max(0, document.Content.End - 1)
        start = end
        document.Range(end, end).InsertAfter(f"{text}\r")

        paragraph = document.Range(start, start + len(text) + 1).Paragraphs(1)
        if tag == "title":
            paragraph.Style = wd_style_heading_1
            return

        paragraph.Style = wd_style_normal
        paragraph.Range.Font.Name = "Segoe UI"
        paragraph.Range.Font.Size = size

    def _word_document_has_text(self, document):
        text = document.Content.Text.replace("\r", "").replace("\x07", "").strip()
        return bool(text)

    def _trim_word_trailing_empty_paragraphs(self, document):
        while document.Paragraphs.Count > 1:
            paragraph = document.Paragraphs(document.Paragraphs.Count)
            text = paragraph.Range.Text.replace("\r", "").replace("\x07", "").strip()
            if text:
                break
            paragraph.Range.Delete()

    def _docx_has_text(self, document):
        for paragraph in document.paragraphs:
            if paragraph.text.strip():
                return True

        for table in document.tables:
            for row in table.rows:
                for cell in row.cells:
                    if cell.text.strip():
                        return True

        return False

    def _trim_docx_trailing_empty_paragraphs(self, document):
        body = document._body._element
        children = list(body)
        index = len(children) - 1

        if index >= 0 and children[index].tag.endswith("}sectPr"):
            index -= 1

        while index >= 0:
            element = children[index]
            if not element.tag.endswith("}p") or self._docx_paragraph_has_content(element):
                break

            body.remove(element)
            index -= 1

    def _docx_paragraph_has_content(self, paragraph_element):
        text = "".join(
            element.text or ""
            for element in paragraph_element.iter()
            if element.tag.endswith("}t")
        )
        if text.strip():
            return True

        content_tags = ("}drawing", "}pict", "}object", "}fldSimple")
        return any(
            element.tag.endswith(content_tags)
            for element in paragraph_element.iter()
        )

    def _remove_docx_paragraph(self, paragraph):
        element = paragraph._element
        element.getparent().remove(element)

    def _show_file_status(self, message, success):
        foreground = self.palette["success"] if success else self.palette["error"]
        self.file_status_label.configure(foreground=foreground)
        self.file_status.set(message)

    def _plain_text(self, sections):
        return "\n".join(text for _tag, text in sections)

    def _html_text(self, sections):
        lines = []
        for tag, text in sections:
            size = DESCRIPTION_FONT_SIZE if tag == "description" else DEFAULT_FONT_SIZE
            escaped = html.escape(text).replace("\n", "<br>") or "<br>"
            lines.append(
                f'<div style="font-family: Segoe UI, Arial, sans-serif; '
                f'font-size: {size}px; line-height: 1.35;">{escaped}</div>'
            )
        return "".join(lines)

    def _copy_html_to_clipboard(self, html_text, plain_text):
        if sys.platform.startswith("win"):
            self._copy_html_to_windows_clipboard(html_text, plain_text)
            return

        self.clipboard_clear()
        self.clipboard_append(plain_text)
        self.update_idletasks()

    def _copy_html_to_windows_clipboard(self, html_text, plain_text):
        import ctypes
        from ctypes import wintypes

        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32

        cf_unicode_text = 13
        cf_html = user32.RegisterClipboardFormatW("HTML Format")

        user32.OpenClipboard.argtypes = [wintypes.HWND]
        user32.OpenClipboard.restype = wintypes.BOOL
        user32.EmptyClipboard.argtypes = []
        user32.EmptyClipboard.restype = wintypes.BOOL
        user32.SetClipboardData.argtypes = [wintypes.UINT, wintypes.HANDLE]
        user32.SetClipboardData.restype = wintypes.HANDLE
        user32.CloseClipboard.argtypes = []
        user32.CloseClipboard.restype = wintypes.BOOL
        kernel32.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
        kernel32.GlobalAlloc.restype = wintypes.HGLOBAL
        kernel32.GlobalLock.argtypes = [wintypes.HGLOBAL]
        kernel32.GlobalLock.restype = wintypes.LPVOID
        kernel32.GlobalUnlock.argtypes = [wintypes.HGLOBAL]
        kernel32.GlobalUnlock.restype = wintypes.BOOL
        kernel32.GlobalFree.argtypes = [wintypes.HGLOBAL]
        kernel32.GlobalFree.restype = wintypes.HGLOBAL

        def set_clipboard_data(format_id, data):
            handle = kernel32.GlobalAlloc(0x0042, len(data))
            if not handle:
                raise OSError("GlobalAlloc nie przydzielił pamięci.")

            locked = kernel32.GlobalLock(handle)
            if not locked:
                kernel32.GlobalFree(handle)
                raise OSError("GlobalLock nie zablokował pamięci.")

            ctypes.memmove(locked, data, len(data))
            kernel32.GlobalUnlock(handle)

            if not user32.SetClipboardData(format_id, handle):
                kernel32.GlobalFree(handle)
                raise OSError("SetClipboardData nie zapisał danych.")

        fragment = html_text
        clipboard_html = self._make_cf_html(fragment)
        unicode_text = plain_text.encode("utf-16le") + b"\x00\x00"

        if not user32.OpenClipboard(None):
            raise OSError("Schowek jest aktualnie niedostępny.")

        try:
            if not user32.EmptyClipboard():
                raise OSError("Nie udało się wyczyścić schowka.")
            set_clipboard_data(cf_unicode_text, unicode_text)
            set_clipboard_data(cf_html, clipboard_html)
        finally:
            user32.CloseClipboard()

    def _make_cf_html(self, fragment):
        start_fragment = "<!--StartFragment-->"
        end_fragment = "<!--EndFragment-->"
        html_payload = (
            "<html><body>"
            + start_fragment
            + fragment
            + end_fragment
            + "</body></html>"
        )

        header_template = (
            "Version:0.9\r\n"
            "StartHTML:{start_html:010d}\r\n"
            "EndHTML:{end_html:010d}\r\n"
            "StartFragment:{start_fragment:010d}\r\n"
            "EndFragment:{end_fragment:010d}\r\n"
        )
        placeholder = header_template.format(
            start_html=0,
            end_html=0,
            start_fragment=0,
            end_fragment=0,
        )

        start_html_offset = len(placeholder.encode("utf-8"))
        start_index = html_payload.index(start_fragment) + len(start_fragment)
        end_index = html_payload.index(end_fragment)
        start_fragment_offset = start_html_offset + len(html_payload[:start_index].encode("utf-8"))
        end_fragment_offset = start_html_offset + len(html_payload[:end_index].encode("utf-8"))
        html_bytes = html_payload.encode("utf-8")
        end_html_offset = start_html_offset + len(html_bytes)

        header = header_template.format(
            start_html=start_html_offset,
            end_html=end_html_offset,
            start_fragment=start_fragment_offset,
            end_fragment=end_fragment_offset,
        )
        return header.encode("utf-8") + html_bytes + b"\x00"


if __name__ == "__main__":
    app = ScribblesoApp()
    app.mainloop()
