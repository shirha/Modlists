import os
import re
import glob
import json
import logging
import configparser
import shutil
import pprint
import markdown
from flask import Flask, render_template, request, jsonify, session
from pathlib import Path
from html import escape
from datetime import datetime
from typing import Optional, Tuple
from collections import defaultdict, Counter
from packaging.version import Version
from concurrent.futures import ThreadPoolExecutor, as_completed
from static import generate_modlist_html, get_product_version, get_mo_game_info, find_game_versions
try:
    from exiftool import ExifToolHelper
    EXIFTOOL_AVAILABLE = True
except ImportError:
    EXIFTOOL_AVAILABLE = False

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Required for session management

# Configuration
CURRENT_DATE_NOW = datetime.now().strftime('%y%m%d')
OUTPUT_LOG_DIR = r"O:\Wabbajack\project\logs"
ARCHIVE_DIR = r"O:\Wabbajack\Archive"
ICON_DIR = r"static/icons"
EXIFTOOL_PATH = r"C:\Users\xxxxxx\miniforge3\envs\opencv\bin\exiftool.exe"

parms = {
    'Fallout4': {'json': 'Fallout 4',              'nexus': 'fallout4'},
    'SkyrimSE': {'json': 'Skyrim Special Edition', 'nexus': 'skyrimspecialedition'},
}
meta_key = {"SkyrimSpecialEdition":"SkyrimSE", "Fallout4":"Fallout4"}

rename_modlist = {
    "ADT": "Althro's Dev Tools",
    "CSVO - Community Shaders Visual Overhaul": "CSVO",
    "Worromot - Tamriel gone off the skooma again": "Worromot",
    "Fallout 4 NG Curated": "Fallout 4 NG Curated2",
    "Ashveil - Eine Deutsche Modliste": "Ashveil",
    "Horizon - Official Modlist": "Horizon",
    "Sim Settlements 2 City Plan Contest Helper": "Sim Settlement 2",
    "Worromot - Tamriel gone off the skooma again":"Worromot - off skooma",
    "Fallout Anomaly - True Survival": "Fallout Anomaly",
    "Gate to Sovngarde AE Version": "Gate to Sovngarde",
    "Mad God Overhaul": "Mad Gods Overhaul SFW",
    "CSVP - A NGVO Fork": "CSVP Vanilla",
    "Aurora":"Aurora - A Visual Overhaul"
}

discord = { # use if repo is wj-featured_*.wabbajack.metadata
# Alpyne, Althro's Dev Tools, Aurora - A Visual Overhaul, Cursedelica, Legends of the Frost, Skyrim Modding Essentials, Slidikins' Strenuous Skyrim, The Old North, The Phoenix Flavour, Untitled Skyrim Modlist
    "https://discord.gg/xRrHRsb5e9": {"server_name": "Aetherius Modding"},    # "modlist": ["The Phoenix Flavour"]},
    "https://discord.gg/yABEjwB":    {"server_name": "Lively’s Modding Hub"}, # "modlist": ["Tempus Maledictum", "Magnum Opus"]},
    "https://discord.gg/FAfPb9T":    {"server_name": "Elysium - Aldrnari"},   # "modlist": ["Aldrnari", "Elysium Remastered"]},
    "https://discord.gg/esGVnCjWpJ": {"server_name": "Scenic Route Games"},   # "modlist": ["Librum SE"]},
    "https://discord.gg/WKZgPuxvHS": {"server_name": "ForgottenGlory"},       # "modlist": ["Living Skyrim", "Zenithar's Forge"]},
    "https://discord.gg/JycmyqzZz7": {"server_name": "Requiem - Wabbajack"},  # "modlist": ["Nocturnia", "Wanderlust"]},
    "https://discord.gg/vKuB7nazBk": {"server_name": "The Astral Forge"},     # "modlist": ["Wunduniik"]},
}

