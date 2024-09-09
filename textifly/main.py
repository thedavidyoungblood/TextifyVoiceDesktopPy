import logging
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from threading import Thread, Event

import whisper
import warnings
import os
from docx import Document
import webbrowser
from plyer import notification
import winsound
import ffmpeg
import json
import tqdm
import urllib.request
# GUI
from ui import create_gui 
#Config
from config import load_config
from config import CONFIG_FILE
from config import logger_config
warnings.filterwarnings("ignore", category=FutureWarning, message="FP16 is not supported on CPU; using FP32 instead")
warnings.filterwarnings("ignore", category=UserWarning, message="FP16 is not supported on CPU; using FP32 instead")


# Global Variables
config = load_config()
cancelar_desgravacao = False
threads = []
stop_event = Event()


def extrair_audio(filepath, temp_dir):
    try:
        if filepath.lower().endswith(('.mp3', '.wav', '.aac', '.flac', '.m4a', '.ogg')):
            logging.info(f"O arquivo {filepath} já é um formato de áudio suportado. Não é necessário extrair o áudio.")
            return filepath
        
        logging.info(f"Extraindo áudio do vídeo: {filepath}")
        
        output_path = os.path.join(temp_dir, "temp_audio.aac")
        
        (
            ffmpeg
            .input(filepath)
            .output(output_path, acodec='aac')
            .run(capture_stdout=True, capture_stderr=True)
        )
        
        logging.info(f"Áudio extraído com sucesso para: {output_path}")
        return output_path
    except ffmpeg.Error as e:
        logging.error(f"Erro ao extrair áudio com ffmpeg: {e.stderr.decode()}")
        raise


def abrir_local_salvamento(filepaths):
    if filepaths:
        diretorio = os.path.dirname(filepaths[0])
        webbrowser.open(diretorio)
        logging.info(f"Abrindo diretório de salvamento: {diretorio}")

def iniciar_transcricao_thread(filepaths, text_var, btn_abrir, btn_select, btn_qualidade, model_path):
    thread = Thread(target=lambda: extract_transcribe(filepaths, text_var, btn_abrir, btn_select, btn_qualidade, model_path))
    threads.append(thread)
    thread.start()

def selecionar_arquivo_e_salvar(text_var, btn_select, btn_abrir, btn_qualidade, model_path):
    global cancelar_desgravacao
    filepaths = filedialog.askopenfilenames(title="Escolher os vídeos que serão transcritos para texto",
                                            filetypes=[("Arquivos Selecionáveis", "*.mp4;*.mp3;*.wav;*.mkv"),("MP4 files", "*.mp4",), ("MP3 files", "*.mp3"),("WAV files", "*.wav")])
    if not filepaths:
        text_var.set("Seleção de arquivo cancelada. Operação interrompida.")
        logging.info("Seleção de arquivo cancelada pelo usuário.")
        return None

    filepaths = [filepath.replace("/", "\\") for filepath in filepaths] 

    text_var.set(f"{len(filepaths)} arquivo(s) selecionado(s) para transcrição.")
    btn_select.config(text="Cancelar desgravação", command=lambda: cancelar_desgravacao_fn(btn_select, btn_qualidade))
    btn_abrir.config(state=tk.DISABLED)
    btn_qualidade.config(state=tk.DISABLED)
    logging.info(f"{len(filepaths)} arquivo(s) selecionado(s) para transcrição.")
    return filepaths

def cancelar_desgravacao_fn(btn_select, btn_qualidade):
    global cancelar_desgravacao
    cancelar_desgravacao = True
    btn_select.config(text="Selecionar Arquivos", command=lambda: iniciar_processo(btn_abrir, btn_select, btn_qualidade))
    btn_qualidade.config(state=tk.NORMAL)
    text_var.set("Cancelamento em processo...")
    logging.info("Processo de desgravação cancelado pelo usuário.")

def selecionar_modelo():
    janela_modelo = tk.Toplevel()
    janela_modelo.title("Selecionar Modelo Whisper")
    janela_modelo.geometry("400x200")
    janela_modelo.grab_set()

    label = ttk.Label(janela_modelo, text="Selecione o caminho do modelo:")
    label.pack(pady=20)

    model_path_var_local = tk.StringVar(value=config.get('model_path', ''))

    entry = ttk.Entry(janela_modelo, textvariable=model_path_var_local, width=50)
    entry.pack(pady=10)

    def escolher_modelo():
        filepath = filedialog.askopenfilename(title="Selecionar Modelo Whisper", filetypes=[("Modelo Whisper", "*.pt")])
        if filepath:
            model_path_var_local.set(filepath)
            try:
                whisper.load_model(filepath)
                config['model_path'] = filepath
                with open(CONFIG_FILE, 'w') as f:
                    json.dump(config, f)
                model_path_var.set(filepath)
                messagebox.showinfo("Sucesso", "Modelo carregado e caminho salvo com sucesso!")
                janela_modelo.destroy()
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao carregar o modelo: {e}")
                logging.info(f"Modelo inicial carregado com sucesso. {e}")

    btn_escolher = ttk.Button(janela_modelo, text="Escolher Modelo", command=escolher_modelo)
    btn_escolher.pack(pady=10)

def verificar_modelo_inicial():
    model_path = config.get('model_path')
    if model_path:
        try:
            whisper.load_model(model_path)
            logging.info("Modelo inicial carregado com sucesso.")
        except Exception as e:
            logging.error(f"Erro ao carregar o modelo inicial: {e}")
            messagebox.showerror("Erro", f"Erro ao carregar o modelo inicial: {e}")
            select_transcription_quality()
    else:
        select_transcription_quality()


def iniciar_processo(btn_abrir, btn_select, btn_qualidade):
    filepaths = selecionar_arquivo_e_salvar(text_var, btn_select, btn_abrir, btn_qualidade, model_path_var.get())
    if filepaths:
        iniciar_transcricao_thread(filepaths, text_var, btn_abrir, btn_select, btn_qualidade, model_path_var.get())

def on_closing():
    global cancelar_desgravacao
    cancelar_desgravacao = True
    stop_event.set()
    for thread in threads:
        thread.join()
    root.destroy()

logger_config()

root = tk.Tk()

create_gui(root)

root.protocol("WM_DELETE_WINDOW", on_closing)

root.after(10, verificar_modelo_inicial)

root.mainloop()
