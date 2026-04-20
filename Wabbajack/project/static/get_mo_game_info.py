from pathlib import Path
import configparser
from typing import Optional, Tuple
import logging
# import json
import re
from exiftool import ExifToolHelper
from static import get_product_version

def normalize_drive(path: Path) -> Path:
    """
    Remap F: → O: for backup environment
    """
    try:
        if path.drive.upper() in ["F:","C:"]:
            return Path("O:" + path.as_posix()[2:])
    except Exception:
        pass
    return path

def parse_game_path(raw_path: Optional[str]) -> Optional[Path]:
    if not raw_path:
        return None

    path = raw_path.strip().strip('"')

    # --- Extract @ByteArray(...) ---
    if path.startswith("@ByteArray(") and path.endswith(")"):
        path = path[len("@ByteArray("):-1]

    # --- Fix escaped backslashes ---
    path = path.replace("\\\\", "\\")

    return Path(path)

def get_mo_game_info(
    modlist_dir: Path,
    exe_name: str,
    et: ExifToolHelper,
    cache: dict
) -> Tuple[str, str]:
    """
    Returns:
        (folder, product_version)

    Rules:
    - Use ONLY mo.ini (ModOrganizer.ini)
    - If exe is inside modlist_dir → return relative folder + version
    - If exe is outside → return absolute gamePath + blank version
    """

    logger = logging.getLogger(__name__) 
    ini_path = modlist_dir / "ModOrganizer.ini"
    if not ini_path.exists():
        return "", ""

    config = configparser.ConfigParser()

    try:
      # config.read(ini_path)
        with open(ini_path, encoding="utf-8-sig") as f:
            config.read_file(f)
        raw_game_path = config.get("General", "gamePath", fallback=None)
        # logger.info(f"raw_game_path= {raw_game_path}")
        game_path = parse_game_path(raw_game_path)

        if not game_path:
            return "", ""

        # just use game_path.parent for all Folder values

        # exe_path = game_path / exe_name
        game_path = normalize_drive(game_path).parts[-1] # .parent # windows object
        exe_path = modlist_dir / game_path / exe_name
        # logger.info(f"game_path= {exe_path}")

        if exe_path.is_file():
            try:
                # rel = normalize_drive(exe_path.parent.resolve()).relative_to(modlist_dir.resolve())
                # inside modlist → return relative folder + version
                _, product_version = get_product_version(exe_path, et, cache)
                return game_path, product_version or ""
                # return rel.name, product_version or ""

            except ValueError:
                # outside modlist → absolute path, blank version
                return game_path, ""

        # exe missing → treat as external
        return game_path, ""

    except Exception as e:
        logger.warning(f"{modlist_dir}: failed to read mo.ini: {e}")
        return "", ""
