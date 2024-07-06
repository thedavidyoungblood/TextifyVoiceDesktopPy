import os
import logging
from logging.handlers import RotatingFileHandler
from docx import Document
import tkinter as tk
from plyer import notification
import winsound
import whisper
from threading import Thread
import webbrowser
from tkinter import filedialog, messagebox, ttk
import json
import subprocess
import warnings

warnings.filterwarnings("ignore", category=FutureWarning, message="FP16 is not supported on CPU; using FP32 instead")
warnings.filterwarnings("ignore", category=UserWarning, message="FP16 is not supported on CPU; using FP32 instead")

CONFIG_FILE = "config.json"
DEFAULT_CONFIG = {
    "model_path": "",
    "language": "pt"  # Linguagem padrão alterada para português
}

# Verificar se o arquivo de configuração existe, caso contrário, criar um com valores padrão
if not os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(DEFAULT_CONFIG, f, indent=4)
    logging.info(f"Arquivo de configuração criado: {CONFIG_FILE}")

# Carregar a configuração
config = {}
try:
    with open(CONFIG_FILE, 'r') as f:
        config = json.load(f)
except FileNotFoundError:
    pass

def configurar_logger():
    if not os.path.exists("logs"):
        os.makedirs("logs")
    
    # Configurar o RotatingFileHandler
    log_handler = RotatingFileHandler('logs/info.log', maxBytes=5*1024*1024, backupCount=5)
    log_handler.setLevel(logging.INFO)
    log_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(log_handler)

configurar_logger()

cancelar_desgravacao = False

def extrair_audio(filepath, output_path):
    try:
        logging.info(f"Extraindo áudio do vídeo: {filepath}")
        # Caminho para o executável do FFmpeg dentro da pasta da aplicação
        ffmpeg_path = os.path.join('.', 'ffmpeg', 'ffmpeg.exe')
        
        command = [
            ffmpeg_path,
            '-i', filepath,
            output_path
        ]
        # Redirecionar a saída para suprimir as mensagens do FFmpeg
        with open(os.devnull, 'w') as devnull:
            subprocess.run(command, stdout=devnull, stderr=devnull)
        logging.info(f"Áudio extraído com sucesso para: {output_path}")
    except subprocess.CalledProcessError as e:
        logging.error(f"Erro ao extrair áudio com ffmpeg: {e}")
        raise

