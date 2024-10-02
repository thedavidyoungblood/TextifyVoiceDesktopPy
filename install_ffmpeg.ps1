param (
    [switch]$webdl
)

$arguments = [System.Environment]::GetCommandLineArgs()

# Definir o diretório de instalação no perfil do usuário
$ffmpegPath = Join-Path -Path $env:USERPROFILE -ChildPath "ffmpeg"

# Criar o diretório de instalação
New-Item -Type Directory -Path $ffmpegPath -Force
Set-Location $ffmpegPath

# Baixar o FFmpeg
Write-Host "Baixando o FFmpeg..."
Invoke-WebRequest -Uri 'https://github.com/GyanD/codexffmpeg/releases/download/6.0/ffmpeg-6.0-essentials_build.zip' -OutFile 'ffmpeg.zip'

# Expandir o arquivo zip
Write-Host "Extraindo o FFmpeg..."

# Verificar se o Expand-Archive está disponível
if (Get-Command Expand-Archive -ErrorAction SilentlyContinue) {
    Expand-Archive -Path 'ffmpeg.zip' -DestinationPath $ffmpegPath -Force
} else {
    # Usar métodos .NET para extrair o zip
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    [System.IO.Compression.ZipFile]::ExtractToDirectory("$ffmpegPath\ffmpeg.zip", "$ffmpegPath")
}

# Listar o conteúdo para verificar a estrutura de pastas
Write-Host "Conteúdo após extração:"
Get-ChildItem -Path $ffmpegPath

# Verificar se a pasta 'ffmpeg-6.0-essentials_build' existe
$extractedFolder = Join-Path -Path $ffmpegPath -ChildPath 'ffmpeg-6.0-essentials_build'
if (Test-Path $extractedFolder) {
    # Mover os arquivos executáveis para o diretório principal
    Get-ChildItem -Recurse -Path "$extractedFolder\bin\*.exe" |
    ForEach-Object {
        Move-Item -Path $_.FullName -Destination $ffmpegPath -Force
    }

    # Limpar arquivos desnecessários
    Write-Host "Limpando arquivos temporários..."
    Remove-Item $extractedFolder -Recurse -Force
} else {
    Write-Host "Erro: A pasta extraída '$extractedFolder' não foi encontrada."
    Write-Host "Verifique a estrutura do arquivo zip e ajuste o script conforme necessário."
    Exit 1
}

# Remover o arquivo zip
Remove-Item .\ffmpeg.zip -Force

# Adicionar o caminho do FFmpeg à variável de ambiente do usuário
Write-Host "Adicionando o FFmpeg à variável PATH do usuário..."
[System.Environment]::SetEnvironmentVariable(
    "PATH",
    "$ffmpegPath;$([System.Environment]::GetEnvironmentVariable('PATH','User'))",
    "User"
)

# Atualizar a variável PATH na sessão atual
$env:Path = [System.Environment]::GetEnvironmentVariable("PATH","User")

Write-Host "Instalação concluída. Verifique executando 'ffmpeg -version'."
