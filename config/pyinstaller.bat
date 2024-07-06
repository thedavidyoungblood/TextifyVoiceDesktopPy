#!/bin/bash


echo "Iniciando o processo de build com PyInstaller..."

pyinstaller --windowed --noconsole --hidden-import=whisper --icon=./bin/icon.ico textifyVoice.py
pyinstaller --add-data "path/to/icon.ico;./bin" --add-data "path/to/config.json;." your_script.py

if [ $? -eq 0 ]; then
    echo "Build concluído com sucesso!"
else
    echo "Ocorreu um erro durante o build."
fi

read -p "Pressione qualquer tecla para continuar..."