from flask import Flask, request, send_file
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import io
from PIL import Image

app = Flask(__name__)

@app.route("/sign-pdf", methods=["POST"])
def sign_pdf():
    try:
        # Récupérer les fichiers
        pdf_file = request.files["pdf"]
        signature_file = request.files["signature"]

        # Paramètres
        page_number = int(request.form.get("page", 1)) - 1
        x = float(request.form.get("x", 350))
        y = float(request.form.get("y", 80))
        scale = float(request.form.get("scale", 1.0))

        # Lire le PDF
        reader = PdfReader(pdf_file)
        writer = PdfWriter()

        # Préparer la signature
        sig_bytes = signature_file.read()
        sig_buffer = io.BytesIO(sig_bytes)
        pil_img = Image.open(io.BytesIO(sig_bytes))  # nouvelle instance pour ImageReader
        sig_width, sig_height = pil_img.size
        sig_width *= scale
        sig_height *= scale

        img_reader = ImageReader(io.BytesIO(sig_bytes))  # 🔹 ImageReader propre

        # Parcourir les pages
        for i, page in enumerate(reader.pages):
            # Copier la page dans le writer
            writer.add_page(page)

            # Ajouter la signature sur la page ciblée
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

        # PDF final
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
