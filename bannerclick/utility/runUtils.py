import re
from ..config import *
import sqlite3
import os
import time
from typing import List, Tuple, Dict, Optional, Union
import subprocess
import shutil
from pathlib import Path
from openwpm.config import BrowserParams, ManagerParams
from openwpm.command_sequence import CommandSequence, DumpProfileCommand
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By

from openwpm.commands.utils.webdriver_utils import (
    is_displayed,
    scroll_down,
    wait_until_loaded,
)
from urllib import parse as urlparse
import requests
from selenium.webdriver import Firefox
from .shared_utils import repeat, read_txt_file, url_to_uniform_domain
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By
import logging
import random
GENERAL_SELECTORS_URL = "https://raw.githubusercontent.com/easylist/easylist/master/easylist_cookie/easylist_cookie_general_hide.txt"
SPECIFIC_SELECTORS_URL = "https://raw.githubusercontent.com/easylist/easylist/master/easylist_cookie/easylist_cookie_specific_hide.txt"
SELECTORS_EXCEPTIONS_URL = "https://raw.githubusercontent.com/easylist/easylist/master/easylist_cookie/easylist_cookie_allowlist_general_hide.txt"
BANNED_CHARACTERS = {"!", "[", "@", "|", "/"}

from pathlib import Path
def make_url(domain: str, mode=URL_MODE):
    domain = domain.strip("\n")
    if "https://" in domain or "http://" in domain:
        url = domain
    else:
        if mode == 1:
            url = "https://" + domain
        elif mode == 2:
            url = "http://" + domain
        else:
            url = ""
    return url

def scroll_to_bottom(webdriver: Firefox) -> None:
    try:
        webdriver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    except WebDriverException:
        pass




def write_to_file(
    s: Union[str, bytes], save_path: Union[Path, str], save_path_suffix: str = ""
) -> None:
    if isinstance(s, str):
        s = s.encode("utf8")
    with open(f"{save_path}{save_path_suffix}", "wb") as f:
        f.write(s)
        f.write(b"\n")


def parse_general_selectors(raw_selectors: List[str]) -> List[str]:
    selectors = []
    for line in raw_selectors:
        if line[0] in BANNED_CHARACTERS:
            continue
        if line[0:2] == "##":
            selector = line[2:]
            selectors.append(selector.strip())
    return selectors


def get_selectors() -> Tuple[List[str], ...]:
    selectors = []
    for desc, url in zip(
        ["general_selectors", "specific_selectors", "selectors_exceptions"],
        [GENERAL_SELECTORS_URL, SPECIFIC_SELECTORS_URL, SELECTORS_EXCEPTIONS_URL],
    ):
        filename = Path(os.path.join(os.path.dirname(__file__),"selectors",f"{desc}.txt"))
        if filename.is_file():
            print("Loading selectors from cache ..")
            tmp_selectors = read_txt_file(filename)
        else:
            print("Downloading selectors ..")
            filename.parent.mkdir(exist_ok=True, parents=True)
            tmp_selectors = requests.get(url).text.splitlines()
            write_to_file("\n".join(tmp_selectors), filename)
        selectors.append(tmp_selectors)
    selectors[0] = parse_general_selectors(selectors[0])
    return tuple(selectors)

@repeat(raise_exception_if_fails=False, sleep=3)
def find_elements_by_selectors(
    selectors: List[str], webdriver: Firefox
) -> Tuple[List[WebElement], List[str]]:
    return webdriver.execute_script(
        open(os.path.join(os.path.dirname(__file__), "find_elements_by_selector.js")).read(),
        selectors,
    )



def file_to_list(path):
    file = open(path, "r")
    domains = []
    while True:
        domain = file.readline().strip("\n")
        if not domain:
            break
        if domain == "#":
            break
        if domain == "$":
            break
        domains.append(make_url(domain))
    return domains


def get_intra_links(webdriver: Firefox, url: str) -> List[WebElement]:
    ps1 = url_to_uniform_domain(url)
    links = list()
    for elem in webdriver.find_elements(By.TAG_NAME, "a"):
        try:
            href = elem.get_attribute("href")
        except StaleElementReferenceException:
            continue
        if href is None:
            continue
        full_href = urlparse.urljoin(url, href)
        if not full_href.startswith("http"):
            continue
        if url_to_uniform_domain(full_href) == ps1:
            links.append(elem)
    return links

