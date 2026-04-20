import logging
from datetime import datetime
import re
from static import generate_modlist_html

# Set up logging
current_date = datetime.now().strftime('%y%m%d')
log_file = f'/Wabbajack/project/logs/modlist_to_html_{current_date}.log'
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    args = [
        "Fallout4, The Midnight Ride, 9.8.25, The Midnight Ride",
        "SkyrimSE, Krentoraan,        1.2.0,  Krentoraan - Ultra",
        "SkyrimSE, Anvil,             3.1.1,  Anvil - Main Profile",
        "SkyrimSE, CSVO,              2.1.1,  BottleRim",
        "SkyrimSE, Tuxborn,           1.1.3,  Tuxborn - Desktop",
    ]
    game, modlist, version, profile = re.split(r',\s*', args[0])

    generate_modlist_html(game, modlist, version, profile)
