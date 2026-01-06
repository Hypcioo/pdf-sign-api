from flask import Flask, request, send_file
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from PIL import Image
import io

app = Flask(__name__)

@app.route("/sign-pdf", methods=["POST"])
def sign_pdf():
    try:
        # Récupérer les fichiers
        pdf_file = request.files["pdf"]
        signature_file = request.files["signature"]

        # Paramètres optionnels
        page_number = int(request.form.get("page", 1)) - 1
        x = float(request.form.get("x", 350))
        y = float(request.form.get("y", 80))
        scale = float(request.form.get("scale", 1.0))  # optionnel, pour réduire la signature

        # Charger le PDF
        reader = PdfReader(pdf_file)
        writer = PdfWriter()

        # Convertir la signature en image et buffer pour reportlab
        sig_bytes = signature_file.read()
        sig_buffer = io.BytesIO(sig_bytes)
        signature_img = Image.open(sig_buffer).convert("RGBA")
        sig_width, sig_height = signature_img.size
        sig_width *= scale
        sig_height *= scale

        for i, page in enumerate(reader.pages):
            # Copier la page dans le writer
            writer.add_page(page)

            # Si c'est la page à signer
            if i == page_number:
                # Créer un buffer PDF pour la signature
                packet = io.BytesIO()
                page_width = float(page.mediabox.width)
                page_height = float(page.mediabox.height)

                c = canvas.Canvas(packet, pagesize=(page_width, page_height))
                # drawImage accepte maintenant BytesIO
                c.drawImage(sig_buffer, x, y, width=sig_width, height=sig_height, mask="auto")
                c.save()
                packet.seek(0)

                overlay_page = PdfReader(packet).pages[0]
                page.merge_page(overlay_page)

        # Sortie finale
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
