"""
PDF filler — overlays user answers onto the uploaded PDF using VLM-provided
bounding boxes.

Implementation: create a per-page overlay with reportlab, then merge it onto the
original PDF using pypdf.
"""

from __future__ import annotations

import io
from pathlib import Path
from typing import Iterable

from pypdf import PdfReader, PdfWriter
from pypdf.generic import BooleanObject, NameObject
from reportlab.pdfgen import canvas

from models.session_state import SessionState

# Static mapping for FEMA 009-0-3 AcroForm field names → friendly keys we emit
# during VLM analysis. This keeps AcroForm filling aligned even when the PDF
# uses opaque internal names.
FEMA_FIELD_MAP = {
    "citizen_status": "CBP303[0].FEMAFormTemplate[0].CheckBox1[0]",
    "qualified_alien_status": "CBP303[0].FEMAFormTemplate[0].CheckBox1[1]",
    "parent_guardian_status": "CBP303[0].FEMAFormTemplate[0].CheckBox1[2]",
    "minor_child_details": "CBP303[0].FEMAFormTemplate[0].TextField1[0]",
    "name_print": "CBP303[0].FEMAFormTemplate[0].TextField1[1]",
    "date_of_birth": "CBP303[0].FEMAFormTemplate[0].DateTimeField1[0]",
    "address_of_damaged_property": "CBP303[0].FEMAFormTemplate[0].TextField1[2]",
    "city": "CBP303[0].FEMAFormTemplate[0].TextField1[9]",
    "state": "CBP303[0].FEMAFormTemplate[0].TextField1[6]",
    "zip_code": "CBP303[0].FEMAFormTemplate[0].TextField1[7]",
}


def _draw_overlays(
    base_reader: PdfReader,
    fields: Iterable[dict],
    answers: dict[str, str],
) -> list[bytes]:
    """Return a list of overlay PDF bytes, one per base PDF page."""
    overlays: list[bytes] = []
    # Pre-group fields by page for faster lookup
    fields_by_page: dict[int, list[dict]] = {}
    for f in fields:
        bbox = f.get("bounding_box") or {}
        page_num = int(bbox.get("page", 0)) if bbox else 0
        if page_num:
            fields_by_page.setdefault(page_num, []).append(f)

    for page_index, page in enumerate(base_reader.pages):
        page_num = page_index + 1
        width = float(page.mediabox.width)
        height = float(page.mediabox.height)

        packet = io.BytesIO()
        can = canvas.Canvas(packet, pagesize=(width, height))
        can.setFont("Helvetica", 10)

        for field in fields_by_page.get(page_num, []):
            bbox = field.get("bounding_box") or {}
            field_name = field.get("field_name")
            value = answers.get(field_name, "")
            if not value:
                continue

            x_norm = float(bbox.get("x_norm", 0))
            y_norm = float(bbox.get("y_norm", 0))
            w_norm = float(bbox.get("w_norm", 0))
            h_norm = float(bbox.get("h_norm", 0))

            # Convert normalised coords (top-left origin) to PDF coords (bottom-left origin)
            x_abs = x_norm * width
            y_top = y_norm * height
            y_abs = height - y_top - (h_norm * height * 0.25)  # nudge inside box

            # Clip within page bounds
            x_abs = max(0, min(width, x_abs))
            y_abs = max(0, min(height, y_abs))

            # Draw text; wrap long strings to fit bbox width
            max_width = max(10, w_norm * width)
            text_obj = can.beginText(x_abs, y_abs)
            text_obj.setFont("Helvetica", 10)
            for line in _wrap_text(value, max_width, can, font_size=10):
                text_obj.textLine(line)
            can.drawText(text_obj)

        can.save()
        packet.seek(0)
        overlays.append(packet.read())

    return overlays


def _wrap_text(text: str, max_width: float, can: canvas.Canvas, font_size: int) -> list[str]:
    """Simple word wrap using reportlab's stringWidth."""
    if not text:
        return [""]
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if can.stringWidth(candidate, "Helvetica", font_size) <= max_width or not current:
            current = candidate
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def list_acroform_field_names(pdf_path: Path) -> list[str]:
    """Return all AcroForm field names using PyMuPDF if available, else pypdf."""
    names: set[str] = set()
    try:
        import fitz  # type: ignore
        with fitz.open(str(pdf_path)) as doc:
            for page in doc:
                for widget in page.widgets() or []:
                    if widget.field_name:
                        names.add(widget.field_name)
    except Exception:
        pass

    if names:
        return sorted(names)

    try:
        reader = PdfReader(str(pdf_path))
        fields = reader.get_fields() or {}
        names.update(fields.keys())
    except Exception:
        pass

    return sorted(n for n in names if n)


def _has_acroform_fields(reader: PdfReader) -> bool:
    """Return True if the PDF has AcroForm fields to fill."""
    try:
        acroform = reader.trailer["/Root"].get("/AcroForm")
        fields = reader.get_fields()
        return bool(acroform and fields)
    except Exception:
        return False


