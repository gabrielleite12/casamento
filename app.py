from flask import Flask, request, render_template
from werkzeug.utils import secure_filename
import io
import os

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

app = Flask(__name__)

# Configurações
SERVICE_ACCOUNT_FILE = 'credenciais.json'  # arquivo da conta de serviço
PASTA_ID = '1mfSWCfboJH2kNVAZGLBz8OHSbSd-DOwD'      # ID da pasta no Google Drive

# Credenciais da API
credenciais = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE,
    scopes=["https://www.googleapis.com/auth/drive.file"]
)
drive_service = build('drive', 'v3', credentials=credenciais)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload():
    if 'imagem' not in request.files:
        return "Nenhum arquivo enviado", 400

    imagem = request.files['imagem']
    if imagem.filename == '':
        return "Nome do arquivo vazio", 400

    filename = secure_filename(imagem.filename)

    file_metadata = {
        'name': filename,
        'parents': [PASTA_ID]
    }
    media = MediaIoBaseUpload(io.BytesIO(imagem.read()), mimetype='image/jpeg')

    drive_service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id'
    ).execute()

    return "Imagem enviada com sucesso!"


if __name__ == '__main__':
    app.run(debug=True)
