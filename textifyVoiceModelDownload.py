import logging
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from threading import Thread, Event
from logging.handlers import RotatingFileHandler
import whisper
import warnings
import os
from docx import Document
from plyer import notification
import json
import time
import shutil
import torch
import requests
import subprocess
from platform import system
import sys


warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)

# Função para gerenciar caminhos de recursos
def resource_path(relative_path):
    """Obtém o caminho absoluto para o recurso, funciona tanto para desenvolvimento quanto para empacotamento."""
    try:
        # PyInstaller cria um atributo _MEIPASS que aponta para a pasta temporária
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# Classe personalizada para ocultar o console no Windows
class NoConsolePopen(subprocess.Popen):
    """
    A custom Popen class that disables creation of a console window in Windows.
    """
    def __init__(self, args, **kwargs):
        if system() == 'Windows' and 'startupinfo' not in kwargs:
            kwargs['startupinfo'] = subprocess.STARTUPINFO()
            kwargs['startupinfo'].dwFlags |= subprocess.STARTF_USESHOWWINDOW
        super().__init__(args, **kwargs)

# Substituir subprocess.Popen pela classe personalizada
subprocess.Popen = NoConsolePopen

# Caminhos dos recursos
CONFIG_FILE = resource_path("config.json")
LOGS_DIR = resource_path("logs")
TEMP_DIR = resource_path("temp")
ICON_PATH = resource_path("bin/icon.ico")

# Configuração do Logger
def configurar_logger():
    if not os.path.exists(LOGS_DIR):
        os.makedirs(LOGS_DIR)
        logging.info(f"Diretório de logs criado: {LOGS_DIR}")
    
    log_handler = RotatingFileHandler(os.path.join(LOGS_DIR, 'info.log'), maxBytes=5*1024*1024, backupCount=5)
    log_handler.setLevel(logging.INFO)
    log_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    # Remover handlers existentes para evitar logs no console
    if logger.hasHandlers():
        logger.handlers.clear()
    logger.addHandler(log_handler)

# Configuração padrão
DEFAULT_CONFIG = {
    "model_path": "",
    "language": "pt"
}

# Criar arquivo de configuração se não existir
if not os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(DEFAULT_CONFIG, f, indent=4)
    configurar_logger()
    logging.info(f"Arquivo de configuração criado: {CONFIG_FILE}")

# Variáveis Globais
config = {}
cancelar_desgravacao = False
threads = []
stop_event = Event()
transcricao_em_andamento = False
confirm_dialog_open = False
janela_qualidade = None
janela_selecao = None
janela_modelo = None

# Carregar configuração
try:
    with open(CONFIG_FILE, 'r') as f:
        config = json.load(f)
except FileNotFoundError:
    configurar_logger()
    logging.error(f"Arquivo de configuração não encontrado: {CONFIG_FILE}")

# Função para extrair áudio usando FFmpeg
def extrair_audio(filepath, temp_dir):
    try:
        # Certificar-se de que o diretório temp existe
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
            logging.info(f"Diretório temporário criado: {temp_dir}")
        else:
            # Verificar se o diretório temp está vazio e limpar se necessário
            if os.listdir(temp_dir):
                for filename in os.listdir(temp_dir):
                    file_path = os.path.join(temp_dir, filename)
                    try:
                        if os.path.isfile(file_path) or os.path.islink(file_path):
                            os.unlink(file_path)
                        elif os.path.isdir(file_path):
                            shutil.rmtree(file_path)
                    except Exception as e:
                        logging.error(f'Falha ao deletar {file_path}. Motivo: {e}')

        # Verificar se o arquivo já é um formato de áudio suportado
        if filepath.lower().endswith(('.mp3', '.wav', '.aac', '.flac', '.m4a', '.ogg')):
            logging.info(f"O arquivo {filepath} já é um formato de áudio suportado. Não é necessário extrair o áudio.")
            return filepath

        logging.info(f"Extraindo áudio do vídeo: {filepath}")
        output_path = os.path.join(temp_dir, "temp_audio.aac")  # ./temp/temp_audio.aac
        output_path = os.path.abspath(output_path)

        # Comando para extrair áudio usando FFmpeg
        command = ['ffmpeg', '-i', filepath, '-acodec', 'aac', output_path, '-y']
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        logging.info(f"FFmpeg output: {result}")

        if result.returncode != 0:
            logging.error(f"Erro ao extrair áudio com ffmpeg: {result.stderr.decode()}")
            raise subprocess.CalledProcessError(result.returncode, command, output=result.stdout, stderr=result.stderr)

        logging.info(f"Áudio extraído com sucesso para: {output_path}")
        return output_path
    except subprocess.CalledProcessError as e:
        logging.error(f"Erro ao extrair áudio com ffmpeg: {e.stderr.decode()}")
        raise

