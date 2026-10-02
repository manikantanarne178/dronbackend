import os
import shutil
import subprocess
import time
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List

logger = logging.getLogger("reconstruction.colmap")


def resolve_colmap_executable() -> Optional[str]:
    """
    Resolve the COLMAP executable path in a cross-platform manner.
    Checks:
    1. COLMAP_PATH environment variable
    2. System PATH (shutil.which)
    3. Common Linux install locations (/usr/bin/colmap, /usr/local/bin/colmap, /opt/colmap/bin/colmap, /snap/bin/colmap)
    4. Common Windows install locations (only if os.name == 'nt')
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
    which_colmap = shutil.which("colmap") or (shutil.which("colmap.exe") if os.name == "nt" else None)
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

    which_interface = shutil.which("InterfaceCOLMAP") or (shutil.which("InterfaceCOLMAP.exe") if os.name == "nt" else None)
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


def get_colmap_version(colmap_exec: Optional[str] = None) -> str:
    """
    Queries COLMAP version safely with a 5s timeout.
    """
    if not colmap_exec:
        colmap_exec = resolve_colmap_executable()

    if not colmap_exec:
        return "Unavailable"

    try:
        res = subprocess.run(
            [colmap_exec, "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if res.returncode == 0 and res.stdout.strip():
            return res.stdout.strip().splitlines()[0]
        # Fallback to -h
        res_h = subprocess.run(
            [colmap_exec, "-h"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        lines = (res_h.stdout or res_h.stderr or "").splitlines()
        if lines:
            return lines[0].strip()
    except Exception as e:
        return f"Detection error: {e}"

    return "COLMAP (version unknown)"


def get_colmap_diagnostics() -> Dict[str, Any]:
    """
    Provides real-time photogrammetry engine diagnostic metrics.
    """
    colmap_exec = resolve_colmap_executable()
    openmvs_dir = resolve_openmvs_bin()
    version_str = get_colmap_version(colmap_exec)

    return {
        "colmap_available": colmap_exec is not None,
        "colmap_executable": colmap_exec,
        "colmap_version": version_str,
        "openmvs_available": openmvs_dir is not None,
        "openmvs_dir": str(openmvs_dir) if openmvs_dir else None,
        "os": os.name,
    }


def execute_colmap_command(cmd: List[str], cwd: Optional[str] = None, timeout: int = 60) -> subprocess.CompletedProcess:
    """
    Executes a photogrammetry subprocess command with comprehensive structured logging.
    Logs:
      - COLMAP_COMMAND_START
      - COLMAP_COMMAND_EXIT
      - COLMAP_STDOUT
      - COLMAP_STDERR
    """
    colmap_exec = resolve_colmap_executable()
    openmvs_bin = resolve_openmvs_bin()

    env = os.environ.copy()
    extra_paths = []
    if openmvs_bin:
        extra_paths.append(str(openmvs_bin))
    if colmap_exec:
        extra_paths.append(str(Path(colmap_exec).parent))

    if extra_paths:
        env["PATH"] = os.pathsep.join(extra_paths) + os.pathsep + env.get("PATH", "")

    cmd_str = " ".join(map(str, cmd))
    print(f"[COLMAP_COMMAND_START] {cmd_str}")
    logger.info(f"COLMAP_COMMAND_START: {cmd_str}")
    start_t = time.time()

    try:
        result = subprocess.run(
            list(map(str, cmd)),
            env=env,
            cwd=cwd,
            text=True,
            capture_output=True,
            timeout=timeout,
        )
        duration = round(time.time() - start_t, 2)
        print(f"[COLMAP_COMMAND_EXIT] Code={result.returncode} Duration={duration}s")
        if result.stdout.strip():
            print(f"[COLMAP_STDOUT] {result.stdout.strip()}")
        if result.stderr.strip():
            print(f"[COLMAP_STDERR] {result.stderr.strip()}")

        if result.returncode != 0:
            raise RuntimeError(
                f"COLMAP command failed with exit code {result.returncode}.\n"
                f"Command: {cmd_str}\n"
                f"STDOUT: {result.stdout}\n"
                f"STDERR: {result.stderr}"
            )
        return result

    except subprocess.TimeoutExpired as e:
        duration = round(time.time() - start_t, 2)
        print(f"[COLMAP_COMMAND_EXIT] TIMEOUT ({timeout}s) Duration={duration}s")
        print(f"[COLMAP_STDERR] Process timed out after {timeout} seconds")
        raise RuntimeError(f"Command timed out after {timeout}s: {cmd_str}") from e
    except Exception as e:
        duration = round(time.time() - start_t, 2)
        print(f"[COLMAP_COMMAND_EXIT] EXCEPTION: {e} Duration={duration}s")
        raise

