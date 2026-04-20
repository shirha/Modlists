from pathlib import Path
import json
import requests
import shutil
from typing import Dict, Any, Optional

# 1) move all /downloaded_mod_lists/(*.wabbajack, *.metadata) to Archive
# 2) get current app detail from raw.github*/{search_path}/status.json

COMMAND = 'move-metadata' # 'update-json-only' #
METADATA_DIR = Path(r"O:\Wabbajack\4.1.0.0\downloaded_mod_lists")
ARCHIVE_DIR = Path(r"O:\Wabbajack\Archive")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Referer": "https://www.wabbajack.org/",
}


def fetch_status_json(repository_name: str, machine_url: str) -> Optional[Dict[str, Any]]:
    """Fetch status.json. Returns None if the request fails."""
    if not repository_name or not machine_url:
        return None

    search_path = f"{repository_name}/{machine_url}"
    status_url = f"https://raw.githubusercontent.com/wabbajack-tools/mod-lists/master/reports/{search_path}/status.json"
    
    print(f"Fetching status for: {search_path}")

    try:
        response = requests.get(status_url, headers=HEADERS, timeout=10)
        response.raise_for_status()           # Still raises on HTTP errors
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"    → Failed to fetch status for {search_path}: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"    → Invalid JSON received for {search_path}: {e}")
        return None