# Função para extrair e transcrever arquivos
def extrair_e_transcrever_arquivo(filepath, item, lista_arquivos):
    global cancelar_desgravacao

    if cancelar_desgravacao:
        return

    try:
        model_path = config.get('model_path')
        logging.info(f"Tentando carregar o modelo do caminho: {model_path}")
        # Verificar se GPU está disponível
        device = "cuda" if torch.cuda.is_available() else "cpu"
        logging.info(f"Usando dispositivo: {device}")
        model = whisper.load_model(model_path, device=device)
        if model:
            logging.info(f"Modelo de transcrição carregado com sucesso")
    except Exception as e:
        logging.error(f"Erro ao carregar o modelo de transcrição: {e}")
        if lista_arquivos.winfo_exists():
            lista_arquivos.after(0, lambda: lista_arquivos.set(item, 'Status', 'Erro no modelo'))
        return

    temp_dir = TEMP_DIR
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
        logging.info(f"Diretório temporário criado: {temp_dir}")

    filepath = filepath.replace("/", "\\") 
    logging.info(f"Analisando arquivo: {filepath}")

    nome_arquivo = os.path.splitext(os.path.basename(filepath))[0]
    local_salvamento = os.path.join(os.path.dirname(filepath), nome_arquivo + "_text.docx")
    local_salvamento = local_salvamento.replace("/", "\\") 
    logging.info(f"Transcrição será salva em: {local_salvamento}")

    try:
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"O arquivo {filepath} não foi encontrado.")

        audio_path = extrair_audio(filepath, temp_dir)

        if not audio_path:
            raise Exception(f"Erro ao extrair áudio do arquivo {filepath}")

        logging.info(f"Iniciando transcrição do arquivo: {audio_path}")

        if lista_arquivos.winfo_exists():
            lista_arquivos.after(0, lambda: lista_arquivos.set(item, 'Status', 'Em processamento...'))

        # Iniciar a transcrição em uma thread separada
        def transcrever():
            try:
                result = model.transcribe(audio_path, language="pt")
                total_segments = len(result["segments"])

                doc = Document()
                for i, segment in enumerate(result["segments"]):
                    text = segment["text"]
                    doc.add_paragraph(text)

                doc.save(local_salvamento)
                logging.info(f"Transcrição concluída e salva em: {local_salvamento}")

                if audio_path != filepath:
                    os.remove(audio_path)

                if lista_arquivos.winfo_exists():
                    lista_arquivos.after(0, lambda: lista_arquivos.set(item, 'Status', 'Finalizado'))
                    # Salvar o caminho do arquivo transcrito nos dados do item
                    lista_arquivos.item(item, values=(filepath, 'Finalizado', local_salvamento))
            except Exception as e:
                logging.error(f"Erro ao transcrever {nome_arquivo}. Motivo: {e}")
                if lista_arquivos.winfo_exists():
                    lista_arquivos.after(0, lambda: lista_arquivos.set(item, 'Status', 'Erro'))

        transcription_thread = Thread(target=transcrever)
        transcription_thread.daemon = True  # Definir a thread como daemon
        transcription_thread.start()

        # Adicionar a thread à lista global para gerenciamento
        threads.append(transcription_thread)

        # Monitorar a thread de transcrição para cancelamento
        while transcription_thread.is_alive():
            if cancelar_desgravacao:
                # Não espera a thread terminar
                return
            time.sleep(0.1)  # Evitar uso excessivo de CPU

        # Só chama join se não foi cancelado
        transcription_thread.join()

        if cancelar_desgravacao:
            # Excluir arquivo parcialmente transcrito, se existir
            if os.path.exists(local_salvamento):
                os.remove(local_salvamento)
                logging.info(f"Arquivo parcialmente transcrito excluído: {local_salvamento}")
            if lista_arquivos.winfo_exists():
                lista_arquivos.after(0, lambda: lista_arquivos.set(item, 'Status', 'Cancelado'))
            return

    except Exception as e:
        logging.error(f"Erro ao transcrever {nome_arquivo}. Motivo: {e}")
        if lista_arquivos.winfo_exists():
            lista_arquivos.after(0, lambda: lista_arquivos.set(item, 'Status', 'Erro'))

