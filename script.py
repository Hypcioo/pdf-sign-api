from flask import Flask, request, send_file
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from PIL import Image
import io
import os

app = Flask(__name__)

API_KEY = os.environ.get("API_KEY")

@app.route("/sign-pdf", methods=["POST"])
def sign_pdf():

    # Sécurité
    if API_KEY and request.headers.get("X-API-KEY") != API_KEY:
        return "Unauthorized", 401

    pdf_file = request.files["pdf"]
    signature_file = request.files["signature"]

    page_number = int(request.form.get("page", 1)) - 1
    x = float(request.form.get("x", 350))
    y = float(request.form.get("y", 80))
    scale = float(request.form.get("scale", 0.4))

    reader = PdfReader(pdf_file)
    writer = PdfWriter()

    signature_img = Image.open(signature_file).convert("RGBA")
    sig_width, sig_height = signature_img.size
    sig_width *= scale
    sig_height *= scale

    for i, page in enumerate(reader.pages):
        if i == page_number:
            packet = io.BytesIO()
            page_width = float(page.mediabox.width)
            page_height = float(page.mediabox.height)

            c = canvas.Canvas(packet, pagesize=(page_width, page_height))
            c.drawImage(
                signature_file,
                x,
                y,
                sig_width,
                sig_height,
                mask="auto"
            )
            c.save()
            packet.seek(0)

            overlay = PdfReader(packet).pages[0]
            page.merge_page(overlay)

        writer.add_page(page)

    output = io.BytesIO()
    writer.write(output)
    output.seek(0)

    return send_file(
        output,
        mimetype="application/pdf",
        download_name="signed.pdf"
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
