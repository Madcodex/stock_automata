
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


def buy_sell_order_es(espressoApi,customerId,scrip_code,tradingSymbol,trans_type,quantity,price,
                      strike_price,ce_pe,expiry_date):
    orderparams={
      "customerId": customerId,
      "scripCode": scrip_code,
      "tradingSymbol": tradingSymbol,
      "exchange": "NF",  #  -->  (Allowed parameters NC/BC/NF/RN/BF)
      "transactionType": trans_type,#      --> (Allowed parameters (B, S, BM, SM, SAM))
      "quantity": quantity,
      "disclosedQty": 0,
      "price": price,
      "triggerPrice": "0",
      "rmsCode": "ANY",
      "afterHour": "N",
      "orderType": "NORMAL",
      "channelUser": "20277125", # --> (Use LoginId as ChannelUser)
      "validity": "GFD",       #--> (Validity of an order (GFD/MyGTD/IOC))
      "requestType": "NEW",
      "productType": "CNF",    #--> (For Equity Exchange – CNC (Normal),For F&O – CNF(Normal), MIS or MIS+)
      "instrumentType": "OI",      # --> ((Future Stocks(FS)/ Future Index(FI)/ Option Index(OI)/ Option Stocks(OS)/ Future Currency(FUTCUR)/ Option Currency(OPTCUR)))
      "strikePrice":strike_price,
      "optionType": ce_pe,
      "expiry":expiry_date
    }
    print(orderparams)
    order=espressoApi.placeOrder(orderparams)
    print("PlaceOrder: {}".format(order))
    return order

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

    if df_expiry_hist_data.empty:
        return df_expiry_hist_data
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
        time_frame = "15minute"
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

