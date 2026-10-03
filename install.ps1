# ==============================================================================
# job0t — Instalador Universal para Windows (PowerShell)
# Repositorio: https://github.com/ivanlopez0k/job0t
# Uso: irm https://raw.githubusercontent.com/ivanlopez0k/job0t/main/install.ps1 | iex
# ==============================================================================

$ErrorActionPreference = 'Stop'

# Configurar salida segura UTF-8
try {
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
} catch {}

$Logo = @'
    o8o            .o8         .oooo.       .   
    `"'           "888        d8P'`Y8b    .o8   
   oooo  .ooooo.   888oooo.  888    888 .o888oo 
   `888 d88' `88b  d88' `88b 888    888   888   
    888 888   888  888   888 888    888   888   
    888 888   888  888   888 `88b  d88'   888 . 
    888 `Y8bod8P'  `Y8bod8P'  `Y8bd8P'    "888" 
    888                                         
.o. 88P                                         
`Y888P                                          
'@

Write-Host ""
Write-Host $Logo -ForegroundColor Cyan
Write-Host "   Buscador, clasificador y exportador de empleo" -ForegroundColor DarkCyan
Write-Host "----------------------------------------------------------" -ForegroundColor DarkGray
Write-Host ""

# 1. Detección de Python
Write-Host "[1/5] Verificando instalación de Python..." -ForegroundColor Yellow

function Find-Python {
    foreach ($cmd in @("python", "py")) {
        try {
            $ver = & $cmd -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>$null
            if ($ver) {
                $major, $minor = $ver.Split('.')
                if ([int]$major -ge 3 -and [int]$minor -ge 10) {
                    return $cmd
                }
            }
        } catch {}
    }
    return $null
}

$PythonCmd = Find-Python

if (-not $PythonCmd) {
    Write-Host "Python 3.10 o superior no fue detectado en el sistema." -ForegroundColor Yellow
    $WingetCmd = Get-Command winget -ErrorAction SilentlyContinue

    if ($WingetCmd) {
        Write-Host "Intentando instalar Python automáticamente vía winget..." -ForegroundColor Cyan
        try {
            winget install Python.Python.3.12 --source winget --accept-package-agreements --accept-source-agreements --silent
            # Refrescar PATH de la sesión actual
            $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
            $PythonCmd = Find-Python
        } catch {
            Write-Host "No se pudo completar la instalación automática vía winget." -ForegroundColor Red
        }
    }

    if (-not $PythonCmd) {
        Write-Host ""
        Write-Host "Se requiere Python 3.10 o superior para continuar." -ForegroundColor Red
        Write-Host "Podés descargarlo desde el sitio oficial: https://www.python.org/downloads/" -ForegroundColor White
        Write-Host "Asegurate de marcar la opción 'Add Python to PATH' durante la instalación." -ForegroundColor Yellow
        Write-Host ""
        exit 1
    }
}

Write-Host "  -> Python detectado: $PythonCmd" -ForegroundColor Green

# 2. Configurar directorios en el perfil de usuario (~/.job0t)
Write-Host "[2/5] Configurando directorio de instalación..." -ForegroundColor Yellow
$Job0tHome = Join-Path $HOME ".job0t"
$AppDir    = Join-Path $Job0tHome "app"
$VenvDir   = Join-Path $Job0tHome "venv"
$BinDir    = Join-Path $Job0tHome "bin"

New-Item -ItemType Directory -Force -Path $Job0tHome | Out-Null
New-Item -ItemType Directory -Force -Path $BinDir     | Out-Null

# 3. Descargar / Actualizar el código fuente de job0t
Write-Host "[3/5] Descargando la versión más reciente de job0t..." -ForegroundColor Yellow
$GitCmd = Get-Command git -ErrorAction SilentlyContinue