def browse(
    website: str,
    webdriver: Firefox,
    num_links: int,
    sleep: int,
    seed: int,
) -> None:
    links = [
        x
        for x in get_intra_links(webdriver, website)
        if is_displayed(x) is True
    ]
    if not links:
        return
    links_ids = get_selector_from_element(links, webdriver)
    random.seed(seed)
    for i in range(num_links):
        r = int(random.random() * len(links))

        try:

            link = (
                find_element_by_selector(links_ids[r], webdriver) if i > 0 else links[r]
            )
            if link is None:
                continue
            click(link, webdriver)
            wait_until_loaded(webdriver, 4)
            time.sleep(0.5)
            scroll_to_bottom(webdriver)
            wait_until_loaded(webdriver, 3)
            time.sleep(0.5)
            webdriver.back()
        except Exception:
            pass

def url_to_uniform_domain(url: str) -> str:
    """Takes a URL or a domain string and transforms it into a uniform format.
    Examples: {"www.example.com", "https://example.com/", ".example.com"} --> "example.com"
    :param url: URL to clean and bring into uniform format
    """
    new_url = url.strip()
    new_url = re.sub("^http(s)?://", "", new_url)
    new_url = re.sub("^www([0-9])?", "", new_url)
    new_url = re.sub("^\\.", "", new_url)
    new_url = re.sub("/.*", "", new_url)
    return new_url


@repeat()
def click(element: WebElement, webdriver: Firefox, sleep: int = 3) -> None:
    webdriver.execute_script(
        "arguments[0].scrollIntoView(true);arguments[0].click();", element
    )
    time.sleep(sleep)

@repeat()
def get_selector_from_element(
    elements: Union[WebElement, List[WebElement]],
    webdriver: Firefox,
    keep_text_elements_only: bool = False,
    return_matched_elements: bool = False,
) -> Optional[Union[List[str], str, Tuple[List[str], List[WebElement]]]]:
    unique_element = False
    if isinstance(elements, WebElement):
        elements = [elements]
        unique_element = True
    selectors, matched_elements = webdriver.execute_script(
        open(os.path.join(os.path.dirname(__file__), "optimal_select.js")).read(),
        elements,
        keep_text_elements_only,
    )
    if unique_element:
        if len(selectors) > 0:
            return selectors[0]
        raise RuntimeError("Unable to assign selector to element.")
    else:
        if return_matched_elements:
            return selectors, matched_elements
        return selectors

def find_element_by_selector(
    selector: Optional[str],
    webdriver: Firefox,
) -> Optional[WebElement]:
    if selector is None:
        return None
    elements, _ = find_elements_by_selectors([selector], webdriver)
    if len(elements) == 0:
        return None
    return elements[0]


def get_domains_from_file(target_file_name):
    global STEP_SIZE
    if ".csv" in target_file_name:
        sites_csv = pd.read_csv(target_file_name)
        num_rows = sites_csv.shape[0]
        if TIERED300:
            sites = [
                make_url(sites_csv.iloc[row].domain) for row in range(0, 0 + STEP_SIZE)
            ]
            sites.extend(
                [
                    make_url(sites_csv.iloc[row].domain)
                    for row in range(1000, 1000 + STEP_SIZE)
                ]
            )
            sites.extend(
                [
                    make_url(sites_csv.iloc[row].domain)
                    for row in range(9900, 9900 + STEP_SIZE)
                ]
            )

        elif STATUS_AVAILABLE:
            sites = list(
                zip(
                    sites_csv['domain'].apply(make_url),
                    sites_csv['status'],
                ))

        else:  # read from .csv file. from START_POINT to START_POINT + STEP_SIZE
            if num_rows < STEP_SIZE:
                 STEP_SIZE = num_rows
            sites = [
                make_url(sites_csv.iloc[row].domain)
                for row in range(START_POINT, START_POINT + STEP_SIZE)
            ]
    else:  # read from .txt file
        if "custom" in target_file_name:
            sites = file_to_list(target_file_name)
        else:
            with open(target_file_name, 'r') as file:
                all_sites = [make_url(domain) for domain in file.readlines()]
                sites = all_sites[START_POINT: START_POINT + STEP_SIZE]


    return sites


