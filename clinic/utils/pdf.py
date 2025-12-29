import io
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.utils import ImageReader
import qrcode
import barcode
from barcode.writer import ImageWriter
from django.conf import settings
from django.core.files.storage import default_storage
from decimal import Decimal
from datetime import datetime

CLINIC_INFO = {
    'name': 'Nora Dental Clinic',
    'address': 'KIGALI / GASABO',
    'email': 'norhadentalclinic@gmail.com',
    'phone': '+250798287919',
}

def _make_qr(data: str):
    qr = qrcode.QRCode(box_size=4, border=1)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white").convert('RGB')
    return img

def _make_barcode(data: str):
    CODE39 = barcode.get_barcode_class('code39')
    bar = CODE39(data, writer=ImageWriter(), add_checksum=False)
    fp = io.BytesIO()
    bar.write(fp, {'module_height': 6.0, 'module_width': 0.3, 'font_size': 10})
    fp.seek(0)
    from PIL import Image
    return Image.open(fp)

def generate_invoice_pdf_bytes(invoice):
    """
    Returns PDF bytes for invoice (ReportLab). Adds logo, QR code (link or invoice id),
    barcode with receipt number, clinic info footer, signature lines.
    """
    buffer = io.BytesIO()
    # Use A4 landscape for a wider, premium look — change to A4 for portrait
    width, height = A4  # portrait
    c = canvas.Canvas(buffer, pagesize=A4)

    # Margins
    left_margin = 20 * mm
    right_margin = 20 * mm
    usable_width = width - left_margin - right_margin

    # Header: logo (if exists) and clinic name
    y = height - 20 * mm

    # Try to load logo from settings.MEDIA_ROOT or static
    logo_path = getattr(settings, 'CLINIC_LOGO_PATH', None)  # set in settings for convenience
    if logo_path:
        try:
            logo = ImageReader(logo_path)
            c.drawImage(logo, left_margin, y - 25*mm, width=40*mm, height=25*mm, preserveAspectRatio=True)
        except Exception:
            pass

    c.setFont("Helvetica-Bold", 16)
    c.drawString(left_margin + 45*mm, y - 5*mm, CLINIC_INFO['name'])

    # Invoice meta
    c.setFont("Helvetica", 10)
    c.drawRightString(width - right_margin, y, f"Invoice #{invoice.id}")
    c.drawRightString(width - right_margin, y - 12, f"Date: {invoice.created_at.strftime('%Y-%m-%d %H:%M')}")

    # Patient details box
    y -= 40*mm
    c.setStrokeColor(colors.grey)
    c.roundRect(left_margin, y, usable_width, 30*mm, 4*mm, stroke=1, fill=0)
    x = left_margin + 6*mm
    inner_y = y + 22*mm
    patient = invoice.visit.patient
    # Patient info
    c.setFont("Helvetica-Bold", 11)
    c.drawString(x, inner_y, f"Patient: {patient.first_name} {patient.last_name}")
    c.setFont("Helvetica", 10)
    c.drawString(x, inner_y - 12, f"Phone: {patient.phone or '-'}")
    c.drawString(x + 140, inner_y - 12, f"Age: {patient.age if patient.age is not None else '-'}")
    if patient.is_insured:
        c.drawString(x, inner_y - 24, f"Insurance: {patient.insurance} (Member #: {patient.membership_number or '-'})")
    else:
        c.drawString(x, inner_y - 24, "Insurance: None")

    # Table header for billing items
    y -= 36*mm
    table_x = left_margin
    c.setFont("Helvetica-Bold", 10)
    c.drawString(table_x + 2, y + 12, "Code")
    c.drawString(table_x + 80, y + 12, "Description")
    c.drawString(table_x + 300, y + 12, "Qty")
    c.drawRightString(width - right_margin - 120, y + 12, "Unit")
    c.drawRightString(width - right_margin - 40, y + 12, "Total")

    c.line(table_x, y + 8, width - right_margin, y + 8)

    # Billing lines
    y_line = y
    c.setFont("Helvetica", 10)
    for bi in invoice.visit.billing_items.select_related('tariff').all():
        y_line -= 14
        if y_line < 80*mm:  # simple page break handling
            c.showPage()
            y_line = height - 40*mm
        code = bi.tariff.code
        name = (bi.tariff.name[:40] + '...') if len(bi.tariff.name) > 40 else bi.tariff.name
        qty = bi.qty or 1
        unit = bi.price_private_snapshot or bi.tariff.price_private
        total = (Decimal(unit) * qty)
        c.drawString(table_x + 2, y_line, code)
        c.drawString(table_x + 80, y_line, name)
        c.drawString(table_x + 300, y_line, str(qty))
        c.drawRightString(width - right_margin - 120, y_line, f"{Decimal(unit):,.2f}")
        c.drawRightString(width - right_margin - 40, y_line, f"{total:,.2f}")

    # Totals block
    # compute totals again to be safe
    total_private = invoice.total_private or 0
    total_insurance = invoice.total_insurance or 0
    totals_y = y_line - 30
    c.setFont("Helvetica-Bold", 11)
    c.drawRightString(width - right_margin - 40, totals_y + 18, f"Subtotal: {total_private:,.2f}")
    c.drawRightString(width - right_margin - 40, totals_y, f"Insurance: {total_insurance:,.2f}")
    c.drawRightString(width - right_margin - 40, totals_y - 18, f"Total Due: {total_private - total_insurance:,.2f}")

    # QR code (invoice verification) and barcode (receipt number)
    qr_data = f"invoice:{invoice.id}"
    qr_img = _make_qr(qr_data)
    qr_buffer = io.BytesIO()
    qr_img.save(qr_buffer, format='PNG')
    qr_buffer.seek(0)
    c.drawImage(ImageReader(qr_buffer), left_margin, totals_y - 60, width=40*mm, height=40*mm)

    # barcode for receipt number (we encode invoice id)
    try:
        bar_img = _make_barcode(str(invoice.id))
        bar_buf = io.BytesIO()
        bar_img.save(bar_buf, format='PNG')
        bar_buf.seek(0)
        c.drawImage(ImageReader(bar_buf), left_margin + 50*mm, totals_y - 50, width=60*mm, height=20*mm)
    except Exception:
        pass

    # Signatures area (patient + doctor)
    sign_y = totals_y - 90
    c.setFont("Helvetica", 10)
    c.drawString(left_margin, sign_y, "Patient signature:")
    c.line(left_margin + 40*mm, sign_y, left_margin + 100*mm, sign_y)
    c.drawString(left_margin + 120*mm, sign_y, "Date:")
    c.line(left_margin + 133*mm, sign_y, left_margin + 180*mm, sign_y)

    c.drawString(left_margin, sign_y - 25, "Doctor signature:")
    c.line(left_margin + 40*mm, sign_y - 25, left_margin + 100*mm, sign_y - 25)
    c.drawString(left_margin + 120*mm, sign_y - 25, "Date:")
    c.line(left_margin + 133*mm, sign_y - 25, left_margin + 180*mm, sign_y - 25)

    # Footer with clinic info
    footer_y = 20 * mm
    c.setFont("Helvetica", 9)
    c.setFillColor(colors.grey)
    footer_text = f"{CLINIC_INFO['address']}   |   Email: {CLINIC_INFO['email']}   |   Tel: {CLINIC_INFO['phone']}"
    c.drawCentredString(width / 2, footer_y, footer_text)

    c.showPage()
    c.save()
    pdf = buffer.getvalue()
    buffer.close()
    return pdf
