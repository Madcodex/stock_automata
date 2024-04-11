
import pandas as pd



def buy_sell_order(kite,strike_price = None,ce_pe = None, price = None, trans_type = None,order_type = "MARKET",quantity = 50):
    print("Placed order: ", strike_price, ce_pe, price,trans_type, order_type,f"{strike_price}{ce_pe}")
    order = kite.place_order(
        variety = kite.VARIETY_REGULAR,
        exchange = kite.EXCHANGE_NFO,
        tradingsymbol = f"{strike_price}{ce_pe}",
        transaction_type = trans_type,
        quantity = quantity,
        product = kite.PRODUCT_MIS,
        order_type = order_type,
        price=price,
        validity=kite.VALIDITY_DAY,
        disclosed_quantity=None,
        trigger_price=None,
        squareoff=None,
        stoploss=None,
        trailing_stoploss=None, 
        # tag="TradeviaPython",
    )
    return order

import datetime


def fetch_market_data(kite, expiry_march, start_dt, end_dt, time_frame="minute"):
    df_expiry_hist_data = pd.DataFrame()
    strike_symbol_dict = dict(
        zip(expiry_march.instrument_token, expiry_march["strike_type"])
    )
    inst_expiry = expiry_march["instrument_token"].unique().tolist()
    for i in inst_expiry:
        df = pd.DataFrame(
            kite.historical_data(
                i,
                from_date=start_dt,
                to_date=end_dt,
                interval=time_frame,
                continuous=False,
                oi=True,
            )
        )
        df["strike_type"] = strike_symbol_dict[i]
        df_expiry_hist_data = df_expiry_hist_data.append(df)
    df_expiry_hist_data["date"] = pd.to_datetime(
        df_expiry_hist_data["date"]
    ).dt.tz_localize(None)
    df_expiry_hist_data["date_only"] = pd.to_datetime(
        df_expiry_hist_data["date"].dt.date
    )
    return df_expiry_hist_data


def reorder_column(df):
    strike_prices = sorted(
        set(int(col.split("_")[1]) for col in df.columns if "oi" or "chg" in col)
    )
    reordered_columns = []
    for price in strike_prices:
        reordered_columns.extend(
            [f"oi_{price}_CE", f"chg_{price}_CE",f"chg_{price}_PE", f"oi_{price}_PE" ]
        )
    return reordered_columns


def prev_day_oi(kite, oi_strike, itm_strike, atm_strike, otm_strike):
    for i in range(1, 6):
        day = datetime.datetime.now() - datetime.timedelta(days=i)
        start_dt_prev = day.strftime("%Y-%m-%d")
        end_dt_prev = day.strftime("%Y-%m-%d")
        time_frame = "minute"
        print(start_dt_prev, end_dt_prev)
        df_prev = fetch_market_data(kite,oi_strike, start_dt_prev, end_dt_prev, time_frame)
        if df_prev.empty:
            continue
        else:
            df_prev["strike"] = df_prev["strike_type"].str[:-2].astype(int)
            df_prev["ce_pe"] = df_prev["strike_type"].str[-2:]
            break
    df_prev = (
        df_prev[df_prev["strike"].isin(itm_strike + [atm_strike] + otm_strike)]
        .groupby("strike_type")
        .tail(1)
    )
    return df_prev




def active_oi_chg(kite,expiry_march, start_dt, end_dt, time_frame="minute"):
    df_prev = pd.DataFrame()
    ltp_dict = kite.ltp([256265, 260105])
    nifty_price = ltp_dict["256265"]["last_price"]
    banknifty_price = ltp_dict["260105"]["last_price"]
    atm_strike = int(banknifty_price // 100 * 100)
    otm_strike = [atm_strike + i * 100 for i in range(1, 2)]
    itm_strike = [atm_strike - i * 100 for i in range(1, 2)]
    print(atm_strike, otm_strike, itm_strike)

    oi_strike = expiry_march.query(
        "strike in @otm_strike or strike in @itm_strike or strike == @atm_strike"
    )

    if df_prev.empty:
        df_prev = prev_day_oi(kite, oi_strike, itm_strike, atm_strike, otm_strike)

    df_oi = fetch_market_data(kite,oi_strike, start_dt, end_dt, time_frame)
    df_oi["strike"] = df_oi["strike_type"].str[:-2].astype(int)
    df_oi["ce_pe"] = df_oi["strike_type"].str[-2:]

    df_oi_merge = pd.merge(
        df_oi, df_prev[["strike_type", "oi"]], on="strike_type", suffixes=("_live", "_prev")
    ).assign(chg=lambda x: x["oi_live"] - x["oi_prev"])
    df_oi_merge = df_oi_merge.drop(["oi_prev"], axis=1).rename(columns={"oi_live": "oi"})
    df_oi_merge_pivot = (
        df_oi_merge[df_oi_merge["strike"].isin(itm_strike + [atm_strike] + otm_strike)]
        .pivot_table(
            index="date", columns=["strike", "ce_pe"], values=["oi", "chg"], aggfunc="sum"
        )
        .sort_values("date", ascending=False)
    )
    df_oi_merge_pivot.columns = [
        "_".join([str(i) for i in col]) for col in df_oi_merge_pivot.columns
    ]

    return df_oi_merge_pivot[reorder_column(df_oi_merge_pivot)].reset_index()



def indian_number_format(num):
    if num < 1000:
        return str(num)
    else:
        s = str(num)
        last_three = s[-3:]
        other_digits = s[:-3]
        formatted_number = ','.join([other_digits[i:i+2] for i in range(0, len(other_digits), 2)]) + ',' + last_three
        return formatted_number.strip(',')
    


def format_dataframe(df):
    formatted_df = df.copy()
    for col in formatted_df.columns:
        if col != 'date':
        # Assuming all columns you want to format are numeric
            formatted_df[col] = formatted_df[col].apply(indian_number_format)
    return formatted_df