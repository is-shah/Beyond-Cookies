from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
import requests
from adblockparser import AdblockRules
import os
from global_variables import LIST_DIR
URLS = {
    "easyprivacy": "https://easylist.to/easylist/easyprivacy.txt",
    "easylist": "https://easylist.to/easylist/easylist.txt",
    "adserverlist": "https://pgl.yoyo.org/adservers/serverlist.php?hostformat=hosts&showintro=1&mimetype=plaintext",
    "adguardlist": "https://adguardteam.github.io/AdGuardSDNSFilter/Filters/filter.txt",
}

def fetch_url_content(url):
    return requests.get(url, timeout=60).text


def load_adblock_rules():
    """Download lists and return initialized AdblockRules objects"""
    with ThreadPoolExecutor() as executor:
        future_to_url = {executor.submit(fetch_url_content, url): name for name, url in URLS.items()}
        results = {future_to_url[f]: f.result() for f in tqdm(future_to_url, desc="Fetching adblock lists")}

    return {
        "easyprivacy": AdblockRules(results['easyprivacy'].splitlines()),
        "easylist": AdblockRules(results['easylist'].splitlines()),
        "adserverlist": AdblockRules(results['adserverlist'].splitlines()),
        "adguardlist": AdblockRules(results['adguardlist'].splitlines()),
    }