# Set up logging
log_file = os.path.join(OUTPUT_LOG_DIR, f"flask_app_{CURRENT_DATE_NOW}.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file, encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

def store_func(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return path, json.load(f)
    except (json.JSONDecodeError, OSError):
        return path, None

def read_store_stream(file_list, store_func):
    total = len(file_list)
    completed = 0

    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(store_func, f) for f in file_list]

        for future in as_completed(futures):
            try:
                path, data = future.result()
                yield path, data
            except Exception as e:
                print(f"\nFailed: {e}")
                continue

            completed += 1
            print(f"\rProcessed: {completed}/{total}", end="")

    print()


# ---- stream all meta to meta_store ----

meta_files = list(Path(ARCHIVE_DIR).glob("*.wabbajack.metadata"))
meta_store = defaultdict(dict)
meta_notekeys = set()

for path, data in read_store_stream(meta_files, store_func):
    if not data:
        continue

    raw_title = data.get("title", "")
    title = rename_modlist.get(raw_title, raw_title)
    version = data.get("version", "")
    repository_name = data.get("repositoryName", "")
    machine_url = data.get("links", {}).get("machineURL", "")
    base_path = f"{repository_name}_{machine_url}"

    meta_notekeys.add(f"{title} {version}")
    meta_store[base_path][version] = data

logger.info(f"Streamed all metadata files {len(meta_files)}")

with open("meta_store.json", "w", encoding="utf-8") as f:
    json.dump(meta_store, f, indent=2)

# ---- filter json to most current match ----
json_files = Path(ARCHIVE_DIR).glob("*.json")
token = defaultdict(list)
match_files = {}

def max_common_version(meta, json):
    meta_versions = {Version(v) for v in meta}
    json_versions = set(json) # {Version(v) for v in json}
    
    common = meta_versions & json_versions
    return str(max(common)) if common else None

for json_file in json_files:
    match = re.match(r"^(.+?) (\d+(?:\.\d+){1,3})$", json_file.stem)
    if match:
        path = match.group(1)
        version = match.group(2)
        token[path].append(Version(version))
      # if version in meta_store[path]:
        if max_common_version(meta_store[path].keys(), token[path]) == version:
            match_files[path] = str(json_file)

logger.info(f'Total json files {len(glob.glob("/Wabbajack/Archive/*.json"))}')
logger.info(f'Filter w/ max_common_version()')
#
# -------------------------------------------
#
json_store = []

for path, data in read_store_stream(match_files.values(), store_func):
    if not data:
        continue

    json_store.append(data)

logger.info(f"Streamed filtered json files {len(json_store)}")

# with open("json_store.json", "w", encoding="utf-8") as f:
#     json.dump(json_store, f, indent=2)
# quit()

#
# ---- load list reviews -----------------
#
note_files = Path('notes').glob("*.md")
note_store = {path.stem: path.read_text(encoding='utf-8') for path in note_files}

for note in note_store:
    if not note in meta_notekeys:
        logger.info(f"Note missing meta '{note}'")

logger.info(f"Streamed all notes files {len(note_store)}")
#
# ---- Detail json archives mods list ----
#
def build_json_detail(): 
    ext_counter = Counter()
    archive_names = {
        'Fallout4': defaultdict(list),
        'SkyrimSE': defaultdict(list),
    }

    for json_data in json_store:
        base_path = json_data.get("MachineURL").replace("/","_")
        json_version = json_data.get("Version")
        game = meta_key.get(meta_store[base_path][json_version].get("game"))

        modlist_name = json_data.get("Name", "")
        modlist_name = rename_modlist.get(modlist_name, modlist_name)
        archives = json_data.get("Archives", [])

        for archive in archives:
            original = archive.get("Original", {})
            archive_name = original.get("Name", "").strip()

            if not archive_name:
                continue
            ext = archive_name.rsplit('.', 1)[-1]
            if ext in {'ba2','bsa','js','dll','ini','html','exe','png','bk2','css','tlx','cdx','csg','ccc','vdf','txt','bik','gif','clx','bat','jpg','log','dat','json','cdf','pdf','py','php','ico','xml','cfg','config','cs','xsd','esf','pdb'}:
                continue

            state = original.get("State", {})
            game_file = state.get("GameFile", "")
            mod_id = state.get("ModID", "")
            file_id = state.get("FileID", "")

            if game_file or (mod_id and file_id):
                if mod_id and file_id:
                    archive_names[game][modlist_name].append(
                        f'<a href="https://www.nexusmods.com/{parms[game]["nexus"]}/mods/{mod_id}" target="_blank">{archive_name}</a> <span>{file_id}</span>'
                    )
                else:
                    archive_names[game][modlist_name].append(archive_name)
                    ext = archive_name.rsplit('.', 1)[-1]
                    ext_counter.update([ext])

    # ---- Final formatting ----
    logger.info("* json archives \033[33mw/o\033[0m modids *")
    for char, count in ext_counter.most_common():
        logger.info(f"{repr(char):4}: {count}")
    # research Curated2 West Tek in Detail vs modlist.txt

    results = {}

    for game in archive_names:
        sorted_archive_names = [
            f"<b>{modlist}</b>: {archive}"
            for modlist in sorted(archive_names[game], key=lambda x: x.lower())
            for archive in archive_names[game][modlist]
        ]

        results[game] = sorted_archive_names

    return results

def format_size(size: int) -> str:
    if size == 0:
        return "0b"

    for unit in ("b", "k", "m", "g", "t"):
        if size < 1024 or unit == "t":
            return f"{int(size)}{unit}" if unit == "b" else f"{size:.1f}{unit}"
        size /= 1024

def tag_type(search_path):
    tags_list = {'SkyGround Chronicles':'Requiem','WakingDreams/fahluaan':'SimonRim','Geborgen/nordic-souls': 'SimonRim', 'Animonculory/noct': 'Requiem', 'LostOutpost/lostlegacy': 'EnaiRim', 'wj-featured/sss': 'SimonRim', 'Just_Another_Requiem_List/Just_Another_Requiem_List': 'Requiem', 'NGVO/DNGG': 'Requiem', 'LoreRim/LoreRim': 'Requiem', 'wj-featured/arkayscommandment': 'Requiem', 'HoS/HoS': 'Requiem', 'wj-featured/aldrnari': 'EnaiRim', 'SkyFurry_NG-Otherkin/SkyFurry-NG---Otherkin': 'SimonRim', 'LostOutpost/windsofthenorth': 'SimonRim', 'LostOutpost/arcanaeum': 'SimonRim', 'Dying_Breath/ViirSuum': 'Requiem', 'Elysium/elysium': 'EnaiRim', 'Wildlander/wildlander': 'Requiem'}
    return tags_list.get(search_path,"")

#
# ---- Summary info - profiles, links ----
#
def build_meta_summary(): 
    results = {"Fallout4": [], "SkyrimSE": []}

    # base_path not title
    for base_path, versions in meta_store.items():
      for version, meta_data in versions.items():

        game = meta_data.get("game")
        if game not in meta_key:
            continue

        game_key = meta_key[game]

        raw_title = meta_data.get("title", base_path)
        title = rename_modlist.get(raw_title, raw_title)

        repository_name = meta_data.get("repositoryName", "")
        repository = escape(repository_name)

        machine_url = meta_data.get("links", {}).get("machineURL", "")
        search_path = f"{repository_name}/{machine_url}"
        # base_path = f"{repository_name}_{machine_url}"
        meta_version = meta_data.get("version", "")
        archive_count = meta_data.get("download_metadata", {}).get("NumberOfArchives", 0)
        install_size = format_size(meta_data.get("download_metadata", {}).get("SizeOfInstalledFiles", 0))

        # ---- links ----
        links = meta_data.get("links", {})
        link_html = []
        profile_links = []

        if links.get("image"):
            link_html.append(f'<a href="image/{base_path}@{meta_version}" target="_blank"><img src="{ICON_DIR}/scenic.png" alt="Image" class="icon"></a>')

        if links.get("discordURL"):
            discord_url = escape(links["discordURL"])
            link_html.append(f'<a href="{escape(links["discordURL"])}" target="_blank"><img src="{ICON_DIR}/discord.png" class="icon"></a>')

        if links.get("readme"):
            readme_url = escape(links["readme"])
            link_html.append(f'<a href="{readme_url}" target="_blank"><img src="{ICON_DIR}/github.png" alt="GitHub" class="icon"></a>')

        if links.get("websiteURL"):
            website_url = escape(links["websiteURL"])
            link_html.append(f'<a href="{website_url}" target="_blank"><img src="{ICON_DIR}/nexusmod.png" alt="Nexus Mods" class="icon"></a>')

        tag_icon, tag = ('', tag_type(search_path))
        if tag: 
            tag_icon = (f'<img src="{ICON_DIR}/{tag.lower()}.png" alt="Nexus Mods" class="icon">')

        # ---- version info ----
        version_key_info = db[game_key]['version_data'].get(title, {})
        version_info = (
            version_key_info.get(meta_version)
            or version_key_info.get("")
            or {}
        )

        profiles = version_info.get("Profile", [])

        for profile in profiles:
            profile_links.append(
                f'<a href="/modlist/{title}?profile={escape(profile)}&version={escape(meta_version)}" target="_blank">'
                f'<img src="{ICON_DIR}/mo2.png" class="icon"> {escape(profile)}</a>'
            )

        # ---- JSON version comparison ----
        json_v = token[base_path]
        meta_v = Version(meta_version)

        if meta_v in json_v:
            if meta_v < max(json_v):
                jv_cls = "jv_upg"
            else:
                jv_cls = "jv_ok"
        else:
            jv_cls = "jv_not"

        tip = str([str(x) for x in sorted(json_v)])
        note_link = ""
        note_key = f"{title} {version}"
        safe_note_key = note_key.replace("'", "\\'")
        note_data = note_store.get(note_key, "")
        if note_data:
            # print(safe_note_key)
            note_link = f'''
                <a href="#" onclick="showNoteModal('{safe_note_key}'); return false;">
                    <img src="{ICON_DIR}/note.png" alt="Note" class="icon zero">
                </a>'''            

        title_html = f'''
            <div class="title-row">
                <div title="{search_path}" class="title">{title}</div>
                {note_link}
            </div>'''

        results[game_key].append({ 
            "sort_key": [title.lower(), Version(version)],
            "title": title_html,
            "repository": discord.get(discord_url, {}).get("server_name", f'<span class="repo">{repository}</span>'),
            "archive_count": archive_count,
            "install_size": install_size,
            "version": f'<div class="{jv_cls}" title="{tip}"><a href="json/{base_path}@{version}" target="_blank">{version}</a></div>',
            "mo2_version": version_info.get("MO2 Version", ""),
            "product_version": version_info.get("Product Version", ""),
            "tag_icon": tag_icon,
            "profile_links": profile_links,
            "links": " ".join(link_html),
        })

    return results

# 1. Scan backup directories
db = {}
version_cache: dict[Path, tuple[str | None, str | None]] = {}

with ExifToolHelper(executable=EXIFTOOL_PATH) as et:
    for game in parms:
        db[game] = {
            "version_data": find_game_versions(game, et, version_cache, parms, rename_modlist)
        }

logger.info("w/ profiles, game.exe versions")

with open("bkup_scan.json", "w", encoding="utf-8") as f:
    json.dump({g:db[g]['version_data'] for g in parms}, f, indent=2)

# 2. Builds archives from json filtered list
archives = build_json_detail()

for game in parms:
    db[game]['archives'] = archives[game]

logger.info(f"build json detail")

# 3. Build modlists (uses "version_data")
modlists = build_meta_summary()

for game in parms:
    db[game]['modlists'] = sorted(modlists[game], key=lambda x: x["sort_key"])

logger.info("build meta summary")
logger.info("w/ profiles, game.exe versions")
logger.info("Initialization completed successfully")

import static.simple_report as rpt
rpt_data = rpt.run(parms,db,meta_store,token,rename_modlist)
# with open("simple_report.txt", "w", encoding="utf-8") as f:
#     simple_report_data = rpt.run(parms,db,meta_store,token,rename_modlist)
#     f.write(simple_report_data)

# Routes
@app.route("/")
def index():
    return render_template(
        "index.html",
        game=game, 
        gametitle=parms[game]['json'],
        modlists=db[game]['modlists'], # summary
        archives=db[game]['archives'], # detail
    )

@app.route('/toggle_game', methods=['POST'])
def toggle_game():
    global game
    data = request.get_json()
    game = data.get('game')
    
    if game not in parms:
        return jsonify({'success': False, 'error': 'Invalid game specified.'}), 400
    
    # Update session with the new game
    session['game'] = game
    return jsonify({'success': True})

@app.route("/modlist/<modlist_name>")
def modlist_details(modlist_name):
    profile = request.args.get("profile", None)
    version = request.args.get("version", None)
    logger.info(f"Generating modlist details for {modlist_name}, profile: {profile}, version: {version}")
    html_content = generate_modlist_html(game, modlist_name, version, profile)
    if html_content:
        return html_content
    logger.error(f"Failed to generate HTML for {modlist_name}, profile: {profile}")
    return f"Error generating modlist details for {modlist_name}", 500

@app.route('/json/<modlist_name>')
def modlist_json(modlist_name):
    match = re.match(r"^(.+?)@(\d+(?:\.\d+){1,3})$", modlist_name)
    if match:
        title = match.group(1)
        version = match.group(2)
        data = meta_store[title][version]
        return f"<pre>{json.dumps(data, indent=4)}</pre>"
    return f"Error generating metadata {modlist_name}", 500

@app.route('/image/<modlist_name>')
def modlist_image(modlist_name):

    match = re.match(r"^(.+?)@(\d+(?:\.\d+){1,3})$", modlist_name)
    if match:
        title = match.group(1)
        version = match.group(2)
        data = meta_store[title][version]

        image_url = escape(data.get("links", {}).get("image"))
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} Image</title>
    <style>
        html, body {{margin: 0; padding: 0; overflow-y: scroll; overflow-x: hidden; 
                     scrollbar-width: none; -ms-overflow-style: none;}}
        html::-webkit-scrollbar, body::-webkit-scrollbar {{display: none;}}
        img {{width: 100%; height: auto; display: block;}}
    </style>
</head>
<body class="no-scrollbar">
    <img src="{image_url}" alt="{title} Banner">
</body>
</html>
"""
    return f"Error generating image {modlist_name}", 500

doc_style = f"<style>pre{{margin:20px;}}</style>"
@app.route('/viewrpt')
def view_rpt():
    return f"<style>pre{{margin:20px;}}</style>\n<pre>{rpt_data}</pre>"

@app.route('/viewdoc')
def view_doc():
    doc_path = Path(R"O:\Wabbajack\project\docs\readme.md")
    doc_data = markdown.markdown(doc_path.read_text(encoding='utf-8')) 
    return f"<style>.con{{margin:20px;width:450px;}}</style>\n<div class='con'>{doc_data}</div>"

@app.route('/note/<modlist_name>')
def modlist_note(modlist_name):

    return markdown.markdown(note_store[modlist_name])

if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)

