import os
from django.template.loader import render_to_string
from django.conf import settings
from django.core.files.base import ContentFile

def generate_invoice_pdf_weasy(invoice):
    from weasyprint import HTML
    logo_path = os.path.join(settings.BASE_DIR, 'assets', 'logo.png')
    html = render_to_string('invoices/invoice.html', {'invoice': invoice, 'logo_path': logo_path})
    pdf_bytes = HTML(string=html, base_url=str(settings.BASE_DIR)).write_pdf()
    invoice.pdf_file.save(f'invoice_{invoice.id}.pdf', ContentFile(pdf_bytes))
    invoice.save()
    return invoice.pdf_file.url

def generate_invoice_pdf_reportlab(invoice):
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from io import BytesIO
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    logo_path = os.path.join(settings.BASE_DIR, 'assets', 'logo.png')
    if os.path.exists(logo_path):
        try:
            c.drawImage(logo_path, 40, height - 110, width=120, preserveAspectRatio=True, mask='auto')
        except Exception:
            pass
    c.setFont('Helvetica-Bold', 14)
    c.drawString(170, height - 60, 'Nora Dental Clinic')
    c.setFont('Helvetica', 10)
    c.drawString(170, height - 75, 'KIGALI / GASABO')
    c.drawString(170, height - 90, 'Email: norhadentalclinic@gmail.com  Tel: +250798287919')
    c.setFont('Helvetica-Bold', 12)
    c.drawString(40, height - 140, f'Invoice #{invoice.id}')
    c.setFont('Helvetica', 10)
    c.drawString(40, height - 155, f'Patient: {invoice.visit.patient.first_name} {invoice.visit.patient.last_name}')
    c.drawString(300, height - 155, f'Date: {invoice.created_at.strftime("%Y-%m-%d %H:%M")}')
    y = height - 190
    c.setFont('Helvetica-Bold', 10)
    c.drawString(40, y, 'Act')
    c.drawString(300, y, 'Qty')
    c.drawString(340, y, 'Unit')
    c.drawString(420, y, 'Patient')
    c.drawString(500, y, 'Insurance')
    y -= 14
    c.setFont('Helvetica', 10)
    for it in invoice.visit.billing_items.all():
        c.drawString(40, y, it.tariff.name[:40])
        c.drawString(300, y, str(it.qty))
        c.drawString(340, y, f"{it.price_private_snapshot:.2f}")
        c.drawRightString(480, y, f"{(it.price_private_snapshot * it.qty):.2f}")
        c.drawRightString(560, y, f"{(it.price_insurance_snapshot or 0):.2f}")
        y -= 14
        if y < 80:
            c.showPage()
            y = height - 50
    y -= 14
    c.setFont('Helvetica-Bold', 10)
    c.drawRightString(480, y, f"Patient Total: {invoice.total_private:.2f}")
    y -= 14
    c.drawRightString(480, y, f"Insurance Total: {invoice.total_insurance:.2f}")
    c.line(40, 80, 220, 80)
    c.drawString(70, 64, 'Patient Signature')
    c.line(320, 80, 560, 80)
    c.drawString(360, 64, 'Doctor Signature')
    c.showPage()
    c.save()
    pdf = buffer.getvalue()
    buffer.close()
    invoice.pdf_file.save(f"invoice_{invoice.id}.pdf", ContentFile(pdf))
    invoice.save()
    return invoice.pdf_file.url

def generate_invoice_pdf(invoice):
    try:
        return generate_invoice_pdf_weasy(invoice)
    except Exception:
        return generate_invoice_pdf_reportlab(invoice)
