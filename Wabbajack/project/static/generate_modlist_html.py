from pathlib import Path
from html import escape
import configparser
import logging
import re

# required to have logging in caller!

def generate_modlist_html(game, modlist, version, profile):
    logger = logging.getLogger(__name__) 
    MODLIST_HTML_VERSION = "/* version 3.1.1 */"

    base_dir = Path('/Wabbajack')
    output_dir = base_dir / 'Modlists'
    modlist_dir = base_dir / game / f'{modlist} {version}'

    if not modlist_dir.exists():
        logger.info(f"Trying '{modlist}' directory \033[33mWITHOUT\033[0m the version {version}")
        modlist_dir = base_dir / game / modlist

    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / f'mods_{modlist} ({profile}) {version}.html'

    # Reuse existing file if already generated
    if output_path.exists():
        html_content = output_path.read_text(encoding='utf-8')
        if MODLIST_HTML_VERSION in html_content:
            return html_content

    # --- Read modlist.txt ---
    modlist_file = modlist_dir / 'profiles' / profile / 'modlist.txt'
    logger.info(modlist_file)

    try:
        modlist_lines = [
            line.strip()
            for line in modlist_file.read_text(encoding='utf-8').splitlines()
            if line.strip() and not line.startswith('#')
        ]
        modlist_lines.reverse()
        logger.info(f"Read {len(modlist_lines)} lines from {modlist_file}")
    except Exception as e:
        logger.error(f"Error reading {modlist_file}: {e}")
        exit(1)

    # --- Process meta.ini files ---
    mod_data = {}
    mods_dir = modlist_dir / 'mods'

    for line in modlist_lines:
        if line.endswith('_separator'):
            continue

        prefix = line[0] if line[0] in ['-', '+', '*'] else ''
        mod_name = line[1:].strip() if prefix else line.strip()

        meta_path = mods_dir / mod_name / 'meta.ini'

        if meta_path.exists():
            try:
                config = configparser.ConfigParser()
                config.read(meta_path)

                mod_id = config.get('General', 'modid', fallback='')
                file_id = config.get('installedFiles', r'1\fileid', fallback='')

                if mod_id and file_id:
                    mod_data[mod_name] = {
                        'mod_id': mod_id,
                        'file_id': file_id
                    }
                    logger.info(f"Indexed mod: {mod_name}, ModID={mod_id}, FileID={file_id}")
                else:
                    logger.warning(f"Missing modid or fileid in {meta_path}")

            except Exception as e:
                logger.error(f"Error parsing {meta_path}: {e}")
        else:
            logger.warning(f"meta.ini not found for mod: {mod_name} at {meta_path}")

    # --- Generate HTML ---
    game_nexus = 'skyrimspecialedition' if game == 'SkyrimSE' else 'fallout4'

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mods for {modlist} ({profile}) {version}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <style> {MODLIST_HTML_VERSION}
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .list-group {{ max-height: 750px; overflow-y: auto; border: 1px solid #ccc; padding: 10px; margin-top: 10px; }}
        .list-group-item {{ word-break: break-all; }}
        img.icon {{ width: 20px; height: 20px; object-fit: contain; vertical-align: middle; margin-right: 5px; }}
        a {{ text-decoration: none; }}
    </style>
</head>
<body>
    <h1>Mods for {modlist} ({profile}) {version}</h1>
    <ul id="archiveList" class="list-group">
"""

    for line in modlist_lines:
        if line.endswith('_separator'):
            separator_name = line[1:-len('_separator')].strip()
            html_content += f'        <li class="list-group-item list-group-item-secondary">&mdash; {escape(separator_name)}</li>\n'
            logger.info(f"Processed separator: {separator_name}")
            continue

        prefix = line[0] if line[0] in ['-', '+', '*'] else ''
        mod_name = line[1:].strip() if prefix else line.strip()

        if mod_name in mod_data:
            mod_id = mod_data[mod_name]['mod_id']
            file_id = mod_data[mod_name]['file_id'] or ""

            if file_id == "0":
                file_id = ""

            if mod_id and mod_id != "0":
                html_content += (
                    f'        <li class="list-group-item">{prefix} '
                    f'<a target="_blank" href="https://www.nexusmods.com/{game_nexus}/mods/{mod_id}">'
                    f'{escape(mod_name)}</a> {file_id}</li>\n'
                )
                logger.info(f"Linked mod: {mod_name}, ModID={mod_id}, FileID={file_id}")
                continue

        html_content += f'        <li class="list-group-item"><i>{prefix} {escape(mod_name)}</i></li>\n'
        logger.info(f"Unmatched mod: {mod_name}")

    html_content += """    </ul>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""

    # --- Save HTML ---
    try:
        output_path.write_text(html_content, encoding='utf-8')
        logger.info(f"Saved HTML to {output_path}")
    except Exception as e:
        logger.error(f"Error writing {output_path}: {e}")
        exit(1)

    logger.info(f"Generated HTML for {modlist} with {len(modlist_lines)} entries")
    return html_content
