import tkinter as tk
from tkinter import filedialog, ttk
import whisper
from threading import Thread
import warnings
import os
from docx import Document
import webbrowser
from plyer import notification
import winsound
import logging

warnings.filterwarnings("ignore", category=FutureWarning, message="FP16 is not supported on CPU; using FP32 instead")


def configurar_logger():
    if not os.path.exists("logs"):
        os.makedirs("logs")
    logging.basicConfig(filename='logs/info.log', level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')

configurar_logger()

cancelar_desgravacao = False

def extrair_e_transcrever(filepaths, text_var, btn_abrir, btn_select):
    global cancelar_desgravacao
    
    model = whisper.load_model("large")

    for filepath in filepaths:
        text_var.set("Processando arquivos...")

        if cancelar_desgravacao:
            text_var.set("Desgravação cancelada. Selecione arquivos para começar.")
            btn_select.config(text="Selecionar Arquivos e Local de Salvamento", command=lambda: iniciar_processo(btn_abrir, btn_select))
            cancelar_desgravacao = False
            logging.info("Desgravação cancelada pelo usuário.")
            return
        
        nome_arquivo = os.path.splitext(os.path.basename(filepath))[0]
        local_salvamento = os.path.join(os.path.dirname(filepath), nome_arquivo + "-transcrição.docx")
        
        try:
            text_var.set(f"Desgravando: {nome_arquivo} ⏳ Por favor, aguarde.")
            logging.info(f"Iniciando transcrição do arquivo: {filepath}")
            
            result = model.transcribe(filepath)
            
            doc = Document()
            
            for segment in result["segments"]:
                text = segment["text"]
                doc.add_paragraph(text)
            
            doc.save(local_salvamento)
            logging.info(f"Transcrição concluída e salva em: {local_salvamento}")
        
        except Exception as e:
            logging.error(f"Erro ao transcrever {nome_arquivo}. Motivo: {e}")
            cancelar_desgravacao = True
            text_var.set(f"Erro no desgravando {nome_arquivo}. Motivo: {e}")
            btn_select.config(text="Selecionar Arquivos e Local de Salvamento", command=lambda: iniciar_processo(btn_abrir, btn_select))
            notification.notify(
                title="Erro na Transcrição",
                message=f"Ocorreu um erro ao transcrever {nome_arquivo}.",
                timeout=10
            )
            winsound.MessageBeep(winsound.MB_ICONHAND)
            return
        
    text_var.set("Todas as transcrições foram concluídas.")
    btn_select.config(text="Selecionar Arquivos e Local de Salvamento", command=lambda: iniciar_processo(btn_abrir, btn_select))
    btn_abrir.config(state=tk.NORMAL, command=lambda: abrir_local_salvamento(filepaths))
    
    logging.info("Todas as transcrições foram concluídas com sucesso.")
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
        logging.info(f"Abrindo diretório de salvamento: {diretorio}")

def iniciar_transcricao_thread(filepaths, text_var, btn_abrir, btn_select):
    Thread(target=lambda: extrair_e_transcrever(filepaths, text_var, btn_abrir, btn_select)).start()

def selecionar_arquivo_e_salvar(text_var, btn_select, btn_abrir):
    global cancelar_desgravacao
    filepaths = filedialog.askopenfilenames(title="Escolher os vídeos que serão transcritos para texto", filetypes=[("MP4 files", "*.mp4"), ("MP3 files", "*.mp3")])
    if not filepaths:
        text_var.set("Seleção de arquivo cancelada. Operação interrompida.")
        logging.info("Seleção de arquivo cancelada pelo usuário.")
        return None

    text_var.set(f"{len(filepaths)} arquivo(s) selecionado(s) para transcrição.")
    btn_select.config(text="Cancelar desgravação", command=lambda: cancelar_desgravacao_fn(btn_select))
    btn_abrir.config(state=tk.DISABLED)
    logging.info(f"{len(filepaths)} arquivo(s) selecionado(s) para transcrição.")
    return filepaths

def cancelar_desgravacao_fn(btn_select):
    global cancelar_desgravacao
    cancelar_desgravacao = True
    btn_select.config(text="Selecionar Arquivos e Local de Salvamento", command=lambda: iniciar_processo(btn_abrir, btn_select))
    text_var.set("Cancelamento em processo...")
    logging.info("Processo de desgravação cancelado pelo usuário.")

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

title_frame = ttk.Frame(root, style="TFrame", height=70)
title_frame.pack(side=tk.TOP, fill=tk.X)
title_frame.pack_propagate(False)

titulo = ttk.Label(title_frame, text="Transcritor de Áudio", style="Title.TLabel", anchor="center")
titulo.pack(side=tk.TOP, fill=tk.X,pady=20)

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