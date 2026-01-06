from flask import Flask, request, send_file
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from PIL import Image
import io

app = Flask(__name__)

@app.route("/sign-pdf", methods=["POST"])
def sign_pdf():
    try:
        # Récupérer les fichiers envoyés
        pdf_file = request.files["pdf"]
        signature_file = request.files["signature"]

        # Paramètres
        page_number = int(request.form.get("page", 1)) - 1  # page à signer
        x = float(request.form.get("x", 350))               # position x
        y = float(request.form.get("y", 80))                # position y
        scale = float(request.form.get("scale", 1.0))       # échelle de la signature

        # Lire le PDF
        reader = PdfReader(pdf_file)
        writer = PdfWriter()

        # Préparer l'image signature
        sig_bytes = signature_file.read()
        sig_buffer = io.BytesIO(sig_bytes)
        pil_img = Image.open(sig_buffer).convert("RGBA")
        sig_width, sig_height = pil_img.size
        sig_width *= scale
        sig_height *= scale

        img_reader = ImageReader(sig_buffer)  # conversion compatible ReportLab

        # Parcourir les pages du PDF
        for i, page in enumerate(reader.pages):
            writer.add_page(page)

            # Si c'est la page à signer
            if i == page_number:
                packet = io.BytesIO()
                page_width = float(page.mediabox.width)
                page_height = float(page.mediabox.height)

                c = canvas.Canvas(packet, pagesize=(page_width, page_height))
                c.drawImage(img_reader, x, y, width=sig_width, height=sig_height, mask="auto")
                c.save()
                packet.seek(0)

                overlay_page = PdfReader(packet).pages[0]
                page.merge_page(overlay_page)

        # Préparer le PDF final
        output = io.BytesIO()
        writer.write(output)
        output.seek(0)

        return send_file(
            output,
            mimetype="application/pdf",
            download_name="signed.pdf"
        )

    except Exception as e:
        return f"Error: {str(e)}", 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
