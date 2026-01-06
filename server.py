from flask import Flask, request, send_file
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from PIL import Image
import io

app = Flask(__name__)

@app.route("/sign-pdf", methods=["POST"])
def sign_pdf():
    pdf_file = request.files["pdf"]
    signature_file = request.files["signature"]

    page_number = int(request.form.get("page", 1)) - 1
    x = float(request.form.get("x", 350))
    y = float(request.form.get("y", 80))

    reader = PdfReader(pdf_file)
    writer = PdfWriter()

    # Convertir FileStorage en BytesIO pour reportlab
    sig_bytes = signature_file.read()
    sig_buffer = io.BytesIO(sig_bytes)
    signature_img = Image.open(sig_buffer).convert("RGBA")

    for i, page in enumerate(reader.pages):
        if i == page_number:
            packet = io.BytesIO()
            page_width = float(page.mediabox.width)
            page_height = float(page.mediabox.height)

            c = canvas.Canvas(packet, pagesize=(page_width, page_height))
            # Attention : drawImage attend un chemin ou un BytesIO
            c.drawImage(sig_buffer, x, y, width=signature_img.width, height=signature_img.height, mask="auto")
            c.save()
            packet.seek(0)

            overlay = PdfReader(packet).pages[0]
            page.merge_page(overlay)

        writer.add_page(page)

    output = io.BytesIO()
    writer.write(output)
    output.seek(0)

    return send_file(output, mimetype="application/pdf", download_name="signed.pdf")
