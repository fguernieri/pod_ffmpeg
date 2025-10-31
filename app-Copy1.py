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

@app.post("/ffmpeg_ken_simple")
async def gerar_video_kenburns_simples(
    audio_file: str = Form(...),
    image_pattern: str = Form(...),
    output_name: str = Form("video_simple.mp4"),
    zoom_start: float = Form(1.0),
    zoom_end: float = Form(1.1),
    pan_strength: float = Form(20),
    fps_final: int = Form(60),  # AUMENTADO PARA 60 FPS
    delay_start: float = Form(0.0),
    fade: bool = Form(True),
    audio_delay: float = Form(0.0),
    codec: str = Form("h264_nvenc"),
    preset: str = Form("p5")
):
    try:
        # Caminhos
        audio_path = os.path.join(UPLOAD_DIR, audio_file)
        imagens_glob = os.path.join(UPLOAD_DIR, "imagens", image_pattern)
        output_path = os.path.join(OUTPUT_DIR, output_name)
        os.makedirs(OUTPUT_DIR, exist_ok=True)

        # Validação de imagens
        imagens = sorted(glob.glob(imagens_glob))
        if not imagens:
            return JSONResponse({"error": f"Nenhuma imagem encontrada: {imagens_glob}"}, status_code=400)

        # Validação de áudio
        if not os.path.exists(audio_path):
            return JSONResponse({"error": f"Arquivo de áudio não encontrado: {audio_path}"}, status_code=400)

        # Tenta carregar o áudio com validação
        try:
            audio = AudioFileClip(audio_path)
            if audio is None or audio.duration is None or audio.duration <= 0:
                return JSONResponse({"error": f"Arquivo de áudio inválido ou corrompido: {audio_path}"}, status_code=400)
        except Exception as e:
            return JSONResponse({"error": f"Erro ao carregar áudio: {str(e)}"}, status_code=400)

        if audio_delay > 0:
            audio = audio.set_start(audio_delay)

        num_imagens = len(imagens)
        duracao_por_imagem = max(audio.duration / num_imagens, 0.1)

        # FUNÇÃO KENBURNS OTIMIZADA E SUAVE
        def kenburns(img_path, duration=4, zoom_start=1.0, zoom_end=1.1, pan_strength=20, fps=30):
            import math
            from moviepy.editor import VideoClip
            from PIL import Image
            import numpy as np
            
            # Pré-carrega e redimensiona a imagem UMA VEZ
            pil_img = Image.open(img_path)
            w, h = pil_img.size
            
            if h < 1080:
                scale = 1080 / h
                new_size = (int(w * scale), 1080)
                pil_img = pil_img.resize(new_size, Image.BICUBIC)  # BICUBIC é mais suave
                w, h = pil_img.size
            
            target_w, target_h = 1920, 1080
            
            # Cache de frames pré-renderizados
            total_frames = int(duration * fps)
            cached_frames = []
            
            print(f"Pré-renderizando {total_frames} frames para {img_path}...")
            
            for frame_idx in range(total_frames):
                t = frame_idx / fps
                progress = t / duration
                
                # SUAVIZAÇÃO MELHORADA - Ease-in-out cúbico (mais suave que cosseno)
                if progress < 0.5:
                    smooth = 4 * progress ** 3
                else:
                    smooth = 1 - pow(-2 * progress + 2, 3) / 2
                
                current_zoom = zoom_start + (zoom_end - zoom_start) * smooth
                
                new_w = math.ceil(w * current_zoom)
                new_h = math.ceil(h * current_zoom)
                new_w = new_w + (new_w % 2)
                new_h = new_h + (new_h % 2)
                
                # BICUBIC para resize mais suave
                img_zoomed = pil_img.resize((new_w, new_h), Image.BICUBIC)
                
                # Pan mais suave (reduzido pela metade)
                x_pan = int(pan_strength * math.sin(progress * math.pi) * 0.5)
                y_pan = int(pan_strength * math.cos(progress * math.pi) * 0.25)
                
                x_center = (new_w - target_w) // 2
                y_center = (new_h - target_h) // 2
                
                x1 = max(0, min(x_center + x_pan, new_w - target_w))
                y1 = max(0, min(y_center + y_pan, new_h - target_h))
                
                img_cropped = img_zoomed.crop((x1, y1, x1 + target_w, y1 + target_h))
                cached_frames.append(np.array(img_cropped))
            
            pil_img.close()
            
            # Adiciona motion blur para suavidade extra
            def add_motion_blur(frames, blur_amount=0.3):
                blurred = []
                for i in range(len(frames)):
                    if i == 0:
                        blurred.append(frames[i])
                    else:
                        blended = (frames[i] * (1 - blur_amount) + frames[i-1] * blur_amount).astype(np.uint8)
                        blurred.append(blended)
                return blurred
            
            cached_frames = add_motion_blur(cached_frames)
            
            def make_frame(t):
                frame_idx = min(int(t * fps), len(cached_frames) - 1)
                return cached_frames[frame_idx]
            
            return VideoClip(make_frame, duration=duration).set_fps(fps)

        # Cria clipes com zoom alternado
        clips = []
        for i, img in enumerate(imagens):
            if os.path.exists(img):
                # Alterna direção do zoom
                if i % 2 == 0:
                    current_zoom_start = zoom_start
                    current_zoom_end = zoom_end
                else:
                    current_zoom_start = zoom_end
                    current_zoom_end = zoom_start
                    
                clip = kenburns(
                    img,
                    duration=duracao_por_imagem,
                    zoom_start=current_zoom_start,
                    zoom_end=current_zoom_end,
                    pan_strength=pan_strength,
                    fps=fps_final
                )
                clips.append(clip)

        if not clips:
            return JSONResponse({"error": "Nenhum clipe válido gerado."}, status_code=500)

        # Combina e adiciona delay inicial
        video = concatenate_videoclips(clips, method="compose").set_fps(fps_final)
        if delay_start > 0:
            video = video.set_start(delay_start)

        # Aplica áudio e corta 0.2s de segurança no final
        safe_duration = audio.duration - 0.2
        final = video.set_audio(audio).subclip(0, safe_duration)

        # Renderiza com NVENC otimizado
        final.write_videofile(
            output_path,
            fps=fps_final,
            codec=codec,
            audio_codec="aac",
            preset=preset,
            ffmpeg_params=[
                "-pix_fmt", "yuv420p",
                "-gpu", "0",
                "-rc", "vbr",
                "-cq", "19",
                "-b:v", "8M",  # Aumentado para 8M (melhor qualidade em 60fps)
            ],
            threads=8,
            logger=None
        )
        
        # Limpa recursos
        audio.close()
        final.close()

        return JSONResponse({
            "message": "✅ Vídeo gerado com sucesso (Ken Burns suave)!",
            "imagens": num_imagens,
            "tempo_por_imagem": round(duracao_por_imagem, 2),
            "duracao_audio": round(audio.duration, 2),
            "zoom_start": zoom_start,
            "zoom_end": zoom_end,
            "pan_strength": pan_strength,
            "delay_start": delay_start,
            "fade": fade,
            "fps_final": fps_final,
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