# Função para transcrever arquivos em fila
def transcrever_arquivos_em_fila(lista_arquivos, btn_iniciar, btn_adicionar):
    global cancelar_desgravacao, transcricao_em_andamento
    transcricao_em_andamento = True
    items = lista_arquivos.get_children()
    if not items:
        if btn_iniciar.winfo_exists():
            messagebox.showwarning("Aviso", "Nenhum arquivo selecionado para transcrição.")
            btn_iniciar.config(state=tk.NORMAL)
        if btn_adicionar.winfo_exists():
            btn_adicionar.config(state=tk.NORMAL)
        transcricao_em_andamento = False
        return

    # Atualizar status para 'Aguardando processamento'
    for item in items:
        if cancelar_desgravacao:
            break
        if lista_arquivos.winfo_exists():
            status_values = lista_arquivos.item(item, 'values')
            if len(status_values) > 1:
                status = status_values[1]
                if status not in ['Finalizado', 'Cancelado', 'Erro']:
                    lista_arquivos.set(item, 'Status', 'Aguardando processamento')
            else:
                continue  # Pular se os valores não estiverem completos

    for item in items:
        if cancelar_desgravacao:
            break
        if lista_arquivos.winfo_exists():
            status_values = lista_arquivos.item(item, 'values')
            if len(status_values) > 1:
                status = lista_arquivos.item(item, 'values')[1]
                if status in ['Finalizado', 'Cancelado', 'Erro']:
                    continue  # Pular arquivos já processados
                filepath = status_values[0]
                extrair_e_transcrever_arquivo(filepath, item, lista_arquivos)
            else:
                continue  # Pular se os valores não estiverem completos

    # Atualizar status para 'Cancelado' nos itens restantes
    if cancelar_desgravacao:
        for item in items:
            if lista_arquivos.winfo_exists():
                status_values = lista_arquivos.item(item, 'values')
                if len(status_values) > 1:
                    status = status_values[1]
                    if status not in ['Finalizado', 'Erro']:
                        lista_arquivos.set(item, 'Status', 'Cancelado')

    # Após o processamento de todos os arquivos ou cancelamento
    if btn_iniciar.winfo_exists():
        btn_iniciar.config(state=tk.NORMAL)
    if btn_adicionar.winfo_exists():
        btn_adicionar.config(state=tk.NORMAL)
    if cancelar_desgravacao:
        if btn_iniciar.winfo_exists():
            messagebox.showinfo("Transcrição Cancelada", "A transcrição foi cancelada pelo usuário.")
        cancelar_desgravacao = False  # Resetar para futuras transcrições
    else:
        if btn_iniciar.winfo_exists():
            messagebox.showinfo("Transcrição Concluída", "Todas as transcrições foram concluídas.")
    transcricao_em_andamento = False

# Função para iniciar a transcrição
def iniciar_transcricao(lista_arquivos, btn_iniciar, btn_adicionar):
    global cancelar_desgravacao
    cancelar_desgravacao = False
    btn_iniciar.config(state=tk.DISABLED)
    btn_adicionar.config(state=tk.DISABLED)

    thread = Thread(target=transcrever_arquivos_em_fila, args=(lista_arquivos, btn_iniciar, btn_adicionar))
    thread.daemon = True  # Definir a thread como daemon
    thread.start()

