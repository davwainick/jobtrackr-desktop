"""Reusable UI widgets for JobTrackr."""

from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Any, Callable, Optional


class FormField(ttk.Frame):
    """A labeled form field with optional required marker."""

    def __init__(
        self,
        parent: tk.Widget,
        label: str,
        required: bool = False,
        widget_type: str = "entry",
        values: Optional[list[str]] = None,
        height: int = 3,
        **kw: Any,
    ):
        super().__init__(parent, **kw)
        self.columnconfigure(0, weight=1)
        lbl_text = f"{label} *" if required else label
        ttk.Label(self, text=lbl_text, font=("", 9, "bold")).grid(
            row=0, column=0, sticky="w", pady=(0, 2)
        )

        if widget_type == "combo":
            self.var = tk.StringVar()
            self.widget = ttk.Combobox(
                self, textvariable=self.var, values=values or [], state="readonly", width=30
            )
        elif widget_type == "text":
            self.widget = tk.Text(self, height=height, width=40, wrap="word",
                                 font=("", 10), relief="solid", borderwidth=1)
            self.var = None
        elif widget_type == "check":
            self.var = tk.BooleanVar()
            self.widget = ttk.Checkbutton(self, text=label, variable=self.var)
        elif widget_type == "date":
            self.var = tk.StringVar()
            self.widget = ttk.Entry(self, textvariable=self.var, width=32)
            # Placeholder for date format
        else:
            self.var = tk.StringVar()
            self.widget = ttk.Entry(self, textvariable=self.var, width=32)

        if widget_type != "check":
            self.widget.grid(row=1, column=0, sticky="ew", pady=(0, 4))
        else:
            self.widget.grid(row=1, column=0, sticky="w", pady=(0, 4))

    def get(self) -> str:
        if isinstance(self.widget, tk.Text):
            return self.widget.get("1.0", "end-1c").strip()
        if self.var is not None:
            val = self.var.get()
            if isinstance(val, bool):
                return val  # type: ignore
            return str(val).strip()
        return ""

    def set(self, value: Any) -> None:
        if isinstance(self.widget, tk.Text):
            self.widget.delete("1.0", "end")
            self.widget.insert("1.0", str(value or ""))
        elif isinstance(self.var, tk.BooleanVar):
            self.widget.configure(state="normal")
            self.var.set(bool(value))
        elif self.var is not None:
            self.var.set(str(value or ""))

    def clear(self) -> None:
        self.set("")


class FormDialog(tk.Toplevel):
    """Base dialog for create/edit forms."""

    def __init__(
        self,
        parent: tk.Widget,
        title: str,
        width: int = 520,
        height: int = 600,
    ):
        super().__init__(parent)
        self.title(title)
        self.geometry(f"{width}x{height}")
        self.resizable(True, True)
        self.transient(parent)
        self.grab_set()

        # Scrollable content area
        container = ttk.Frame(self)
        container.pack(fill="both", expand=True)

        canvas = tk.Canvas(container, highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        self.scroll_frame = ttk.Frame(canvas)

        self.scroll_frame.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Bind mousewheel
        def _on_mousewheel(event: tk.Event) -> None:
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        self.bind("<Destroy>", lambda e: canvas.unbind_all("<MouseWheel>"))

        # Bottom buttons
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill="x", padx=15, pady=10)
        self.save_btn = ttk.Button(
            btn_frame, text="Save", style="primary.TButton", command=self._on_save
        )
        self.save_btn.pack(side="right", padx=(5, 0))
        ttk.Button(btn_frame, text="Cancel", command=self.destroy).pack(side="right")

        self.fields: dict[str, FormField] = {}
        self.result: Optional[dict[str, Any]] = None

    def add_field(
        self, key: str, label: str, required: bool = False,
        widget_type: str = "entry", values: Optional[list[str]] = None,
        height: int = 3,
    ) -> FormField:
        field = FormField(
            self.scroll_frame, label, required=required,
            widget_type=widget_type, values=values, height=height,
        )
        field.pack(fill="x", padx=15, pady=2)
        self.fields[key] = field
        return field

    def add_separator(self) -> None:
        ttk.Separator(self.scroll_frame).pack(fill="x", padx=15, pady=8)

    def get_data(self) -> dict[str, Any]:
        return {k: f.get() for k, f in self.fields.items()}

    def set_data(self, data: dict[str, Any]) -> None:
        for key, field in self.fields.items():
            if key in data:
                field.set(data[key])

    def _on_save(self) -> None:
        """Override in subclass or set a callback."""
        self.result = self.get_data()
        self.destroy()


