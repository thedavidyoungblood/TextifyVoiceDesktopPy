#!/bin/bash


echo "Iniciando o processo de build com PyInstaller..."

pyinstaller --windowed --hidden-import=whisper --icon="./bin/icon.ico" --add-data="./bin/ffmpeg.exe;bin" --add-data="config.json;." textifyVoiceModelDownload.py

if [ $? -eq 0 ]; then
    echo "Build concluído com sucesso!"
else
    echo "Ocorreu um erro durante o build."
fi

read -p "Pressione qualquer tecla para continuar..."

