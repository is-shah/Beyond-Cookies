# printing utility functions
from global_variables import *
from import_lib import *
from adblock_rules import load_adblock_rules
processed_url_df = None
tables_for_process = None
tracking_list = None
rules = None
cookie_urls = {
    "easyprivacy": "https://easylist.to/easylist/easyprivacy.txt",
    "easylist": "https://easylist.to/easylist/easylist.txt",
    "adguarddns": "https://adguardteam.github.io/AdGuardSDNSFilter/Filters/filter.txt",
    "nocoin": "https://raw.githubusercontent.com/hoshsadiq/adblock-nocoin-list/master/nocoin.txt",
}

ref_df = pd.read_csv("common_domains_only_translated.csv")

# convert to set for fast lookup
allowed_domains = set(ref_df["domains"].dropna().unique())

def show_detection_status(run_cat="desktop"):
    for name, aws in runs[run_cat].AWS_map.items():
        df = aws.visits
        if 'banners' in df:
            print('{:14} detect {:4} and {:4} websites with banners and CMP respectively out of {:4} entries in DB.'.format(name, df[df.banners>0].shape[0], df[df.__tcfapi==1].shape[0], df.shape[0]))

def show_run_status(run_cat="desktop"):
    for name, aws in runs[run_cat].AWS_map.items():
        df = aws.visits
        if 'banners' in df:
            print('{:14} reachable: {:3}, selenium timeout: {:3}, unreachable: {:3}, exception during banner detection {:3}.'.format(name, df[df.status==0].shape[0], df[df.status==1].shape[0], df[df.status==2].shape[0], df[df.status==-1].shape[0]))


# logical utility functions

def awstoserver(aws):
    return f"inet-gc-p-{aws}.dyn.mpi-klsb.mpg.de"

def make_suffix(string):
    return "_" + string.replace('-', '_')

def add_suffix(df, name, base_column=["visit_id", "domain"], inplace=False):
    suffix = make_suffix(name)
    if inplace:
        df = df.add_suffix(suffix).rename(columns=dict(zip([f"{bc}{suffix}" for bc in base_column], base_column)), inplace=True)
        return df
    else:
        temp = df.add_suffix(suffix)
        return temp.rename(columns=dict(zip([f"{bc}{suffix}" for bc in base_column], base_column)), inplace=False)

def get_unique_first_last(df, sort_columns=["visit_id", "event_ordinal"], columns=['visit_id', 'host_url', 'name']):
    try:


        # Sort the DataFrame by the specified columns
        df = df.sort_values(by=sort_columns)

        # Identify the first and last occurrences of each duplicate based on the specified columns
        first_dup = df.drop_duplicates(subset=columns, keep="first")
        last_dup = df.drop_duplicates(subset=columns, keep="last")

        # Concatenate the first and last duplicates, removing any further duplicates
        df = pd.concat([first_dup, last_dup]).drop_duplicates().sort_values(by=sort_columns).reset_index(drop=True)
    except:
        # df = df.sort_values(by=["is_stateful", "id"]).drop_duplicates(subset=columns, keep="last")
        raise
    return df

def get_unique(df, sort_columns=["visit_id", "event_ordinal"], columns=['visit_id', 'host_url', 'name']):
    try:
        df = df.sort_values(by=sort_columns).drop_duplicates(subset=columns, keep="last").reset_index(drop=True)
    except:
        raise
    return df

def get_db_path(server_name, batch=-1, run_name="desktop", folder_order=False):
    if server_name in local_names:
        server_url = "inet-"+server_name+".mpi-inf.mpg.de"
    else:
        server_url = "inet-gc-p-"+server_name+".dyn.mpi-klsb.mpg.de"
    data_dir = "data"
    # run_folder = run_to_folder[run_name]
    run_folder = run_to_folder.get(run_name, run_name)
    dir_list = os.listdir(f"{data_dir}/{run_folder}/{server_url}/")
    if folder_order:
        if r'.ipynb_checkpoints' in dir_list :
            dir_list.remove(r'.ipynb_checkpoints')
        dir_list.sort()
        try :
            data_file = dir_list[batch]
        except Exception as e :
            pass
    else:

        SP_list = [int(directory.split("SP")[1]) for directory in dir_list]
        SP_list = list(set(SP_list))
        SP_list.sort()
        data_file = dir_list[-1]
        if batch != -1:
            top = str(SP_list[batch])
            folder_names = [name for name in dir_list if "SP" in name and top == name.split("SP")[1]]
            data_file = folder_names[-1]
    path = f"{data_dir}/{run_folder}/{server_url}/{data_file}/crawl-data.sqlite"
    return path

