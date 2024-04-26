# Aplicação de Transcrição de Áudio

## Sobre a Aplicação

Esta aplicação é uma ferramenta de transcrição de áudio que permite aos usuários converter o áudio de arquivos MP4 em texto, utilizando a biblioteca Whisper para a transcrição. A interface gráfica é construída com Tkinter, facilitando a seleção de arquivos e a visualização do progresso da transcrição. Após a transcrição, o texto é salvo em um documento do Word (.docx) com o mesmo nome base do arquivo de entrada, facilitando a organização e revisão do conteúdo transcrito.

## Funcionamento

1. **Seleção de Arquivo**: O usuário seleciona um arquivo MP4 para transcrição através de uma interface gráfica simples.
2. **Extração de Áudio**: Utilizando o `ffmpeg`, o áudio é extraído do arquivo de vídeo selecionado.
3. **Transcrição**: O áudio extraído é então transcrito em texto utilizando o modelo "base" da biblioteca Whisper.
4. **Salvamento do Texto**: O texto transcrito é salvo em um documento do Word (.docx), no mesmo diretório do arquivo original, com um sufixo "transcrição" no nome do arquivo.
5. **Limpeza**: O arquivo de áudio temporário é removido após a conclusão da transcrição.

## Pré-requisitos

Antes de executar a aplicação, certifique-se de que o Python (versão 3.7 ou superior) está instalado em seu sistema, assim como o `ffmpeg`, necessário para a extração de áudio dos arquivos MP4.

## Instalação das Dependências

Para instalar todas as dependências necessárias para a aplicação, você pode usar o seguinte comando Bash. Este comando instala o Whisper para transcrição de áudio, o python-docx para criação de documentos do Word, e o PyInstaller para a geração de um executável, caso deseje distribuir sua aplicação.

```bash
pip install whisper python-docx pyinstaller
```

Além disso, você precisará do `ffmpeg` instalado em seu sistema. A instalação do `ffmpeg` varia de acordo com o sistema operacional:

- **No Windows**: Baixe o `ffmpeg` do [site oficial](https://ffmpeg.org/download.html) e adicione o diretório binário ao PATH do sistema.
- **No Linux**: Você pode instalar o `ffmpeg` usando o gerenciador de pacotes da sua distribuição, por exemplo, `sudo apt-get install ffmpeg` para distribuições baseadas em Debian.
- **No macOS**: Instale o `ffmpeg` usando o Homebrew com o comando `brew install ffmpeg`.

## Executando a Aplicação

Para executar a aplicação, navegue até o diretório do script no terminal e execute:

```bash
python nome_do_seu_script.py
```

Substitua `nome_do_seu_script.py` pelo nome real do seu arquivo de script Python.

## Criando um Executável

Se desejar criar um executável da sua aplicação para distribuição, você pode usar o PyInstaller com o seguinte comando:

```bash
pyinstaller --onefile --windowed --add-data "<caminho_para_ffmpeg>/ffmpeg.exe;." --hidden-import "whisper" nome_do_seu_script.py
```

Lembre-se de substituir `<caminho_para_ffmpeg>` pelo caminho onde o `ffmpeg.exe` está localizado no seu sistema e `nome_do_seu_script.py` pelo nome do seu arquivo de script.

