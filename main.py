import tkinter as tk
from tkinter import filedialog, messagebox
import subprocess
import whisper
from threading import Thread
import warnings
import os
from docx import Document

warnings.filterwarnings("ignore", message="FP16 is not supported on CPU; using FP32 instead")

def extrair_e_transcrever(filepath, local_salvamento, text_var):
    if not filepath or not local_salvamento:
        text_var.set("Operação cancelada.")
        return

    arquivoTemporarioAudio = "saida_audio.aac"
    comando_ffmpeg = ["ffmpeg", "-i", filepath, "-vn", "-acodec", "copy", arquivoTemporarioAudio]
    subprocess.run(comando_ffmpeg, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    text_var.set("Desgravando... ⏳ Por favor, aguarde.")

    # Carrega o modelo "medium" do Whisper
    model = whisper.load_model("medium")
    result = model.transcribe(arquivoTemporarioAudio)

    doc = Document()
    doc.add_paragraph(result["text"])
    doc.save(local_salvamento)

    text_var.set(f"Transcrição concluída. Documento salvo com sucesso em: {local_salvamento}")

    os.remove(arquivoTemporarioAudio)

def iniciar_transcricao_thread(filepath, local_salvamento, text_var):
    Thread(target=lambda: extrair_e_transcrever(filepath, local_salvamento, text_var)).start()

def selecionar_arquivo_e_salvar():
    filepath = filedialog.askopenfilename(title="Escolher o vídeo que será transcrito para texto", filetypes=[("MP4 files", "*.mp4"), ("MP3 files", "*.mp3")])
    if not filepath:
        text_var.set("Seleção de arquivo cancelada. Operação interrompida.")
        return None

    local_salvamento = filedialog.asksaveasfilename(title="Salvar desgravação em:", defaultextension=".docx", filetypes=[("Documentos Word", "*.docx")])
    if not local_salvamento:
        text_var.set("Seleção de local de salvamento cancelada. Operação interrompida.")
        return None, None

    return filepath, local_salvamento

root = tk.Tk()
root.title("Transcritor de Áudio")

frame = tk.Frame(root)
frame.pack(padx=10, pady=10)

text_var = tk.StringVar()
text_var.set("Selecione um arquivo MP4 para transcrever.")
text_label = tk.Label(frame, textvariable=text_var, wraplength=400)
text_label.pack()

def iniciar_processo():
    filepath, local_salvamento = selecionar_arquivo_e_salvar()
    if filepath and local_salvamento:
        iniciar_transcricao_thread(filepath, local_salvamento, text_var)

btn_select = tk.Button(frame, text="Selecionar Arquivo e Local de Salvamento", command=iniciar_processo)
btn_select.pack(pady=10)

root.mainloop()