def get_last_visit(visits):  # not a good implementation since the last one can be unrechable by OpenWPM
    last_visit = visits[visits.visit_id<OFFSET_ACCEPT-2].visit_id.max() + 1
    return last_visit

def to_bool(df, cmp_mod, x):
    if cmp_mod == 1:
        return df == x
    elif cmp_mod == -1:
        return df != x

def do_all(dfs, operand, cmp_mod, to_cmp):
    if operand == '&':
        res = reduce(lambda x, y: x&y, [to_bool(df,cmp_mod,to_cmp) for df in dfs])
    if operand == '|':
        res = reduce(lambda x, y: x|y, [to_bool(df,cmp_mod,to_cmp) for df in dfs])
    if operand == '+':
        res = reduce(lambda x, y: x+y, [to_bool(df,cmp_mod,to_cmp) for df in dfs])

    return res

# return dataframe contains all vantage points togethers. Column names appended by "_AWS_NAME"
def merge_dfs(AWS_list, table='visits'):
    dfs = []
    for aws in AWS_list:
        aws_name = aws.name
        df = aws.table_map[table]
        df = add_suffix(df, aws_name)
        dfs.append(df)
    merged = reduce(lambda  left,right: pd.merge(left, right, how='outer', left_on=['visit_id','domain'], right_on=['visit_id','domain']), dfs)
    return merged

def get_column(df, base_column, aws_name):
    cl = base_column + make_suffix(aws_name)
    return df[cl]

def get_columns(df, base_column, aws_names):
    cls = [base_column + make_suffix(name) for name in aws_names]
    return df[cls]

def get_AWS_obj(run, location):
    return runs[run].AWS_map[loc_to_server[location]]

# return only rechables crawls
# status=1 means loaded websites, if it is the case for all VP then we considdefer ot
# TODO: these should be changed, here we assume runs with same visit_id should consider together which is wrong.
# However it is too rare that not all of the crawls for the same domain in one VP behave differently. (see appendix.1)
def pulish_with_status(merged, aws_names=[]):
    rd = merged[get_columns(merged, 'status', aws_names).any(axis=1).eq(0)]
    return rd

def append_series(servers, table, column):
    dfs = pd.Series()
    flag = False
    for server in servers:
        aws_name = server.name
        df = server.table_map[table][column]
        if not flag:
            flag = True
            dfs = df
            continue
        dfs = dfs.append(df, ignore_index=True)
    return dfs
# d = append_series(runs['mobile-sc'].AWS_list, 'visits', 'ttw')

# logical utility functions

def awstoserver(aws):
    return f"inet-gc-p-{aws}.dyn.mpi-klsb.mpg.de"

def make_suffix(string):
    return "_" + string.replace('-', '_')

def add_suffix(df, name, base_column=["visit_id", "domain"], inplace=False):
    suffix = make_suffix(name)
    if inplace:
        df = df.add_suffix(suffix).rename(columns=dict(zip([f"{bc}{suffix}" for bc in base_column], base_column)), inplace=True)
        return df
    else:
        temp = df.add_suffix(suffix)
        return temp.rename(columns=dict(zip([f"{bc}{suffix}" for bc in base_column], base_column)), inplace=False)

