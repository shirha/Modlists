from pathlib import Path
import logging
import re
from exiftool import ExifToolHelper
from static import get_product_version, get_mo_game_info
from collections import defaultdict

def find_game_versions(
    game: str,
    et: ExifToolHelper,
    cache: dict,
    parms: dict,
    rename_modlist: dict
) -> dict:

    logger = logging.getLogger(__name__) 
    root_path = Path(fr"O:\Wabbajack\{game}")
    if not root_path.exists():
        logger.error(f"Directory {root_path} does not exist.")
        return {}

    target_exe = game + '.exe'
    results = []

    for modlist_dir in filter(Path.is_dir, root_path.iterdir()):
        # logger.info(modlist_dir)

        # --- Profiles ---
        profiles = []
        profiles_dir = modlist_dir / "profiles"
        if profiles_dir.exists():
            profiles = [
                p.name for p in profiles_dir.iterdir()
                if (p / "modlist.txt").exists()
            ]

        # --- MO2 Version ---
        _, mo2_version = get_product_version(
            modlist_dir / "ModOrganizer.exe",
            et,
            cache
        )
        if mo2_version: 
            mo2_version = re.findall(r'\d\.\d\.\d', mo2_version)[0]

        # --- Game Info (STRICT mo.ini logic) ---
        folder, product_version = get_mo_game_info(
            modlist_dir,
            target_exe,
            et,
            cache
        )

        # --- Normalize Modlist Name ---
        dirname = modlist_dir.name
        version = None
        match = re.match(r"^(.+?) (\d+(?:\.\d+){1,3})$", dirname)
        if match:
            dirname = match.group(1)
            version = match.group(2)

        dirname = rename_modlist.get(dirname, dirname)

        results.append({
            "Modlist": dirname,
            "Installed Version": version or "",
            "MO2 Version": mo2_version or "",
            "Product Version": product_version,
            "Folder": folder,
            "Profile": profiles,
        })

    logger.info(f"find_game_versions: {game} {len(results)}")
    # return {item["Modlist"]: item for item in results}

    def group_versions(results: list[dict]) -> dict:
        grouped = defaultdict(dict)

        for item in results:
            modlist = item["Modlist"]
            version = item["Installed Version"]
            grouped[modlist][version] = item

        return dict(grouped)

    return group_versions(results)