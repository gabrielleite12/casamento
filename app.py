
from flask import Flask, render_template, request, redirect, flash
import dropbox
import base64
from datetime import datetime
import os
from werkzeug.utils import secure_filename

# ✅ Token do Dropbox
DROPBOX_ACCESS_TOKEN = "sl.u.AF2-3mJ3LdIE2A2pnma008dzL0zbORdHPB2OxiNXeJ6lkwm3TJeZcuDQDYrxTeCBzuR5ROjwDFeAPnSMOsRJd8QYh-qGuIyt0RNCTrU1W9KdNbart1xbluVmaMLYW-fZNHxococh4WqpqSlPNrU9DylWFj8hZZmTWGOXkNkI1FO228wOcKq76I6i-3rpXbmtOVMBaUsQqanosbUTNxEXwHPZk68oJ09VETQKmeAZCfAEzpOqYGXrNcPg97Bp937ZRm6lKIdO2a4KiuGsVwrRWLKMdq1DVBhbQMXrMOxpRyw307YUWmaxhx1eGOgYjGlHZJYMhi7R36pVIK4QtItcYax4mwjG5UJtaUVXYnODgWy8XtFsWnmbiLKenqJJp87brUdcJpeu2AEA1RLggpG8uIbjClwWzfTsgp1dDOdvtnHjG9IMTWb1rWW8khtJeLeHvqRW0bijw6hyipWF57byQQfaf1e-yBcAQScW1aYdmslQfpf_Ub_m9j6cvrZL91hnHNv4Ld6Njak6IXlj_AAGmI7HTOQkokzF74KBiw4K7alikG25MS7pZkJy3FWBRXojYYVMraWqy-Mqej1azNiJG9nFlW6HPr4RYuD32pLci4peoNYyr0Zzsl_42yQXWU4qF2EdhL7TFIyIxGS2SmHQ7dKoHB72e8pPyZvWR3fM5bA-arTeiK4jBqYIUUNjvmCBWuya0Hql3KIEoybsVjAouTP5JlFakOskG8CBhKhIOCL_7L2GqBNRgPw26Npl3xBXt1mYKHwoMKHClK7olssgI14IVxNu-duA9mPOtsgNBd7bb6CYh77dVb8BcI2IntnEMAtoqqh32Q4EBVs9ONA89YuVYTc1r_J8MxAU3j7rrlvKcULmQ6P31Z2c5abzrphNpuuh5pz3ZpxvtEuVf4dGdNM3WKN2aEOxTRxh5wT1KJF5O5BdMjrtONNe4O6OAUzeaGwqPpEoFSuWm7ZrexcBYn2Uyakv8n6vDupbStEt7wMC9n5YI88FkemYhf28dwcLq_DBQ49xy85b_RhSJaUu54dGJ4M1k8i3l24zrvnM2Ie_cIdUkV2-N5l1AkF5flXa7bpa7Tm0gq52N8jzOtlm5mPAo_sLkg3JTBjsxcl8orp3jsBo9tDSDrWdKjg6jtvebmprIh-g2b5CyNKnWoOp8ByqmcYnkhr0fPaTpYunsm8XkIDZ1jYeKGj12IFCw_o3MBiY2R8zrjAyTigKMUqaDLZckoC6dcaRZDkPAjDi1cjF2O2BK5Zq5G2npLTFYfCPa5DoH3dnVkw1Ozv0iqAqgpaBnyqEkORygbiaRQ9plHwN2w"
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

        # Upload vídeo via câmera (novo)
        if 'captured_video' in request.form:
            data_url = request.form['captured_video']
            if data_url.startswith("data:video"):
                header, encoded = data_url.split(",", 1)
                video_data = base64.b64decode(encoded)
                nome = datetime.now().strftime("video_%Y%m%d_%H%M%S.webm")
                caminho_dropbox = f"/uploads/{nome}"
                dbx.files_upload(video_data, caminho_dropbox)
                flash("Vídeo gravado e enviado com sucesso!")
                return redirect("/")

    return render_template("index.html")

@app.route('/album')
def album():
    folder_path = '/Uploads'  # raiz do app: /casamentomar
    fotos = []

    try:
        res = dbx.files_list_folder(folder_path)
        while True:
            for entry in res.entries:
                if isinstance(entry, dropbox.files.FileMetadata):
                    if entry.name.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                        temp_link = dbx.files_get_temporary_link(entry.path_lower).link
                        fotos.append(temp_link)
            if res.has_more:
                res = dbx.files_list_folder_continue(res.cursor)
            else:
                break
    except Exception as e:
        print("Erro ao acessar Dropbox:", e)

    return render_template('album.html', fotos=fotos)

if __name__ == "__main__":
    app.run(debug=True)