def get_profile_path():
    if DEFAULT_PROFILE_PATH:
        # Get a list of all files in the directory
        profiles_dir_all_files = os.listdir(PROFILES_PATH)
        # Filter out directories, leaving only files
        files = [
            file
            for file in profiles_dir_all_files
            if os.path.isfile(os.path.join(PROFILES_PATH, file))
        ]
        if files:
            # Get the most recently modified file
            last_modified_file = max(
                files, key=lambda x: os.path.getmtime(
                    os.path.join(PROFILES_PATH, x))
            )
            # Get the full path of the last modified file
            last_modified_file_path = os.path.join(
                PROFILES_PATH, last_modified_file)
            return Path(last_modified_file_path)
    else:
        PROFILE_PATH = STATE_LOAD_RUN_PATH / PROFILE_NAME
        # print("PROFILE_PATH: ", PROFILE_PATH)
        return Path(PROFILE_PATH)


def load_profile(browser_param):
    browser_param.seed_tar = get_profile_path()

def gpc_signal(browser_param):
    browser_param.prefs[
        "privacy.globalprivacycontrol.enabled"
    ] = GPC_signal
    browser_param.prefs[
        "privacy.globalprivacycontrol.functionality.enabled"
    ] = GPC_signal


def store_db(bu=False, name=""):
    if name:
        name = name + "_"
    if bu:
        destination_path = DBBACKUP_PATH / (name + "crawl-data.sqlite")
    else:
        destination_path = STATE_RUN_PATH / (name + "crawl-data.sqlite")
    source_path = Path(data_dir) / "crawl-data.sqlite"
    shutil.copy(source_path, destination_path)


def disable_caching(browser_param):
    # Disable disk cache
    browser_param.prefs["browser.cache.disk.enable"] = False
    # Disable memory cache
    browser_param.prefs["browser.cache.memory.enable"] = False
    # Disable offline cache
    browser_param.prefs["browser.cache.offline.enable"] = False
    # Disable caching of SSL content
    browser_param.prefs["browser.cache.disk_cache_ssl"] = False
    # Optional: Clear the cache on shutdown
    browser_param.prefs["privacy.clearOnShutdown.cache"] = True


def load_db(bu=False, name=""):
    if name:
        name = name + "_"
    if bu:
        source_path = DBBACKUP_PATH / (name + "crawl-data.sqlite")
    else:
        source_path = STATE_LOAD_RUN_PATH / (name + "crawl-data.sqlite")
    destination_path = Path(data_dir) / "crawl-data.sqlite"
    shutil.copy(source_path, destination_path)
    visit_ids = previous_visit_ids(destination_path)
    return visit_ids


def get_browser_params(num_browsers, headless=True, LOAD_PRO = False, image_param=None):
    if headless:
        browser_params = [
            BrowserParams(display_mode="headless") for _ in range(num_browsers)
        ]
    else:
        browser_params = [
            BrowserParams(display_mode="native") for _ in range(num_browsers)
        ]

    # Update browser configuration (use this for per-browser settings)
    for browser_param in browser_params:
        if image_param:
            browser_param = image_param
            continue
        # Record HTTP Requests and Responses
        # browser_param.http_instrument = True
        browser_param.http_instrument = HTTP_INSTRUMENT
        # Record cookie changes
        browser_param.cookie_instrument = COOKIE_INSTRUMENT
        # Record Navigations
        browser_param.navigation_instrument = NAV_INSTRUMENT
        # Record JS Web API calls
        browser_param.js_instrument = JS_INSTRUMENT
        # Record the callstack of all WebRequests made
        browser_param.callstack_instrument = False
        # Record DNS resolution
        browser_param.dns_instrument = DNS_INSTRUMENT
        browser_param.prefs = {
            # Kill remote settings errors
            "services.settings.verify_signature": False,
            "services.settings.server": "",

            # Disable failing collections
            "services.settings.main.query-stripping.enabled": False,
            "services.settings.main.fingerprinting-protection-overrides.enabled": False,
            "services.settings.main.quicksuggest.enabled": False,
            "services.settings.security-state.cert-revocations.enabled": False,
            "services.settings.security-state.intermediates.enabled": False,
            "services.settings.security-state.onecrl.enabled": False,

            # Disable updates
            "app.update.enabled": False,
            "browser.safebrowsing.downloads.remote.enabled": False,

            # Optional: Enable software WebGL for fingerprinting detection
            "webgl.force-enabled": True,
            "webgl.disable-fail-if-major-performance-caveat": True,
            "layers.acceleration.disabled": True,
        }
        if MOBILE_AGENT:
            browser_param.prefs[
                "general.useragent.override"
            ] = "Mozilla/5.0 (Android 12; Mobile; rv:68.0) Gecko/68.0 Firefox/93.0"
        gpc_signal(browser_param)
        browser_param.extension_enabled = XPI
        if OFF_CACHING:
            disable_caching(browser_param)
        if LOAD_PRO and not TEST_RUN:
            load_profile(browser_param)
        if browser_params and not browser_params[0].custom_params:
            browser_params[0].custom_params = dict()

    return browser_params


