"""
services/export_service.py - CSV, Excel, PDF export utilities
"""
from __future__ import annotations
import io
import pandas as pd
from datetime import datetime
from config import MONTH_NUM_TO_NAME


def _flatten_entries(entries: list[dict]) -> list[dict]:
    """Flatten nested profile data from joined queries."""
    flat = []
    for e in entries:
        row = dict(e)
        if "profiles" in row and isinstance(row["profiles"], dict):
            row["faculty_name"] = row["profiles"].get("full_name", "")
            row["faculty_email"] = row["profiles"].get("email", "")
            del row["profiles"]
        if row.get("month"):
            row["month_name"] = MONTH_NUM_TO_NAME.get(row["month"], str(row["month"]))
        flat.append(row)
    return flat


DISPLAY_COLUMNS = [
    "title", "research_type", "journal_or_patent_office",
    "indexing", "status", "authors",
    "submission_date", "month_name", "year", "academic_year",
    "department", "faculty_name", "doi", "patent_number",
    "funding_agency", "funding_amount", "notes", "document_url",
]


def entries_to_dataframe(entries: list[dict]) -> pd.DataFrame:
    if not entries:
        df = pd.DataFrame(columns=DISPLAY_COLUMNS)
    else:
        flat = _flatten_entries(entries)
        df = pd.DataFrame(flat)
        for c in DISPLAY_COLUMNS:
            if c not in df.columns:
                df[c] = None

    cols = [c for c in DISPLAY_COLUMNS if c in df.columns]
    df = df[cols].rename(columns={
        "title": "Title",
        "research_type": "Type",
        "journal_or_patent_office": "Journal / Patent Office",
        "indexing": "Indexing",
        "status": "Status",
        "authors": "Authors",
        "submission_date": "Date",
        "month_name": "Month",
        "year": "Year",
        "academic_year": "Academic Year",
        "department": "Department",
        "faculty_name": "Faculty Name",
        "doi": "DOI",
        "patent_number": "Patent No.",
        "funding_agency": "Funding Agency",
        "funding_amount": "Funding (₹)",
        "notes": "Abstract",
        "document_url": "Document",
    })
    
    # CRITICAL: Prevent Streamlit JSON serialization errors
    df = df.astype(object).where(pd.notnull(df), None)
    return df


def to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")


def to_excel_bytes(df: pd.DataFrame, sheet_name: str = "Research Data") -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)
        # Auto-fit column widths
        ws = writer.sheets[sheet_name]
        for col in ws.columns:
            max_len = max(len(str(cell.value or "")) for cell in col)
            ws.column_dimensions[col[0].column_letter].width = min(max_len + 4, 60)
    return output.getvalue()


def nba_report_dataframe(entries: list[dict], dept: str = None,
                          academic_year: str = None) -> pd.DataFrame:
    """Generate NBA-formatted report."""
    filtered = entries
    if dept:
        filtered = [e for e in filtered if e.get("department") == dept]
    if academic_year:
        filtered = [e for e in filtered if e.get("academic_year") == academic_year]

    df = entries_to_dataframe(filtered)
    return df


def to_pdf_bytes(df: pd.DataFrame, title: str = "Research Report",
                 institution: str = "HKBK College of Engineering",
                 filters_summary: str = "") -> bytes:
    """
    Generate a formatted PDF report from a DataFrame.
    Requires: fpdf2  (pip install fpdf2)
    Falls back gracefully if fpdf2 is not installed.
    """
    try:
        from fpdf import FPDF
    except ImportError:
        # Fallback: return a plain-text PDF stub so the download still works
        text = f"{title}\n{institution}\n{filters_summary}\n\n"
        text += df.to_string(index=False)
        return text.encode("utf-8")

    pdf = FPDF(orientation="L", unit="mm", format="A4")  # Landscape for wide tables
    pdf.set_auto_page_break(auto=True, margin=12)
    pdf.add_page()

    # ── Header ───────────────────────────────────────────
    pdf.set_font("Helvetica", "B", 16)
    pdf.set_fill_color(46, 134, 171)   # primary blue
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 12, institution, fill=True, ln=True, align="C")

    pdf.set_font("Helvetica", "B", 13)
    pdf.set_fill_color(30, 58, 95)
    pdf.cell(0, 9, title, fill=True, ln=True, align="C")

    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "", 9)
    generated_at = datetime.now().strftime("%d %b %Y, %I:%M %p")
    pdf.cell(0, 6, f"Generated: {generated_at}    |    Records: {len(df)}{('    |    Filters: ' + filters_summary) if filters_summary else ''}",
             ln=True, align="C")
    pdf.ln(4)

    if df.empty:
        pdf.set_font("Helvetica", "I", 11)
        pdf.cell(0, 10, "No records found for the selected filters.", ln=True, align="C")
        return bytes(pdf.output())

    # ── Table ────────────────────────────────────────────
    # Choose columns that fit landscape A4 (297mm usable ~ 277mm after margins)
    priority_cols = ["Title", "Type", "Status", "Year", "Department",
                     "Faculty Name", "Indexing", "Journal / Patent Office",
                     "DOI", "Authors"]
    cols = [c for c in priority_cols if c in df.columns]
    if not cols:
        cols = list(df.columns[:8])   # fallback: first 8 columns

    page_w = pdf.w - 2 * pdf.l_margin
    col_widths = _calc_col_widths(df[cols], page_w)

    # Header row
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_fill_color(46, 134, 171)
    pdf.set_text_color(255, 255, 255)
    for col, w in zip(cols, col_widths):
        pdf.cell(w, 7, col[:22], border=1, fill=True)
    pdf.ln()

    # Data rows — alternating row color
    pdf.set_font("Helvetica", "", 7)
    for i, (_, row) in enumerate(df[cols].iterrows()):
        if i % 2 == 0:
            pdf.set_fill_color(240, 248, 255)
        else:
            pdf.set_fill_color(255, 255, 255)
        pdf.set_text_color(0, 0, 0)
        # Check if adding this row would overflow the page
        if pdf.get_y() + 7 > pdf.page_break_trigger:
            pdf.add_page()
            pdf.set_font("Helvetica", "B", 8)
            pdf.set_fill_color(46, 134, 171)
            pdf.set_text_color(255, 255, 255)
            for col, w in zip(cols, col_widths):
                pdf.cell(w, 7, col[:22], border=1, fill=True)
            pdf.ln()
            pdf.set_font("Helvetica", "", 7)
            pdf.set_text_color(0, 0, 0)
        for col, w in zip(cols, col_widths):
            val = str(row[col]) if row[col] is not None else ""
            val = val.replace("—", "-").replace("‘", "'").replace("’", "'").replace('“', '"').replace('”', '"')
            val = val.encode("latin-1", "replace").decode("latin-1")
            val = val[:int(w / 1.8)]  # truncate to fit cell width
            pdf.cell(w, 6, val, border=1, fill=True)
        pdf.ln()

    # ── Footer ───────────────────────────────────────────
    pdf.set_y(-12)
    pdf.set_font("Helvetica", "I", 7)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 6, f"Research Information Collection Portal  -  {institution}  -  Page {pdf.page_no()}",
             align="C")

    return bytes(pdf.output())


def _calc_col_widths(df: pd.DataFrame, total_width: float) -> list[float]:
    """Distribute column widths proportionally based on content length."""
    weights = []
    for col in df.columns:
        max_content = max(
            len(str(col)),
            df[col].astype(str).str.len().max() if not df.empty else 0
        )
        weights.append(min(max_content, 30))  # cap at 30 chars
    total_w = sum(weights) or 1
    return [round(total_width * w / total_w, 1) for w in weights]
