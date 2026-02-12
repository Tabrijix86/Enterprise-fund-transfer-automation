import customtkinter as ctk
from tkinter import messagebox, ttk
from PIL import Image
from tkcalendar import Calendar
from tkinter import filedialog
from datetime import datetime
from decimal import Decimal, InvalidOperation
import csv
import re
import logging

logging.basicConfig(
    filename="transfers.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


# ---------------- APP THEME ---------------- #
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

APP_BG = "#F1F5F9"
CARD_BG = "#FFFFFF"
HEADER_BG = "#0F172A"
TEXT_DARK = "#0F172A"
TEXT_MUTED = "#64748B"
BORDER = "#E2E8F0"
GRIDLINE = "#E5E7EB"
ACCENT = "#2563EB"
WARNING = "#F59E09"

# ---------------- FONTS ---------------- #
FONT_TITLE = ("Open Sans", 22, "bold")
FONT_H1 = ("Open Sans", 14, "bold")
FONT_LABEL = ("Open Sans", 14)
FONT_BODY = ("Open Sans", 13)
# Preview fonts
PREVIEW_FONT = ("Open Sans", 16)
PREVIEW_HEADING_FONT = ("Open Sans", 16, "bold")
PREVIEW_ROW_HEIGHT = 44

# ---------------- DATA ---------------- #
entries_data = []

bank_account_map = {
    "SCB (02-01)": "X0002110915401",
    "SCB (01-02)": "X0001110915402",
    "SCB (01-01)": "X01110915401",
}


def get_bank_acc(display_name: str) -> str:
    if display_name not in bank_account_map:
        raise ValueError(f"Unmapped bank selection: {display_name}")
    return bank_account_map[display_name]


# ---------------- AMOUNT SPLIT LOGIC ---------------- #
MAX_PER_ROW = Decimal("10000000")


def parse_amount(text: str) -> Decimal:
    # cleaned = text.strip().replace(",", "")
    cleaned = re.sub(r"[^\d.]", "", text)
    amt = Decimal(cleaned)
    if amt <= 0:
        raise InvalidOperation
    return amt


def split_amount(total: Decimal, max_per_row: Decimal = MAX_PER_ROW):
    chunks = []
    remaining = total
    while remaining > 0:
        chunk = min(remaining, max_per_row)
        chunks.append(chunk)
        remaining -= chunk
    return chunks


def excel_number(d: Decimal):
    # return int(d) if d == d.to_integral_value() else float(d)
    return format(d, "f")


# ---------------- OPTION-MENU LIST STYLING (DROPDOWN) ---------------- #
def style_optionmenu_dropdown(opt: ctk.CTkOptionMenu):
    for attr in ("_dropdown_menu", "dropdown_menu"):
        dd = getattr(opt, attr, None)
        if dd is not None:
            try:
                dd.configure(
                    fg_color=CARD_BG,
                    text_color=TEXT_DARK,
                    hover_color="#EEF2FF",
                    font=FONT_BODY,
                    corner_radius=10,
                )
            except Exception:
                pass


# ---------------- DATE PICKER ---------------- #
class ModernDatePicker(ctk.CTkFrame):
    def __init__(self, master, initial_date=None, date_pattern="%d/%m/%Y", **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.date_pattern = date_pattern
        self._selected = initial_date or datetime.now()

        self.grid_columnconfigure(0, weight=1)

        self.entry = ctk.CTkEntry(
            self,
            height=42,
            font=FONT_BODY,
            border_color=BORDER,
            fg_color=CARD_BG,
            text_color=TEXT_DARK,
        )
        self.entry.grid(row=0, column=0, sticky="ew")

        self.btn = ctk.CTkButton(
            self,
            text="Pick",
            width=90,
            height=42,
            fg_color=ACCENT,
            hover_color="#1D4ED8",
            font=FONT_BODY,
            command=self.open,
        )
        self.btn.grid(row=0, column=1, padx=(10, 0))

        self.set_date(self._selected)

    def set_date(self, dt: datetime):
        self._selected = dt
        self.entry.delete(0, "end")
        self.entry.insert(0, dt.strftime(self.date_pattern))

    def get(self) -> str:
        return self.entry.get().strip()

    def open(self):
        top = ctk.CTkToplevel(self)
        top.title("Payment Date")
        top.resizable(False, False)
        top.attributes("-topmost", True)

        try:
            top.update_idletasks()
            w, h = 380, 380
            x = top.winfo_screenwidth() // 2 - w // 2
            y = top.winfo_screenheight() // 2 - h // 2
            top.geometry(f"{w}x{h}+{x}+{y}")
        except Exception:
            top.geometry("380x380")

        wrap = ctk.CTkFrame(top, fg_color=CARD_BG, corner_radius=16)
        wrap.pack(fill="both", expand=True, padx=16, pady=16)

        ctk.CTkLabel(
            wrap, text="Select Payment Date", font=FONT_H1, text_color=TEXT_DARK
        ).pack(anchor="w", padx=12, pady=(12, 8))

        cal = Calendar(
            wrap,
            selectmode="day",
            year=self._selected.year,
            month=self._selected.month,
            day=self._selected.day,
            date_pattern="dd/mm/yyyy",
            font=("Segoe UI", 14),
            background=CARD_BG,
            foreground=TEXT_DARK,
            bordercolor=BORDER,
            headersbackground="#FFFFFF",
            headersforeground=TEXT_DARK,
            selectbackground=ACCENT,
            selectforeground="white",
            normalbackground=CARD_BG,
            normalforeground=TEXT_DARK,
            weekendbackground=CARD_BG,
            weekendforeground=TEXT_DARK,
            othermonthbackground=CARD_BG,
            othermonthforeground=TEXT_MUTED,
            disabledbackground=CARD_BG,
            disabledforeground="#B3B4B5",
        )
        cal.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        btn_row = ctk.CTkFrame(wrap, fg_color="transparent")
        btn_row.pack(fill="x", padx=12, pady=(0, 12))

        def on_apply():
            picked = cal.get_date()
            try:
                dt = datetime.strptime(picked, "%d/%m/%Y")
                self.set_date(dt)
                top.destroy()
            except ValueError:
                messagebox.showerror("Error", "Invalid date selected.")

        ctk.CTkButton(
            btn_row,
            text="Cancel",
            height=40,
            fg_color="#E2E8F0",
            hover_color="#CBD5E1",
            text_color=TEXT_DARK,
            font=FONT_BODY,
            command=top.destroy,
        ).pack(side="right")

        ctk.CTkButton(
            btn_row,
            text="Apply",
            height=40,
            fg_color=ACCENT,
            hover_color="#1D4ED8",
            font=FONT_BODY,
            command=on_apply,
        ).pack(side="right", padx=(0, 45))


# ---------------- FILENAME HELPERS ---------------- #
def bank_label_parts(label: str):
    # "SCB (02-01)" -> ("SCB", "02-01")
    # m = re.match(r"^\s*([A-Za-z0-9]+)\s*$$([^)]+)$$\s*$", label)
    m = re.match(r"^\s*([A-Za-z0-9]+)\s*\(([^)]+)\)\s*$", label)

    if m:
        return m.group(1).strip(), m.group(2).strip()
    return label.strip(), ""


def build_transfer_phrase(from_label: str, to_label: str) -> str:
    b1, c1 = bank_label_parts(from_label)
    b2, c2 = bank_label_parts(to_label)
    if b1 == b2 and c1 and c2:
        return f"{b1} {c1} to {c2}"
    if c1 and c2:
        return f"{b1} {c1} to {b2} {c2}"
    return f"{from_label} to {to_label}"


def safe_filename(name: str) -> str:
    name = re.sub(r'[<>:"/\\|?*]', "-", name)
    name = re.sub(r"\s+", " ", name).strip()
    return name


def build_csv_filename(
    custom_ref: str, debit_label: str, payee_label: str, pay_date_ddmmyyyy: str
) -> str:
    try:
        dt = datetime.strptime(pay_date_ddmmyyyy, "%d/%m/%Y")
        date_part = dt.strftime("%d.%m.%Y")
    except ValueError:
        date_part = pay_date_ddmmyyyy.replace("/", ".")
    prefix = f"{custom_ref}_BT"
    transfer_phrase = build_transfer_phrase(debit_label, payee_label)
    filename = f"{prefix} {transfer_phrase} - Fund Transfer -{date_part}.csv"
    return safe_filename(filename)


# ---------------- APP WINDOW ---------------- #
app = ctk.CTk()
app.title("Fund Transfer File Generator")
app.geometry("1150x700")
app.configure(fg_color=APP_BG)
app.grid_rowconfigure(2, weight=1)
app.grid_rowconfigure(3, weight=0)
app.grid_columnconfigure(0, weight=1)

# ---------------- HEADER ---------------- #
header = ctk.CTkFrame(app, height=60, corner_radius=0, fg_color=HEADER_BG)
header.grid(row=0, column=0, sticky="ew")
header.grid_columnconfigure(1, weight=1)

# Load icon image
icon_image = ctk.CTkImage(
    light_image=Image.open("ui_components\\transfer_icon.png"), size=(40, 40)  # adjust size if needed
)

# Icon label
icon_label = ctk.CTkLabel(header, image=icon_image, text="logo")
icon_label.grid(row=0, column=0, padx=(30, 10), pady=5)

# Title label
title = ctk.CTkLabel(header, text="FUND TRANSFERS", font=FONT_TITLE, text_color="white")
title.grid(row=0, column=1, sticky="w", pady=20)


# ---------------- MAIN AREA ---------------- #
main_frame = ctk.CTkFrame(app, fg_color="transparent")
main_frame.grid(row=1, column=0, sticky="nsew", padx=30, pady=20)
main_frame.grid_columnconfigure(0, weight=1)
main_frame.grid_columnconfigure(1, weight=2)
main_frame.grid_columnconfigure(2, weight=1)
main_frame.grid_rowconfigure(0, weight=1)

# Defaults for reset
DEFAULT_DATE = datetime.now()
DEBIT_VALUES = ["SCB (02-01)", "SCB (01-02)", "SCB (01-01)"]
PAYEE_VALUES = ["SCB (01-01)", "SCB (01-02)", "SCB (02-01)"]
REASON_VALUES = ["OTH/FT", "OTH/PULLING", "OTH/RETURN"]
EMAIL_VALUES = [
    "tabriji.islam@robi.com.bd",
]

DEFAULT_DEBIT = DEBIT_VALUES[0]
DEFAULT_PAYEE = PAYEE_VALUES[0]
DEFAULT_REASON = REASON_VALUES[0]
DEFAULT_EMAIL = EMAIL_VALUES[0]

# ============ LEFT CARD ============ #
left_card = ctk.CTkFrame(
    main_frame, corner_radius=20, fg_color=CARD_BG, border_width=1, border_color=BORDER
)
left_card.grid(row=0, column=0, sticky="nsew", padx=15, pady=10)

ctk.CTkLabel(
    left_card, text="Payment Details", font=FONT_H1, text_color=TEXT_DARK
).pack(anchor="w", padx=20, pady=(18, 6))
ctk.CTkLabel(
    left_card, text="Enter Payment Date", font=FONT_LABEL, text_color=TEXT_MUTED
).pack(anchor="w", padx=20, pady=(10, 6))

date_picker = ModernDatePicker(left_card, initial_date=DEFAULT_DATE)
date_picker.pack(fill="x", padx=20)

ctk.CTkLabel(
    left_card,
    text="Select Debit Bank Acc Number",
    font=FONT_LABEL,
    text_color=TEXT_MUTED,
).pack(anchor="w", padx=20, pady=(20, 6))
debit_dropdown = ctk.CTkOptionMenu(
    left_card,
    values=DEBIT_VALUES,
    height=42,
    fg_color="#E2E8F0",
    button_color=ACCENT,
    button_hover_color="#1D4ED8",
    text_color=TEXT_DARK,
)
debit_dropdown.pack(fill="x", padx=20)
debit_dropdown.set(DEFAULT_DEBIT)
style_optionmenu_dropdown(debit_dropdown)

ctk.CTkLabel(
    left_card,
    text="Select Payee Bank Acc Number",
    font=FONT_LABEL,
    text_color=TEXT_MUTED,
).pack(anchor="w", padx=20, pady=(18, 6))
payee_dropdown = ctk.CTkOptionMenu(
    left_card,
    values=PAYEE_VALUES,
    height=42,
    fg_color="#E2E8F0",
    button_color=ACCENT,
    button_hover_color="#1D4ED8",
    text_color=TEXT_DARK,
)
payee_dropdown.pack(fill="x", padx=20, pady=(0, 20))
payee_dropdown.set(DEFAULT_PAYEE)
style_optionmenu_dropdown(payee_dropdown)

# ============ CENTER CARD ============ #
center_card = ctk.CTkFrame(
    main_frame, corner_radius=20, fg_color=CARD_BG, border_width=1, border_color=BORDER
)
center_card.grid(row=0, column=1, sticky="nsew", padx=15, pady=10)
center_card.grid_columnconfigure((0, 1), weight=1)


def label(text, row, col):
    ctk.CTkLabel(center_card, text=text, font=FONT_LABEL, text_color=TEXT_MUTED).grid(
        row=row, column=col, padx=25, pady=(18, 6), sticky="w"
    )


ctk.CTkLabel(
    center_card, text="Transfer Info", font=FONT_H1, text_color=TEXT_DARK
).grid(row=0, column=0, columnspan=2, padx=25, pady=(18, 4), sticky="w")

label("Enter Customer Reference (GL)", 1, 0)
customer_ref = ctk.CTkEntry(
    center_card, height=42, font=FONT_BODY, border_color=BORDER, fg_color="#FFFFFF"
)
customer_ref.grid(row=2, column=0, padx=25, sticky="ew")

label("Total Amount (BDT)", 1, 1)
amount_entry = ctk.CTkEntry(
    center_card, height=42, font=FONT_BODY, border_color=BORDER, fg_color="#FFFFFF"
)
amount_entry.grid(row=2, column=1, padx=25, sticky="ew")

label("Reason", 3, 0)
reason_dropdown = ctk.CTkOptionMenu(
    center_card,
    values=REASON_VALUES,
    height=42,
    fg_color="#E2E8F0",
    button_color=ACCENT,
    button_hover_color="#1D4ED8",
    text_color=TEXT_DARK,
)
reason_dropdown.grid(row=4, column=0, padx=25, sticky="ew")
reason_dropdown.set(DEFAULT_REASON)
style_optionmenu_dropdown(reason_dropdown)

label("Payee Email", 3, 1)
email_dropdown = ctk.CTkOptionMenu(
    center_card,
    values=EMAIL_VALUES,
    height=42,
    fg_color="#E2E8F0",
    button_color=ACCENT,
    button_hover_color="#1D4ED8",
    text_color=TEXT_DARK,
)
email_dropdown.grid(row=4, column=1, padx=25, sticky="ew")
email_dropdown.set(DEFAULT_EMAIL)
style_optionmenu_dropdown(email_dropdown)

ctk.CTkLabel(
    center_card,
    text="Note: Amounts above 10,000,000 will be automatically split into multiple rows.",
    font=("Segoe UI", 12),
    text_color=TEXT_MUTED,
).grid(row=5, column=0, columnspan=2, padx=25, pady=(14, 18), sticky="w")

# ============ RIGHT CARD (ACTIONS) ============ #
right_card = ctk.CTkFrame(
    main_frame, corner_radius=20, fg_color=CARD_BG, border_width=1, border_color=BORDER
)
right_card.grid(row=0, column=2, sticky="nsew", padx=15, pady=10)

ctk.CTkLabel(right_card, text="Actions", font=FONT_H1, text_color=TEXT_DARK).pack(
    anchor="w", padx=20, pady=(18, 10)
)

# ---------------- PREVIEW SECTION ---------------- #
preview_frame = ctk.CTkFrame(app, fg_color="transparent")
preview_frame.grid(row=2, column=0, sticky="nsew", padx=30, pady=(0, 20))
preview_frame.grid_rowconfigure(0, weight=1)
preview_frame.grid_columnconfigure(0, weight=1)

preview_card = ctk.CTkFrame(
    preview_frame,
    corner_radius=20,
    fg_color=CARD_BG,
    border_width=1,
    border_color=BORDER,
)
preview_card.grid(row=0, column=0, sticky="nsew")
preview_card.grid_rowconfigure(1, weight=1)
preview_card.grid_columnconfigure(0, weight=1)

# Header bar inside preview card (Preview + total line items)
preview_header = ctk.CTkFrame(preview_card, fg_color="transparent")
preview_header.grid(row=0, column=0, sticky="ew", padx=16, pady=(12, 6))
preview_header.grid_columnconfigure(0, weight=1)

ctk.CTkLabel(preview_header, text="Preview", font=FONT_H1, text_color=TEXT_DARK).grid(
    row=0, column=0, sticky="w"
)

line_items_var = ctk.StringVar(value="Total line items: 0")
line_items_label = ctk.CTkLabel(
    preview_header, textvariable=line_items_var, font=FONT_BODY, text_color=TEXT_MUTED
)
line_items_label.grid(row=0, column=1, sticky="e")

tree_host = ctk.CTkFrame(preview_card, fg_color="transparent")
tree_host.grid(row=1, column=0, sticky="nsew", padx=14, pady=(0, 14))
tree_host.grid_rowconfigure(0, weight=1)
tree_host.grid_columnconfigure(0, weight=1)
tree_host.grid_columnconfigure(1, weight=0)

columns = [
    "Customer Reference (GL)",
    "Payee Name",
    "Payee Bank Acc No.",
    "Amount",
    "Reason",
    "Payment Date (dd-mm-yy)",
    "Debit Acc No.",
    "Payee Email Address",
]

# ttk styling
style = ttk.Style()
try:
    style.theme_use("clam")
except Exception:
    pass

# Fix common Treeview misalignment issues:
# - ensure heading + cell style consistent
# - set row height and fonts
# - keep a stable highlight thickness on some platforms
style.configure(
    "Modern.Treeview",
    font=PREVIEW_FONT,
    rowheight=PREVIEW_ROW_HEIGHT,
    background="#FFFFFF",
    fieldbackground="#FFFFFF",
    foreground=TEXT_DARK,
    bordercolor=GRIDLINE,
    borderwidth=1,
    relief="flat",
)
style.configure(
    "Modern.Treeview.Heading",
    font=PREVIEW_HEADING_FONT,
    background="#A8B7C9",
    foreground=TEXT_DARK,
    relief="flat",
)
style.map(
    "Modern.Treeview",
    background=[("selected", ACCENT)],
    foreground=[("selected", "#FFFFFF")],
)

tree = ttk.Treeview(
    tree_host, columns=columns, show="headings", style="Modern.Treeview"
)
tree.grid(row=0, column=0, sticky="nsew")

# scrollbars
scroll_y = ttk.Scrollbar(tree_host, orient="vertical", command=tree.yview)
scroll_x = ttk.Scrollbar(tree_host, orient="horizontal", command=tree.xview)
tree.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
scroll_y.grid(row=0, column=1, sticky="ns")
scroll_x.grid(row=1, column=0, sticky="ew")

# headings
for col in columns:
    tree.heading(col, text=col)

# Better alignment: auto-fit based on actual available width (minus scrollbar width)
COLUMN_WEIGHTS = [1.25, 1.35, 1.15, 0.85, 1.35, 1.25, 1.10, 1.60]
COLUMN_MIN_WIDTHS = [240, 260, 220, 160, 260, 260, 220, 320]


def autosize_columns(event=None):
    tree_host.update_idletasks()

    tree_width = tree.winfo_width()
    sbw = scroll_y.winfo_width() if scroll_y.winfo_ismapped() else 0

    available = tree_width - 2  # small padding
    if available <= 300:
        return

    total_weight = sum(COLUMN_WEIGHTS)
    widths = []
    for w, mw in zip(COLUMN_WEIGHTS, COLUMN_MIN_WIDTHS):
        cw = int((available * (w / total_weight)))
        widths.append(max(mw, cw))

    total = sum(widths)
    if total > available:
        scale = available / total
        scaled = []
        for base, mw in zip(widths, COLUMN_MIN_WIDTHS):
            scaled.append(max(mw, int(base * scale)))
        widths = scaled

    for col, width, mw in zip(columns, widths, COLUMN_MIN_WIDTHS):
        tree.column(col, width=width, minwidth=mw, anchor="w", stretch=True)


tree.bind("<Configure>", autosize_columns)
app.after(250, autosize_columns)

# zebra stripes
tree.tag_configure("odd", background="#FFFFFF")
tree.tag_configure("even", background="#E5EAEF")


# ---------------- FUNCTIONS ---------------- #
def update_line_items():
    line_items_var.set(f"Total line items: {len(entries_data)}")


# ---------------- STATUS BAR ---------------- #
status_var = ctk.StringVar(value="Status: Ready")

footer = ctk.CTkFrame(app, height=32, fg_color="#E2E8F0", corner_radius=0)
footer.grid(row=3, column=0, sticky="ew")
footer.grid_columnconfigure(0, weight=1)

status_label = ctk.CTkLabel(
    footer,
    textvariable=status_var,
    font=("Open Sans", 12),
    text_color=TEXT_DARK,
)
status_label.grid(row=0, column=0, sticky="w", padx=15)


def set_status(message):
    status_var.set(f"Status: {message}")


def build_rows_from_form():
    ref = customer_ref.get().strip()
    amt_text = amount_entry.get().strip()

    if not ref or not amt_text:
        messagebox.showerror("Error!", "Fill required fields.")
        return None

    try:
        total_amt = parse_amount(amt_text)
    except (InvalidOperation, ValueError):
        messagebox.showerror(
            "Error!", "Amount must be a positive number (commas allowed)."
        )
        return None

    try:
        debit_acc_no = get_bank_acc(debit_dropdown.get())
        payee_acc_no = get_bank_acc(payee_dropdown.get())
    except ValueError as e:
        messagebox.showerror("Error", str(e))
        return None

    if debit_dropdown.get() == payee_dropdown.get():
        messagebox.showerror("Error!", "Debit and Payee accounts cannot be the same.")
        return None

    pay_date = date_picker.get()
    if not pay_date:
        messagebox.showerror("Error!", "Please select a payment date.")
        return None

    chunks = split_amount(total_amt, MAX_PER_ROW)

    rows = []
    for chunk in chunks:
        rows.append(
            (
                ref,
                "Robi Axiata Limited",
                payee_acc_no,
                str(excel_number(chunk)),  # CSV-safe (no commas)
                reason_dropdown.get() + ref,
                pay_date,
                debit_acc_no,
                email_dropdown.get(),
            )
        )
    return rows


def load_preview(rows):
    tree.delete(*tree.get_children())
    for idx, row in enumerate(rows):
        tag = "even" if idx % 2 else "odd"
        tree.insert("", "end", values=row, tags=(tag,))
    autosize_columns()
    update_line_items()
    set_status("Preview Generated")


# def preview_file():
#     global entries_data
#     rows = build_rows_from_form()
#     if rows is None:
#         return
#     entries_data = rows
#     load_preview(rows)


def preview_file():
    global entries_data

    preview_btn.configure(state="disabled")
    app.update_idletasks()

    try:
        rows = build_rows_from_form()
        if rows is None:
            return

        entries_data = rows
        load_preview(rows)

        logging.info(
            f"PREVIEW | Ref={customer_ref.get().strip()} | " f"Rows={len(rows)}"
        )

    except Exception as e:
        logging.error(f"Preview failed: {str(e)}")
        messagebox.showerror("Error", "Unexpected error during preview.")

    finally:
        preview_btn.configure(state="normal")


def clear_preview():
    entries_data.clear()
    tree.delete(*tree.get_children())
    update_line_items()
    set_status("Preview Cleared")


def clear_selection():
    customer_ref.delete(0, "end")
    amount_entry.delete(0, "end")

    debit_dropdown.set(DEFAULT_DEBIT)
    payee_dropdown.set(DEFAULT_PAYEE)
    reason_dropdown.set(DEFAULT_REASON)
    email_dropdown.set(DEFAULT_EMAIL)

    date_picker.set_date(DEFAULT_DATE)
    clear_preview()
    set_status("Form Reset")


def download_file():
    if not entries_data:
        messagebox.showerror("Error", "Nothing to export. Click Preview File first.")
        return

    ref = customer_ref.get().strip()
    pay_date = date_picker.get()
    debit_label = debit_dropdown.get()
    payee_label = payee_dropdown.get()

    filename = build_csv_filename(ref, debit_label, payee_label, pay_date)
    # filepath = os.path.join(os.getcwd(), filename)
    filepath = filedialog.asksaveasfilename(
        defaultextension=".csv",
        initialfile=filename,
        filetypes=[("CSV files", "*.csv")],
    )

    # if not filepath:
    #     logging.info("User cancelled save dialog.")
    # return

    try:
        with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(columns)
            writer.writerows(entries_data)
        # logging.info(f"CSV created: {filepath}")

        logging.info(
            f"SUCCESS | Ref={ref} | Debit={debit_label} | "
            f"Payee={payee_label} | Rows={len(entries_data)} | File={filepath}"
        )

        messagebox.showinfo("Success", f"CSV saved:\n{filepath}")
        set_status("CSV Saved Successfully")

    except Exception as e:
        # logging.error(f"Failed to save CSV: {e}")

        logging.error(
            f"ERROR | Ref={ref} | Debit={debit_label} | "
            f"Payee={payee_label} | Reason={str(e)}"
        )

        messagebox.showerror("Error", f"Failed to save CSV:\n{e}")

    if not filepath:
        logging.info("User cancelled save dialog.")
    return


# ---------------- BUTTONS ---------------- #
preview_btn = ctk.CTkButton(
    right_card,
    text="Preview File",
    height=46,
    fg_color=WARNING,
    hover_color="#C66B03",
    font=FONT_BODY,
    text_color="#FFFFFF",
    command=preview_file,
)
preview_btn.pack(fill="x", padx=25, pady=(5, 10))

download_btn = ctk.CTkButton(
    right_card,
    text="Download CSV",
    height=46,
    fg_color=ACCENT,
    hover_color="#173CA2",
    text_color="#FFFFFF",
    font=FONT_BODY,
    command=download_file,
)
download_btn.pack(fill="x", padx=25, pady=10)

clear_btn = ctk.CTkButton(
    right_card,
    text="Clear Preview",
    height=40,
    fg_color="#E2E8F0",
    hover_color="#CBD5E1",
    text_color=TEXT_DARK,
    font=FONT_BODY,
    command=clear_preview,
)
clear_btn.pack(fill="x", padx=25, pady=(0, 10))

clear_sel_btn = ctk.CTkButton(
    right_card,
    text="Clear Selection",
    height=40,
    fg_color="#E2E8F0",
    hover_color="#CBD5E1",
    text_color=TEXT_DARK,
    font=FONT_BODY,
    command=clear_selection,
)
clear_sel_btn.pack(fill="x", padx=25, pady=(0, 10))

# init footer count
update_line_items()


def main():
    app.mainloop()


if __name__ == "__main__":
    main()
