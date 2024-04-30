import tkinter as tk
from tkinter import filedialog, ttk
import subprocess
import whisper
from threading import Thread
import warnings
import os
from docx import Document
import webbrowser

warnings.filterwarnings("ignore", message="FP16 is not supported on CPU; using FP32 instead")

# Variável global para controle de cancelamento
cancelar_desgravacao = False

def extrair_e_transcrever(filepath, local_salvamento, text_var, btn_abrir, btn_select):
    global cancelar_desgravacao
    if not filepath or not local_salvamento:
        text_var.set("Operação cancelada.")
        return

    arquivoTemporarioAudio = "saida_audio.aac"
    comando_ffmpeg = ["ffmpeg", "-i", filepath, "-vn", "-ar", "16000", "-ac", "1", "-ab", "32k", arquivoTemporarioAudio]
    subprocess.run(comando_ffmpeg, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    text_var.set("Desgravando... ⏳ Por favor, aguarde.")

    model = whisper.load_model("medium")
    # Simulação de verificação de cancelamento (a implementação real dependeria da tarefa específica)
    if cancelar_desgravacao:
        text_var.set("Desgravação cancelada. Selecione um arquivo para começar.")
        btn_select.config(text="Selecionar Arquivo e Local de Salvamento", command=lambda: iniciar_processo(btn_abrir, btn_select))
        cancelar_desgravacao = False
        return

    result = model.transcribe(arquivoTemporarioAudio)

    doc = Document()
    doc.add_paragraph(result["text"])
    doc.save(local_salvamento)

    text_var.set(f"Transcrição concluída. Documento salvo com sucesso em: {local_salvamento}")
    btn_abrir.config(command=lambda: webbrowser.open(local_salvamento), state=tk.NORMAL)
    btn_select.config(text="Selecionar Arquivo e Local de Salvamento", command=lambda: iniciar_processo(btn_abrir, btn_select))

    os.remove(arquivoTemporarioAudio)

def iniciar_transcricao_thread(filepath, local_salvamento, text_var, btn_abrir, btn_select):
    Thread(target=lambda: extrair_e_transcrever(filepath, local_salvamento, text_var, btn_abrir, btn_select)).start()

def selecionar_arquivo_e_salvar(text_var, btn_select, btn_abrir):
    global cancelar_desgravacao
    filepath = filedialog.askopenfilename(title="Escolher o vídeo que será transcrito para texto", filetypes=[("MP4 files", "*.mp4"), ("MP3 files", "*.mp3")])
    if not filepath:
        text_var.set("Seleção de arquivo cancelada. Operação interrompida.")
        return None, None

    # Extrai apenas o nome do arquivo do caminho completo
    nome_arquivo = os.path.basename(filepath)
    # Opcional: Remove a extensão do arquivo para obter apenas o título
    titulo_video = os.path.splitext(nome_arquivo)[0]

    nome_base_arquivo = titulo_video + "_desgravação.docx"
    diretorio_padrao = os.path.dirname(filepath)
    local_salvamento = filedialog.asksaveasfilename(
        title="Salvar desgravação em:",
        initialdir=diretorio_padrao,
        initialfile=nome_base_arquivo,
        defaultextension=".docx",
        filetypes=[("Documentos Word", "*.docx")]
    )
    if not local_salvamento:
        text_var.set("Seleção de local de salvamento cancelada. Operação interrompida.")
        return None, None

    # Atualiza o texto para mostrar apenas o título do vídeo
    text_var.set(f"Arquivo selecionado: {titulo_video}\n\nSalvar em: {local_salvamento}")
    btn_select.config(text="Cancelar desgravação", command=lambda: cancelar_desgravacao_fn(btn_select))
    btn_abrir.config(state=tk.DISABLED)  # Desabilita o botão até a transcrição ser concluída
    return filepath, local_salvamento

def cancelar_desgravacao_fn(btn_select):
    global cancelar_desgravacao
    cancelar_desgravacao = True
    btn_select.config(text="Selecionar Arquivo e Local de Salvamento", command=lambda: iniciar_processo(btn_abrir, btn_select))
    text_var.set("Cancelamento em processo...")

root = tk.Tk()
root.title("Transcritor de Áudio Profissional")

# Definindo a resolução inicial da janela
root.geometry("600x400")

# Configurando o estilo
style = ttk.Style()
style.configure("TFrame", background="#f0f0f0")
style.configure("TButton", background="#0078D7", foreground="black", font=("Arial", 10))
style.configure("TLabel", background="#f0f0f0", foreground="black", font=("Arial", 12))
style.configure("Title.TLabel", background="black", foreground="white", font=("Arial", 16, "bold"))

# Frame do título com altura aumentada
title_frame = ttk.Frame(root, style="TFrame", height=60)  # Altura aumentada para 60
title_frame.pack(side=tk.TOP, fill=tk.X)
title_frame.pack_propagate(False)

# Título
titulo = ttk.Label(title_frame, text="Transcritor de Áudio", style="Title.TLabel", anchor="center")
titulo.pack(side=tk.TOP, fill=tk.X)

# Frame principal
frame = ttk.Frame(root, style="TFrame")
frame.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)

# Texto de status
text_var = tk.StringVar()
text_var.set("Clique no botão abaixo para iniciar.")
text_label = ttk.Label(frame, textvariable=text_var, wraplength=550, style="TLabel")
text_label.pack()

btn_abrir = ttk.Button(frame, text="Abrir Documento Transcrito", state=tk.DISABLED, style="TButton")
btn_abrir.pack(pady=10)
btn_abrir.pack_forget()  # Inicialmente, o botão fica invisível

btn_select = ttk.Button(frame, text="Selecionar Arquivo e Local de Salvamento", style="TButton")
btn_select.pack(pady=10)

def iniciar_processo(btn_abrir, btn_select):
    filepath, local_salvamento = selecionar_arquivo_e_salvar(text_var, btn_select, btn_abrir)
    if filepath and local_salvamento:
        iniciar_transcricao_thread(filepath, local_salvamento, text_var, btn_abrir, btn_select)
        btn_abrir.pack(pady=10)  # Torna o botão visível após iniciar a transcrição

btn_select.config(command=lambda: iniciar_processo(btn_abrir, btn_select))

root.mainloop()