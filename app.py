from flask import Flask, render_template, request, redirect, flash, session
import base64
from datetime import datetime
import os
import requests
import dropbox
from werkzeug.utils import secure_filename
from io import BytesIO
import json

# Variáveis de ambiente ou diretamente no código (RECOMENDADO: use env no Render)
APP_KEY = "62a0x76y9e50nk2"
APP_SECRET = "4qshc24vqj8x0xq"
REDIRECT_URI = "http://127.0.0.1:5000/oauth_callback"  # Troque pelo domínio do Render depois

app = Flask(__name__)
app.secret_key = "segredo_seguro"
app.config['UPLOAD_FOLDER'] = "static/uploads"
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Salva refresh_token permanentemente (aqui só para exemplo; prefira salvar em banco/variável segura)
REFRESH_TOKEN_PATH = "refresh_token.txt"

def get_dropbox_access_token():
    """Troca refresh_token por access_token válido."""
    if not os.path.exists(REFRESH_TOKEN_PATH):
        raise Exception("Refresh token não encontrado. Acesse /auth primeiro.")

    with open(REFRESH_TOKEN_PATH) as f:
        refresh_token = f.read().strip()

    response = requests.post("https://api.dropbox.com/oauth2/token", data={
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": APP_KEY,
        "client_secret": APP_SECRET,
    })

    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        raise Exception(f"Erro ao renovar token: {response.text}")

def get_dropbox_client():
    access_token = get_dropbox_access_token()
    return dropbox.Dropbox(access_token)

@app.route("/auth")
def auth():
    """Inicia autenticação Dropbox."""
    auth_url = f"https://www.dropbox.com/oauth2/authorize?client_id={APP_KEY}&response_type=code&redirect_uri={REDIRECT_URI}&token_access_type=offline"
    return redirect(auth_url)

@app.route("/oauth_callback")
def oauth_callback():
    """Recebe código do Dropbox e troca por refresh_token."""
    code = request.args.get("code")
    if not code:
        return "Erro: Código não fornecido"

    response = requests.post("https://api.dropbox.com/oauth2/token", data={
        "code": code,
        "grant_type": "authorization_code",
        "client_id": APP_KEY,
        "client_secret": APP_SECRET,
        "redirect_uri": REDIRECT_URI
    })

    if response.status_code == 200:
        data = response.json()
        refresh_token = data.get("refresh_token")
        with open(REFRESH_TOKEN_PATH, "w") as f:
            f.write(refresh_token)

        # Exibe mensagem com redirecionamento e GIF
        return """
        <html>
        <head>
            <meta charset="utf-8">
            <title>Autorizado!</title>
            <script>
                setTimeout(function() {
                    window.location.href = "/";
                }, 5000); // 5 segundos
            </script>
        </head>
        <body style="font-family: sans-serif; text-align: center; padding: 40px;">
            <h2>✅ Autorizado com sucesso!</h2>
            <p>Você será redirecionado automaticamente para o sistema principal em alguns segundos...</p>
            <img src="/static/loading.gif" alt="Carregando..." style="margin-top:20px; width:450px; height:auto;">
        </body>
        </html>
        """
    else:
        return f"Erro ao autorizar: {response.text}"



@app.route("/", methods=["GET", "POST"])
def index():
    dbx = get_dropbox_client()

    if request.method == "POST":
        if 'imagem' in request.files and request.files['imagem'].filename != '':
            imagem = request.files['imagem']
            nome_arquivo = secure_filename(imagem.filename)
            caminho_dropbox = f"/uploads/{nome_arquivo}"
            dbx.files_upload(imagem.read(), caminho_dropbox)
            flash("Imagem enviada com sucesso!")
            return redirect("/")

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
    dbx = get_dropbox_client()
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




@app.route("/mensagem-texto", methods=["POST"])
def mensagem_texto():
    dbx = get_dropbox_client()
    dados = request.get_json()
    mensagem = dados.get("mensagem", "").strip()

    if not mensagem:
        return "Mensagem vazia", 400

    # Nome do arquivo no Dropbox
    nome = datetime.now().strftime("mensagem_%Y%m%d_%H%M%S.txt")
    caminho = f"/mensagens/{nome}"

    try:
        dbx.files_upload(mensagem.encode("utf-8"), caminho)
        return "Mensagem enviada", 200
    except Exception as e:
        return f"Erro ao salvar no Dropbox: {e}", 500


@app.route("/mensagem-audio", methods=["POST"])
def mensagem_audio():
    dbx = get_dropbox_client()

    if "audio" not in request.files:
        return "Nenhum áudio enviado", 400

    audio = request.files["audio"]
    nome = datetime.now().strftime("audio_%Y%m%d_%H%M%S.webm")
    caminho = f"/mensagens/{nome}"

    try:
        dbx.files_upload(audio.read(), caminho)
        return "Áudio enviado com sucesso", 200
    except Exception as e:
        return f"Erro ao salvar áudio: {e}", 500
@app.route("/cookies.html")
def cookies():
    return render_template("cookies.html")


if __name__ == "__main__":
    app.run(debug=True)
