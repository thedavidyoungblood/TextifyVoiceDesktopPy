# TextifyVoice

TextifyVoice é uma aplicação desenvolvida em Python que permite transcrever arquivos de áudio e vídeo em texto, utilizando o modelo Whisper da OpenAI. A aplicação possui uma interface gráfica construída com Tkinter, facilitando a interação do usuário.

## Índice

- [Descrição Geral](#descrição-geral)
- [Funcionalidades](#funcionalidades)
- [Arquitetura do Código](#arquitetura-do-código)
- [Instalação](#instalação)
- [Uso](#uso)
- [Dependências](#dependências)
- [Logs](#logs)
- [Erros Comuns](#erros-comuns)
- [Contribuição](#contribuição)
- [Licença](#licença)
- [Autor](#autor)

## Descrição Geral

A aplicação tem como objetivo facilitar o processo de transcrição de arquivos de áudio e vídeo, suportando diversos formatos e utilizando modelos de transcrição de alta qualidade. O usuário pode selecionar arquivos, escolher o modelo de transcrição e acompanhar o progresso da transcrição em tempo real.

## Funcionalidades

- **Suporte a Múltiplos Formatos**: MP4, MP3, WAV, MKV, AAC, FLAC, M4A, OGG.
- **Interface Gráfica Intuitiva**: Desenvolvida com Tkinter.
- **Seleção de Modelo Whisper**: Possibilidade de selecionar entre diferentes modelos e qualidades.
- **Download Automático de Modelos**: Baixa modelos necessários caso não estejam disponíveis localmente.
- **Suporte a GPU**: Utiliza aceleração por GPU se disponível.
- **Gerenciamento de Transcrições**: Permite adicionar múltiplos arquivos à fila de transcrição.
- **Cancelamento de Transcrição**: Possibilidade de cancelar transcrições em andamento.

## Arquitetura do Código

### Estrutura Geral

- **Módulos e Bibliotecas**:
  - `tkinter` e `ttk`: Construção da interface gráfica.
  - `whisper`: Modelo de transcrição de áudio para texto.
  - `torch`: Verificação de disponibilidade de GPU.
  - `docx`: Criação e manipulação de documentos `.docx`.
  - `subprocess`: Execução de comandos do sistema, como o FFmpeg.
  - `threading`: Gerenciamento de threads para operações assíncronas.
  - `logging`: Registro e gerenciamento de logs.
  - `json`: Leitura e escrita de arquivos de configuração.
  - `requests`: Download de modelos pela internet.

### Organização do Código

- **Funções Utilitárias**:
  - `resource_path(relative_path)`: Gerencia caminhos de recursos, especialmente quando a aplicação é empacotada com ferramentas como PyInstaller.
  - `configurar_logger()`: Configura o sistema de logging, incluindo o formato e a rotação de arquivos de log.

- **Classes Personalizadas**:
  - `NoConsolePopen`: Subclasse de `subprocess.Popen` que impede a abertura de janelas de console no Windows durante a execução de comandos do FFmpeg.

- **Funções Principais**:
  - `extrair_audio(filepath, temp_dir)`: Extrai o áudio de um arquivo de vídeo utilizando o FFmpeg.
  - `extrair_e_transcrever_arquivo(filepath, item, lista_arquivos)`: Gerencia o processo completo de extração de áudio e transcrição de um arquivo específico.
  - `transcrever_arquivos_em_fila(lista_arquivos, btn_iniciar, btn_adicionar)`: Processa todos os arquivos na fila de transcrição.
  - `iniciar_transcricao(lista_arquivos, btn_iniciar, btn_adicionar)`: Inicia o processo de transcrição em uma thread separada.
  - `adicionar_arquivo(lista_arquivos)`: Abre um diálogo para o usuário selecionar arquivos a serem adicionados à lista.
  - `abrir_local_do_arquivo(event, lista_arquivos)`: Abre o diretório onde o arquivo transcrito foi salvo.
  - `selecionar_modelo()`: Permite ao usuário selecionar manualmente um modelo Whisper existente.
  - `verificar_modelo_inicial()`: Verifica se um modelo padrão está configurado e carrega-o.
  - `selecionar_qualidade()`: Interface para seleção e download de modelos Whisper de diferentes qualidades.

### Gerenciamento de Estados e Eventos

- **Variáveis Globais**:
  - `cancelar_desgravacao`: Controla o cancelamento das transcrições.
  - `transcricao_em_andamento`: Indica se uma transcrição está em progresso.
  - `threads`: Lista de threads ativas para gerenciamento.

- **Eventos**:
  - `Event()`: Utilizado para sinalizar o encerramento de threads e operações.

### Interface Gráfica

- **Janela Principal**:
  - Contém botões para selecionar arquivos e escolher a qualidade do modelo.
  - Exibe o caminho do modelo atual selecionado.

- **Janela de Seleção de Arquivos**:
  - Permite adicionar arquivos à fila de transcrição.
  - Mostra uma lista dos arquivos com seus respectivos status.
  - Possibilita iniciar ou cancelar a transcrição.

- **Janela de Seleção de Qualidade**:
  - Oferece opções de modelos Whisper para download.
  - Mostra o progresso do download do modelo selecionado.

### Fluxo de Execução

1. **Inicialização**:
   - Configura o logger e carrega as configurações iniciais.
   - Verifica se um modelo padrão está configurado e disponível.

2. **Interação do Usuário**:
   - O usuário seleciona arquivos e o modelo de transcrição desejado.
   - Inicia o processo de transcrição.

3. **Processamento**:
   - Para cada arquivo, extrai o áudio se necessário.
   - Transcreve o áudio utilizando o modelo Whisper.
   - Salva a transcrição em um arquivo `.docx`.

4. **Finalização**:
   - Atualiza o status de cada arquivo na interface.
   - Permite ao usuário abrir o local do arquivo transcrito.

## Instalação

### Passos

1. **Clone o Repositório**:

   ```bash
   git clone https://github.com/seu_usuario/textifyvoice.git
   cd textifyvoice
   ```

2. **Crie um Ambiente Virtual (Opcional)**:

   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate  # Windows
   ```

3. **Instale as Dependências**:

4. **Instale o FFmpeg**:

   - **Windows**:
     - Clique no executavel `setup.exe` para instalar ffmpeg como uma variavel de perfil.


5. **Execute a Aplicação**:

   ```bash
   python textifyvoice.py
   ```

## Uso

1. **Inicie a Aplicação**:

   - A interface principal será exibida com opções para selecionar arquivos e ajustar configurações.

2. **Selecione os Arquivos**:

   - Clique em **"Selecionar Arquivos"** para abrir a janela de seleção.
   - Na janela de seleção, clique em **"Adicionar Arquivo"** e escolha os arquivos desejados.
   - Os arquivos aparecerão em uma lista com o status **"Preparado"**.

3. **Selecione a Qualidade do Modelo**:

   - Opcionalmente, clique em **"Selecionar Qualidade"** para escolher a qualidade do modelo Whisper.
   - Se o modelo não estiver disponível localmente, a aplicação oferecerá a opção de download.

4. **Inicie a Transcrição**:

   - Na janela de seleção, clique em **"Iniciar Transcrição"**.
   - O status de cada arquivo será atualizado conforme o progresso.

5. **Acompanhe o Progresso**:

   - O status dos arquivos mudará para **"Em processamento..."**, **"Finalizado"**, ou **"Erro"**.
   - Duplo clique em um arquivo com status **"Finalizado"** para abrir o diretório do arquivo transcrito.

6. **Transcrições**:

   - As transcrições são salvas no mesmo diretório dos arquivos originais com o sufixo `_text.docx`.

## Dependências

- **Pacotes Python**:

  - `tkinter`: Interface gráfica.
  - `whisper`: Modelo de transcrição.
  - `torch`: Suporte a GPU.
  - `python-docx`: Manipulação de arquivos `.docx`.
  - `requests`: Download de modelos.
  - `ffmpeg-python` (opcional): Integração com FFmpeg.

- **Outras Dependências**:

  - **FFmpeg**: Necessário para extração de áudio.
  - **CUDA** (Opcional): Para aceleração por GPU.

## Logs

- Os logs são armazenados na pasta `logs/`, com o arquivo principal sendo `info.log`.
- Utiliza `RotatingFileHandler` para limitar o tamanho dos arquivos de log e manter backups.

## Erros Comuns

- **Modelo Não Encontrado**:

  - Certifique-se de que o modelo Whisper está corretamente configurado.
  - Utilize a opção **"Selecionar Qualidade"** para baixar e configurar o modelo.

- **FFmpeg Não Encontrado**:

  - Verifique se o FFmpeg está instalado e se o executável está no `PATH` do sistema.

- **Erro ao Carregar o Modelo**:

  - Verifique a compatibilidade do modelo com a versão do Whisper instalada.
  - Certifique-se de que o arquivo do modelo não está corrompido.

- **Transcrição Não Inicia**:

  - Verifique se todos os arquivos adicionados são suportados.
  - Consulte os logs para detalhes específicos do erro.

## Contribuição

Contribuições são bem-vindas! Sinta-se à vontade para abrir issues e pull requests para melhorar este projeto.

### Como Contribuir

1. **Fork o Repositório**.
2. **Crie uma Branch**:

   ```bash
   git checkout -b feature/nova-funcionalidade
   ```

3. **Commit suas Alterações**:

   ```bash
   git commit -m "Adiciona nova funcionalidade"
   ```

4. **Envie para o Repositório Remoto**:

   ```bash
   git push origin feature/nova-funcionalidade
   ```

5. **Abra um Pull Request**.


## Autor

Desenvolvido por [Felipe](https://github.com/finnzao).

