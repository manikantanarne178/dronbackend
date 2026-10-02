import os
import shutil
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any

def resolve_colmap_executable() -> Optional[str]:
    """
    Resolve the COLMAP executable path in a cross-platform manner.
    Checks:
    1. COLMAP_PATH environment variable
    2. System PATH (shutil.which)
    3. Common Linux install locations
    4. Common Windows install locations
    """
    # 1. Environment variable
    env_path = os.getenv("COLMAP_PATH")
    if env_path:
        p = Path(env_path)
        if p.is_file() and os.access(p, os.X_OK):
            return str(p)
        which_env = shutil.which(env_path)
        if which_env:
            return which_env

    # 2. System PATH
    which_colmap = shutil.which("colmap") or shutil.which("colmap.exe")
    if which_colmap:
        return which_colmap

    # 3. Known Linux paths
    linux_candidates = [
        "/usr/bin/colmap",
        "/usr/local/bin/colmap",
        "/opt/colmap/bin/colmap",
        "/snap/bin/colmap",
    ]
    for cand in linux_candidates:
        p = Path(cand)
        if p.is_file():
            return str(p)

    # 4. Known Windows paths (only if on Windows)
    if os.name == "nt":
        windows_candidates = [
            r"C:\colmap-x64-windows-nocuda\bin\colmap.exe",
            r"C:\Program Files\COLMAP\bin\colmap.exe",
            r"C:\Program Files\COLMAP\colmap.exe",
        ]
        for cand in windows_candidates:
            p = Path(cand)
            if p.is_file():
                return str(p)

    return None


def resolve_openmvs_bin() -> Optional[Path]:
    """
    Resolve OpenMVS binary directory in a cross-platform manner.
    """
    env_bin = os.getenv("OPENMVS_BIN")
    if env_bin:
        p = Path(env_bin)
        if p.is_dir():
            return p

    which_interface = shutil.which("InterfaceCOLMAP") or shutil.which("InterfaceCOLMAP.exe")
    if which_interface:
        return Path(which_interface).parent

    linux_paths = [
        Path("/usr/local/bin/OpenMVS"),
        Path("/usr/bin/OpenMVS"),
        Path("/opt/openMVS/build/bin"),
    ]
    for lp in linux_paths:
        if lp.is_dir() and (lp / "InterfaceCOLMAP").exists():
            return lp

    if os.name == "nt":
        win_paths = [
            Path(r"C:\OpenMVS_Windows_x64\vc17\x64\Release"),
            Path(r"C:\Program Files\OpenMVS\bin"),
        ]
        for wp in win_paths:
            if wp.is_dir() and (wp / "InterfaceCOLMAP.exe").exists():
                return wp

    return None


def get_colmap_diagnostics() -> Dict[str, Any]:
    colmap_exec = resolve_colmap_executable()
    openmvs_dir = resolve_openmvs_bin()
    version_str = "Unavailable"

    if colmap_exec:
        try:
            res = subprocess.run(
                [colmap_exec, "-h"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            lines = (res.stdout or res.stderr or "").splitlines()
            if lines:
                version_str = lines[0].strip()
        except Exception as e:
            version_str = f"Error: {e}"

    return {
        "colmap_available": colmap_exec is not None,
        "colmap_executable": Path(colmap_exec).name if colmap_exec else None,
        "colmap_version": version_str,
        "openmvs_available": openmvs_dir is not None,
        "os": os.name,
    }
