"""Módulo de actualización automática para job0t."""

import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from typing import Optional, Tuple
import zipfile
import httpx

GITHUB_REPO = "ivanlopez0k/job0t"
GITHUB_API_COMMITS_URL = f"https://api.github.com/repos/{GITHUB_REPO}/commits/main"
GITHUB_ZIP_URL = f"https://github.com/{GITHUB_REPO}/archive/refs/heads/main.zip"


def get_app_root() -> Path:
    """Devuelve la ruta raíz de la instalación de job0t."""
    return Path(__file__).resolve().parent.parent.parent


def get_current_git_branch(app_root: Path) -> Optional[str]:
    """Obtiene el nombre de la rama actual de git, si aplica."""
    if not (app_root / ".git").exists():
        return None
    try:
        res = subprocess.run(
            ["git", "-C", str(app_root), "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        return res.stdout.strip()
    except Exception:
        return None


def get_local_commit_sha(app_root: Path) -> Optional[str]:
    """Obtiene el SHA del commit local actual."""
    # 1. Si es un repositorio git
    if (app_root / ".git").exists():
        try:
            res = subprocess.run(
                ["git", "-C", str(app_root), "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                check=True,
            )
            return res.stdout.strip()
        except Exception:
            pass

    # 2. Si fue instalado vía ZIP, leer archivo de versión
    version_file = app_root / ".version_sha"
    if version_file.exists():
        try:
            return version_file.read_text(encoding="utf-8").strip()
        except Exception:
            pass

    return None


def get_remote_commit_info(branch: str = "main") -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """Consulta la API de GitHub para obtener información del último commit en la rama remota.

    Devuelve (sha, mensaje, error).
    """
    url = f"https://api.github.com/repos/{GITHUB_REPO}/commits/{branch}"
    try:
        response = httpx.get(
            url,
            headers={
                "User-Agent": "job0t-updater",
                "Accept": "application/vnd.github.v3+json",
            },
            timeout=8.0,
        )
        if response.status_code == 200:
            data = response.json()
            sha = data.get("sha", "")
            commit_msg = data.get("commit", {}).get("message", "").split("\n")[0]
            return sha, commit_msg, None
        elif response.status_code == 403 or response.status_code == 429:
            return None, None, "Límite de peticiones de la API de GitHub alcanzado. Probá nuevamente en unos minutos."
        else:
            return None, None, f"Error del servidor de GitHub (código {response.status_code})"
    except httpx.RequestError as exc:
        return None, None, f"No se pudo conectar con GitHub ({exc})"


def check_uncommitted_changes(app_root: Path) -> bool:
    """Verifica si hay cambios locales sin confirmar en git."""
    if not (app_root / ".git").exists():
        return False
    try:
        res = subprocess.run(
            ["git", "-C", str(app_root), "status", "--porcelain"],
            capture_output=True,
            text=True,
            check=True,
        )
        return bool(res.stdout.strip())
    except Exception:
        return False


def update_via_git(app_root: Path, branch: str) -> Tuple[bool, str]:
    """Actualiza la instalación utilizando git pull."""
    try:
        # 1. Ejecutar git pull
        pull_res = subprocess.run(
            ["git", "-C", str(app_root), "pull", "origin", branch],
            capture_output=True,
            text=True,
            check=True,
        )

        # 2. Reinstalar el paquete y actualizar dependencias
        pip_res = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-e", str(app_root), "--quiet"],
            capture_output=True,
            text=True,
            check=True,
        )

        return True, pull_res.stdout.strip()
    except subprocess.CalledProcessError as exc:
        err = exc.stderr or exc.stdout or str(exc)
        return False, f"Fallo al ejecutar git pull: {err}"
    except Exception as exc:
        return False, f"Error inesperado al actualizar: {exc}"


def update_via_zip(app_root: Path, target_sha: Optional[str] = None) -> Tuple[bool, str]:
    """Actualiza la instalación descargando el ZIP desde GitHub (para entornos sin git)."""
    try:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            zip_dest = tmp_path / "job0t.zip"

            # 1. Descargar archivo ZIP
            with httpx.stream("GET", GITHUB_ZIP_URL, headers={"User-Agent": "job0t-updater"}, timeout=20.0) as resp:
                resp.raise_for_status()
                with open(zip_dest, "wb") as f:
                    for chunk in resp.iter_bytes():
                        f.write(chunk)

            # 2. Descomprimir
            extract_dir = tmp_path / "extracted"
            with zipfile.ZipFile(zip_dest, "r") as zip_ref:
                zip_ref.extractall(extract_dir)

            extracted_root = next(extract_dir.iterdir(), None)
            if not extracted_root or not extracted_root.is_dir():
                return False, "Estructura inesperada en el archivo ZIP descargado."

            # 3. Copiar archivos actualizados a app_root (sin sobreescribir configs personalizadas de usuario si existen)
            for item in extracted_root.iterdir():
                dest_item = app_root / item.name
                if item.is_dir():
                    shutil.copytree(item, dest_item, dirs_exist_ok=True)
                else:
                    shutil.copy2(item, dest_item)

            # Guardar SHA de versión
            if target_sha:
                (app_root / ".version_sha").write_text(target_sha, encoding="utf-8")

            # 4. Actualizar dependencias en el entorno virtual
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "-e", str(app_root), "--quiet"],
                capture_output=True,
                text=True,
                check=True,
            )

            return True, "Archivos y dependencias actualizados correctamente."
    except Exception as exc:
        return False, f"Error al descargar o aplicar el paquete ZIP: {exc}"