def _fill_acroform(reader: PdfReader, answers: dict[str, str]) -> tuple[bytes, int, list[str]] | None:
    """
    Attempt to fill AcroForm fields using pypdf's native helper.

    Returns PDF bytes if successful; None if no fields matched or an error occurred.
    """
    try:
        writer = PdfWriter()
        writer.clone_document_from_reader(reader)

        # Mark appearances so values render in most PDF viewers
        if "/AcroForm" in writer._root_object:
            writer._root_object["/AcroForm"].update(
                {NameObject("/NeedAppearances"): BooleanObject(True)}
            )

        matched = 0
        fields = writer.get_fields() or {}
        available = sorted(fields.keys())

        # update_page_form_field_values works per page
        for page in writer.pages:
            page_fields = {}
            for fname in fields.keys():
                if fname in answers:
                    page_fields[fname] = answers[fname]
                    matched += 1
            if page_fields:
                writer.update_page_form_field_values(page, page_fields)

        if matched == 0:
            return None

        out = io.BytesIO()
        writer.write(out)
        out.seek(0)
        return out.read(), matched, available
    except Exception:
        return None


def _fill_acroform_fitz(pdf_path: Path, answers: dict[str, str]) -> tuple[bytes, int, list[str]] | None:
    """
    Try filling AcroForm fields using PyMuPDF (fitz) if available.
    This is the fastest and most reliable path for real form PDFs.
    """
    try:
        import fitz  # PyMuPDF
    except ImportError:
        return None

    try:
        doc = fitz.open(str(pdf_path))
    except Exception:
        return None

    try:
        matched = 0
        available: set[str] = set()
        for page in doc:
            widgets = page.widgets() or []
            for widget in widgets:
                fname = widget.field_name
                if not fname or fname not in answers:
                    if fname:
                        available.add(fname)
                    continue
                val = answers[fname]

                try:
                    if widget.field_type == fitz.PDF_WIDGET_TYPE_CHECKBOX:
                        truthy = str(val).strip().lower() in {"yes", "true", "1", "on", "x", "checked"}
                        widget.set_value(truthy)
                    else:
                        widget.set_value(str(val))
                    widget.update()
                    matched += 1
                except Exception:
                    continue

        if matched == 0:
            return None

        pdf_bytes = doc.tobytes(garbage=4, deflate=True)
        return pdf_bytes, matched, sorted(available)
    finally:
        doc.close()


def _map_answers_to_pdf_fields(answers: dict[str, str]) -> dict[str, str]:
    """Map friendly field keys to the PDF's internal AcroForm names when known."""
    mapped = {}
    for key, val in answers.items():
        pdf_key = FEMA_FIELD_MAP.get(key, key)
        mapped[pdf_key] = val
    return mapped


async def fill_pdf_with_answers(
    pdf_path: Path,
    fields: list[dict],
    answers: dict[str, str],
) -> bytes:
    """
    Fill an uploaded PDF. Preference order:
      1) PyMuPDF native AcroForm filling (fast, best fidelity)
      2) pypdf AcroForm filling
      3) Overlay text using normalized bounding boxes (only when no AcroForm)
    """
    # 1) PyMuPDF path (if installed and fields present)
    mapped_answers = _map_answers_to_pdf_fields(answers)

    fitz_result = _fill_acroform_fitz(pdf_path, mapped_answers)
    if fitz_result:
        pdf_bytes, matched, avail = fitz_result
        if matched == 0:
            raise ValueError(
                "AcroForm detected but none of your answers matched field names. "
                f"Available fields: {', '.join(avail[:40])}"
            )
        return pdf_bytes

    reader = PdfReader(str(pdf_path))

    # 2) pypdf AcroForm path
    if _has_acroform_fields(reader):
        pypdf_result = _fill_acroform(reader, mapped_answers)
        if pypdf_result:
            pdf_bytes, matched, avail = pypdf_result
            if matched == 0:
                raise ValueError(
                    "AcroForm detected but none of your answers matched field names. "
                    f"Available fields: {', '.join(avail[:40])}"
                )
            return pdf_bytes
        else:
            raise ValueError(
                "AcroForm detected but could not write values. "
                "Ensure answer keys match PDF field names."
            )

    # 3) Fallback overlay only when no AcroForm exists
    writer = PdfWriter()
    overlays = _draw_overlays(reader, fields, answers)

    for page_idx, page in enumerate(reader.pages):
        overlay_reader = PdfReader(io.BytesIO(overlays[page_idx]))
        overlay_page = overlay_reader.pages[0]
        page.merge_page(overlay_page)
        writer.add_page(page)

    out = io.BytesIO()
    writer.write(out)
    out.seek(0)
    return out.read()


# ── Legacy template stub (kept for session router) ──────
async def generate_pdf(session: SessionState) -> bytes:
    """Generate a placeholder text file for the legacy session flow."""
    lines = [
        "=" * 50,
        "  FEMA DISASTER AID FORM 009-0-3",
        "  (Generated by FormWhisper)",
        "=" * 50,
        "",
    ]

    for field_name, value in session.answers.items():
        label = field_name.replace("_", " ").title()
        lines.append(f"  {label}: {value}")

    content = "\n".join(lines)
    return content.encode("utf-8")