def get_manager_params(num_browsers):
    manager_params = ManagerParams(num_browsers=num_browsers)
    manager_params.data_directory = Path(data_dir)
    manager_params.log_path = Path(data_dir + "/openwpm.log")
    # memory_watchdog and process_watchdog are useful for large scale cloud crawls.
    # Please refer to docs/Configuration.md#platform-configuration-options for more information
    manager_params.memory_watchdog = WATCHDOG
    manager_params.process_watchdog = WATCHDOG

    # Allow for many consecutive failures
    # The default is 2 x the number of browsers plus 10 (2x20+10 = 50)
    manager_params.failure_limit = 100_000
    return manager_params


def dir_mks():
    try:
        original_umask = os.umask(0)
        if not os.path.exists(data_dir):
            os.makedirs(data_dir, 0o0777)
        if not STATE_RUN_PATH.exists():
            STATE_RUN_PATH.mkdir(mode=0o0777, parents=True)

        if not PROFILES_PATH.exists():
            PROFILES_PATH.mkdir(
                parents=True,
                exist_ok=True,
            )
        if not DBBACKUP_PATH.exists():
            DBBACKUP_PATH.mkdir(
                parents=True,
                exist_ok=True,
            )
    finally:
        os.umask(original_umask)

    # setting the temp directory
    os.makedirs(name=BC_TEMP_DIR, mode=0o0777, exist_ok=True)
    os.environ['TMPDIR'] = BC_TEMP_DIR
    print(subprocess.check_output("echo $TMPDIR", shell=True, text=True))


def extract_compressed_db(compressed_path: Path, target_path: Path) -> Path:
    try:
        tar_command = f"tar -xzvf {compressed_path} -C {target_path.parent}"
        tar_output = subprocess.run(
            tar_command, shell=True, check=True, capture_output=True, text=True)
        print("Output of tar command: ")
        print(tar_output.stdout)
        print(tar_output.stderr)

        # List the contents of the tar file
        list_command = f"tar -tzf {compressed_path}"
        list_output = subprocess.check_output(
            list_command, shell=True, text=True)
        file_names = list_output.strip().split('\n')
        original_file_path = target_path.parent / file_names[0]
        new_file_path = target_path.parent / 'crawl-data.sqlite'
        os.rename(original_file_path, new_file_path)
        print(f"Renamed {original_file_path} to {new_file_path}")

        ls_command = f"ls -lah {target_path.parent}"
        ls_output = subprocess.check_output(ls_command, shell=True, text=True)
        print(ls_output)
        return target_path
    except Exception as e:
        print(f"Exception while extracting compressed db: {e}")
        return None


