import tkinter as tk
from tkinter import filedialog, ttk
import subprocess
import whisper
from threading import Thread
import warnings
import os
from docx import Document
import webbrowser
from plyer import notification
import winsound

warnings.filterwarnings("ignore", category=FutureWarning, message="FP16 is not supported on CPU; using FP32 instead")

cancelar_desgravacao = False

def criar_pasta_tmp():
    if not os.path.exists("tmp"):
        os.makedirs("tmp")
    else:
        # Apaga todos os arquivos dentro da pasta tmp
        for filename in os.listdir("tmp"):
            file_path = os.path.join("tmp", filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    os.rmdir(file_path)
            except Exception as e:
                print(f"Falha ao deletar {file_path}. Motivo: {e}")

def extrair_e_transcrever(filepaths, text_var, btn_abrir, btn_select):
    global cancelar_desgravacao
    criar_pasta_tmp()
    
    for filepath in filepaths:
        if cancelar_desgravacao:
            text_var.set("Desgravação cancelada. Selecione arquivos para começar.")
            btn_select.config(text="Selecionar Arquivos e Local de Salvamento", command=lambda: iniciar_processo(btn_abrir, btn_select))
            cancelar_desgravacao = False
            return
        
        nome_arquivo = os.path.splitext(os.path.basename(filepath))[0]
        local_salvamento = os.path.join(os.path.dirname(filepath), nome_arquivo + "-transcrição.docx")
        arquivoTemporarioAudio = os.path.join("tmp", nome_arquivo + ".aac")
        
        comando_ffmpeg = ["ffmpeg", "-i", filepath, "-vn", "-acodec", "copy", arquivoTemporarioAudio]
        subprocess.run(comando_ffmpeg, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        text_var.set(f"Desgravando: {nome_arquivo} ⏳ Por favor, aguarde.")
        
        model = whisper.load_model("large")
        result = model.transcribe(arquivoTemporarioAudio)
        
        doc = Document()
        
        # Adiciona a transcrição sem formatação de tempo e falante
        for segment in result["segments"]:
            text = segment["text"]
            doc.add_paragraph(text)
        
        doc.save(local_salvamento)
        
        os.remove(arquivoTemporarioAudio)
        
    text_var.set("Todas as transcrições foram concluídas.")
    btn_select.config(text="Selecionar Arquivos e Local de Salvamento", command=lambda: iniciar_processo(btn_abrir, btn_select))
    btn_abrir.config(state=tk.NORMAL, command=lambda: abrir_local_salvamento(filepaths))
    
    # Exibir notificação e tocar som
    notification.notify(
        title="Transcrição Concluída",
        message="Todas as transcrições foram concluídas com sucesso.",
        timeout=10
    )
    winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)

def abrir_local_salvamento(filepaths):
    if filepaths:
        diretorio = os.path.dirname(filepaths[0])
        webbrowser.open(diretorio)

def iniciar_transcricao_thread(filepaths, text_var, btn_abrir, btn_select):
    Thread(target=lambda: extrair_e_transcrever(filepaths, text_var, btn_abrir, btn_select)).start()

def selecionar_arquivo_e_salvar(text_var, btn_select, btn_abrir):
    global cancelar_desgravacao
    filepaths = filedialog.askopenfilenames(title="Escolher os vídeos que serão transcritos para texto", filetypes=[("MP4 files", "*.mp4"), ("MP3 files", "*.mp3")])
    if not filepaths:
        text_var.set("Seleção de arquivo cancelada. Operação interrompida.")
        return None

    text_var.set(f"{len(filepaths)} arquivo(s) selecionado(s) para transcrição.")
    btn_select.config(text="Cancelar desgravação", command=lambda: cancelar_desgravacao_fn(btn_select))
    btn_abrir.config(state=tk.DISABLED)
    return filepaths

def cancelar_desgravacao_fn(btn_select):
    global cancelar_desgravacao
    cancelar_desgravacao = True
    btn_select.config(text="Selecionar Arquivos e Local de Salvamento", command=lambda: iniciar_processo(btn_abrir, btn_select))
    text_var.set("Cancelamento em processo...")

root = tk.Tk()
root.title("Desgravador [ Beta ]")

root.geometry("650x450")

cor_fundo = "#343a40"
root.configure(bg=cor_fundo)

style = ttk.Style()
style.theme_use('clam')

cor_frente = "#f8f9fa"
cor_acento = "#007bff"

style.configure("TFrame", background=cor_fundo)
style.configure("TButton", background=cor_acento, foreground=cor_frente, font=("Arial", 10, "bold"), borderwidth=1)
style.configure("TLabel", background=cor_fundo, foreground=cor_frente, font=("Arial", 12))
style.configure("Title.TLabel", background=cor_fundo, foreground=cor_frente, font=("Arial", 16, "bold"))

title_frame = ttk.Frame(root, style="TFrame", height=60)
title_frame.pack(side=tk.TOP, fill=tk.X)
title_frame.pack_propagate(False)

titulo = ttk.Label(title_frame, text="Transcritor de Áudio", style="Title.TLabel", anchor="center")
titulo.pack(side=tk.TOP, fill=tk.X)

frame = ttk.Frame(root, style="TFrame")
frame.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)

text_var = tk.StringVar()
text_var.set("Selecione os arquivos MP4 para transcrever.")
text_label = ttk.Label(frame, textvariable=text_var, wraplength=550, style="TLabel")
text_label.pack()

btn_abrir = ttk.Button(frame, text="Abrir Pasta de Documentos Transcritos", state=tk.DISABLED, style="TButton")
btn_select = ttk.Button(frame, text="Selecionar Arquivos e Local de Salvamento", style="TButton")

def iniciar_processo(btn_abrir, btn_select):
    filepaths = selecionar_arquivo_e_salvar(text_var, btn_select, btn_abrir)
    if filepaths:
        iniciar_transcricao_thread(filepaths, text_var, btn_abrir, btn_select)

btn_select.config(command=lambda: iniciar_processo(btn_abrir, btn_select))
btn_select.pack(pady=(10, 0))
btn_abrir.pack(pady=(10, 20))

root.mainloop()