def get_db_path(server_name, batch=-1, run_name="desktop", folder_order=False):
    if server_name in local_names:
        server_url = "inet-"+server_name+".mpi-inf.mpg.de"
    else:
        server_url = "inet-gc-p-"+server_name+".dyn.mpi-klsb.mpg.de"
    data_dir = "data"
    # run_folder = run_to_folder[run_name]
    run_folder = run_to_folder.get(run_name, run_name)
    dir_list = os.listdir(f"{data_dir}/{run_folder}/{server_url}/")
    if folder_order:
        if r'.ipynb_checkpoints' in dir_list :
            dir_list.remove(r'.ipynb_checkpoints')
        dir_list.sort()
        try :
            data_file = dir_list[batch]
        except Exception as e :
            pass
    else:

        SP_list = [int(directory.split("SP")[1]) for directory in dir_list]
        SP_list = list(set(SP_list))
        SP_list.sort()
        data_file = dir_list[-1]
        if batch != -1:
            top = str(SP_list[batch])
            folder_names = [name for name in dir_list if "SP" in name and top == name.split("SP")[1]]
            data_file = folder_names[-1]
    path = f"{data_dir}/{run_folder}/{server_url}/{data_file}/crawl-data.sqlite"
    return path

def get_last_visit(visits):  # not a good implementation since the last one can be unrechable by OpenWPM
    last_visit = visits[visits.visit_id<OFFSET_ACCEPT-2].visit_id.max() + 1
    return last_visit

def to_bool(df, cmp_mod, x):
    if cmp_mod == 1:
        return df == x
    elif cmp_mod == -1:
        return df != x

def do_all(dfs, operand, cmp_mod, to_cmp):
    if operand == '&':
        res = reduce(lambda x, y: x&y, [to_bool(df,cmp_mod,to_cmp) for df in dfs])
    if operand == '|':
        res = reduce(lambda x, y: x|y, [to_bool(df,cmp_mod,to_cmp) for df in dfs])
    if operand == '+':
        res = reduce(lambda x, y: x+y, [to_bool(df,cmp_mod,to_cmp) for df in dfs])

    return res

# return dataframe contains all vantage points togethers. Column names appended by "_AWS_NAME"
def merge_dfs(AWS_list, table='visits'):
    dfs = []
    for aws in AWS_list:
        aws_name = aws.name
        df = aws.table_map[table]
        df = add_suffix(df, aws_name)
        dfs.append(df)
    merged = reduce(lambda  left,right: pd.merge(left, right, how='outer', left_on=['visit_id','domain'], right_on=['visit_id','domain']), dfs)
    return merged

def get_column(df, base_column, aws_name):
    cl = base_column + make_suffix(aws_name)
    return df[cl]

def get_columns(df, base_column, aws_names):
    cls = [base_column + make_suffix(name) for name in aws_names]
    return df[cls]

def get_AWS_obj(run, location):
    return runs[run].AWS_map[loc_to_server[location]]

# return only rechables crawls
# status=1 means loaded websites, if it is the case for all VP then we considdefer ot
# TODO: these should be changed, here we assume runs with same visit_id should consider together which is wrong.
# However it is too rare that not all of the crawls for the same domain in one VP behave differently. (see appendix.1)


def append_series(servers, table, column):
    dfs = pd.Series()
    flag = False
    for server in servers:
        aws_name = server.name
        df = server.table_map[table][column]
        if not flag:
            flag = True
            dfs = df
            continue
        dfs = dfs.append(df, ignore_index=True)
    return dfs
# d = append_series(runs['mobile-sc'].AWS_list, 'visits', 'ttw')

class MinorSymLogLocator(Locator):
    """
    Dynamically find minor tick positions based on the positions of
    major ticks for a symlog scaling.
    """
    def __init__(self, linthresh):
        """
        Ticks will be placed between the major ticks.
        The placement is linear for x between -linthresh and linthresh,
        otherwise its logarithmically
        """
        self.linthresh = linthresh

    def __call__(self):
        'Return the locations of the ticks'
        majorlocs = self.axis.get_majorticklocs()

        # iterate through minor locs
        minorlocs = []

        # handle the lowest part
        for i in range(1, len(majorlocs)):
            majorstep = majorlocs[i] - majorlocs[i-1]
            if abs(majorlocs[i-1] + majorstep/2) < self.linthresh:
                ndivs = 10
            else:
                ndivs = 9
            if i == 1:
                ndivs = 0
            minorstep = majorstep / ndivs
            locs = np.arange(majorlocs[i-1], majorlocs[i], minorstep)[1:]
            minorlocs.extend(locs)

        return self.raise_if_exceeds(np.array(minorlocs))

    def tick_values(self, vmin, vmax):
        raise NotImplementedError('Cannot get tick locations for a '
                                  '%s type.' % type(self))




