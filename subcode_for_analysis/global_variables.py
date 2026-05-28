# Directory paths
FIG_DIR = './files/figs'
INPUT_DIR = './files/inputs'  # Fixed the typo
BU_DIR = './files/backups'

# Optional: location mapping (only if needed later)
server_to_loc = {'eu-central-1': "Germany"}
# initializing vars

AWS_names = ['eu-central-1']
local_names = []
servers_to_fetch = AWS_names

server_to_loc = {'eu-central-1': "Germany" }
loc_to_server = {'Germany': "eu-central-1"}
locations = ['Germany']
EU_locs = ['Germany']
# nonEU_locs = ['US East', 'US West', 'India', 'Brazil', 'South Africa', 'Australia']
NUM_BATCH = 1

run_to_folder = {'js_first': 'js_first_20k'}
rule_params = {"third-party": True}

tracking_lists = ["adguarddns", "easylist", "easyprivacy", "nocoin"]

js_runs = ["js_first"]
load_from_backup = False   # if true then load the previously proccessed urls otherwise run the process_urls() method again
store_in_backup = True   # if true store the current processed urls in the backup

FIG_DIR = './files/figs'
INPUT_DIR = './files/inputs'
BU_DIR = './files/backups'
MY_DB_PATH = "/home/subcode/crawl-data.sqlite"
runs = {}
LIST_DIR = "./files/inputs/blocklists/lists/"
url_column='host_url'

AD_BLOCK_DIR = '/home/subcode/adblock_lists'
