import pandas as pd
import gc

for var in list(globals()):
    obj = globals()[var]
    if isinstance(obj, pd.DataFrame):
        del globals()[var]

gc.collect()