def extrair_e_transcrever(filepaths, text_var, btn_abrir, btn_select, btn_modelo, language_dropdown, model_path, language):
    global cancelar_desgravacao

    try:
        logging.info(f"Tentando carregar o modelo do caminho: {model_path}")
        model = whisper.load_model(model_path)
        if model:
            logging.info(f"Modelo de transcrição carregado com sucesso: {model}")
    except Exception as e:
        logging.error(f"Erro ao carregar o modelo de transcrição: {e}")
        text_var.set(f"Erro ao carregar o modelo. Verifique o caminho.")
        return

    temp_dir = "./temp"
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
        logging.info(f"Diretório temporário criado: {temp_dir}")

    for filepath in filepaths:
        filepath = filepath.replace("/", "\\")  # Garantir barra invertida
        logging.info(f"Analisando arquivo: {filepath}")
        text_var.set("Processando arquivos...")

        if cancelar_desgravacao:
            text_var.set("Desgravação cancelada. Selecione arquivos para começar.")
            btn_select.config(text="Selecionar Arquivos",
                              command=lambda: iniciar_processo(btn_abrir, btn_select, btn_modelo, language_dropdown, language_var))
            btn_modelo.config(state=tk.NORMAL)
            language_dropdown.config(state=tk.NORMAL)
            cancelar_desgravacao = False
            logging.info("Desgravação cancelada pelo usuário.")
            return

        nome_arquivo = os.path.splitext(os.path.basename(filepath))[0]
        local_salvamento = os.path.join(os.path.dirname(filepath), nome_arquivo + "_text.docx")
        local_salvamento = local_salvamento.replace("/", "\\")  # Garantir barra invertida
        logging.info(f"Transcrição será salva em: {local_salvamento}")

        try:
            if not os.path.exists(filepath):
                raise FileNotFoundError(f"O arquivo {filepath} não foi encontrado.")

            # Extrair áudio do vídeo
            audio_temp_path = os.path.join(temp_dir, nome_arquivo + "_audio.wav")
            extrair_audio(filepath, audio_temp_path)

            text_var.set(f"Desgravando: {nome_arquivo} ⏳ Por favor, aguarde.")
            logging.info(f"Iniciando transcrição do arquivo: {audio_temp_path}")

            result = model.transcribe(audio_temp_path, language=language)
            doc = Document()
            for segment in result["segments"]:
                text = segment["text"]
                doc.add_paragraph(text)

            doc.save(local_salvamento)
            logging.info(f"Transcrição concluída salva em: {local_salvamento}")

            # Remover arquivo de áudio temporário
            os.remove(audio_temp_path)

        except FileNotFoundError as fnf_error:
            logging.error(f"Erro ao transcrever {nome_arquivo}. Motivo: {fnf_error}")
            cancelar_desgravacao = True
            text_var.set(f"Erro no desgravando {nome_arquivo}. Motivo: {fnf_error}")
            btn_select.config(text="Selecionar Arquivos para transcrição",
                              command=lambda: iniciar_processo(btn_abrir, btn_select, btn_modelo, language_dropdown, language_var))
            btn_modelo.config(state=tk.NORMAL)
            language_dropdown.config(state=tk.NORMAL)
            notification.notify(
                title="Erro na Transcrição",
                message=f"O arquivo {filepath} não foi encontrado.",
                timeout=10
            )
            winsound.MessageBeep(winsound.MB_ICONHAND)
            return

        except PermissionError as perm_error:
            logging.error(f"Erro ao transcrever {nome_arquivo}. Motivo: {perm_error}")
            cancelar_desgravacao = True
            text_var.set(f"Erro no desgravando {nome_arquivo}. Motivo: {perm_error}")
            btn_select.config(text="Selecionar Arquivos para transcrição",
                              command=lambda: iniciar_processo(btn_abrir, btn_select, btn_modelo, language_dropdown, language_var))
            btn_modelo.config(state=tk.NORMAL)
            language_dropdown.config(state=tk.NORMAL)
            notification.notify(
                title="Erro na Transcrição",
                message=f"Permissão negada para acessar o arquivo {filepath}.",
                timeout=10
            )
            winsound.MessageBeep(winsound.MB_ICONHAND)
            return

        except ValueError as val_error:
            logging.error(f"Erro ao transcrever {nome_arquivo}. Motivo: {val_error}")
            cancelar_desgravacao = True
            text_var.set(f"Erro no desgravando {nome_arquivo}. Motivo: {val_error}")
            btn_select.config(text="Selecionar Arquivos para transcrição",
                              command=lambda: iniciar_processo(btn_abrir, btn_select, btn_modelo, language_dropdown, language_var))
            btn_modelo.config(state=tk.NORMAL)
            language_dropdown.config(state=tk.NORMAL)
            notification.notify(
                title="Erro na Transcrição",
                message=f"O arquivo {filepath} não contém uma faixa de áudio.",
                timeout=10
            )
            winsound.MessageBeep(winsound.MB_ICONHAND)
            return

        except Exception as e:
            logging.error(f"Erro ao transcrever {nome_arquivo}. Motivo: {e}")
            cancelar_desgravacao = True
            text_var.set(f"Erro no desgravando {nome_arquivo}.")
            btn_select.config(text="Selecionar Arquivos para transcrição",
                              command=lambda: iniciar_processo(btn_abrir, btn_select, btn_modelo, language_dropdown, language_var))
            btn_modelo.config(state=tk.NORMAL)
            language_dropdown.config(state=tk.NORMAL)
            notification.notify(
                title="Erro na Transcrição",
                message=f"Ocorreu um erro ao transcrever {nome_arquivo}.",
                timeout=10
            )
            winsound.MessageBeep(winsound.MB_ICONHAND)
            return

    text_var.set("Todas as transcrições foram concluídas.")
    btn_select.config(text="Selecionar Arquivos",
                      command=lambda: iniciar_processo(btn_abrir, btn_select, btn_modelo, language_dropdown, language_var))
    btn_modelo.config(state=tk.NORMAL)
    language_dropdown.config(state=tk.NORMAL)
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

def iniciar_transcricao_thread(filepaths, text_var, btn_abrir, btn_select, btn_modelo, language_dropdown, model_path, language):
    Thread(target=lambda: extrair_e_transcrever(filepaths, text_var, btn_abrir, btn_select, btn_modelo, language_dropdown, model_path, language)).start()

def selecionar_arquivo_e_salvar(text_var, btn_select, btn_abrir, btn_modelo, language_dropdown, model_path, language):
    global cancelar_desgravacao
    filepaths = filedialog.askopenfilenames(title="Escolher os vídeos que serão transcritos para texto",
                                            filetypes=[("MP4 files", "*.mp4"), ("MP3 files", "*.mp3")])
    if not filepaths:
        text_var.set("Seleção de arquivo cancelada. Operação interrompida.")
        logging.info("Seleção de arquivo cancelada pelo usuário.")
        return None

    filepaths = [filepath.replace("/", "\\") for filepath in filepaths]  # Garantir barra invertida

    text_var.set(f"{len(filepaths)} arquivo(s) selecionado(s) para transcrição.")
    btn_select.config(text="Cancelar desgravação", command=lambda: cancelar_desgravacao_fn(btn_select, btn_modelo, language_dropdown))
    btn_modelo.config(state=tk.DISABLED)
    language_dropdown.config(state=tk.DISABLED)
    btn_abrir.config(state=tk.DISABLED)
    logging.info(f"{len(filepaths)} arquivo(s) selecionado(s) para transcrição.")
    return filepaths

def cancelar_desgravacao_fn(btn_select, btn_modelo, language_dropdown):
    global cancelar_desgravacao
    cancelar_desgravacao = True
    btn_select.config(text="Selecionar Arquivos", command=lambda: iniciar_processo(btn_abrir, btn_select, btn_modelo, language_dropdown, language_var))
    btn_modelo.config(state=tk.NORMAL)
    language_dropdown.config(state=tk.NORMAL)
    text_var.set("Cancelamento em processo...")
    logging.info("Processo de desgravação cancelado pelo usuário.")