# Função para adicionar arquivos à lista
def adicionar_arquivo(lista_arquivos):
    filepaths = filedialog.askopenfilenames(
        title="Escolha os arquivos de áudio ou vídeo para transcrever",
        filetypes=[
            ("Arquivos suportados", "*.mp4;*.mp3;*.wav;*.mkv;*.aac;*.flac;*.m4a;*.ogg"),
            ("Arquivos MP4", "*.mp4"), 
            ("Arquivos MP3", "*.mp3"), 
            ("Arquivos WAV", "*.wav"), 
            ("Arquivos AAC", "*.aac"), 
            ("Arquivos FLAC", "*.flac"), 
            ("Arquivos M4A", "*.m4a"), 
            ("Arquivos OGG", "*.ogg")
        ]
    )
    for filepath in filepaths:
        # Verificar se o arquivo já está na lista
        already_exists = False
        for item in lista_arquivos.get_children():
            if lista_arquivos.item(item, 'values')[0] == filepath:
                already_exists = True
                break
        if not already_exists:
            # Adicionar o arquivo à Treeview com status 'Preparado'
            lista_arquivos.insert('', 'end', values=(filepath, 'Preparado', ''))

# Função para abrir o diretório do arquivo transcrito
def abrir_local_do_arquivo(event, lista_arquivos):
    item = lista_arquivos.identify_row(event.y)
    if item:
        status = lista_arquivos.item(item, 'values')[1]
        if status == 'Finalizado':
            # Obter o caminho do arquivo transcrito
            transcribed_file = lista_arquivos.item(item, 'values')[2]
            if os.path.exists(transcribed_file):
                diretorio = os.path.dirname(transcribed_file)
                os.startfile(diretorio)
            else:
                messagebox.showerror("Erro", "O arquivo transcrito não foi encontrado.")
        else:
            messagebox.showinfo("Informação", "O arquivo ainda não foi transcrito.")

# Função para selecionar o modelo Whisper manualmente
def selecionar_modelo():
    global janela_modelo
    if janela_modelo and janela_modelo.winfo_exists():
        janela_modelo.lift()
        return
    janela_modelo = tk.Toplevel()
    janela_modelo.title("Selecionar Modelo Whisper")
    janela_modelo.geometry("400x200")
    janela_modelo.grab_set()

    label = ttk.Label(janela_modelo, text="Selecione o modelo Whisper:")
    label.pack(pady=20)

    model_path_var_local = tk.StringVar(value=config.get('model_path', ''))

    entry = ttk.Entry(janela_modelo, textvariable=model_path_var_local, width=50)
    entry.pack(pady=10)

    def escolher_modelo():
        filepath = filedialog.askopenfilename(
            title="Selecionar Modelo Whisper", 
            filetypes=[("Modelo Whisper", "*.pt")]
        )
        if filepath:
            model_path_var_local.set(filepath)
            try:
                whisper.load_model(filepath)
                config['model_path'] = filepath
                with open(CONFIG_FILE, 'w') as f:
                    json.dump(config, f)
                model_path_var.set(filepath)
                messagebox.showinfo("Sucesso", "Modelo carregado e o caminho foi salvo com sucesso!")
                janela_modelo.destroy()
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao carregar o modelo: {e}")
                logging.info(f"Modelo inicial carregado com sucesso. {e}")

    btn_escolher = ttk.Button(janela_modelo, text="Escolher Modelo", command=escolher_modelo)
    btn_escolher.pack(pady=10)

# Função para verificar se o modelo inicial está configurado
def verificar_modelo_inicial():
    model_path = config.get('model_path')
    if model_path:
        try:
            whisper.load_model(model_path)
            logging.info("Modelo inicial carregado com sucesso.")
        except Exception as e:
            logging.error(f"Erro ao carregar o modelo inicial: {e}")
            messagebox.showerror("Erro", f"Erro ao carregar o modelo inicial: {e}")
            selecionar_qualidade()
    else:
        selecionar_qualidade()

