import pandas as pd
import numpy as np
import sqlite3
import os
from bs4 import BeautifulSoup as bs
import re
from functools import reduce
import seaborn as sns
import matplotlib as mpl
import matplotlib.ticker as mtick
import matplotlib.pyplot as plt
sns.set_theme()
import requests
import warnings
import scipy.stats
import scikit_posthocs as sp
from publicsuffix2 import PublicSuffixList
import time
from datetime import datetime,timedelta,timezone
import matplotlib.patches as mpatches
import pingouin as pg
import tldextract
import copy
import requests
import re
import os
from tqdm import tqdm
from adblockparser import AdblockRules
import csv
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import ProcessPoolExecutor
from matplotlib.ticker import Locator
from statannotations.Annotator import Annotator
psl = PublicSuffixList()
warnings.filterwarnings('ignore')
from collections import defaultdict
import glob