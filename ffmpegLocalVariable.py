import logging
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from threading import Thread, Event
from logging.handlers import RotatingFileHandler
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
import time  # Import necessário para pausas

warnings.filterwarnings("ignore", category=FutureWarning, message="FP16 is not supported on CPU; using FP32 instead")
warnings.filterwarnings("ignore", category=UserWarning, message="FP16 is not supported on CPU; using FP32 instead")

CONFIG_FILE = "config.json"
DEFAULT_CONFIG = {
    "model_path": "",
    "language": "pt"
}

if not os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(DEFAULT_CONFIG, f, indent=4)
    logging.info(f"Arquivo de configuração criado: {CONFIG_FILE}")

# Variáveis Globais
config = {}
cancelar_desgravacao = False
threads = []
stop_event = Event()
try:
    with open(CONFIG_FILE, 'r') as f:
        config = json.load(f)
except FileNotFoundError:
    pass

def configurar_logger():
    if not os.path.exists("logs"):
        os.makedirs("logs")
    
    log_handler = RotatingFileHandler('logs/info.log', maxBytes=5*1024*1024, backupCount=5)
    log_handler.setLevel(logging.INFO)
    log_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(log_handler)

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

def extrair_e_transcrever_arquivo(filepath, item, lista_arquivos):
    global cancelar_desgravacao

    if cancelar_desgravacao:
        return

    try:
        model_path = config.get('model_path')
        logging.info(f"Tentando carregar o modelo do caminho: {model_path}")
        model = whisper.load_model(model_path)
        if model:
            logging.info(f"Modelo de transcrição carregado com sucesso")
    except Exception as e:
        logging.error(f"Erro ao carregar o modelo de transcrição: {e}")
        lista_arquivos.after(0, lambda: lista_arquivos.set(item, 'Status', 'Erro no modelo'))
        return

    temp_dir = "./temp"
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

        lista_arquivos.after(0, lambda: lista_arquivos.set(item, 'Status', 'Em processo...'))

        # Iniciar a transcrição em uma thread separada para permitir o cancelamento
        transcription_result = [None]
        transcription_thread = Thread(target=lambda: transcription_result.__setitem__(0, model.transcribe(audio_path, language="pt")))
        transcription_thread.start()

        # Monitorar a thread de transcrição para cancelamento
        while transcription_thread.is_alive():
            if cancelar_desgravacao:
                # O cancelamento será efetivo após o término da transcrição atual
                break
            time.sleep(0.1)  # Evitar uso excessivo de CPU

        transcription_thread.join()

        if cancelar_desgravacao:
            # Excluir arquivo parcialmente transcrito, se existir
            if os.path.exists(local_salvamento):
                os.remove(local_salvamento)
                logging.info(f"Arquivo parcialmente transcrito excluído: {local_salvamento}")
            lista_arquivos.after(0, lambda: lista_arquivos.set(item, 'Status', 'Cancelado'))
            return

        result = transcription_result[0]
        total_segments = len(result["segments"])

        doc = Document()
        for i, segment in enumerate(result["segments"]):
            text = segment["text"]
            doc.add_paragraph(text)

        doc.save(local_salvamento)
        logging.info(f"Transcrição concluída salva em: {local_salvamento}")

        if audio_path != filepath:
            os.remove(audio_path)

        lista_arquivos.after(0, lambda: lista_arquivos.set(item, 'Status', 'Finalizado'))
        # Salvar o caminho do arquivo transcrito nos dados do item
        lista_arquivos.item(item, values=(filepath, 'Finalizado', local_salvamento))

    except Exception as e:
        logging.error(f"Erro ao transcrever {nome_arquivo}. Motivo: {e}")
        lista_arquivos.after(0, lambda: lista_arquivos.set(item, 'Status', 'Erro'))

