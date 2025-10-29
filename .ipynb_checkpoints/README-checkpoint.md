# 🎬 pod_ffmpeg API

Serviço HTTP baseado em FastAPI para **transcrição (Whisper)** e **conversão de mídia (FFmpeg)**.

## 🔧 Instalação
```bash
bash setup.sh
🚀 Inicialização
bash
Copiar código
bash boot_env.sh
🧠 Endpoints
/whisper → Transcreve áudio/vídeo para texto.

/ffmpeg → Converte arquivos de mídia (ex: mp4 → wav).

Servidor roda em http://<IP_DO_POD>:8090

yaml
Copiar código

---

# 🧩 **3️⃣ Fluxo completo de uso**

1. **Instala tudo (apenas 1 vez):**
   ```bash
   bash /workspace/pod_ffmpeg/setup.sh
Inicia o servidor:

bash
Copiar código
bash /workspace/pod_ffmpeg/boot_env.sh
Testa no navegador ou curl:

bash
Copiar código
curl http://<IP_DO_POD>:8090/