if ($GitCmd) {
    if (Test-Path (Join-Path $AppDir ".git")) {
        Write-Host "  -> Actualizando repositorio existente..." -ForegroundColor Gray
        git -C $AppDir pull --quiet
    } else {
        if (Test-Path $AppDir) { Remove-Item -Recurse -Force $AppDir }
        git clone --quiet https://github.com/ivanlopez0k/job0t.git $AppDir
    }
} else {
    Write-Host "  -> Git no detectado. Descargando paquete ZIP desde GitHub..." -ForegroundColor Gray
    $ZipPath = Join-Path $Job0tHome "job0t.zip"
    $TempExtract = Join-Path $Job0tHome "temp_extract"

    Invoke-WebRequest -Uri "https://github.com/ivanlopez0k/job0t/archive/refs/heads/main.zip" -OutFile $ZipPath
    Expand-Archive -Path $ZipPath -DestinationPath $TempExtract -Force
    Remove-Item -Force $ZipPath

    if (Test-Path $AppDir) { Remove-Item -Recurse -Force $AppDir }
    $ExtractedFolder = Get-ChildItem -Path $TempExtract -Directory | Select-Object -First 1
    Move-Item -Path $ExtractedFolder.FullName -Destination $AppDir
    Remove-Item -Recurse -Force $TempExtract
}

Write-Host "  -> Código fuente listo en: $AppDir" -ForegroundColor Green

# 4. Crear entorno virtual aislado e instalar dependencias
Write-Host "[4/5] Configurando entorno virtual e instalando dependencias..." -ForegroundColor Yellow
if (-not (Test-Path $VenvDir)) {
    & $PythonCmd -m venv $VenvDir
}

$VenvPython = Join-Path $VenvDir "Scripts\python.exe"
if (-not (Test-Path $VenvPython)) {
    Write-Host "No se pudo inicializar el entorno virtual en $VenvDir" -ForegroundColor Red
    exit 1
}

Write-Host "  -> Instalando paquetes requeridos..." -ForegroundColor Gray
& $VenvPython -m pip install --upgrade pip --quiet
& $VenvPython -m pip install -e $AppDir --quiet

# 5. Generar wrappers ejecutables y agregarlos al PATH
Write-Host "[5/5] Registrando el comando 'job0t' en el sistema..." -ForegroundColor Yellow

$CmdWrapper = Join-Path $BinDir "job0t.cmd"
$PsWrapper  = Join-Path $BinDir "job0t.ps1"

# Wrapper CMD
"@echo off`r`n`"$VenvPython`" -m job0t %*" | Set-Content -Path $CmdWrapper -Encoding ASCII

# Wrapper PowerShell
"& `"$VenvPython`" -m job0t @args" | Set-Content -Path $PsWrapper -Encoding UTF8

# Agregar ~/.job0t/bin al PATH de usuario en Windows
$CurrentPath = [Environment]::GetEnvironmentVariable("PATH", "User")
if ($CurrentPath -notlike "*$BinDir*") {
    $NewPath = if ([string]::IsNullOrEmpty($CurrentPath)) { $BinDir } else { "$CurrentPath;$BinDir" }
    [Environment]::SetEnvironmentVariable("PATH", $NewPath, "User")
    Write-Host "  -> Directorio $BinDir agregado al PATH de usuario." -ForegroundColor Green
}
$env:PATH = "$env:PATH;$BinDir"

Write-Host ""
Write-Host "==========================================================" -ForegroundColor Green
Write-Host "   Instalación completada exitosamente                    " -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Para comenzar a utilizar job0t:" -ForegroundColor White
Write-Host "  1. Abrí una nueva ventana de terminal (PowerShell o CMD)." -ForegroundColor Cyan
Write-Host "  2. Ejecutá el comando:" -ForegroundColor Cyan
Write-Host "         job0t run" -ForegroundColor Yellow
Write-Host ""
Write-Host "Ya podés ejecutar job0t desde cualquier directorio." -ForegroundColor Green
Write-Host ""
