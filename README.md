# TextifyVoice [ Beta ] 

## Descrição

O **Desgravador** é uma aplicação desenvolvida em Python que permite a transcrição de vídeos e áudios para texto. Utilizando a biblioteca Whisper para transcrição e FFmpeg para extração de áudio, o software oferece uma interface gráfica amigável para facilitar o processo de transcrição.

## Funcionalidades

- **Transcrição de Vídeos e Áudios**: Suporta arquivos MP4 e MP3.
- **Extração de Áudio**: Utiliza FFmpeg para extrair o áudio de vídeos.
- **Notificações**: Notifica o usuário sobre o progresso e conclusão das transcrições.
- **Configuração de Modelo**: Permite selecionar e salvar o caminho do modelo Whisper para transcrição.
- **Rotação de Logs**: Utiliza `RotatingFileHandler` para gerenciar o tamanho dos arquivos de log.

## Requisitos

- Python 3.6 ou superior
- Bibliotecas Python: `tkinter`, `plyer`, `winsound`, `whisper`, `docx`, `json`, `subprocess`, `warnings`
- FFmpeg (incluso na pasta `ffmpeg`)

## Instalação

1. Clone o repositório:
    ```bash
    git clone https://github.com/finnzao/WhisperDesktopPy.git
    ```
2. Certifique-se de que o FFmpeg está na pasta `ffmpeg` dentro do diretório do projeto().

## Uso

1. Execute o script principal:
    ```bash
    python textifyVoice.py
    ```

2. Na interface gráfica:
    - Clique em **Selecionar qualidade** para escolher o modelo Whisper.
    - Clique em **Selecionar Arquivos** para escolher os vídeos ou áudios que deseja transcrever.
    - Acompanhe o progresso e as notificações na interface.

## Estrutura do Projeto

```plaintext
desgravador/
├── bin/
│   └── icon.ico
├── ffmpeg/
│   └── ffmpeg.exe
├── logs/
│   └── info.log
├── config.json
├── textifyVoice.py
├── requirements.txt
└── README.md
```

## Configuração

O arquivo `config.json` é usado para armazenar o caminho do modelo Whisper selecionado. Ele é criado automaticamente na primeira execução do programa, caso não exista.

### Exemplo de `config.json`

```json
{
    "model_path": "caminho/para/o/modelo/whisper.pt"
}
```

## Logs

Os logs são armazenados na pasta `logs` e gerenciados pelo `RotatingFileHandler`. O arquivo de log `info.log` é rotacionado quando atinge 5 MB, mantendo até 5 arquivos de backup.

## Contribuição

Contribuições são bem-vindas! Sinta-se à vontade para abrir issues e pull requests.

## Licença

Este projeto está licenciado sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