def make_copy_of_DB(DB_PATH: Path, DBBACKUP_DIR: Path, index: int):
    print("Backuping DB")

    if not os.path.exists(DB_PATH):
        print("DB not found")
        return

    if not os.path.exists(DBBACKUP_DIR):
        os.makedirs(DBBACKUP_DIR)

    source_basename = os.path.basename(os.path.normpath(DB_PATH))
    tar_filename = os.path.join(
        DBBACKUP_DIR, f"{index}_{source_basename}_compressed.tar.gz"
    )

    # with tarfile.open(tar_filename, "w:gz") as tar:
    #     if not os.path.isfile(DB_PATH):
    #         print(f"DB PATH IS NOT A FILE {DB_PATH}")
    #     tar.add(DB_PATH, arcname=os.path.basename(DB_PATH))

    try:
        bash_command = f"tar -czvf {tar_filename} -C {DB_PATH.parent} {DB_PATH.name}"
        tar_output = subprocess.run(bash_command, shell=True, check=True)
        print("Output of tar command: ")
        print(tar_output.stdout)
        print(tar_output.stderr)
        ls_command = f"ls -lah {DBBACKUP_DIR}"
        ls_output = subprocess.check_output(ls_command, shell=True, text=True)
        print(ls_output)
    except Exception as e:
        print(f"Exception while compressing db: {e}")
        return
    print(f"Compression completed. Resulting file: '{tar_filename}'")


def dump_profile_index(profile_path, index, manager, site, dump_profile_cb, name=None):
    if name is None:
        name = index
    manager.logger.warning(f"dumping profile on index: {index}")
    command_sequence = CommandSequence(
        url=f'{PROFILE_DUMP_URL_START}{site}',
        reset=STATELESS,
        blocking=True,
        retry_number=2,
        site_rank=-1 * index,
        callback=dump_profile_cb,
    )
    command_sequence.append_command(
        command=DumpProfileCommand(
            tar_path=profile_path / f"{name}{PROFILE_EXTENSION}",
            close_webdriver=False,
            compress=PROFILE_COMPRESS,
        ),
        timeout=60 * 2,
    )
    manager.execute_command_sequence(command_sequence=command_sequence)


def task_sleep(manager):
    try:
        if not hasattr(manager.storage_controller_handle, "task_count"):
            return
        task_count = manager.storage_controller_handle.task_count
        print("=" * 60)
        if DEBUG_TASK:
            manager.logger.error(
                f"""
                Inside Demo Checking task_count
                task count print: {task_count}
                task count id: {id(task_count)}
                task count value print: {task_count.value}
                task count value id: {id(task_count.value)}
                """
            )
        print(
            f"""
            Task Count Value inside Demo:
            {task_count.value}
            """
        )
        task_count_prev = task_count.value
        task_count_repeat_count = 0
        while task_count.value > TASK_COUNT_MAX and task_count_repeat_count < 10:
            time.sleep(10 * 1)

            if task_count.value == task_count_prev:
                task_count_repeat_count += 1
            else:
                task_count_repeat_count = 0

            task_count_prev = task_count.value
        print("=" * 60)
    except:
        pass


def remove_previous_profiles(PROFILES_DIR: str, manager):
    # List all tar.gz files
    manager.logger.info('removing previous profiles')
    files = [f for f in os.listdir(
        PROFILES_DIR) if re.match(r'\d+\.tar\.gz', f)]
    accept_profiles = []
    reject_profiles = []
    sorted_files = sorted(
        files, key=lambda file_name: int(file_name.split('.')[0]))
    for file in sorted_files:
        file_name = file.split('.')[0]
        int_file_name = int(file_name)
        if int_file_name <= SWITCH_INDEX:
            accept_profiles.append(file)
        else:
            reject_profiles.append(file)

    if len(accept_profiles) > 2:
        for file_to_delete in accept_profiles[:-2]:
            os.remove(os.path.join(PROFILES_DIR, file_to_delete))
            manager.logger.warning(f"removed profile {file_to_delete}")
    elif len(reject_profiles) > 2:
        for file_to_delete in reject_profiles[:-2]:
            os.remove(os.path.join(PROFILES_DIR, file_to_delete))
            manager.logger.warning(f"removed profile {file_to_delete}")

    manager.logger.info(f"files: {files}")


def previous_visit_ids(DB_PATH: Path):
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    cursor.execute("SELECT visit_id FROM site_visits")
    visit_ids = cursor.fetchall()
    connection.close()
    return set(visit_ids)