def active_oi_chg(kite,ltp_data,symbol, expiry_march, start_dt, end_dt, time_frame="minute", near_strike_count = 2):
    df_prev = pd.DataFrame()
    # ltp_dict = kite.ltp([nifty_inst_token, bn_inst_token, fin_inst_token, midcp_inst_token, sensex_inst_token])
    # nifty_price = ltp_dict[str(nifty_inst_token)]["last_price"] +10
    # banknifty_price = ltp_dict[str(bn_inst_token)]["last_price"] +15
    # finnifty_price = ltp_dict[str(fin_inst_token)]["last_price"]
    # midcpnifty_price = ltp_dict[str(midcp_inst_token)]["last_price"]
    # sensex_price = ltp_dict[str(sensex_inst_token)]["last_price"]

    
    nifty_price = ltp_data[nifty_inst_token]["last_price"]
    banknifty_price = ltp_data[bn_inst_token]["last_price"]
    finnifty_price = ltp_data[fin_inst_token]["last_price"]
    midcpnifty_price = ltp_data[midcp_inst_token]["last_price"]
    sensex_price = ltp_data[sensex_inst_token]["last_price"]

    if symbol == "NIFTY":
        atm_strike = int(nifty_price // 50 * 50)
        otm_strike = [atm_strike + i * 50 for i in range(1, near_strike_count)]
        itm_strike = [atm_strike - i * 50 for i in range(1, near_strike_count)]
    elif symbol == "BANKNIFTY":
        atm_strike = int(banknifty_price // 100 * 100)
        otm_strike = [atm_strike + i * 100 for i in range(1, near_strike_count)]
        itm_strike = [atm_strike - i * 100 for i in range(1, near_strike_count)]
    elif symbol == "FINNIFTY":
        atm_strike = int(finnifty_price // 50 * 50)
        otm_strike = [atm_strike + i * 50 for i in range(1, near_strike_count)]
        itm_strike = [atm_strike - i * 50 for i in range(1, near_strike_count)]    
    elif symbol == "MIDCPNIFTY":
        atm_strike = int(midcpnifty_price // 25 * 25)
        otm_strike = [atm_strike + i * 25 for i in range(1, near_strike_count)]
        itm_strike = [atm_strike - i * 25 for i in range(1, near_strike_count)]
    elif symbol == "SENSEX":
        atm_strike = int(sensex_price // 100 * 100)
        otm_strike = [atm_strike + i * 100 for i in range(1, near_strike_count)]
        itm_strike = [atm_strike - i * 100 for i in range(1, near_strike_count)]

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


# def indian_number_format(num):
#     # Check if the number is negative
#     negative = num < 0
#     if negative:
#         num = -num  # Convert to positive for processing
        
#     num_str = str(num)
#     if len(num_str) <= 3:
#         return f"-{num_str}" if negative else num_str
    
#     # Separate the last three digits
#     last_three = num_str[-3:]
#     # Remaining digits
#     remaining = num_str[:-3]
    
#     # Create groups of two from right to left
#     groups = []
#     while len(remaining) > 2:
#         groups.append(remaining[-2:])
#         remaining = remaining[:-2]
#     if remaining:
#         groups.append(remaining)
    
#     # Reverse the list to get the correct order and join all parts
#     groups.reverse()
#     formatted_number = ','.join(groups) + ',' + last_three
    
#     # Reattach the negative sign if the number was negative
#     return f"-{formatted_number}" if negative else formatted_number

def indian_number_format(num):
    if num < 100000:  # Less than 1 lakh
        if num < 1000:
            return str(num)  # For numbers less than 1000, show as is
        else:
            return f"{num // 1000}k"  # For thousands
    elif num < 10000000:  # Less than 1 crore
        return f"{(num // 1000)/ 100}L"  # For lakhs
    else:
        return f"{(num // 100000)/100}Cr"  # For crores

def format_dataframe(df):
    formatted_df = df.copy()
    for col in formatted_df.columns:
        if col != 'date' and 'temp' not in col:
        # Assuming all columns you want to format are numeric
            formatted_df[col] = formatted_df[col].apply(indian_number_format)
    return formatted_df


def get_strike_price(kite, default_strike,expiry,call_stike_dd,put_strike_dd, value_to_add,ltp_data,stock):
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
    symbol_ce = f"{expiry}{default_call_strike}CE"
    symbol_pe = f"{expiry}{default_put_strike}PE"
    symbol_ce = pd.DataFrame([stock]).T.reset_index().query("index == @symbol_ce")[0].values[0]
    symbol_pe = pd.DataFrame([stock]).T.reset_index().query("index == @symbol_pe")[0].values[0]

    call_price = ltp_data[symbol_ce]['last_price']
    put_price = ltp_data[symbol_pe]['last_price']

    call_display = f"Call Price: {call_price}" if call_price is not None else "Select a Call Strike"
    put_display = f"Put Price: {put_price}" if put_price is not None else "Select a Put Strike" 

    return strike_prices, default_call_strike, default_put_strike, call_display, put_display



# def value_to_color(value, min_val, max_val):
#     normalized = (value - min_val) / (max_val - min_val)
#     r = int(255 * (1 - normalized))
#     g = int(255 * normalized)
#     b = 0
#     return f'rgb({r},{g},{b})'


# def value_to_color(value, min_val, max_val):
#     normalized = (value - min_val) / (max_val - min_val)
#     # Use HSL (Hue, Saturation, Lightness) instead of RGB for smoother color transitions
#     # Hue from 240 (blue) to 120 (green)
#     hue = 240 - (normalized * 120)
#     # Fixed saturation at 50% to avoid too bright colors, lightness at 80% for a lighter tone
#     saturation = 50
#     lightness = 80
#     return f'hsl({hue}, {saturation}%, {lightness}%)'


# def value_to_color(value, min_val, max_val):
#     # Normalize the value to the range [0, 1]
#     normalized = (value - min_val) / (max_val - min_val)
#     # Create a smoother transition between colors
#     # Starting from a cool light blue to a warmer peach
#     # Using HSL for better control over color transitions
#     hue_start = 200  # Light blue
#     hue_end = 30    # Warm peach
#     hue = hue_start + (hue_end - hue_start) * normalized
#     saturation = 70  # Relatively high saturation for distinctiveness
#     lightness = 60   # Not too bright, not too dark
#     return f'hsl({hue}, {saturation}%, {lightness}%)'

# def value_to_color(value, min_val, max_val):
#     # Normalize the value to the range [0, 1]
#     normalized = (value - min_val) / (max_val - min_val)
#     # Transition from green (120 degrees) to red (0 degrees) on the HSL color wheel
#     hue_start = 120  # Green
#     hue_end = 0      # Red
#     hue = hue_start + (hue_end - hue_start) * normalized
#     saturation = 70  # Good saturation to keep the colors vivid but not overwhelming
#     lightness = 60   # Balanced lightness for good visibility
#     return f'hsl({hue}, {saturation}%, {lightness}%)'

def value_to_color(value, min_val, max_val):
    # Normalize the value to the range [0, 1]
    normalized = (value - min_val) / (max_val - min_val)
    # Create a smoother transition between colors
    # Starting from a warm peach to a cooler light blue
    # Using HSL for better control over color transitions
    hue_start = 30    # Warm peach
    hue_end = 200     # Light blue
    hue = hue_start + (hue_end - hue_start) * normalized
    saturation = 70   # Relatively high saturation for distinctiveness
    lightness = 60    # Not too bright, not too dark
    return f'hsl({hue}, {saturation}%, {lightness}%)'

