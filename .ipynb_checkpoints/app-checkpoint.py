from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse, FileResponse
import subprocess
import whisper
import os
import uuid

app = FastAPI(
    title="FFmpeg + Whisper API",
    description="Serviço HTTP unificado para conversão e transcrição",
    version="1.0.0"
)

# === CONFIGURAÇÕES ===
UPLOAD_DIR = "/workspace/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# === CARREGA O MODELO WHISPER ===
print("🔊 Carregando modelo Whisper (base)...")
model = whisper.load_model("base")

# ========================
# 🧠 ENDPOINT: /whisper
# ========================
@app.post("/whisper")
async def transcribe_audio(file: UploadFile = File(...)):
    """
    Recebe um arquivo de áudio/vídeo e retorna a transcrição em texto.
    """
    try:
        input_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}_{file.filename}")
        with open(input_path, "wb") as f:
            f.write(await file.read())

        result = model.transcribe(input_path)
        os.remove(input_path)

        return JSONResponse({
            "text": result["text"],
            "language": result["language"]
        })

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


# ========================
# 🎬 ENDPOINT: /ffmpeg
# ========================
@app.post("/ffmpeg")
async def convert_media(
    file: UploadFile = File(...),
    output_format: str = Form("mp3")
):
    """
    Converte um arquivo de mídia (áudio ou vídeo) usando FFmpeg.
    Exemplo de uso:
    POST /ffmpeg com 'file=@video.mp4' e 'output_format=wav'
    """
    try:
        input_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}_{file.filename}")
        output_path = f"{os.path.splitext(input_path)[0]}.{output_format}"

        with open(input_path, "wb") as f:
            f.write(await file.read())

        # Executa FFmpeg silenciosamente
        cmd = ["ffmpeg", "-y", "-i", input_path, output_path]
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        os.remove(input_path)
        return FileResponse(output_path, filename=os.path.basename(output_path))

    except subprocess.CalledProcessError as e:
        return JSONResponse({"error": f"Erro FFmpeg: {e.stderr.decode('utf-8')}"}, status_code=500)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

# ========================
#  ENDPOINT: /upload de arquivos
# ========================
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Recebe um arquivo via HTTP e salva em /workspace/uploads/
    """
    try:
        # Cria nome único pra evitar sobrescrita
        filename = f"{uuid.uuid4()}_{file.filename}"
        filepath = os.path.join(UPLOAD_DIR, filename)

        # Salva o conteúdo
        with open(filepath, "wb") as f:
            f.write(await file.read())

        return JSONResponse({
            "status": "success",
            "filename": file.filename,
            "saved_as": filename,
            "path": filepath
        })

    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)


# ========================
# ❤️ TESTE / HEALTHCHECK
# ========================
@app.get("/")
def healthcheck():
    return {
        "status": "ok",
        "message": "API FFmpeg + Whisper ativa 🚀",
        "routes": ["/ffmpeg", "/whisper"]
    }