class Server:
    def __init__(self, name=None, visits=None,javascript_cookies=None, javascript=None):
        table_map = {}
        self.name = name
        self.location = server_to_loc[name]
        self.visits = visits
        self.javascript_cookies = javascript_cookies
        self.javascript = javascript
        table_map["visits"] = self.visits
        table_map["javascript_cookies"] = self.javascript_cookies
        table_map["javascript"] = self.javascript
        self.table_map = table_map

class Run:
    def __init__(self, name=None, server_map=None, AWS_list=None):
        self.name = name
        self.server_map = server_map
        self.AWS_list = AWS_list
        self.AWS_names = self.server_map.keys()
        self.aws_to_var()
        self.merged = merge_dfs(AWS_list, 'visits')

    def aws_to_var(self):
        server_map = self.server_map
        if "eu-central-1" in server_map:
            self.eu_central = server_map["eu-central-1"]
        if "eu-north-1" in server_map:
            self.eu_north = server_map["eu-north-1"]
        if "us-east-1" in server_map:
            self.us_east = server_map["us-east-1"]
        if "us-west-1" in server_map:
            self.us_west = server_map["us-west-1"]
        if "ap-south-1" in server_map:
            self.ap_south = server_map["ap-south-1"]
        if "sa-east-1" in server_map:
            self.a_east = server_map["sa-east-1"]
        if "af-south-1" in server_map:
            self.af_south = server_map["af-south-1"]
        if "ap-southeast-2" in server_map:
            self.ap_southeast = server_map["ap-southeast-2"]
        if "scan-2" in server_map:
            self.scan2 = server_map["scan-2"]


def fetch_db(
    run_name="desktop",
    batch_size=40,
    server_names=servers_to_fetch,
):
    servers = {}
    AWS_list = []

    global rules
    rules = load_adblock_rules()

    base_dir = "/home/subcode"

    db_files = []

    # print("\n🔍 Searching SQLite files...\n")

    # # -----------------------------
    # # CASE 1: REJECT main machines
    # # -----------------------------
    # reject_machines = [
    #     "inet-c-banners-germany-0_dyn_mpi-klsb_mpg_de",
    #     "inet-c-banners-germany-1_dyn_mpi-klsb_mpg_de",
    #     "inet-c-banners-germany-2_dyn_mpi-klsb_mpg_de",
    # ]

    # for machine in reject_machines:
    #     pattern = os.path.join(
    #         base_dir,
    #         "REJECT",
    #         machine,
    #         "*",
    #         "crawl-data.sqlite"
    #     )

    #     matched = glob.glob(pattern)

    #     print(f"\n[{machine}]")
    #     print(f"Pattern: {pattern}")

    #     if matched:
    #         print(f"✅ Found {len(matched)} files")
    #         db_files.extend(matched)
    #     else:
    #         print("❌ No files found")

    # # -----------------------------
    # # CASE 2: REJECT Acc-i runs
    # # -----------------------------
    # for i in range(1, 31):

    #     pattern = os.path.join(
    #         base_dir,
    #         "REJECT",
    #         f"rej-{i}",
    #         "ShadowMap",
    #         "datadir",
    #         "test-artifact",
    #         "*",
    #         "crawl-data.sqlite"
    #     )

    #     matched = glob.glob(pattern)

    #     print(f"\n[rej-{i}]")
    #     print(f"Pattern: {pattern}")

    #     if matched:
    #         print(f"✅ Found {len(matched)} files")
    #         db_files.extend(matched)
    #     else:
    #         print("❌ No files found")

    # print(f"\n🔥 Total DB files found: {len(db_files)}\n")

    # # -----------------------------
    # # processing unchanged
    # # -----------------------------
    for i in range(1, 2):
        pattern = os.path.join(
            base_dir,
            f"Acc-{i}",
            "crawl-data.sqlite"
        )

        matched_files = glob.glob(pattern)

        print(f"[Acc-{i}] Pattern:")
        print(f"    {pattern}")

        if matched_files:
            print(f"✅ Found {len(matched_files)} file(s)")

            for f in matched_files:
                print(f"📄 {f}")

            db_files.extend(matched_files)

        else:
            print(f"❌ No files found")

    print(f"total files in ACCEPT = {len(db_files)}")
    for db_idx, db_file in enumerate(db_files, start=1):

        print(f"\n📂 [{db_idx}/{len(db_files)}] Processing:")
        print(db_file)

        db = sqlite3.connect(db_file)
        db.row_factory = sqlite3.Row

        visit_cursor = db.execute("SELECT * FROM visits")

        batch = []

        for idx, visit_row in enumerate(visit_cursor, start=1):

            # append only if domain exists in ref_file.csv
            if visit_row["domain"] in allowed_domains:
                batch.append(visit_row)

            if len(batch) == batch_size:
                print(f"⚡ Batch ending at visit #{idx}")
                process_batch(db, batch, server_names)
                batch = []

        if batch:
            print(f"⚡ Final batch ({len(batch)} visits)")
            process_batch(db, batch, server_names)

        db.close()

        print("✅ Finished database")


