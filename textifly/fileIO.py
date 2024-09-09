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
    btn_select.config(text="Cancelar desgravação", command=lambda: cancel_transcript(btn_select, btn_qualidade))
    btn_abrir.config(state=tk.DISABLED)
    btn_qualidade.config(state=tk.DISABLED)
    logging.info(f"{len(filepaths)} arquivo(s) selecionado(s) para transcrição.")
    return filepaths


def cancel_transcript(btn_select, btn_qualidade):
    global cancelar_desgravacao
    cancelar_desgravacao = True
    btn_select.config(text="Selecionar Arquivos", command=lambda: start_process(btn_abrir, btn_select, btn_qualidade))
    btn_qualidade.config(state=tk.NORMAL)
    text_var.set("Cancelamento em processo...")
    logging.info("Processo de desgravação cancelado pelo usuário.")


def start_process(btn_abrir, btn_select, btn_qualidade):
    filepaths = selecionar_arquivo_e_salvar(text_var, btn_select, btn_abrir, btn_qualidade, model_path_var.get())
    if filepaths:
        iniciar_transcricao_thread(filepaths, text_var, btn_abrir, btn_select, btn_qualidade, model_path_var.get())