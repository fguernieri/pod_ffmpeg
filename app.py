import os
os.environ["IMAGEIO_FFMPEG_EXE"] = "/usr/bin/ffmpeg"

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse, FileResponse
import subprocess
import whisper
from whisper.utils import get_writer
from moviepy.editor import *
import uuid, glob, random

app = FastAPI(
    title="FFmpeg + Whisper API",
    description="Serviço HTTP unificado para conversão, transcrição e geração de vídeos com Ken Burns",
    version="2.0.0"
)

# ======================
# ⚙️ CONFIGURAÇÕES GERAIS
# ======================
UPLOAD_DIR = "/workspace/uploads"
OUTPUT_DIR = "/workspace/output"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)


# ========================
# 🧠 ENDPOINT: /whisper
# ========================
@app.post("/whisper")
async def transcribe_audio(
    file: UploadFile = File(...),
    language: str = Form(None),
    model_name: str = Form("small"),
    output_format: str = Form("text")
):
    """
    Transcreve áudio com o modelo Whisper. Suporta formatos: text, srt, vtt, json.
    """
    try:
        input_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}_{file.filename}")
        with open(input_path, "wb") as f:
            f.write(await file.read())

        # Carrega modelo
        model = whisper.load_model(model_name)

        kwargs = {}
        if language:
            kwargs["language"] = language

        result = model.transcribe(input_path, **kwargs)

        # Writer oficial
        writer = get_writer(output_format, UPLOAD_DIR)
        writer(result, input_path)

        output_path = os.path.splitext(input_path)[0] + f".{output_format}"
        with open(output_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Limpeza
        os.remove(input_path)
        os.remove(output_path)

        return JSONResponse({
            "format": output_format,
            "language": result.get("language", language or "auto"),
            "content": content
        })

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


# ========================
# 🎬 ENDPOINT: /ffmpeg (conversão simples)
# ========================
@app.post("/ffmpeg")
async def convert_media(
    file: UploadFile = File(...),
    output_format: str = Form("mp3")
):
    """
    Converte qualquer arquivo de mídia usando FFmpeg.
    Exemplo: POST /ffmpeg com 'file=@video.mp4' e 'output_format=wav'
    """
    try:
        input_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}_{file.filename}")
        output_path = f"{os.path.splitext(input_path)[0]}.{output_format}"

        with open(input_path, "wb") as f:
            f.write(await file.read())

        cmd = ["ffmpeg", "-y", "-i", input_path, output_path]
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        os.remove(input_path)
        return FileResponse(output_path, filename=os.path.basename(output_path))

    except subprocess.CalledProcessError as e:
        return JSONResponse({"error": f"Erro FFmpeg: {e.stderr.decode('utf-8')}"}, status_code=500)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


# ========================
# 📤 ENDPOINT: /upload
# ========================
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Salva um arquivo em /workspace/uploads/
    """
    try:
        filename = f"{uuid.uuid4()}_{file.filename}"
        filepath = os.path.join(UPLOAD_DIR, filename)

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
# 🎞 ENDPOINT: /ffmpeg_ken (MoviePy + NVENC)
# ========================
def kenburns(img_path, duration=4, zoom_factor=1.3):
    """
    Aplica efeito Ken Burns (zoom/pan suave) com duração garantida.
    """
    clip = ImageClip(img_path).resize(height=1080).set_duration(duration)
    w, h = clip.size

    zoom = random.uniform(1.0, zoom_factor)
    start_x = random.uniform(0, w * (zoom - 1))
    start_y = random.uniform(0, h * (zoom - 1))

    return (
        clip.crop(x1=start_x, y1=start_y, x2=start_x + w / zoom, y2=start_y + h / zoom)
        .resize((1920, 1080))
        .fadein(1)
        .fadeout(1)
    )


@app.post("/ffmpeg_ken")
async def gerar_video_kenburns(
    audio_file: str = Form(...),
    image_pattern: str = Form(...),
    output_name: str = Form("video_final.mp4")
):
    """
    Gera vídeo com Ken Burns real (zoom/pan em cada imagem),
    sincronizado com o áudio e renderizado em GPU (NVENC).
    """
    try:
        audio_path = os.path.join(UPLOAD_DIR, audio_file)
        imagens_glob = os.path.join(UPLOAD_DIR, "imagens", image_pattern)
        output_path = os.path.join(OUTPUT_DIR, output_name)
        os.makedirs(OUTPUT_DIR, exist_ok=True)

        imagens = sorted(glob.glob(imagens_glob))
        if not imagens:
            return JSONResponse({"error": f"Nenhuma imagem encontrada em {imagens_glob}"}, status_code=400)

        # Garante que o áudio foi carregado corretamente
        if not os.path.exists(audio_path):
            return JSONResponse({"error": f"Arquivo de áudio não encontrado: {audio_path}"}, status_code=400)

        audio = AudioFileClip(audio_path)
        num_imagens = len(imagens)
        duracao_por_imagem = max(audio.duration / num_imagens, 0.1)  # evita duração zero

        clips = [kenburns(img, duration=duracao_por_imagem) for img in imagens if os.path.exists(img)]
        if not clips:
            return JSONResponse({"error": "Nenhum clipe válido gerado."}, status_code=500)

        # Define FPS fixo para todo o vídeo
        fps_final = 30

        video = concatenate_videoclips(clips, method="compose").set_duration(audio.duration).set_fps(fps_final)

        final = video.set_audio(audio)

        final.write_videofile(
            output_path,
            fps=fps_final,                   # 👈 FPS explícito (corrige o erro)
            codec="h264_nvenc",              # GPU
            audio_codec="aac",
            preset="p5",
            ffmpeg_params=["-pix_fmt", "yuv420p"],
            threads=2,
            logger=None
        )


        return JSONResponse({
            "message": "✅ Vídeo gerado com sucesso (Ken Burns real)!",
            "imagens": num_imagens,
            "tempo_por_imagem": round(duracao_por_imagem, 2),
            "duracao_audio": round(audio.duration, 2),
            "output": output_path
        })

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

# ========================
# ❤️ HEALTHCHECK
# ========================
@app.get("/")
def healthcheck():
    return {
        "status": "ok",
        "message": "API FFmpeg + Whisper + Ken Burns ativa 🚀",
        "routes": ["/upload", "/ffmpeg", "/whisper", "/ffmpeg_ken"]
    }