def process_batch(db, batch, server_names):

    visit_ids = [row["visit_id"] for row in batch]

    visits_df = pd.DataFrame([dict(row) for row in batch])

    js_df = pd.read_sql_query(
        f"""
        SELECT * FROM javascript
        WHERE visit_id IN ({','.join(['?']*len(visit_ids))})
        """,
        db,
        params=visit_ids
    )

    js_cookie_df = pd.read_sql_query(
        f"""
        SELECT * FROM javascript_cookies
        WHERE visit_id IN ({','.join(['?']*len(visit_ids))})
        """,
        db,
        params=visit_ids
    )

    for server in server_names:

        server_obj = Server(
            server,
            visits_df,
            js_cookie_df,
            js_df
        )

        run_obj = Run(
            "stream_run",
            {server: server_obj},
            [server_obj]
        )

        process(run_obj, 1)

        del server_obj
        del run_obj


def process_urls(urls, url_column='host_url'):
    
    num_cores = os.cpu_count()
    max_workers = max(1, int(num_cores * 0.50))
    with ProcessPoolExecutor(max_workers=max_workers) as executor:

        results = list(tqdm(executor.map(check_url, urls), desc="Processing URLs", total=len(urls)))

    results_df = pd.DataFrame(results, columns=[url_column, 'EasyPrivacy', 'EasyList', 'AdServerList', 'AdGuardList', 'AllList'])
    return results_df

def merge_to_processed_urls(df, url_column="host_url"):
    merged_df = df.merge(processed_urls_df, on=url_column, how='left')
    return merged_df

# Function to fetch and return content from a URL
def fetch_url_content(url):
    response = requests.get(url)
    return response.text

def get_all_urls_to_process(url_column='host_url'):
    urls = []
    for table in tables_for_process:
        this_urls = table[url_column].tolist()
        urls.extend(this_urls)
    urls_set = set(urls)
    urls_unique = list(urls_set)
    return urls_unique


# Extract domains from filter list lines
def extract_domains(text):
    domains = set()
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("||") and "^" in line:
            domain = line[2:].split("^")[0]
            if domain:
                domains.add(domain)
    return domains

# Download and create justdomains file
def generate_justdomains(name, url):
    print(f"Fetching {name}...")
    content = requests.get(url).text
    domains = extract_domains(content)

    # Save to file
    out_file = os.path.join(LIST_DIR, f"{name}-justdomains.txt")
    with open(out_file, "w") as f:
        for d in sorted(domains):
            f.write(d + "\n")
    print(f"Saved {len(domains)} domains → {out_file}")

