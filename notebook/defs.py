def f(x):
    return x*x


def square(x):
    return x * x


import pandas as pd
import multiprocessing
import time
import defs
from tqdm import tqdm
multiprocessing.cpu_count()

from pandas.tseries.offsets import MonthEnd
from datetime import timedelta

def temp_fun(start_dt,end_dt,tf,ist,kite):
    
    pool = multiprocessing.Pool()   
    df = pd.DataFrame(pd.date_range(start_dt,end_dt)).rename(columns={0:'start_dt'})
    df['end_dt'] = df.shift(-1)
    df = df[df.index %2 == 0]
    df.fillna(end_dt + timedelta(days = 1), inplace = True)
    df['tf'] = tf
    df['inst'] = ist
    args_lst = df.values.tolist()
    async_results = [pool.apply_async(kite.historical_data, args=(i[3], i[0], i[1], i [2])) for i in args_lst]
    time.sleep(1)
    results = pd.concat([pd.DataFrame(ar.get()) for ar in async_results] )
    final_res = final_res.append(results)
 
    return final_res

def temp_fun1(start_dt,end_dt,tf,ist,kite):
    results = pd.DataFrame()
    df = pd.DataFrame(kite.historical_data(ist,start_dt, end_dt,tf))
    results = results.append(df) 
    return results