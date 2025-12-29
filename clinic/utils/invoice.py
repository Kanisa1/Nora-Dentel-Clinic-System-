from django.template.loader import render_to_string
from weasyprint import HTML
import qrcode
from io import BytesIO
from django.core.files.base import ContentFile

def generate_invoice_pdf(invoice):
    # generate QR with receipt_number pointing to verification URL
    qr_img = qrcode.make(f"https://yourclinic.com/invoice/verify/{invoice.receipt_number}")
    qr_buf = BytesIO()
    qr_img.save(qr_buf, format='PNG')
    qr_data = qr_buf.getvalue()

    # render html
    html = render_to_string('invoices/template.html', {'invoice': invoice, 'clinic_info': {
        'name':'Nora Dental Clinic',
        'address':'KIGALI / GASABO',
        'email':'norhadentalclinic@gmail.com',
        'tel':'+250798287919'
    }})
    pdf_file = HTML(string=html).write_pdf()

    # attach files to invoice.pdf_file
    invoice.pdf_file.save(f"invoice_{invoice.id}.pdf", ContentFile(pdf_file))
    # could also save QR as separate file or embed it in html via data URI
    invoice.save()