def get_tracking_list(tracking_lists_name=['easylist']):
    whole_list = {}
    for l in tracking_lists_name:
        list_file = LIST_DIR+l+"-justdomains.txt"
        with open(list_file) as file:
            lines = file.readlines()
            for line in lines:
                whole_list[line.rstrip()] = True
    return whole_list

def is_tracking(host):
    try:
        host = psl.get_public_suffix(host)
        # print(f"Host : {host}")
        for tracker in tracking_list:
            # print(f"Tracker from list : {tracker}")
            if tracker in host:
                return True
        return False
    except:
        return False

def process_cookies_host(df, url_column='host_url'):

    df["is_tracking"] = df.apply(lambda row: is_tracking(row[url_column]), axis=1)
    tracking_df = df[df["is_tracking"]]
    tracking_count = len(tracking_df)
    # print(f"Number of tracking rows: {tracking_count}")
    # print(df.head(5))
    return df

def get_columns(df, columns):
    return df[columns]

def run_tracking_process(map_of):
    for table in map_of:
        if "cookie" in table:
            map_of[table] = process_cookies_host(map_of[table])
        else:
            map_of[table] = merge_to_processed_urls(map_of[table])
            
def make_unique(map_of, first_last=True):
    for table in map_of:
        clmns = ["visit_id", "host_url"]
        if "cookie" in table:
            clmns.extend(["name"])
        if first_last:
            map_of[table] = get_unique_first_last(map_of[table], ["visit_id", "event_ordinal"], clmns)
        else:
            clmns.extend(['stage'])
            map_of[table] = get_unique(map_of[table], sort_columns=["visit_id", "event_ordinal"], columns=clmns)

def is_rejected(x):
    return (abs(x["btn_status"]) == 2) | (abs(x["btn_set_status"]) == 1)


def is_rejected_df(df, mode=0):
    return is_rejected(df)
    if mode == 0:
        return (df["btn_status"].abs() == 2) | (df["btn_set_status"].abs() == 1)
    elif mode == 2:
        return (df["btn_status"].abs() == 2) & (df["btn_set_status"].abs() != 3)
    elif mode == 3:
        return ((df["btn_status"].abs() == 2) & (df["btn_set_status"].abs() == 3)) | (df["btn_set_status"] == 1)

def add_accept_clicked(df):
    # accepted_domains = df[df.btn_status.abs() == 1].domain.values
    # print(len(accepted_domains))
    df["accept_clicked"] = df.apply(
    lambda x: (
        (abs(x["btn_status"]) == 1)
    ),
    axis=1
)
    return df

def add_reject_clicked(df):

    # rejected_domains = df[df.apply(is_rejected, axis=1)].domain.values
    # print(f"-----------------{len(rejected_domains)}")
    df["reject_clicked"] = df.apply(
    lambda x: (
        (is_rejected(x))
    ),
    axis=1
)
    # df["reject_clicked"] = is_rejected_df(df)
    return df

# def add_click_status(df):
    # df["clicked"] = np.select(
        # condlist=[
            # df["accept_clicked"],
            # df["reject_clicked"]
        # ],
        # choicelist=[
            # "accept",
            # "reject"
        # ],
        # default=None   # <-- KEEP None here
    # )
    # # BUT immediately convert to proper pandas missing value
    # df["clicked"] = df["clicked"].where(df["clicked"].notna(), np.nan)
    # return df

def add_click_status(df):
    cond_accept = df["accept_clicked"].fillna(False).astype(bool)
    cond_reject = df["reject_clicked"].fillna(False).astype(bool)

    df["clicked"] = np.select(
        condlist=[cond_accept, cond_reject],
        choicelist=["accept", "reject"],
        default=None
    )

    df["clicked"] = df["clicked"].where(df["clicked"].notna(), np.nan)
    return df



def add_clicked(df):
    df = add_accept_clicked(df)
    df = add_reject_clicked(df)
    df = add_click_status(df)
    return df

