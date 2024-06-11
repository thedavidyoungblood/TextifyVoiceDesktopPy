import tkinter as tk
from tkinter import filedialog, ttk
import subprocess
import os
from threading import Thread

def criar_pasta_saida():
    if not os.path.exists("saida"):
        os.makedirs("saida")

def converter_mp4_para_mp3(filepaths, text_var, btn_select):
    criar_pasta_saida()
    for filepath in filepaths:
        nome_arquivo = os.path.splitext(os.path.basename(filepath))[0]
        arquivo_saida = os.path.join("saida", nome_arquivo + ".mp3")

        text_var.set(f"Convertendo: {nome_arquivo} ⏳ Por favor, aguarde.")
        
        comando_ffmpeg = ["ffmpeg", "-i", filepath, "-vn", "-acodec", "libmp3lame", arquivo_saida]
        subprocess.run(comando_ffmpeg, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
    text_var.set("Todas as conversões foram concluídas.")
    btn_select.config(state=tk.NORMAL)

def iniciar_conversao_thread(filepaths, text_var, btn_select):
    Thread(target=lambda: converter_mp4_para_mp3(filepaths, text_var, btn_select)).start()

def selecionar_arquivos(text_var, btn_select):
    filepaths = filedialog.askopenfilenames(title="Escolher os arquivos MP4 para converter", filetypes=[("MP4 files", "*.mp4")])
    if not filepaths:
        text_var.set("Seleção de arquivo cancelada. Operação interrompida.")
        return None

    text_var.set(f"{len(filepaths)} arquivo(s) selecionado(s) para conversão.")
    btn_select.config(state=tk.DISABLED)
    iniciar_conversao_thread(filepaths, text_var, btn_select)

root = tk.Tk()
root.title("Conversor MP4 para MP3")

root.geometry("650x450")

# Definição das cores e estilos
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

titulo = ttk.Label(title_frame, text="Conversor MP4 para MP3", style="Title.TLabel", anchor="center")
titulo.pack(side=tk.TOP, fill=tk.X)

frame = ttk.Frame(root, style="TFrame")
frame.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)

text_var = tk.StringVar()
text_var.set("Selecione os arquivos MP4 para converter para MP3.")
text_label = ttk.Label(frame, textvariable=text_var, wraplength=550, style="TLabel")
text_label.pack()

btn_select = ttk.Button(frame, text="Selecionar Arquivos MP4", style="TButton", command=lambda: selecionar_arquivos(text_var, btn_select))
btn_select.pack(pady=(10, 0))

root.mainloop()