def selecionar_modelo():
    janela_modelo = tk.Toplevel()
    janela_modelo.title("Selecionar Modelo Whisper")
    janela_modelo.geometry("400x200")
    janela_modelo.grab_set()

    label = ttk.Label(janela_modelo, text="Selecione o caminho do modelo:")
    label.pack(pady=10)

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
            selecionar_modelo()
    else:
        selecionar_modelo()

root = tk.Tk()
root.title("TextifyVoice [ Beta ]")

root.geometry("650x500")

root.iconbitmap('./bin/icon.ico')

cor_fundo = "#343a40"
root.configure(bg=cor_fundo)

style = ttk.Style()
style.theme_use('clam')

cor_frente = "#f8f9fa"
cor_acento = "#007bff"
cor_modelo = "#28a745"

style.configure("TFrame", background=cor_fundo)
style.configure("TButton", background=cor_acento, foreground=cor_frente, font=("Arial", 10, "bold"), borderwidth=1, relief="flat")
style.configure("Modelo.TButton", background=cor_modelo, foreground=cor_frente, font=("Arial", 10, "bold"), borderwidth=1, relief="flat")
style.configure("TLabel", background=cor_fundo, foreground=cor_frente, font=("Arial", 12))
style.configure("Title.TLabel", background=cor_fundo, foreground=cor_frente, font=("Arial", 16, "bold"))

style.map("TButton", relief=[("pressed", "sunken"), ("active", "raised")])
style.map("Modelo.TButton", relief=[("pressed", "sunken"), ("active", "raised")])

title_frame = ttk.Frame(root, style="TFrame", height=70)
title_frame.pack(side=tk.TOP, fill=tk.X)
title_frame.pack_propagate(False)

titulo = ttk.Label(title_frame, text="Transcritor de Vídeo", style="Title.TLabel", anchor="center")
titulo.pack(side=tk.TOP, fill=tk.X, pady=20)

frame = ttk.Frame(root, style="TFrame")
frame.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)

text_var = tk.StringVar()
text_var.set("Selecione os arquivos MP4 para transcrever.")
text_label = ttk.Label(frame, textvariable=text_var, wraplength=550, style="TLabel")
text_label.pack()

model_path = config.get('model_path')
model_path_var = tk.StringVar(value=model_path)

language = config.get('language', 'pt')
language_var = tk.StringVar(value=language)

btn_abrir = ttk.Button(frame, text="Abrir Pasta de Documentos Transcritos", state=tk.DISABLED, style="TButton")
btn_select = ttk.Button(frame, text="Selecionar Arquivos", style="TButton")
btn_modelo = ttk.Button(frame, text="Selecionar Modelo", command=selecionar_modelo, style="Modelo.TButton")

# Lista de linguagens disponíveis no Whisper
LANGUAGES = [
    "en", "zh", "de", "es", "ru", "ko", "fr", "ja", "pt", "tr", "pl", "ca", "nl", "ar", "sv", "it", "id", "hi", "fi", "vi", "he", "uk", "el", "ms", "cs", "ro", "da", "hu", "ta", "no", "th", "ur", "hr", "bg", "lt", "la", "mi", "ml", "cy", "sk", "te", "fa", "lv", "bn", "sr", "az", "sl", "kn", "et", "mk", "br", "eu", "is", "hy", "ne", "mn", "bs", "kk", "sq", "sw", "gl", "mr", "pa", "si", "km", "sn", "yo", "so", "af", "oc", "ka", "be", "tg", "sd", "gu", "am", "yi", "lo", "uz", "fo", "ht", "ps", "tk", "nn", "mt", "sa", "lb", "my", "bo", "tl", "mg", "as", "tt", "haw", "ln", "ha", "ba", "jw", "su"
]

# Dropdown menu para selecionar a linguagem
language_label = ttk.Label(frame, text="Selecione a Linguagem:", style="TLabel")
language_dropdown = ttk.OptionMenu(frame, language_var, language, *LANGUAGES)


def iniciar_processo(btn_abrir, btn_select, btn_modelo, language_dropdown, language_var):
    filepaths = selecionar_arquivo_e_salvar(text_var, btn_select, btn_abrir, btn_modelo, language_dropdown, model_path_var.get(), language_var.get())
    if filepaths:
        iniciar_transcricao_thread(filepaths, text_var, btn_abrir, btn_select, btn_modelo, language_dropdown, model_path_var.get(), language_var.get())

btn_select.config(command=lambda: iniciar_processo(btn_abrir, btn_select, btn_modelo, language_dropdown, language_var))
btn_select.pack(pady=(10, 0))
btn_abrir.pack(pady=(10, 20))
language_label.pack(pady=(10, 0))
language_dropdown.pack(pady=(0, 10))
btn_modelo.pack(pady=(10, 0))

root.after(100, verificar_modelo_inicial)

root.mainloop()