def add_is_after_ineract(row: pd.Series, run):
    interact_time_series = row.get('interact_time')
    if interact_time_series is None:
        return True

    if hasattr(interact_time_series, "empty"):
        if interact_time_series.empty:
            return True
        interact_time = interact_time_series.iloc[0]
    else:
        interact_time = interact_time_series

    if 'blaize_session' in str(row.get('name', '')):
        return True

    try:
        time_stamp = str(row['time_stamp']).lstrip('+')
        send_time = datetime.strptime(time_stamp, '%Y-%m-%dT%H:%M:%S.%fZ')
        send_time = send_time.replace(tzinfo=timezone.utc)
        send_time_seconds = send_time.timestamp() * 1000
    except Exception:
        return True
    res = send_time_seconds < interact_time
    return res

# def do_after_before(df, run, accept=False):
#     visits_df = runs[run].eu_central.visits
#     visits_df = visits_df[visits_df.status==0]
#     visits_df = add_clicked(visits_df)
#     df = pd.merge(visits_df, df, on='visit_id', how='inner')

#     df["is_after"] = df.apply(lambda row: add_is_after_ineract(row), axis=1)

#     return df

def get_ineract_send_dif(row):
    # Extract the first value from the Series
    interact_time = row.interact_time/1000

    time_format = r'%Y-%m-%dT%H:%M:%S.%fZ'

    # Check and adjust for leading '+' in the year
    try:
        time_stamp = row['time_stamp'].lstrip('+')
    except:
        return 0
        # pass

    try:
        time_stamp = row['time_stamp'].lstrip('+').replace("Z", "+00:00")
        send_time_seconds = datetime.fromisoformat(time_stamp).timestamp()
    except:
        return 0
    res = send_time_seconds - interact_time
    # print(f"{row.visit_id}, {send_time_seconds} , {interact_time} , {res}")
    return res


def add_after_before(df, run, accept=False):
    visits_df = run.visits
    visits_df = visits_df[visits_df.status==0]
    # print(visits_df)
    visits_df = add_clicked(visits_df)
    df = pd.merge(visits_df, df, on='visit_id', how='inner', suffixes=("", "_df"))

    base = -2

    df["interact_dif"] = df.apply(lambda row: get_ineract_send_dif(row), axis=1)
    # print(df["interact_dif"])
    df["is_after"] = df["interact_dif"] > base

    # Solution: Break it into a separate function
    def determine_stage(row):
        if not row['is_after'] :
            return "Before Interaction"
        elif row['is_after'] :
            return "After Interaction"
    
    df['stage'] = df.apply(determine_stage, axis=1)

    def determine_more_stage(row):
        if not row['is_after'] and pd.notna(row['clicked']):
            return f"Before {row['clicked'].capitalize()}"
        elif row['is_after'] and pd.notna(row['clicked']):
            return f"After {row['clicked'].capitalize()}"
        elif not row['is_after'] :
            return "Before Interaction"
        elif row['is_after'] :
            return "After Interaction"
    
    df['more_stage'] = df.apply(determine_more_stage, axis=1)

    return df



def run_after_before(map_of, run):
    for table in map_of:
        if "cookie" in table:
            map_of[table] = add_after_before(map_of[table], run)
        else:
            map_of[table] = add_after_before(map_of[table], run)


def get_stage_counts(df):

    df = df[['visit_id', "clicked_stage", "domain"]]
    
    grouped = df.groupby(['domain', 'clicked_stage']).size().reset_index(name='count')
    print(grouped.head(10))
    # stages = ["Before Interaction", "After Interaction"]
    stages = df["clicked_stage"].unique().tolist()

    stages_df = pd.DataFrame({"clicked_stage": stages})
    print(stages_df)
    stages_df["key"] = 1
    print(stages_df)
    result = pd.merge(
        df[['visit_id', 'domain', 'clicked_stage']],
        grouped,
        on=['domain', 'clicked_stage'],
        how='left'
    )

    # Keep unique rows
    result = result.drop_duplicates()

    # Final column order
    result = result[['visit_id', 'domain', 'clicked_stage', 'count']]

    return result

