
from flask import Flask, render_template, request, redirect, flash
import dropbox
import base64
from datetime import datetime
import os
from werkzeug.utils import secure_filename

# ✅ Token do Dropbox
DROPBOX_ACCESS_TOKEN = "sl.u.AF2G43AziD3mKTGmsno2vzorGVNnYEZDfAD3nenmUOovlqlhrqUvCqRhLBUfGjIyemeazOklYl_8Lv0It3Vi2V5LmJgs91CyRm9nSvSl7hZ-NWTNR8A-g1Nt5b8YLofUJcCWHL_7vy_S2WCeJDCseUgpOHpxgTxHIRdqA0kgYHl0QFI_MbahZ_O7Rdv4_r_qHgFf-BJoP4yom6d-JJFI9nXlgGal5a_1U3qurG06E0wnua5m2Bq3rvs_3Zne2mrOCoVdRAH24PnQWBp7IDR3pQX49Vm4XqtgOC8uevwTxzXqpUhE3PyYt8bEASTxZDXlzYR1xfFM2eZxRL0t0cNlGD6h7fQkiRLKAPGlED6axn8_AHEpvJZmuqK1El9SEWlBQJPkr23wZT9LstVwat6rtX5EzU1B8eRfV7VsxRsp_8ZG7FuoOz_UU0rs9I-7KOkcIXPfTdNw-HcRNngKszh7ozvlJ9rqs_0Qau2xrhbJOayFIMTYYp3CUWL9oEyBaBQ1WCgTvsCnfJfcv-GbSKUwTMg8QgZygWsRJpLgO87aPrXTg6nqNXg75Fqoy1wkvmt_UvgrTABtA0_0eJGW5y-VnpaiV0_jch-AQszq502_1OYwMonk97wb0jZGHqMcLXX2BYifU_dUVdpO1RuKBHqx0QAr12dAsc5bMs_XSfQm9lUn6nouB_0PTww4o0g4kFvXs6JN03Qt4DkzqaJG4MRhQKy3d278222QptnsJwn3NuUiR8Y6XfyAkTQEmJ1jf2rSC7SkJsPLZeyU9KP_ZC8OMttVliJDXYgo2FFRTKKqPTeBM2ALd7MTSCoNU_mALPB63yqinpUirWoCMi_9q1Xsz4MeYeYOWDvyrcT5m1LiSEL4QyHf4jMB9_e7yFE5hjvySEt7QGlNGIopeFZ5kbAt6SpcmuwqF99C3ZV-MzD-u19_l4TxZx3VWeolyZBkhLU_5yJ18zvtaI-PmmHJVnu3CLcPTEcQcjSpvIAEEcxbXRagXn8R1IWXWr1p0Gyx0XuB1hwThZ0N_OhbATMCDdlFoH60TsFywRUy4s9Q8koaY42EtdP2K9DAU_aSNQ4vCebrwVTGvhjB35sLqPvwFQM25Qz014SGvox4K9OubYMnO1DahBN5h3-fHrnFqc5SHcHe7omMUCal6g_aDcD591CZHMKeICeTRXBKeZ994C7UOE98Twc0XSUGMA14-lgx9XhJregffVxhgYrclhZCivjQArOkKdmik4Wh7Km8L_NX4cDFSI8w7fe-T4p5AxKSrjazLJIETOAMvuXKRUdgNqOIOO5ITt3R_FPzT8WpNjs8NXM13A"
dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)

app = Flask(__name__)
app.secret_key = "segredo_seguro"

# Pasta local (opcional)
app.config['UPLOAD_FOLDER'] = "static/uploads"
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        # Upload imagem tradicional
        if 'imagem' in request.files and request.files['imagem'].filename != '':
            imagem = request.files['imagem']
            nome_arquivo = secure_filename(imagem.filename)
            caminho_dropbox = f"/uploads/{nome_arquivo}"
            dbx.files_upload(imagem.read(), caminho_dropbox)
            flash("Imagem enviada com sucesso!")
            return redirect("/")

        # Upload foto via câmera
        if 'captured_image' in request.form:
            data_url = request.form['captured_image']
            if data_url.startswith("data:image"):
                header, encoded = data_url.split(",", 1)
                image_data = base64.b64decode(encoded)
                nome = datetime.now().strftime("foto_%Y%m%d_%H%M%S.jpg")
                caminho_dropbox = f"/uploads/{nome}"
                dbx.files_upload(image_data, caminho_dropbox)
                flash("Foto tirada e enviada com sucesso!")
                return redirect("/")

        # ✅ Upload vídeo via câmera (correto agora)
        if 'video_blob' in request.files:
            video = request.files['video_blob']
            nome = datetime.now().strftime("video_%Y%m%d_%H%M%S.webm")
            caminho_dropbox = f"/uploads/{nome}"
            dbx.files_upload(video.read(), caminho_dropbox)
            flash("Vídeo gravado e enviado com sucesso!")
            return redirect("/")

    return render_template("index.html")

@app.route('/album')
def album():
    folder_path = '/Uploads'
    arquivos = []

    try:
        res = dbx.files_list_folder(folder_path, recursive=False)
        while True:
            for entry in res.entries:
                if isinstance(entry, dropbox.files.FileMetadata):
                    nome = entry.name.lower()
                    if nome.endswith(('.jpg', '.jpeg', '.png', '.gif', '.webm', '.mp4')):
                        temp_link = dbx.files_get_temporary_link(entry.path_lower).link
                        tipo = 'imagem' if nome.endswith(('.jpg', '.jpeg', '.png', '.gif')) else 'video'
                        arquivos.append({'link': temp_link, 'tipo': tipo})
            if res.has_more:
                res = dbx.files_list_folder_continue(res.cursor)
            else:
                break
    except Exception as e:
        print("Erro ao acessar Dropbox:", e)

    return render_template('album.html', arquivos=arquivos)


if __name__ == "__main__":
    app.run(debug=True)
