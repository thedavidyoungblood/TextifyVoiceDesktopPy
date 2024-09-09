import tkinter as tk
from tkinter import ttk, messagebox
import os
import json
import tqdm
import urllib.request
from threading import Thread
from config import load_config
from config import CONFIG_FILE

config = load_config()


def select_transcription_quality():
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
            #model_path_var.set(caminho_modelo)
            messagebox.showinfo("Modelo já existe", "O modelo já foi baixado anteriormente.")
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
                config.model_path.set(caminho_modelo)
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

    def selecionar_modelo_local():
        selecionar_modelo()


def extract_transcribe(filepaths, text_var, btn_abrir, btn_select, btn_qualidade, model_path):
    global cancelar_desgravacao

    try:
        logging.info(f"Tentando carregar o modelo do caminho: {model_path}")
        model = whisper.load_model(model_path)
        if model:
            logging.info(f"Modelo de transcrição carregado com sucesso")
    except Exception as e:
        logging.error(f"Erro ao carregar o modelo de transcrição: {e}")
        text_var.set(f"Erro ao carregar o modelo. Verifique o caminho.")
        return

    temp_dir = "./temp"
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
        logging.info(f"Diretório temporário criado: {temp_dir}")

    for filepath in filepaths:
        filepath = filepath.replace("/", "\\") 
        logging.info(f"Analisando arquivo: {filepath}")
        text_var.set("Processando arquivos...")

        if cancelar_desgravacao or stop_event.is_set():
            text_var.set("Desgravação cancelada. Selecione arquivos para começar.")
            btn_select.config(text="Selecionar Arquivos",
                              command=lambda: iniciar_processo(btn_abrir, btn_select, btn_qualidade))
            btn_qualidade.config(state=tk.NORMAL)
            cancelar_desgravacao = False
            logging.info("Desgravação cancelada pelo usuário.")
            return

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

            text_var.set(f"Desgravando: {nome_arquivo} ⏳ Por favor, aguarde.")
            logging.info(f"Iniciando transcrição do arquivo: {audio_path}")

            result = model.transcribe(audio_path, language="pt")

            total_segments = len(result["segments"])

            doc = Document()
            for i, segment in enumerate(result["segments"]):
                text = segment["text"]
                doc.add_paragraph(text)

            doc.save(local_salvamento)
            logging.info(f"Transcrição concluída salva em: {local_salvamento}")

            if audio_path != filepath:
                os.remove(audio_path)

        except FileNotFoundError as fnf_error:
            logging.error(f"Erro ao transcrever (fnf_error) {nome_arquivo}. Motivo: {fnf_error}")
            cancelar_desgravacao = True
            text_var.set(f"Erro no desgravando {nome_arquivo}.")
            btn_select.config(text="Selecionar Arquivos para transcrição",
                              command=lambda: iniciar_processo(btn_abrir, btn_select, btn_qualidade))
            btn_qualidade.config(state=tk.NORMAL)
            notification.notify(
                title="Erro na Transcrição",
                message=f"O arquivo {filepath} não foi encontrado.",
                timeout=10
            )
            winsound.MessageBeep(winsound.MB_ICONHAND)
            return

        except PermissionError as perm_error:
            logging.error(f"Erro ao transcrever (PermissionError) {nome_arquivo}. Motivo: {perm_error}")
            cancelar_desgravacao = True
            text_var.set(f"Erro no desgravando {nome_arquivo}.")
            btn_select.config(text="Selecionar Arquivos para transcrição",
                              command=lambda: iniciar_processo(btn_abrir, btn_select, btn_qualidade))
            btn_qualidade.config(state=tk.NORMAL)
            notification.notify(
                title="Erro na Transcrição",
                message=f"Permissão negada para acessar o arquivo {filepath}.",
                timeout=10
            )
            winsound.MessageBeep(winsound.MB_ICONHAND)
            return

        except ValueError as val_error:
            logging.error(f"Erro ao transcrever (val_error) {nome_arquivo}. Motivo: {val_error}")
            cancelar_desgravacao = True
            text_var.set(f"Erro no desgravando {nome_arquivo}.")
            btn_select.config(text="Selecionar Arquivos para transcrição",
                              command=lambda: iniciar_processo(btn_abrir, btn_select, btn_qualidade))
            btn_qualidade.config(state=tk.NORMAL)
            notification.notify(
                title="Erro na Transcrição",
                message=f"O arquivo {filepath} não contém uma faixa de áudio.",
                timeout=10
            )
            winsound.MessageBeep(winsound.MB_ICONHAND)
            return

        except Exception as e:
            logging.error(f"Erro ao transcrever (Generic) {nome_arquivo}. Motivo: {e}")
            cancelar_desgravacao = True
            text_var.set(f"Erro no desgravando {nome_arquivo}.")
            btn_select.config(text="Selecionar Arquivos para transcrição",
                              command=lambda: iniciar_processo(btn_abrir, btn_select, btn_qualidade))
            btn_qualidade.config(state=tk.NORMAL)
            notification.notify(
                title="Erro na Transcrição",
                message=f"Ocorreu um erro ao transcrever {nome_arquivo}.",
                timeout=10
            )
            winsound.MessageBeep(winsound.MB_ICONHAND)
            return

    text_var.set("Todas as transcrições foram concluídas.")
    btn_select.config(text="Selecionar Arquivos",
                      command=lambda: iniciar_processo(btn_abrir, btn_select, btn_qualidade))
    btn_abrir.config(state=tk.NORMAL, command=lambda: abrir_local_salvamento(filepaths))
    btn_qualidade.config(state=tk.NORMAL)

    logging.info("Todas as transcrições foram concluídas com sucesso.")
    notification.notify(
        title="Transcrição Concluída",
        message="Todas as transcrições foram concluídas com sucesso.",
        timeout=10
    )
    winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
