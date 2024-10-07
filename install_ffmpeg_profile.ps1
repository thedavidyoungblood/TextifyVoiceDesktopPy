# Salve este conteúdo em um arquivo com a extensão .ps1, por exemplo, Install-FFmpeg.ps1

param (
    [switch]$webdl
)

# Definir o diretório de instalação no perfil do usuário
$ffmpegPath = Join-Path -Path $env:USERPROFILE -ChildPath "ffmpeg"

# Criar o diretório de instalação
if (-Not (Test-Path -Path $ffmpegPath)) {
    New-Item -Type Directory -Path $ffmpegPath -Force | Out-Null
}

Set-Location $ffmpegPath

# Baixar o FFmpeg
Write-Host "Baixando o FFmpeg..."
$ffmpegUrl = 'https://github.com/GyanD/codexffmpeg/releases/download/6.0/ffmpeg-6.0-essentials_build.zip'
$zipFile = 'ffmpeg.zip'

try {
    Invoke-WebRequest -Uri $ffmpegUrl -OutFile $zipFile -UseBasicParsing
} catch {
    Write-Error "Falha ao baixar o FFmpeg. Verifique sua conexão com a internet e tente novamente."
    Exit 1
}

# Expandir o arquivo zip
Write-Host "Extraindo o FFmpeg..."

# Verificar se o Expand-Archive está disponível
if (Get-Command Expand-Archive -ErrorAction SilentlyContinue) {
    Expand-Archive -Path $zipFile -DestinationPath $ffmpegPath -Force
} else {
    # Usar métodos .NET para extrair o zip
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    [System.IO.Compression.ZipFile]::ExtractToDirectory("$ffmpegPath\$zipFile", "$ffmpegPath")
}

# Listar o conteúdo para verificar a estrutura de pastas
Write-Host "Conteúdo após extração:"
Get-ChildItem -Path $ffmpegPath

# Identificar a pasta extraída (ajuste conforme a estrutura do zip, se necessário)
$extractedFolder = Get-ChildItem -Path $ffmpegPath -Directory | Where-Object { $_.Name -like "ffmpeg-*" } | Select-Object -First 1

if ($extractedFolder) {
    $binPath = Join-Path -Path $extractedFolder.FullName -ChildPath 'bin'

    if (Test-Path $binPath) {
        # Mover os arquivos executáveis para o diretório principal
        Get-ChildItem -Path "$binPath\*.exe" | ForEach-Object {
            Move-Item -Path $_.FullName -Destination $ffmpegPath -Force
        }

        # Limpar arquivos desnecessários
        Write-Host "Limpando arquivos temporários..."
        Remove-Item $extractedFolder.FullName -Recurse -Force
    } else {
        Write-Host "Erro: A pasta 'bin' não foi encontrada dentro de '$($extractedFolder.FullName)'."
        Exit 1
    }
} else {
    Write-Host "Erro: Nenhuma pasta extraída correspondente encontrada."
    Write-Host "Verifique a estrutura do arquivo zip e ajuste o script conforme necessário."
    Exit 1
}

# Remover o arquivo zip
Remove-Item "$ffmpegPath\$zipFile" -Force

# Adicionar o caminho do FFmpeg à variável de ambiente do usuário, se ainda não estiver presente
$currentPath = [System.Environment]::GetEnvironmentVariable("PATH", "User")
if ($currentPath -notlike "*$ffmpegPath*") {
    Write-Host "Adicionando o FFmpeg à variável PATH do usuário..."
    [System.Environment]::SetEnvironmentVariable(
        "PATH",
        "$currentPath;$ffmpegPath",
        "User"
    )
} else {
    Write-Host "O caminho do FFmpeg já está presente na variável PATH do usuário."
}

# Atualizar a variável PATH na sessão atual
$env:Path = [System.Environment]::GetEnvironmentVariable("PATH", "User")

Write-Host "Instalação concluída. Verifique executando 'ffmpeg -version' no PowerShell ou Prompt de Comando."