class DataTableView(ttk.Frame):
    """Reusable sortable data table with search, filter, and selection."""

    def __init__(
        self,
        parent: tk.Widget,
        columns: list[tuple[str, str, int]],  # (key, header, width)
        on_select: Optional[Callable[[str], None]] = None,
        on_add: Optional[Callable[[], None]] = None,
        on_delete: Optional[Callable[[list[str]], None]] = None,
        on_export: Optional[Callable[[], None]] = None,
        status_options: Optional[list[str]] = None,
        title: str = "",
        subtitle: str = "",
        **kw: Any,
    ):
        super().__init__(parent, **kw)
        self.columns = columns
        self.on_select = on_select
        self.on_delete = on_delete
        self._all_data: list[dict[str, Any]] = []
        self._sort_col: str = ""
        self._sort_reverse: bool = False

        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        # Header
        header = ttk.Frame(self)
        header.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        header.columnconfigure(1, weight=1)

        title_frame = ttk.Frame(header)
        title_frame.grid(row=0, column=0, sticky="w")
        if title:
            ttk.Label(title_frame, text=title, font=("", 16, "bold")).pack(anchor="w")
        if subtitle:
            ttk.Label(title_frame, text=subtitle, foreground="gray").pack(anchor="w")

        btn_frame = ttk.Frame(header)
        btn_frame.grid(row=0, column=2, sticky="e")
        if on_export:
            ttk.Button(btn_frame, text="Export CSV", command=on_export).pack(side="left", padx=2)
        if on_add:
            ttk.Button(btn_frame, text="+ Add New", style="primary.TButton", command=on_add).pack(
                side="left", padx=2
            )

        # Toolbar
        toolbar = ttk.Frame(self)
        toolbar.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 5))

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._apply_filters())
        search_entry = ttk.Entry(toolbar, textvariable=self.search_var, width=30)
        search_entry.pack(side="left", padx=(0, 10))
        search_entry.insert(0, "")
        ttk.Label(toolbar, text="Search:", foreground="gray").pack(side="left", before=search_entry)

        if status_options:
            self.status_var = tk.StringVar(value="All")
            cb = ttk.Combobox(
                toolbar, textvariable=self.status_var,
                values=["All"] + status_options, state="readonly", width=18,
            )
            cb.pack(side="left", padx=(10, 0))
            cb.bind("<<ComboboxSelected>>", lambda _: self._apply_filters())
        else:
            self.status_var = None

        if on_delete:
            self.del_btn = ttk.Button(
                toolbar, text="Delete Selected", style="danger.TButton",
                command=self._do_delete, state="disabled",
            )
            self.del_btn.pack(side="right")
        else:
            self.del_btn = None

        # Treeview
        col_ids = [c[0] for c in columns]
        self.tree = ttk.Treeview(self, columns=col_ids, show="headings", selectmode="extended")

        for key, header_text, width in columns:
            self.tree.heading(key, text=header_text, command=lambda k=key: self._sort_by(k))
            self.tree.column(key, width=width, minwidth=60)

        self.tree.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0, 5))

        vsb = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        vsb.grid(row=2, column=1, sticky="ns", pady=(0, 5))
        self.tree.configure(yscrollcommand=vsb.set)

        hsb = ttk.Scrollbar(self, orient="horizontal", command=self.tree.xview)
        hsb.grid(row=3, column=0, sticky="ew", padx=10)
        self.tree.configure(xscrollcommand=hsb.set)

        self.tree.bind("<Double-1>", self._on_double_click)
        self.tree.bind("<<TreeviewSelect>>", self._on_selection_change)

        # Status bar
        self.status_label = ttk.Label(self, text="0 records", foreground="gray")
        self.status_label.grid(row=4, column=0, sticky="w", padx=12, pady=(2, 8))

    def load_data(self, data: list[dict[str, Any]], status_key: str = "") -> None:
        self._all_data = data
        self._status_key = status_key
        self._apply_filters()

    def _apply_filters(self) -> None:
        search = self.search_var.get().lower()
        status_filter = self.status_var.get() if self.status_var else "All"

        filtered = self._all_data
        if search:
            filtered = [
                row for row in filtered
                if any(search in str(v).lower() for v in row.values())
            ]
        if status_filter != "All" and self._status_key:
            filtered = [r for r in filtered if r.get(self._status_key) == status_filter]

        self._display(filtered)

    def _display(self, data: list[dict[str, Any]]) -> None:
        self.tree.delete(*self.tree.get_children())
        col_keys = [c[0] for c in self.columns]
        for row in data:
            values = []
            for k in col_keys:
                v = row.get(k)
                if v is None:
                    values.append("")
                elif isinstance(v, bool) or (isinstance(v, int) and k in (
                    "open_role", "warm_intro_available", "response_received", "follow_up_sent"
                )):
                    values.append("Yes" if v else "No")
                else:
                    values.append(str(v))
            self.tree.insert("", "end", iid=row["id"], values=values)
        self.status_label.config(text=f"{len(data)} record{'s' if len(data) != 1 else ''}")

    def _sort_by(self, col: str) -> None:
        if self._sort_col == col:
            self._sort_reverse = not self._sort_reverse
        else:
            self._sort_col = col
            self._sort_reverse = False
        self._all_data.sort(
            key=lambda r: str(r.get(col) or "").lower(), reverse=self._sort_reverse
        )
        self._apply_filters()

    def _on_double_click(self, event: tk.Event) -> None:
        sel = self.tree.selection()
        if sel and self.on_select:
            self.on_select(sel[0])

    def _on_selection_change(self, event: tk.Event) -> None:
        if self.del_btn:
            sel = self.tree.selection()
            self.del_btn.config(state="normal" if sel else "disabled")

    def _do_delete(self) -> None:
        sel = list(self.tree.selection())
        if not sel:
            return
        if not messagebox.askyesno(
            "Confirm Delete", f"Delete {len(sel)} selected record(s)?"
        ):
            return
        if self.on_delete:
            self.on_delete(sel)

    def get_selected_ids(self) -> list[str]:
        return list(self.tree.selection())