def transcrever_arquivos_em_fila(lista_arquivos, btn_iniciar, btn_adicionar):
    global cancelar_desgravacao
    items = lista_arquivos.get_children()
    if not items:
        messagebox.showwarning("Aviso", "Nenhum arquivo selecionado para transcrição.")
        btn_iniciar.config(state=tk.NORMAL)
        btn_adicionar.config(state=tk.NORMAL)
        return

    # Atualizar status para 'Aguardando Processo'
    for item in items:
        status = lista_arquivos.item(item, 'values')[1]
        if status not in ['Finalizado', 'Cancelado', 'Erro']:
            lista_arquivos.set(item, 'Status', 'Aguardando Processo')

    for item in items:
        if cancelar_desgravacao:
            break
        status = lista_arquivos.item(item, 'values')[1]
        if status in ['Finalizado', 'Cancelado', 'Erro']:
            continue  # Pular arquivos já processados
        filepath = lista_arquivos.item(item, 'values')[0]
        extrair_e_transcrever_arquivo(filepath, item, lista_arquivos)

    # Atualizar status para 'Cancelado' nos itens restantes
    if cancelar_desgravacao:
        for item in items:
            status = lista_arquivos.item(item, 'values')[1]
            if status not in ['Finalizado', 'Erro']:
                lista_arquivos.set(item, 'Status', 'Cancelado')

    # Após o processamento de todos os arquivos ou cancelamento
    btn_iniciar.config(state=tk.NORMAL)
    btn_adicionar.config(state=tk.NORMAL)
    if cancelar_desgravacao:
        messagebox.showinfo("Transcrição Cancelada", "A transcrição foi cancelada pelo usuário.")
        cancelar_desgravacao = False  # Resetar para futuras transcrições
    else:
        messagebox.showinfo("Transcrição Concluída", "Todas as transcrições foram concluídas.")

def iniciar_transcricao(lista_arquivos, btn_iniciar, btn_adicionar):
    global cancelar_desgravacao
    cancelar_desgravacao = False
    btn_iniciar.config(state=tk.DISABLED)
    btn_adicionar.config(state=tk.DISABLED)

    thread = Thread(target=transcrever_arquivos_em_fila, args=(lista_arquivos, btn_iniciar, btn_adicionar))
    thread.start()

def adicionar_arquivo(lista_arquivos):
    filepaths = filedialog.askopenfilenames(title="Escolher os vídeos que serão transcritos para texto",
                                            filetypes=[("Arquivos Selecionáveis", "*.mp4;*.mp3;*.wav;*.mkv"),
                                                       ("MP4 files", "*.mp4",), ("MP3 files", "*.mp3"), ("WAV files", "*.wav")])
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
                messagebox.showerror("Erro", "Arquivo transcrito não encontrado.")
        else:
            messagebox.showinfo("Informação", "O arquivo ainda não foi transcrito.")

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
            selecionar_qualidade()
    else:
        selecionar_qualidade()

