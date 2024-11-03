```markdown

NOTE: This was cloned and translated from the original creator for ease of user-experience in English for English Speakers.

---

# TextifyVoice - Audio and Video Transcription with Whisper

**TextifyVoice** is a practical application that combines OpenAI's Whisper ASR model with a simple and intuitive graphical interface. It serves as a versatile tool for transcribing audio and video, allowing users to easily convert spoken language into written text.

Initially, I used the Whisper library locally on my computer, handling files solely through the command prompt. However, as requests for using Whisper to transcribe videos became more frequent, I realized that this need was shared by others. Thus, the idea emerged to create a more accessible solution for those who do not frequently interact with technology—especially for those who feel intimidated by using the command prompt. The solution was to develop a desktop application with two main advantages: it is free and enables transcriptions without the need for an internet connection.

## 🚀 Features

- **Audio and Video Transcription**: Easily convert audio or video files into text.
- **Intuitive Graphical Interface**: Select and transcribe files through a user-friendly interface.
- **Support for Multiple Formats**: Compatible with formats such as MP3, MP4, WAV, AAC, FLAC, M4A, OGG, among others.
- **Customizable Model Download**: Choose from different transcription models based on your needs.
- **Optimized Audio Processing**: Utilizes FFmpeg to extract audio tracks from video files.
- **Automatic Saving**: Transcriptions are saved as `.docx` files in the same directory as the original files.
- **Process Cancellation**: Ability to cancel ongoing model downloads and transcriptions.

## 📜 Requirements

### Compatible Operating Systems:

| Operating System | Pre-compiled Executable | As Python Module | From Git |
| --- | --- | --- | --- |
| **Windows** | ✔️ | ✔️ | ✔️ |
| **macOS** | ❌ | ✔️ | ✔️ |
| **Linux** | ❌ | ✔️ | ✔️ |
- **Python 3.8 or higher** (Python 3.11 recommended) for installation as a module.
- **FFmpeg**: Required to process video files. Ensure that FFmpeg is installed and configured in the system PATH.
- **Internet Connection**: Only necessary for downloading models and updates.

### Hardware Requirements per Model:

| Model | Transcription Time* | Accuracy | Required VRAM | Relative Speed |
| --- | --- | --- | --- | --- |
| **Tiny** | 3 min | Low | ~1 GB | ~32x |
| **Base** | 3 min | Medium | ~1 GB | ~16x |
| **Small** | 15 min | High | ~2 GB | ~6x |
| **Medium** | 25 min | Very High | ~5 GB | ~2x |
| **Large-V1** | 1h 13min | Very High | ~10 GB | 1x |
| **Large-V2** | 1h 7min | Very High | ~10 GB | 1x |
| **Large-V3** | 1h 10min | Very High | ~10 GB | 1x |

\*Estimated time to transcribe 1 hour of audio. May vary depending on hardware.

## 🔧 Installation

**FFmpeg**

There are two files for installation, `install_ffmpeg_profile.ps1` (installation at the current user level) and `install_ffmpeg_adm.ps1` (installation at the administrator level). These PowerShell scripts were created to facilitate the FFmpeg installation process, an essential program for file conversion during the application's use.

There is also a way to install manually [HERE](https://www.wikihow.com/Install-FFmpeg-on-Windows).

### Pre-compiled Executable

1. **Download**: Download the latest version [here](https://github.com/finnzao/TextifyVoiceDesktopPy/releases/tag/v1).
2. **Installation**: Extract the downloaded file.
3. **Execution**: Run the `TextifyVoice.exe` file.
4. **Configuration**: On the first run, configure the preferences according to your needs.
5. **Usage**: Start transcribing your files!

## 🛠️ Development

### Setup

1. **Clone the Repository**:
    
    ```bash
    git clone https://github.com/finnzao/TextifyVoiceDesktopPy.git
    ```
    
2. **Enter the Project Directory**:
    
    ```bash
    cd TextifyVoiceDesktopPy
    ```
    
3. **Create a Virtual Environment**:
    
    ```bash
    python -m venv venv
    ```
    
4. **Activate the Virtual Environment**:
    - **Windows**:
        
        ```bash
        venv\Scripts\activate
        ```
        
    - **Linux/macOS**:
        
        ```bash
        source venv/bin/activate
        ```
        
5. **Install Dependencies**:
    
    ```bash
    pip install -r requirements.txt
    ```
    

### Running the Application

Run the application using the following command:

```bash
python main.py
```

### Compilation

To compile the project into an executable, use **`pyinstaller`**:

```bash
pyinstaller --windowed --hidden-import=whisper --icon="./bin/icon.ico" --add-data="./bin/ffmpeg.exe;bin" --add-data="config.json;." textifyVoiceModelDownload.py
```

### Compatibility

The project is compatible with Windows, Linux, and macOS. If you encounter any bugs or issues, feel free to create an issue.
```