# Função para selecionar a qualidade do modelo e baixar se necessário
def selecionar_qualidade():
    global janela_qualidade
    if janela_qualidade and janela_qualidade.winfo_exists():
        janela_qualidade.lift()
        return
    janela_qualidade = tk.Toplevel()
    janela_qualidade.title("Selecionar Qualidade")
    janela_qualidade.geometry("500x400")
    janela_qualidade.grab_set()

    label = ttk.Label(janela_qualidade, text="Escolha um dos modelos de transcrição:")
    label.pack(pady=20)

    modelos = {
        "small": "https://openaipublic.azureedge.net/main/whisper/models/9ecf779972d90ba49c06d968637d720dd632c55bbf19d441fb42bf17a411e794/small.pt",
        "medium": "https://openaipublic.azureedge.net/main/whisper/models/345ae4da62f9b3d59415adc60127b97c714f32e89e936602e85993674d08dcb1/medium.pt",
        "large-v1": "https://openaipublic.azureedge.net/main/whisper/models/e4b87e7e0bf463eb8e6956e646f1e277e901512310def2c24bf0e11bd3c28e9a/large-v1.pt",
        "large-v2": "https://openaipublic.azureedge.net/main/whisper/models/81f7c96c852ee8fc832187b0132e569d6c3065a3252ed18e56effd0b6a73e524/large-v2.pt",
        "large-v3": "https://openaipublic.azureedge.net/main/whisper/models/e5b1a55b89c1367dacf97e3e19bfd829a01529dbfdeefa8caeb59b3f1b81dadb/large-v3.pt",
        "large": "https://openaipublic.azureedge.net/main/whisper/models/e5b1a55b89c1367dacf97e3e19bfd829a01529dbfdeefa8caeb59b3f1b81dadb/large-v3.pt"
    }

    qualidade_var = tk.StringVar(value="medium")

    drop_down = ttk.OptionMenu(janela_qualidade, qualidade_var, "medium", *modelos.keys())
    drop_down.pack(pady=10)

    def baixar_modelo():
        modelo_selecionado = qualidade_var.get()
        url = modelos[modelo_selecionado]
        diretorio_modelo = resource_path(".model")
        if not os.path.exists(diretorio_modelo):
            os.makedirs(diretorio_modelo)
        caminho_modelo = os.path.join(diretorio_modelo, f"{modelo_selecionado}.pt")

        if os.path.exists(caminho_modelo):
            config['model_path'] = caminho_modelo
            with open(CONFIG_FILE, 'w') as f:
                json.dump(config, f)
            model_path_var.set(caminho_modelo)
            messagebox.showinfo("Sucesso", "Modelo selecionado com sucesso.")
            janela_qualidade.destroy()
            return

        janela_progresso = tk.Toplevel()
        janela_progresso.title("Baixando Modelo")
        janela_progresso.geometry("400x150")
        janela_progresso.resizable(False, False)
        janela_progresso.grab_set()

        progresso_var = tk.DoubleVar()
        barra_progresso = ttk.Progressbar(janela_progresso, variable=progresso_var, maximum=100)
        barra_progresso.pack(pady=20, padx=20, fill=tk.X)

        label_progresso = ttk.Label(janela_progresso, text="Baixando o modelo, por favor aguarde...")
        label_progresso.pack(pady=5)

        cancelar_download = False

        class DownloadCancelado(Exception):
            pass

        def baixar_modelo_thread():
            nonlocal cancelar_download
            try:
                with requests.get(url, stream=True) as response:
                    response.raise_for_status()
                    total_size = int(response.headers.get('content-length', 0))
                    block_size = 65536  # 64 KB
                    downloaded = 0
                    with open(caminho_modelo, 'wb') as out_file:
                        for data in response.iter_content(block_size):
                            if cancelar_download:
                                raise DownloadCancelado()
                            out_file.write(data)
                            downloaded += len(data)
                            percent = downloaded * 100 / total_size
                            progresso_var.set(percent)
                            label_progresso.config(text=f"Baixando... {percent:.2f}%")
                if cancelar_download:
                    if os.path.exists(caminho_modelo):
                        os.remove(caminho_modelo)
                    return
                config['model_path'] = caminho_modelo
                with open(CONFIG_FILE, 'w') as f:
                    json.dump(config, f)
                model_path_var.set(caminho_modelo)
                messagebox.showinfo("Sucesso", "Modelo baixado e o caminho foi salvo com sucesso!")
                janela_progresso.destroy()
                janela_qualidade.destroy()
            except DownloadCancelado:
                if os.path.exists(caminho_modelo):
                    os.remove(caminho_modelo)
                messagebox.showinfo("Download Cancelado", "O download foi cancelado.")
                janela_progresso.destroy()
            except Exception as e:
                if not cancelar_download:
                    messagebox.showerror("Erro", f"Erro ao baixar o modelo: {e}")
                if os.path.exists(caminho_modelo):
                    os.remove(caminho_modelo)
                janela_progresso.destroy()

        def cancelar_download_fn():
            nonlocal cancelar_download
            cancelar_download = True
            janela_progresso.destroy()

        # Adicionando o protocolo para fechar a janela de download
        janela_progresso.protocol("WM_DELETE_WINDOW", cancelar_download_fn)

        btn_cancelar = ttk.Button(janela_progresso, text="Cancelar Download", command=cancelar_download_fn)
        btn_cancelar.pack(pady=10)

        download_thread = Thread(target=baixar_modelo_thread)
        download_thread.daemon = True  # Assegura que a thread não impeça o fechamento da aplicação
        download_thread.start()

    btn_baixar = ttk.Button(janela_qualidade, text="Selecionar Modelo", command=baixar_modelo)
    btn_baixar.pack(pady=10)

