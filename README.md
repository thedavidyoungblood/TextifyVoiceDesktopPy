# Aplicação de Transcrição de Áudio

## Sobre a Aplicação

Esta aplicação é uma ferramenta de transcrição de áudio que permite aos usuários converter o áudio de arquivos MP4 e MP3 em texto, utilizando a biblioteca Whisper para a transcrição. A interface gráfica é construída com Tkinter, facilitando a seleção de arquivos e a visualização do progresso da transcrição. Após a transcrição, o texto é salvo em um documento do Word (.docx) com o mesmo nome base do arquivo de entrada, facilitando a organização e revisão do conteúdo transcrito.

## Funcionamento

1. **Seleção de Arquivo**: O usuário seleciona arquivos MP4 ou MP3 para transcrição através de uma interface gráfica simples.
2. **Extração de Áudio**: Utilizando o `ffmpeg`, o áudio é extraído dos arquivos de vídeo ou áudio selecionados.
3. **Transcrição**: O áudio extraído é então transcrito em texto utilizando o modelo "large" da biblioteca Whisper.
4. **Salvamento do Texto**: O texto transcrito é salvo em um documento do Word (.docx), no mesmo diretório do arquivo original, com um sufixo "-transcrição" no nome do arquivo.
5. **Limpeza**: O arquivo de áudio temporário é removido após a conclusão da transcrição.
6. **Notificação**: Uma notificação é exibida e um som é tocado para informar que a transcrição foi concluída.

## Pré-requisitos

Antes de executar a aplicação, certifique-se de que o Python (versão 3.7 ou superior) está instalado em seu sistema, assim como o `ffmpeg`, necessário para a extração de áudio dos arquivos MP4 e MP3.

## Instalação das Dependências

Para instalar todas as dependências necessárias para a aplicação, você pode usar o seguinte comando:

```bash
pip install whisper python-docx pyinstaller plyer
```

Além disso, você precisará do `ffmpeg` instalado em seu sistema. A instalação do `ffmpeg` varia de acordo com o sistema operacional:

- **No Windows**: Baixe o `ffmpeg` do [site oficial](https://ffmpeg.org/download.html) e adicione o diretório binário ao PATH do sistema.
- **No Linux**: Você pode instalar o `ffmpeg` usando o gerenciador de pacotes da sua distribuição, por exemplo, `sudo apt-get install ffmpeg` para distribuições baseadas em Debian.
- **No macOS**: Instale o `ffmpeg` usando o Homebrew com o comando `brew install ffmpeg`.

## Executando a Aplicação

Para executar a aplicação, navegue até o diretório do script no terminal e execute:

```bash
python transcritor.py
```

Substitua `transcritor.py` pelo nome real do seu arquivo de script Python.

## Criando um Executável

Se desejar criar um executável da sua aplicação para distribuição, você pode usar o PyInstaller com o seguinte comando:

```bash
pyinstaller --onefile --windowed transcritor.py
```

### Passos Detalhados para Criar o Executável

1. **Instale o PyInstaller**:
   Certifique-se de que o PyInstaller está instalado no seu ambiente Python:
   ```bash
   pip install pyinstaller
   ```

2. **Crie o Executável**:
   Navegue até o diretório onde seu script Python está localizado e execute o comando PyInstaller:
   ```bash
   pyinstaller --onefile --windowed transcritor.py
   ```
   - `--onefile`: Cria um único arquivo executável.
   - `--windowed`: Evita que uma janela de terminal seja aberta ao executar o programa (útil para aplicações GUI).

3. **Verifique a Pasta `dist`**:
   Após a execução do PyInstaller, o executável será gerado na pasta `dist`. Navegue até essa pasta e execute o arquivo gerado para testar.

### Estrutura do Projeto

Para facilitar a organização, aqui está uma sugestão de estrutura de diretórios para o seu projeto:

```
transcritor/
├── transcritor.py
├── requirements.txt
├── README.md
└── tmp/
```

### Exemplo de Arquivo `requirements.txt`

Aqui está um exemplo de como pode ser o seu arquivo `requirements.txt` para o projeto:

```
tk
whisper
python-docx
plyer
ffmpeg-python
```

### Considerações Adicionais

- **Ambientes Virtuais**: É uma boa prática usar ambientes virtuais (como `venv` ou `virtualenv`) para gerenciar as dependências do seu projeto. Isso ajuda a evitar conflitos de dependências entre diferentes projetos.
- **Manutenção do `requirements.txt`**: Sempre que você adicionar ou remover uma biblioteca do seu projeto, lembre-se de atualizar o `requirements.txt` para refletir essas mudanças.

### Criando e Usando um Ambiente Virtual

Aqui está um guia rápido sobre como criar e usar um ambiente virtual com `venv`:

1. **Crie um Ambiente Virtual**:
   ```bash
   python -m venv meu_ambiente
   ```

2. **Ative o Ambiente Virtual**:
   - **Windows**:
     ```bash
     meu_ambiente\Scripts\activate
     ```
   - **macOS e Linux**:
     ```bash
     source meu_ambiente/bin/activate
     ```

3. **Instale as Dependências**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Desative o Ambiente Virtual**:
   Quando terminar de trabalhar no seu projeto, você pode desativar o ambiente virtual:
   ```bash
   deactivate
   ```
