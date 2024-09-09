import tkinter as tk
from tkinter import ttk
from config import load_config  
from transcribe import select_transcription_quality
from fileIO import start_process
config = load_config()

# Define colors and styles


def create_gui(root):

  root.title("TextifyVoice [ Beta ] by@felipe.sh")
  cor_fundo = "#343a40"
  cor_frente = "#f8f9fa"
  cor_acento = "#007bff"
  cor_modelo = "#28a745"
  
  style = ttk.Style()
  style.theme_use('clam')
  
  style.configure("TFrame", background=cor_fundo)
  style.configure("TButton", background=cor_acento, foreground=cor_frente, font=("Arial", 10, "bold"), borderwidth=1, relief="flat")
  style.configure("Modelo.TButton", background=cor_modelo, foreground=cor_frente, font=("Arial", 10, "bold"), borderwidth=1, relief="flat")
  style.configure("TLabel", background=cor_fundo, foreground=cor_frente, font=("Arial", 12))
  style.configure("Title.TLabel", background=cor_fundo, foreground=cor_frente, font=("Arial", 16, "bold"))
  
  style.map("TButton", relief=[("pressed", "sunken"), ("active", "raised")])
  style.map("Modelo.TButton", relief=[("pressed", "sunken"), ("active", "raised")])

  root.geometry("650x500")
  root.iconbitmap('./bin/icon.ico')
  
  # Title Frame
  title_frame = ttk.Frame(root, style="TFrame", height=70)
  title_frame.pack(side=tk.TOP, fill=tk.X)
  title_frame.pack_propagate(False)

  titulo = ttk.Label(title_frame, text="Transcritor de Vídeo", style="Title.TLabel", anchor="center")
  titulo.pack(side=tk.TOP, fill=tk.X, pady=20)

  # Main Frame
  frame = ttk.Frame(root, style="TFrame")
  frame.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)

  # Text Label
  text_var = tk.StringVar()
  text_var.set("Selecione os arquivos MP4 para transcrever.")
  text_label = ttk.Label(frame, textvariable=text_var, wraplength=650, style="TLabel")
  text_label.pack()

  # Model Path (assuming it's retrieved from config)
  model_path = config.get('model_path')
  model_path_var = tk.StringVar(value=model_path)

  # Buttons
  btn_abrir = ttk.Button(frame, text="Abrir Pasta de Documentos Transcritos", state=tk.DISABLED, style="TButton")
  btn_select = ttk.Button(frame, text="Selecionar Arquivos", style="TButton")
  btn_qualidade = ttk.Button(frame, text="Selecionar Qualidade", command=select_transcription_quality, style="Modelo.TButton")

  btn_select.config(command=lambda: start_process(btn_abrir, btn_select, btn_qualidade))

  btn_select.pack(pady=(10, 0))
  btn_abrir.pack(pady=(10, 20))
  btn_qualidade.pack(pady=(10, 0))
  
  

