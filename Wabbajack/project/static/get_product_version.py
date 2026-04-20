from pathlib import Path
import logging
from exiftool import ExifToolHelper

def get_product_version(
    file_path: Path,
    et: ExifToolHelper,
    cache: dict[Path, tuple[str | None, str | None]]
) -> tuple[str | None, str | None]:

    logger = logging.getLogger(__name__) 
    file_path = file_path.resolve()

    if file_path in cache:
        return cache[file_path]

    if not file_path.is_file():
        if "ModOrganizer" not in file_path.name:
            logger.error(f"File not found: {file_path}")
        cache[file_path] = (None, None)
        return cache[file_path]

    try:
        metadata = et.get_metadata(str(file_path))

        if not metadata or not isinstance(metadata, list) or not metadata[0]:
            logger.warning(f"No valid metadata returned for {file_path}")
            cache[file_path] = (None, None)
            return cache[file_path]

        data = metadata[0]

        result = (
            data.get("EXE:FileVersion"),
            data.get("EXE:ProductVersion"),
        )

        cache[file_path] = result
        return result

    except Exception as e:
        logger.error(f"Error retrieving version for {file_path}: {e}")
        cache[file_path] = (None, None)
        return cache[file_path]
