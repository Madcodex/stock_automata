import pandas as pd
from tqdm import tqdm
import time
import multiprocessing
from pandas.tseries.offsets import MonthEnd
from datetime import timedelta
import swifter
import dask.dataframe as dd




# def temp_fun(start_dt,end_dt,tf,ist,kite):
    
#     pool = multiprocessing.Pool()   
#     df = pd.DataFrame(pd.date_range(start_dt,end_dt)).rename(columns={0:'start_dt'})
#     df['end_dt'] = df.shift(-1)
#     df = df[df.index %2 == 0]
#     df.fillna(end_dt + timedelta(days = 1), inplace = True)
#     df['tf'] = tf
#     df['inst'] = ist
#     args_lst = df.values.tolist()
#     async_results = [pool.apply_async(kite.historical_data, args=(i[3], i[0], i[1], i [2])) for i in args_lst]
#     time.sleep(1)
#     results = pd.concat([pd.DataFrame(ar.get()) for ar in async_results] )
#     final_res = final_res.append(results)
 
#     return final_res


# def get_instrument_data(kite,instrument, timerframe_list, start_date, end_date):
#     print(start_date,end_date)

#     for tf in timerframe_list: 
#         comp_df = pd.DataFrame()
#         print(tf)
#         if tf == 'day':
#             df = get_day_data(kite, instrument, tf, start_date,start_date)  

#         else:
#             start_mth = pd.date_range(start_date, end_date,freq="MS")
#             start_mth = pd.DataFrame(start_mth).rename(columns = {0:'start_dt'})
#             start_mth['end_dt'] = pd.to_datetime(start_mth.start_dt, format="%Y%m") + MonthEnd(0)
#             start_mth['tf'] = tf
#             start_mth['inst'] = instrument
#             start_mth['kite'] = kite
#             args_lst = start_mth.values.tolist()
#             for i in args_lst:
#                 get_data_parllel(kite = i[4], instrument, time_frame, start_dt, end_dt):


# #             pool = multiprocessing.Pool()
# #             args_lst = start_mth.values.tolist()
# #             async_result = [pool.apply_async(defs.temp_fun1, args=(i[0], i[1], i[2], i[3], i[4])) for i in args_lst]
# # #             time.sleep(1)
# #             results = pd.concat([(ar.get()) for ar in async_result] )

#             results['company'] = ist
#             # comp_df = comp_df.append(results)
#             # comp_df.rename(columns = {'date': "Date",'close':'Close', 'high':'High', 'low':"Low", 'open': "Open"}, inplace = True)
#             # comp_df.rename(columns= {"volume":"Volume"}, inplace = True)
#             # comp_df.set_index('Date', inplace=True)
#             # comp_df.drop(['volume','company'], inplace= True,axis= 1)
#         # table = pa.Table.from_pandas(comp_df)
#         # pq.write_to_dataset(table,root_path = f"historical_data/{tf}/",partition_cols=['company'],use_threads=True)  
#         # break
#     return comp_df

def get_day_data(kite, instrument, time_frame, start_date,end_date):
    results = pd.DataFrame()
    df = pd.DataFrame(kite.historical_data(instrument,start_date, end_date,time_frame))
    results = results.append(df) 
    return results

def get_data_parllel(kite, instrument, time_frame, start_date, end_date):
    df_final = pd.DataFrame()
    df = pd.DataFrame(pd.date_range(start_date,end_date,freq="MS")).rename(columns={0:'start_date'})
    df['end_date'] = df.shift(-1)
    df.dropna(inplace=True)
    df['tf'] = time_frame
    df['inst'] = instrument
    df['fetch_data'] = df.swifter.apply(lambda x: pd.DataFrame(kite.historical_data(x['inst'], x['start_date'], x['end_date'], x['tf'])),axis = 1)
    for i in df['fetch_data']:
        df_final = df_final.append(i)
    df_final.rename(columns = {'date': "Date",'close':'Close', 'high':'High', 'low':"Low", 'open': "Open","volume":"Volume"}, inplace = True)
    df_final.set_index('Date', inplace=True)
    return df_final



# ddf = dd.from_pandas(df, npartitions=30) # find your own number of partitions
# ddf_update = ddf.apply(your_func, axis=1).compute()