# Função para fechar a aplicação
def on_closing():
    global cancelar_desgravacao
    cancelar_desgravacao = True
    stop_event.set()
    # Não espera as threads terminarem
    root.destroy()

# Configurar o logger antes de iniciar a GUI
configurar_logger()

# Configuração da janela principal
root = tk.Tk()
root.title("TextifyVoice [ 1.0 ] by@felipe.sh")

root.geometry("650x500")

# Verifique se o caminho do ícone está correto
if os.path.exists(ICON_PATH):
    root.iconbitmap(ICON_PATH)
else:
    logging.error(f"Ícone não encontrado em: {ICON_PATH}")

cor_fundo = "#343a40"
root.configure(bg=cor_fundo)

# Configuração de estilos
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

# Frame do título
title_frame = ttk.Frame(root, style="TFrame", height=70)
title_frame.pack(side=tk.TOP, fill=tk.X)
title_frame.pack_propagate(False)

titulo = ttk.Label(title_frame, text="TextifyVoice", style="Title.TLabel", anchor="center")
titulo.pack(side=tk.TOP, fill=tk.X, pady=20)

# Frame principal
frame = ttk.Frame(root, style="TFrame")
frame.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)

# Label de instrução
text_var = tk.StringVar()
text_var.set("Selecione os arquivos de áudio ou vídeo para transcrever.")
text_label = ttk.Label(frame, textvariable=text_var, wraplength=650, style="TLabel")
text_label.pack()

# Variável para o caminho do modelo
model_path = config.get('model_path')
model_path_var = tk.StringVar(value=model_path)

# Botões de seleção
btn_select = ttk.Button(frame, text="Selecionar Arquivos", style="TButton")
btn_qualidade = ttk.Button(frame, text="Selecionar Qualidade", command=selecionar_qualidade, style="Modelo.TButton")

btn_select.config(command=lambda: abrir_janela_selecao_arquivos())
btn_select.pack(pady=(10, 0))
btn_qualidade.pack(pady=(10, 0))

# Protocolo para fechar a aplicação
root.protocol("WM_DELETE_WINDOW", on_closing)

# Verificar o modelo inicial após iniciar a GUI
root.after(10, verificar_modelo_inicial)