def process_metadata_file(meta_file: Path) -> None:
    """Process a single .wabbajack.metadata file."""
    try:
        with meta_file.open("r", encoding="utf-8") as f:
            data = json.load(f)

        repository_name = data.get("repositoryName", "")
        machine_url = data.get("links", {}).get("machineURL", "")
        version = data.get("version", "0.0.0")

        if not repository_name or not machine_url:
            print(f"Skipping {meta_file.name}: missing repositoryName or machineURL")
            return

        base_name = f"{repository_name}_{machine_url}"

        # Try to fetch status JSON (but continue even if it fails)
        status_data = fetch_status_json(repository_name, machine_url)
        
        if status_data:
            status_version = status_data.get("Version", "0.0.0")
            status_dest = ARCHIVE_DIR / f"{base_name} {status_version}.json"

            with status_dest.open("w", encoding="utf-8") as f:
                json.dump(status_data, f, indent=2)
            print(f"    ✓ Saved status JSON (v{status_version})")
        else:
            print(f"    ⚠ No status JSON saved for {base_name}")

        # Always move the files regardless of status fetch success
        metadata_dest = ARCHIVE_DIR / f"{base_name} {version}.wabbajack.metadata"
        wabbajack_dest = ARCHIVE_DIR / f"{base_name} {version}.wabbajack"

        wabbajack_file = meta_file.with_suffix("")   # removes .metadata

        if COMMAND.startswith("m"):
            with meta_file.open("w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            shutil.move(str(meta_file), str(metadata_dest))
            shutil.move(str(wabbajack_file), str(wabbajack_dest))

            print(f"✓ Moved files for: {base_name} (v{version})\n")

    except Exception as e:
        print(f"✗ Error processing {meta_file.name}: {e}\n")


def main() -> None:
    """Main entry point."""
    metadata_files = list(METADATA_DIR.glob("*.wabbajack.metadata"))

    print(f"METADATA_DIR = {str(METADATA_DIR)}")
    print(f"ARCHIVE_DIR  = {str(ARCHIVE_DIR)}")
    print(f"Found {len(metadata_files)} metadata files")
    print(json.dumps([str(p) for p in metadata_files],indent=4))
    
    print('''
    [m] COMMAND = 'move-metadata' 
    [u] COMMAND = 'update-json-only'
    [enter] exit\n''')

    choice = input("What do you want to set COMMAND to? m,u: ").lower()

    # Map choices to commands
    commands = {'m': 'move-metadata', 'u': 'update-json-only'}
    COMMAND = commands.get(choice)

    print(COMMAND or 'exit')
    if COMMAND is None:
        exit()

    if choice == 'm' and not metadata_files:
            print("No .wabbajack.metadata files found.")
            return

    for meta_file in metadata_files:
        process_metadata_file(meta_file)

    print("Processing completed!")


if __name__ == "__main__":
    main()


R'''
❌ VERSION MISMATCH BETWEEN METADATA and Github JSON ❌

(opencv) O:\Wabbajack\project>python read_meta2.py
Found 1 metadata files. Starting processing...

Fetching status for: SkyGround_Chronicles/SkyGround
    ✓ Saved status JSON (v3.2.4)              <-------------- changed to 3.2.5
✓ Moved files for: SkyGround_Chronicles_SkyGround (v3.2.5)

Processing completed!



    for meta_file in ARCHIVE_DIR.glob("*.wabbajack.metadata"):
        json_file = json.loads(meta_file.read_text(encoding='utf-8'))
        (ARCHIVE_DIR / meta_file).write_text(json.dumps(json_file, indent=2), encoding='utf-8')


(opencv) O:\Wabbajack\Modlists\project>python read_meta2.py
Found 1 metadata files. Starting processing...

Fetching status for: BtHz/HzOff
    ✓ Saved status JSON (v1.4.3)
✓ Moved files for: BtHz_HzOff (v1.4.3)

Processing completed!

(opencv) O:\Wabbajack\Modlists\project>python read_meta2.py
Found 5 metadata files. Starting processing...

Fetching status for: Cistern/CSVO
    ✓ Saved status JSON (v2.2.0)
✓ Moved files for: Cistern_CSVO (v2.1.1)

Fetching status for: FUSION/FUSION
    ✓ Saved status JSON (v2.1.3)
✓ Moved files for: FUSION_FUSION (v2.1.3)

Fetching status for: Gate_to_Sovngarde/GateToSovngarde_WJ_AE
    ✓ Saved status JSON (v0.101.0)
✓ Moved files for: Gate_to_Sovngarde_GateToSovngarde_WJ_AE (v0.101.0)

Fetching status for: Kahnezzer/OldNewEngland
    ✓ Saved status JSON (v1.2)
✓ Moved files for: Kahnezzer_OldNewEngland (v1.2)

Fetching status for: WakingDreams/ANVIL
    ✓ Saved status JSON (v3.1.1)
✓ Moved files for: WakingDreams_ANVIL (v3.1.1)

Processing completed!

(opencv) O:\Wabbajack\Modlists\project>python read_meta2.py
Found 85 metadata files. Starting processing...

Fetching status for: AD/auriels_dream_ae
    ✓ Saved status JSON (v1.0.4)
✓ Moved files for: AD_auriels_dream_ae (v1.0.1)

Fetching status for: Animonculory/ADT
    ✓ Saved status JSON (v9.0.1)
✓ Moved files for: Animonculory_ADT (v8.0.0)

Fetching status for: Animonculory/aur
    ✓ Saved status JSON (v1.5.6)
✓ Moved files for: Animonculory_aur (v1.5.6)

Fetching status for: Animonculory/Curseadelica
    ✓ Saved status JSON (v3.23)
✓ Moved files for: Animonculory_Curseadelica (v3.23)

Fetching status for: Animonculory/noct
    ✓ Saved status JSON (v2.0.2)
✓ Moved files for: Animonculory_noct (v2.0.2)

Fetching status for: Ash_Lotus/AshLotus
    ✓ Saved status JSON (v1.3)
✓ Moved files for: Ash_Lotus_AshLotus (v1.2.3)

Fetching status for: Beowulf/beowulf
    ✓ Saved status JSON (v2.1.0)
✓ Moved files for: Beowulf_beowulf (v1.1.1)

Fetching status for: BtHz/HzOff
    ✓ Saved status JSON (v1.4.3)
✓ Moved files for: BtHz_HzOff (v1.3)

Fetching status for: CapitalCommonwealth/mt4lcapitalcommonwealth
    ✓ Saved status JSON (v1.1.0)
✓ Moved files for: CapitalCommonwealth_mt4lcapitalcommonwealth (v1.1.0)

Fetching status for: CharGrinn/CharGrinn
    ✓ Saved status JSON (v1.5.0.0)
✓ Moved files for: CharGrinn_CharGrinn (v1.4.1.1)

Fetching status for: Cistern/BottleRim
    ✓ Saved status JSON (v1.9.3)
✓ Moved files for: Cistern_BottleRim (v2.6.0)

Fetching status for: CSVO/BottleRim
    → Failed to fetch status for CSVO/BottleRim: 404 Client Error: Not Found for url: https://raw.githubusercontent.com/wabbajack-tools/mod-lists/master/reports/CSVO/BottleRim/status.json
    ⚠ No status JSON saved for CSVO_BottleRim
✓ Moved files for: CSVO_BottleRim (v2.0.1)

Fetching status for: CSVO/CSVO
    → Failed to fetch status for CSVO/CSVO: 404 Client Error: Not Found for url: https://raw.githubusercontent.com/wabbajack-tools/mod-lists/master/reports/CSVO/CSVO/status.json
    ⚠ No status JSON saved for CSVO_CSVO
✓ Moved files for: CSVO_CSVO (v1.4.2)

Fetching status for: Deckborn/Deckborn
    ✓ Saved status JSON (v0.3.6)
✓ Moved files for: Deckborn_Deckborn (v0.3.6)

Fetching status for: Dying_Breath/dyingbreath
    ✓ Saved status JSON (v1.2)
✓ Moved files for: Dying_Breath_dyingbreath (v1.2)

Fetching status for: Dying_Breath/ViirSuum
    ✓ Saved status JSON (v1.0)
✓ Moved files for: Dying_Breath_ViirSuum (v1.0)

Fetching status for: ELden-Rim_Together/EldenRim
    ✓ Saved status JSON (v3.3.1)
✓ Moved files for: ELden-Rim_Together_EldenRim (v3.2.6)

Fetching status for: EldergleamNG/EldergleamNG
    ✓ Saved status JSON (v4.0.2)
✓ Moved files for: EldergleamNG_EldergleamNG (v3.1.1)

Fetching status for: ElderTeej/ElderTeej
    ✓ Saved status JSON (v4.0.2)
✓ Moved files for: ElderTeej_ElderTeej (v2.0.6)

Fetching status for: ElmoRim/ElmoRim
    ✓ Saved status JSON (v2.1.1)
✓ Moved files for: ElmoRim_ElmoRim (v2.1.1)

Fetching status for: Elysium/elysium
    ✓ Saved status JSON (v3.3.1)
✓ Moved files for: Elysium_elysium (v3.3.1)

Fetching status for: F4FEVR/LaskeumaKuume
    ✓ Saved status JSON (v0.3.3.4)
✓ Moved files for: F4FEVR_LaskeumaKuume (v0.2.10)

Fetching status for: FAnomaly/Fallout_Anomaly
    ✓ Saved status JSON (v0.5.9.8)
✓ Moved files for: FAnomaly_Fallout_Anomaly (v0.5.7)

Fetching status for: FILFY/FILFY
    ✓ Saved status JSON (v2.7.0.9)
✓ Moved files for: FILFY_FILFY (v2.5.7.3)

Fetching status for: FILFY/TheMethod
    ✓ Saved status JSON (v0.0.7)
✓ Moved files for: FILFY_TheMethod (v0.2.5)

Fetching status for: fo4nexNG/fo4nexNG
    ✓ Saved status JSON (v1.6.1)
✓ Moved files for: fo4nexNG_fo4nexNG (v1.6.1)

Fetching status for: ForgottenGlory/zenforge
    ✓ Saved status JSON (v0.0.3)
✓ Moved files for: ForgottenGlory_zenforge (v0.0.3)

Fetching status for: Geborgen/dinoksetiid
    ✓ Saved status JSON (v1.0.1)
✓ Moved files for: Geborgen_dinoksetiid (v1.0.1)

Fetching status for: Geborgen/nordic-souls
    ✓ Saved status JSON (v3.0.1)
✓ Moved files for: Geborgen_nordic-souls (v2.4.1.1)

Fetching status for: HoS/HoS
    ✓ Saved status JSON (v1.3.4)
✓ Moved files for: HoS_HoS (v1.3.4)

Fetching status for: Ilinalta/Ilinalta
    ✓ Saved status JSON (v1.3.0)
✓ Moved files for: Ilinalta_Ilinalta (v1.3.0)

Fetching status for: Journals_of_Jyggalag/Journals_of_Jyggalag
    → Failed to fetch status for Journals_of_Jyggalag/Journals_of_Jyggalag: 404 Client Error: Not Found for url: https://raw.githubusercontent.com/wabbajack-tools/mod-lists/master/reports/Journals_of_Jyggalag/Journals_of_Jyggalag/status.json
    ⚠ No status JSON saved for Journals_of_Jyggalag_Journals_of_Jyggalag
✓ Moved files for: Journals_of_Jyggalag_Journals_of_Jyggalag (v3.4.0)

Fetching status for: Journals_of_Jyggalag/Tomes_of_Talos
    → Failed to fetch status for Journals_of_Jyggalag/Tomes_of_Talos: 404 Client Error: Not Found for url: https://raw.githubusercontent.com/wabbajack-tools/mod-lists/master/reports/Journals_of_Jyggalag/Tomes_of_Talos/status.json
    ⚠ No status JSON saved for Journals_of_Jyggalag_Tomes_of_Talos
✓ Moved files for: Journals_of_Jyggalag_Tomes_of_Talos (v1.1.0)

Fetching status for: Just_Another_Requiem_List/Just_Another_Requiem_List
    ✓ Saved status JSON (v2.5)
✓ Moved files for: Just_Another_Requiem_List_Just_Another_Requiem_List (v2.2)

Fetching status for: Keizaal/keizaal
    ✓ Saved status JSON (v8.0.1.1)
✓ Moved files for: Keizaal_keizaal (v8.0.1)

Fetching status for: LoreRim/LoreRim
    ✓ Saved status JSON (v4.5.3)
✓ Moved files for: LoreRim_LoreRim (v4.0.35)

Fetching status for: LostOutpost/arcanaeum
    → Failed to fetch status for LostOutpost/arcanaeum: 404 Client Error: Not Found for url: https://raw.githubusercontent.com/wabbajack-tools/mod-lists/master/reports/LostOutpost/arcanaeum/status.json
    ⚠ No status JSON saved for LostOutpost_arcanaeum
✓ Moved files for: LostOutpost_arcanaeum (v1.2.1)

Fetching status for: LostOutpost/lostlegacy
    ✓ Saved status JSON (v1.2.1)
✓ Moved files for: LostOutpost_lostlegacy (v1.2.1)

Fetching status for: LostOutpost/windsofthenorth
    ✓ Saved status JSON (v3.0.3)
✓ Moved files for: LostOutpost_windsofthenorth (v2.0.9)

Fetching status for: lukxsofficial/lukxsofficiallists
    → Failed to fetch status for lukxsofficial/lukxsofficiallists: 404 Client Error: Not Found for url: https://raw.githubusercontent.com/wabbajack-tools/mod-lists/master/reports/lukxsofficial/lukxsofficiallists/status.json
    ⚠ No status JSON saved for lukxsofficial_lukxsofficiallists
✓ Moved files for: lukxsofficial_lukxsofficiallists (v0.9)

Fetching status for: Mad_Gods_Overhaul/MadGodsOverhaul
    → Failed to fetch status for Mad_Gods_Overhaul/MadGodsOverhaul: 404 Client Error: Not Found for url: https://raw.githubusercontent.com/wabbajack-tools/mod-lists/master/reports/Mad_Gods_Overhaul/MadGodsOverhaul/status.json
    ⚠ No status JSON saved for Mad_Gods_Overhaul_MadGodsOverhaul
✓ Moved files for: Mad_Gods_Overhaul_MadGodsOverhaul (v3.6.2)

Fetching status for: Mad_Gods_Overhaul/MadGodsOverhaulFO4VR
    → Failed to fetch status for Mad_Gods_Overhaul/MadGodsOverhaulFO4VR: 404 Client Error: Not Found for url: https://raw.githubusercontent.com/wabbajack-tools/mod-lists/master/reports/Mad_Gods_Overhaul/MadGodsOverhaulFO4VR/status.json
    ⚠ No status JSON saved for Mad_Gods_Overhaul_MadGodsOverhaulFO4VR
✓ Moved files for: Mad_Gods_Overhaul_MadGodsOverhaulFO4VR (v1.5.2)

Fetching status for: MagesAndVikings/MagesAndVikings
    ✓ Saved status JSON (v2.5.1)
✓ Moved files for: MagesAndVikings_MagesAndVikings (v1.90)

Fetching status for: ModdingLinked/ADragonbornsFate
    ✓ Saved status JSON (v10.2.26)
✓ Moved files for: ModdingLinked_ADragonbornsFate (v17.8.25)

Fetching status for: NGVO/DNGG
    ✓ Saved status JSON (v2.8.5)
✓ Moved files for: NGVO_DNGG (v2.8.5)

Fetching status for: NGVO/ETERNAL
    → Failed to fetch status for NGVO/ETERNAL: 404 Client Error: Not Found for url: https://raw.githubusercontent.com/wabbajack-tools/mod-lists/master/reports/NGVO/ETERNAL/status.json
    ⚠ No status JSON saved for NGVO_ETERNAL
✓ Moved files for: NGVO_ETERNAL (v1.0.0)

Fetching status for: NGVO/NGVO
    → Failed to fetch status for NGVO/NGVO: 404 Client Error: Not Found for url: https://raw.githubusercontent.com/wabbajack-tools/mod-lists/master/reports/NGVO/NGVO/status.json
    ⚠ No status JSON saved for NGVO_NGVO
✓ Moved files for: NGVO_NGVO (v6.0.2)

Fetching status for: NotToddHoward/SkyrimPluslink
    ✓ Saved status JSON (v1.3.1)
✓ Moved files for: NotToddHoward_SkyrimPluslink (v1.2.0)

Fetching status for: NYA/sandland
    ✓ Saved status JSON (v2.5)
✓ Moved files for: NYA_sandland (v1.3)

Fetching status for: Palette/Alpyne
    ✓ Saved status JSON (v1.6.1)
✓ Moved files for: Palette_Alpyne (v1.5.1)

Fetching status for: Palette/Untitled
    ✓ Saved status JSON (v1.0.0)
✓ Moved files for: Palette_Untitled (v1.0.0)

Fetching status for: SICKnasty-FO4/sicknastyfo4
    → Failed to fetch status for SICKnasty-FO4/sicknastyfo4: 404 Client Error: Not Found for url: https://raw.githubusercontent.com/wabbajack-tools/mod-lists/master/reports/SICKnasty-FO4/sicknastyfo4/status.json
    ⚠ No status JSON saved for SICKnasty-FO4_sicknastyfo4
✓ Moved files for: SICKnasty-FO4_sicknastyfo4 (v3.0.0)

Fetching status for: SkyFurry_NG-Otherkin/SkyFurry-NG---Otherkin
    ✓ Saved status JSON (v2.0.3)
✓ Moved files for: SkyFurry_NG-Otherkin_SkyFurry-NG---Otherkin (v2.0.3)

Fetching status for: SkyGround_Chronicles/SkyGround
    ✓ Saved status JSON (v3.2.2)
✓ Moved files for: SkyGround_Chronicles_SkyGround (v1.2.1)

Fetching status for: SkyGround_Chronicles/Worromot
    ✓ Saved status JSON (v1.1)
✓ Moved files for: SkyGround_Chronicles_Worromot (v1.0.1)

Fetching status for: TempSME/sme
    ✓ Saved status JSON (v2.7.1)
✓ Moved files for: TempSME_sme (v2.7.1)

Fetching status for: TheMidnightRide/TheMidnightRide
    → Failed to fetch status for TheMidnightRide/TheMidnightRide: 404 Client Error: Not Found for url: https://raw.githubusercontent.com/wabbajack-tools/mod-lists/master/reports/TheMidnightRide/TheMidnightRide/status.json
    ⚠ No status JSON saved for TheMidnightRide_TheMidnightRide
✓ Moved files for: TheMidnightRide_TheMidnightRide (v9.8.25)

Fetching status for: theoldnorth/theoldnorth
    ✓ Saved status JSON (v2.0.3)
✓ Moved files for: theoldnorth_theoldnorth (v2.0.3)

Fetching status for: The_Nico_Experience/The_Nico_Experience
    ✓ Saved status JSON (v2.7.6)
✓ Moved files for: The_Nico_Experience_The_Nico_Experience (v2.4.6)

Fetching status for: TNE/tne
    ✓ Saved status JSON (v1.8.0.1)
✓ Moved files for: TNE_tne (v1.7)

Fetching status for: Tuxborn/Tuxborn
    ✓ Saved status JSON (v1.1.3)
✓ Moved files for: Tuxborn_Tuxborn (v1.1.3)

Fetching status for: WakingDreams/ANVIL
    ✓ Saved status JSON (v3.1.1)
✓ Moved files for: WakingDreams_ANVIL (v3.1.1)

Fetching status for: WakingDreams/apostasy
    ✓ Saved status JSON (v3.2.0)
✓ Moved files for: WakingDreams_apostasy (v3.1.4)

Fetching status for: WakingDreams/fahluaan
    ✓ Saved status JSON (v2.3.4)
✓ Moved files for: WakingDreams_fahluaan (v2.3.4)

Fetching status for: WakingDreams/TwistedSkyrim
    ✓ Saved status JSON (v1.7.1.0)
✓ Moved files for: WakingDreams_TwistedSkyrim (v1.3.2.1)

Fetching status for: WakingDreams/VagabondRemastered
    → Failed to fetch status for WakingDreams/VagabondRemastered: 404 Client Error: Not Found for url: https://raw.githubusercontent.com/wabbajack-tools/mod-lists/master/reports/WakingDreams/VagabondRemastered/status.json
    ⚠ No status JSON saved for WakingDreams_VagabondRemastered
✓ Moved files for: WakingDreams_VagabondRemastered (v0.3.12)

Fetching status for: WastelandReborn/Dragonbreak
    → Failed to fetch status for WastelandReborn/Dragonbreak: 404 Client Error: Not Found for url: https://raw.githubusercontent.com/wabbajack-tools/mod-lists/master/reports/WastelandReborn/Dragonbreak/status.json
    ⚠ No status JSON saved for WastelandReborn_Dragonbreak
✓ Moved files for: WastelandReborn_Dragonbreak (v0.41)

Fetching status for: WastelandReborn/wasteland_reborn
    ✓ Saved status JSON (v1.3.6)
✓ Moved files for: WastelandReborn_wasteland_reborn (v2.2.3)

Fetching status for: Wildlander/wildlander
    ✓ Saved status JSON (v1.1.12)
✓ Moved files for: Wildlander_wildlander (v1.1.12)

Fetching status for: wj-featured/aldrnari
    ✓ Saved status JSON (v2.2.5)
✓ Moved files for: wj-featured_aldrnari (v2.2.5)

Fetching status for: wj-featured/arkayscommandment
    ✓ Saved status JSON (v1.1.2)
✓ Moved files for: wj-featured_arkayscommandment (v1.0.1)

Fetching status for: wj-featured/librum_se
    → Failed to fetch status for wj-featured/librum_se: 404 Client Error: Not Found for url: https://raw.githubusercontent.com/wabbajack-tools/mod-lists/master/reports/wj-featured/librum_se/status.json
    ⚠ No status JSON saved for wj-featured_librum_se
✓ Moved files for: wj-featured_librum_se (v3.1.0.1)

Fetching status for: wj-featured/life_in_the_ruins
    ✓ Saved status JSON (v8.0.0.5)
✓ Moved files for: wj-featured_life_in_the_ruins (v7.1.0.2)

Fetching status for: wj-featured/living_skyrim
    ✓ Saved status JSON (v4.3.0.1)
✓ Moved files for: wj-featured_living_skyrim (v4.3.0.1)

Fetching status for: wj-featured/lotf
    ✓ Saved status JSON (v3.3.4)
✓ Moved files for: wj-featured_lotf (v3.3.4)

Fetching status for: wj-featured/magnum_opus
    ✓ Saved status JSON (v9.2.6)
✓ Moved files for: wj-featured_magnum_opus (v7.0.22)

Fetching status for: wj-featured/sss
    ✓ Saved status JSON (v5.0.0)
✓ Moved files for: wj-featured_sss (v5.0.0)

Fetching status for: wj-featured/tempus_maledictum
    ✓ Saved status JSON (v8.0.6)
✓ Moved files for: wj-featured_tempus_maledictum (v8.0.6)

Fetching status for: wj-featured/tpf
    ✓ Saved status JSON (v4.20)
✓ Moved files for: wj-featured_tpf (v4.20)

Fetching status for: Wunduniik/Krentoraan
    ✓ Saved status JSON (v1.3.0)
✓ Moved files for: Wunduniik_Krentoraan (v1.2.0)

Fetching status for: Wunduniik/Wunduniik
    ✓ Saved status JSON (v6.8.1.0)
✓ Moved files for: Wunduniik_Wunduniik (v5.10.0)

Fetching status for: Yagisan/RtC
    ✓ Saved status JSON (v0.0.3)
✓ Moved files for: Yagisan_RtC (v0.0.3)

Fetching status for: Yagisan/SS2CPC
    ✓ Saved status JSON (v4.25.0)
✓ Moved files for: Yagisan_SS2CPC (v4.17.0)

Fetching status for: Yagisan/SS2PAP
    ✓ Saved status JSON (v1.3.8)
✓ Moved files for: Yagisan_SS2PAP (v1.3.3)

Fetching status for: Zediious/aurbaesence
    ✓ Saved status JSON (v1.1.5.2)
✓ Moved files for: Zediious_aurbaesence (v1.1.4)

Processing completed!

(opencv) O:\Wabbajack\Modlists\project>
'''