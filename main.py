import tkinter as tk
from tkinter import filedialog, messagebox
import subprocess
import whisper
from threading import Thread
import warnings
import os
from docx import Document
warnings.filterwarnings("ignore", message="FP16 is not supported on CPU; using FP32 instead")

def extrair_e_transcrever(text_var):
    arquivo_selecionado = False
    filepath = ""

    while not arquivo_selecionado:
        filepath = filedialog.askopenfilename(filetypes=[("MP4 files", "*.mp4")])
        if not filepath:
            text_var.set("Seleção de arquivo cancelada. Operação interrompida.")
            return

        if filepath.endswith(".mp4"):
            arquivo_selecionado = True
        else:
            messagebox.showerror("Erro", "O arquivo selecionado não é um MP4 válido. Por favor, selecione um arquivo MP4.")

    arquivoTemporarioAudio = "saida_audio.aac"
    comando_ffmpeg = ["ffmpeg", "-i", filepath, "-vn", "-acodec", "copy", arquivoTemporarioAudio]
    subprocess.run(comando_ffmpeg, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # Atualiza o texto para mostrar que a desgravação está em andamento
    text_var.set("Desgravando... ⏳ Por favor, aguarde.")

    model = whisper.load_model("base")
    result = model.transcribe(arquivoTemporarioAudio)

    text_var.set("Transcrição concluída. Salvando documento...")

    nome_base_arquivo = os.path.splitext(os.path.basename(filepath))[0]
    arquivo_saida_docx = f"{nome_base_arquivo}_transcrição.docx"

    doc = Document()
    doc.add_paragraph(result["text"])
    doc.save(arquivo_saida_docx)

    text_var.set(f"Transcrição concluída. Documento '{arquivo_saida_docx}' salvo com sucesso.")

    os.remove(arquivoTemporarioAudio)

def iniciar_transcricao_thread():
    Thread(target=lambda: extrair_e_transcrever(text_var)).start()

root = tk.Tk()
root.title("Transcritor de Áudio")

frame = tk.Frame(root)
frame.pack(padx=10, pady=10)

text_var = tk.StringVar()
text_var.set("Selecione um arquivo MP4 para transcrever.")
text_label = tk.Label(frame, textvariable=text_var, wraplength=400)
text_label.pack()

btn_select = tk.Button(frame, text="Selecionar Arquivo e Transcrever", command=iniciar_transcricao_thread)
btn_select.pack(pady=10)

root.mainloop()