def selecionar_qualidade():
    janela_qualidade = tk.Toplevel()
    janela_qualidade.title("Selecionar Qualidade")
    janela_qualidade.geometry("500x400")
    janela_qualidade.grab_set()

    label = ttk.Label(janela_qualidade, text="Escolha um dos modelos de transcrição:")
    label.pack(pady=20)

    modelos = {
        "small":"https://openaipublic.azureedge.net/main/whisper/models/9ecf779972d90ba49c06d968637d720dd632c55bbf19d441fb42bf17a411e794/small.pt",
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
        diretorio_modelo = ".model/"
        if not os.path.exists(diretorio_modelo):
            os.makedirs(diretorio_modelo)
        caminho_modelo = os.path.join(diretorio_modelo, f"{modelo_selecionado}.pt")

        if os.path.exists(caminho_modelo):
            config['model_path'] = caminho_modelo
            with open(CONFIG_FILE, 'w') as f:
                json.dump(config, f)
            model_path_var.set(caminho_modelo)
            messagebox.showinfo("Modelo Status", "Modelo Selecionado.")
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

        label_progresso = ttk.Label(janela_progresso, text="Aguardando o download ser finalizado...")
        label_progresso.pack(pady=5)

        cancelar_download = False

        class DownloadCancelado(Exception):
            pass

        def hook(t):
            last_b = [0]

            def inner(b=1, bsize=1, tsize=None):
                if cancelar_download:
                    raise DownloadCancelado()
                if tsize is not None:
                    t.total = tsize
                t.update((b - last_b[0]) * bsize)
                last_b[0] = b
                progresso_var.set(t.n / t.total * 100)

            return inner

        def baixar_modelo_thread():
            nonlocal cancelar_download
            try:
                with tqdm.tqdm(unit='B', unit_scale=True, unit_divisor=1024, miniters=1, desc=f"Downloading {modelo_selecionado}.pt") as t:
                    urllib.request.urlretrieve(url, caminho_modelo, reporthook=hook(t))
                    if cancelar_download:
                        os.remove(caminho_modelo)
                        return

                config['model_path'] = caminho_modelo
                with open(CONFIG_FILE, 'w') as f:
                    json.dump(config, f)
                model_path_var.set(caminho_modelo)
                messagebox.showinfo("Sucesso", "Modelo baixado e caminho salvo com sucesso!")
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
                janela_progresso.destroy()

        def cancelar_download_fn():
            nonlocal cancelar_download
            cancelar_download = True
            janela_progresso.destroy()

        btn_cancelar = ttk.Button(janela_progresso, text="Cancelar Download", command=cancelar_download_fn)
        btn_cancelar.pack(pady=10)

        Thread(target=baixar_modelo_thread).start()

    btn_baixar = ttk.Button(janela_qualidade, text="Selecionar Modelo", command=baixar_modelo)
    btn_baixar.pack(pady=10)

def on_closing():
    global cancelar_desgravacao
    cancelar_desgravacao = True
    stop_event.set()
    for thread in threads:
        thread.join()
    root.destroy()

configurar_logger()

root = tk.Tk()
root.title("TextifyVoice [ Beta ] by@felipe.sh")

root.geometry("650x500")

# Se tiver um ícone, descomente a linha abaixo e ajuste o caminho
# root.iconbitmap('./bin/icon.ico')

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
text_label = ttk.Label(frame, textvariable=text_var, wraplength=650, style="TLabel")
text_label.pack()

model_path = config.get('model_path')
model_path_var = tk.StringVar(value=model_path)

btn_abrir = ttk.Button(frame, text="Abrir Pasta de Documentos Transcritos", state=tk.DISABLED, style="TButton")
btn_select = ttk.Button(frame, text="Selecionar Arquivos", style="TButton")
btn_qualidade = ttk.Button(frame, text="Selecionar Qualidade", command=selecionar_qualidade, style="Modelo.TButton")

btn_select.config(command=lambda: abrir_janela_selecao_arquivos())
btn_select.pack(pady=(10, 0))
btn_abrir.pack(pady=(10, 20))
btn_qualidade.pack(pady=(10, 0))

root.protocol("WM_DELETE_WINDOW", on_closing)

root.after(10, verificar_modelo_inicial)

def abrir_janela_selecao_arquivos():
    janela_selecao = tk.Toplevel()
    janela_selecao.title("Seleção de Arquivos")
    janela_selecao.geometry("700x400")
    janela_selecao.grab_set()

    # Botão 'Adicionar Arquivo'
    btn_adicionar = ttk.Button(janela_selecao, text="Adicionar Arquivo")
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
    frame_botoes = ttk.Frame(janela_selecao)
    frame_botoes.pack(pady=10)

    btn_iniciar = ttk.Button(frame_botoes, text="Iniciar Transcrição")
    btn_cancelar = ttk.Button(frame_botoes, text="Cancelar Transcrição")
    btn_iniciar.pack(side=tk.LEFT, padx=5)
    btn_cancelar.pack(side=tk.LEFT, padx=5)

    # Função cancelar_transcricao dentro de abrir_janela_selecao_arquivos
    def cancelar_transcricao():
        global cancelar_desgravacao
        resposta = messagebox.askyesno("Cancelar Transcrição", "Os arquivos já transcritos não serão apagados, mas a transcrição dos arquivos restantes será cancelada. Deseja confirmar o cancelamento?")
        if resposta:
            cancelar_desgravacao = True
            janela_selecao.destroy()  # Fecha a janela de seleção de arquivos

    # Configurar comandos
    btn_adicionar.config(command=lambda: adicionar_arquivo(lista_arquivos))
    btn_iniciar.config(command=lambda: iniciar_transcricao(lista_arquivos, btn_iniciar, btn_adicionar))
    btn_cancelar.config(command=cancelar_transcricao)

    # Evento para minimizar a janela principal quando a janela de seleção for minimizada
    def on_iconify(event):
        if janela_selecao.state() == 'iconic':
            root.iconify()
        elif janela_selecao.state() == 'normal':
            root.deiconify()
    janela_selecao.bind("<Unmap>", on_iconify)
    janela_selecao.bind("<Map>", on_iconify)

root.mainloop()