def process(run_obj,idx):
    main_run = run_obj.eu_central
    javascript = main_run.javascript
    javascript_cookies = main_run.javascript_cookies
    javascript.rename(columns={"script_url": "host_url"}, inplace=True)
    javascript_cookies.rename(columns={"host": "host_url"}, inplace=True)
    main_dfs = [javascript, javascript_cookies]
    main_map = {"javascript": javascript, "javascript_cookies": javascript_cookies}
    visits_main = main_run.visits[main_run.visits.status==0]
    global tables_for_process 
    tables_for_process = [javascript,javascript_cookies]
    # Fetch adblock list contents in parallel
    urls_unique = get_all_urls_to_process()
    print(f"URL Unique - {len(urls_unique)}")
    global processed_urls_df
    if load_from_backup:
        processed_urls_df = pd.read_csv(BU_DIR + "/urls_processed.csv")
    else:
        processed_urls_df = process_urls(urls_unique)
    
    if store_in_backup:
        df = processed_urls_df
        df.to_csv(BU_DIR + f"/urls_processed.csv", index=False)
    os.makedirs(LIST_DIR, exist_ok=True)
    if idx==1:
        for name, url in cookie_urls.items():
            generate_justdomains(name, url)
        global tracking_list
        tracking_list = get_tracking_list(tracking_lists)   
    make_unique(main_map)
    run_tracking_process(main_map)
    run_after_before(main_map,main_run)
    main_map_unique = copy.deepcopy(main_map)
    make_unique(main_map_unique, first_last=False)
    
    df_2 = main_map_unique["javascript"]
    df_2 = df_2[df_2["clicked"].notna()]
    df_2["clicked"] = df_2["clicked"].astype(str)
    df_2["clicked_stage"] = df_2["stage"].astype(str) + " (" + df_2["clicked"].astype(str).str.capitalize() + ")"
    df_2['domain_script_url'] = df_2['host_url'].apply(lambda url: tldextract.extract(str(url)).registered_domain if pd.notnull(url) else None)
    js = df_2[['visit_id','domain','clicked_stage','domain_script_url','symbol','AllList','host_url']]
    
    js.to_csv(
        "js.csv",
        mode='a',
        header=not os.path.exists("js.csv"),
        index=False
    )

    df_1 = main_map_unique["javascript_cookies"]
    df_1 = df_1[df_1["clicked"].notna()]
    df_1["clicked"] = df_1["clicked"].astype(str)
    df_1["clicked_stage"] = df_1["stage"].astype(str) + " (" + df_1["clicked"].astype(str).str.capitalize() + ")"
    df_1['domain_cookie'] = df_1['host_url'].apply(lambda url: tldextract.extract(url).registered_domain)
    df_3 = df_1[df_1.is_tracking]
    # print(df_3.columns)
    if not df_3.empty:
        df_3 = df_3[['visit_id','domain','clicked_stage','domain_cookie','host_url','name']]
        df_3.to_csv(
        "javascript_cookies.csv",
        mode='a',
        header=not os.path.exists("javascript_cookies.csv"),
        index=False
        )
    else:
        output_file = "only_1st_party_cookie_related_trackers.csv"

        # pick single row with required columns
        temp_df = df_1[["visit_id","host_url", "current_site","domain_cookie"]].head(1)

        # append if file exists, otherwise create with header
        temp_df.to_csv(
            output_file,
            mode='a',
            header=not os.path.exists(output_file),
            index=False
        )
        
def check_url(url):

    easyprivacy_rules = rules["easyprivacy"]
    easylist_rules = rules["easylist"]
    adserverlist_rules = rules["adserverlist"]
    adguardlist_rules = rules["adguardlist"]
    easyprivacy_result = easyprivacy_rules.should_block(url, rule_params)
    easylist_result = easylist_rules.should_block(url, rule_params)
    adserverlist_result = adserverlist_rules.should_block(url, rule_params)
    adguardlist_result = adguardlist_rules.should_block(url, rule_params)
    alllist_result = easyprivacy_result or easylist_result or adguardlist_result
    return url, easyprivacy_result, easylist_result, adserverlist_result, adguardlist_result, alllist_result
        