# Função para abrir a janela de seleção de arquivos
def abrir_janela_selecao_arquivos():
    global janela_selecao, transcricao_em_andamento, confirm_dialog_open, cancelar_desgravacao
    if janela_selecao and janela_selecao.winfo_exists():
        janela_selecao.lift()
        return
    transcricao_em_andamento = False
    cancelar_desgravacao = False
    janela_selecao = tk.Toplevel()
    janela_selecao.title("Seleção de Arquivos")
    janela_selecao.geometry("700x400")
    janela_selecao.grab_set()
    janela_selecao.configure(bg=cor_fundo)  # Ajustar a cor de fundo da janela

    # Atualizar estilos para a janela de seleção
    style.configure("Selecao.TFrame", background=cor_fundo)
    style.configure("Selecao.TButton", background=cor_acento, foreground=cor_frente, font=("Arial", 10, "bold"), borderwidth=1, relief="flat")
    style.configure("Selecao.TLabel", background=cor_fundo, foreground=cor_frente, font=("Arial", 12))

    # Botão 'Adicionar Arquivo'
    btn_adicionar = ttk.Button(janela_selecao, text="Adicionar Arquivo", style="Selecao.TButton")
    btn_adicionar.pack(pady=10)

    # Treeview para mostrar arquivos e status
    colunas = ('Arquivo', 'Status', 'Transcrito')
    lista_arquivos = ttk.Treeview(janela_selecao, columns=colunas, show='headings')
    lista_arquivos.heading('Arquivo', text='Arquivo')
    lista_arquivos.heading('Status', text='Status')
    # Coluna oculta para armazenar o caminho do arquivo transcrito
    lista_arquivos.heading('Transcrito', text='', anchor='w')
    lista_arquivos.column('Arquivo', width=400)
    lista_arquivos.column('Status', width=150)
    lista_arquivos.column('Transcrito', width=0, stretch=False)
    lista_arquivos.pack(expand=True, fill='both')

    # Evento de duplo clique para abrir o local do arquivo
    lista_arquivos.bind("<Double-1>", lambda event: abrir_local_do_arquivo(event, lista_arquivos))

    # Botões de controle
    frame_botoes = ttk.Frame(janela_selecao, style="Selecao.TFrame")
    frame_botoes.pack(pady=10)

    btn_iniciar = ttk.Button(frame_botoes, text="Iniciar Transcrição", style="Selecao.TButton")
    btn_cancelar = ttk.Button(frame_botoes, text="Cancelar", style="Selecao.TButton")
    btn_iniciar.pack(side=tk.LEFT, padx=5)
    btn_cancelar.pack(side=tk.LEFT, padx=5)

    def cancelar_transcricao():
        global cancelar_desgravacao, transcricao_em_andamento, confirm_dialog_open
        if confirm_dialog_open:
            return  # Se o diálogo já está aberto, não faz nada
        confirm_dialog_open = True
        resposta = messagebox.askyesno("Confirmar", "Você realmente deseja fechar a janela? A transcrição será cancelada se estiver em andamento.")
        confirm_dialog_open = False
        if resposta:
            if transcricao_em_andamento:
                cancelar_desgravacao = True
                # Não espera as threads terminarem
            janela_selecao.destroy()

    # Configurar comandos
    btn_adicionar.config(command=lambda: adicionar_arquivo(lista_arquivos))
    btn_iniciar.config(command=lambda: iniciar_transcricao(lista_arquivos, btn_iniciar, btn_adicionar))
    btn_cancelar.config(command=cancelar_transcricao)

    # Adicionando o protocolo para fechar a janela de transcrição
    janela_selecao.protocol("WM_DELETE_WINDOW", cancelar_transcricao)

    # Evento para minimizar a janela principal quando a janela de seleção for minimizada
    def on_iconify(event):
        if janela_selecao.state() == 'iconic':
            root.iconify()
        elif janela_selecao.state() == 'normal':
            root.deiconify()
    janela_selecao.bind("<Unmap>", on_iconify)
    janela_selecao.bind("<Map>", on_iconify)

# Iniciar a interface gráfica
root.mainloop()
