
import pandas as pd



def buy_sell_order(kite,strike_price = None,ce_pe = None, price = None, trans_type = None,order_type = "MARKET",quantity = 50):
    print("Placed order: ", strike_price, ce_pe, price,trans_type, order_type,f"{strike_price}{ce_pe}")
    if "SENSEX" in strike_price:
        exchange = kite.EXCHANGE_BFO
    else:
        exchange = kite.EXCHANGE_NFO

    order = kite.place_order(
        variety = kite.VARIETY_REGULAR,
        exchange = exchange,
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
    for i in range(2, 6):
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


# config variables 
nifty_inst_token = 256265
bn_inst_token = 260105
fin_inst_token = 257801
midcp_inst_token = 288009
sensex_inst_token = 265

def active_oi_chg(kite,expiry_march, start_dt, end_dt, time_frame="minute"):
    df_prev = pd.DataFrame()
    ltp_dict = kite.ltp([nifty_inst_token, bn_inst_token, fin_inst_token, midcp_inst_token, sensex_inst_token])
    nifty_price = ltp_dict[str(nifty_inst_token)]["last_price"]
    banknifty_price = ltp_dict[str(bn_inst_token)]["last_price"]
    finnifty_price = ltp_dict[str(fin_inst_token)]["last_price"]
    midcpnifty_price = ltp_dict[str(midcp_inst_token)]["last_price"]
    sensex_price = ltp_dict[str(sensex_inst_token)]["last_price"]

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


def get_strike_price(kite,default_strike,expiry,call_stike_dd,put_strike_dd, value_to_add):
    strike_prices = [{'label': str(price), 'value': price} for price in range(default_strike-1000, default_strike+1000, value_to_add)]
    if call_stike_dd not in [strike['value'] for strike in strike_prices]:
        call_stike_dd = None
        put_strike_dd = None

    if call_stike_dd is None:
        default_call_strike = default_strike
    else:
        default_call_strike = call_stike_dd
    
    if put_strike_dd is None:
        default_put_strike = default_strike + value_to_add
    else:
        default_put_strike = put_strike_dd
    if 'SENSEX' in expiry:
        exchg = 'BFO'
    else:
        exchg = 'NFO'
    symbol_ce = f"{exchg}:{expiry}{default_call_strike}CE"
    symbol_pe = f"{exchg}:{expiry}{default_put_strike}PE"
    ltp_dict = kite.ltp([symbol_ce, symbol_pe])
    call_price = ltp_dict[symbol_ce]['last_price']
    put_price = ltp_dict[symbol_pe]['last_price']

    call_display = f"Call Price: {call_price}" if call_price is not None else "Select a Call Strike"
    put_display = f"Put Price: {put_price}" if put_price is not None else "Select a Put Strike" 

    return strike_prices, default_call_strike, default_put_strike, call_display, put_display