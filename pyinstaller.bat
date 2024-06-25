#!/bin/bash


echo "Iniciando o processo de build com PyInstaller..."

pyinstaller --windowed --hidden-import=whisper --collect-all=whisper --icon=./bin/icon.ico main.py

# Verifica se o comando foi bem-sucedido
if [ $? -eq 0 ]; then
    echo "Build concluído com sucesso!"
else
    echo "Ocorreu um erro durante o build."
fi

# Aguarda o usuário pressionar uma tecla antes de fechar o terminal
read -p "Pressione qualquer tecla para continuar..."