class DetailView(ttk.Frame):
    """A scrollable detail view with labeled field rows."""

    def __init__(self, parent: tk.Widget, **kw: Any):
        super().__init__(parent, **kw)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        # Top bar with back button
        self.top_bar = ttk.Frame(self)
        self.top_bar.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))

        self.back_btn = ttk.Button(self.top_bar, text="← Back")
        self.back_btn.pack(side="left")

        self.title_label = ttk.Label(self.top_bar, text="", font=("", 16, "bold"))
        self.title_label.pack(side="left", padx=10)

        self.edit_btn = ttk.Button(self.top_bar, text="Edit")
        self.edit_btn.pack(side="right", padx=2)
        self.delete_btn = ttk.Button(self.top_bar, text="Delete", style="danger.TButton")
        self.delete_btn.pack(side="right", padx=2)

        # Content area with scrollbar
        container = ttk.Frame(self)
        container.grid(row=1, column=0, sticky="nsew")
        container.columnconfigure(0, weight=1)
        container.rowconfigure(0, weight=1)

        canvas = tk.Canvas(container, highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        self.content = ttk.Frame(canvas)
        self.content.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.content, anchor="nw", tags="content_window")

        def _resize_content(event: tk.Event) -> None:
            canvas.itemconfig("content_window", width=event.width)

        canvas.bind("<Configure>", _resize_content)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        def _on_mousewheel(event: tk.Event) -> None:
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind_all("<MouseWheel>", _on_mousewheel)

    def clear_content(self) -> None:
        for w in self.content.winfo_children():
            w.destroy()

    def add_field_row(self, label: str, value: Any) -> None:
        frame = ttk.Frame(self.content)
        frame.pack(fill="x", padx=15, pady=3)
        ttk.Label(frame, text=label, font=("", 9, "bold"), foreground="gray", width=20, anchor="w").pack(
            side="left"
        )
        display = ""
        if value is None or value == "":
            display = "—"
        elif isinstance(value, bool) or (isinstance(value, int) and label.lower() in (
            "open role", "warm intro", "response received", "follow-up sent"
        )):
            display = "Yes" if value else "No"
        else:
            display = str(value)

        val_label = ttk.Label(frame, text=display, wraplength=350, justify="left")
        val_label.pack(side="left", fill="x", expand=True)

    def add_section_header(self, text: str) -> None:
        ttk.Label(self.content, text=text, font=("", 12, "bold")).pack(
            anchor="w", padx=15, pady=(12, 4)
        )
        ttk.Separator(self.content).pack(fill="x", padx=15, pady=(0, 4))

    def add_text_block(self, label: str, text: str) -> None:
        if not text:
            return
        frame = ttk.Frame(self.content)
        frame.pack(fill="x", padx=15, pady=3)
        ttk.Label(frame, text=label, font=("", 9, "bold"), foreground="gray").pack(anchor="w")
        ttk.Label(frame, text=text, wraplength=450, justify="left").pack(anchor="w", pady=(2, 0))
