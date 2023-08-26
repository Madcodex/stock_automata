# -*- coding: utf-8 -*-
"""
Created on Fri Oct 14 09:13:23 2022

Here i coded to fetch option chain data and trade terminal sheet, where all input comes using web socket which leads to zero lag. And you can place order based on your selection.

Contact details :
Telegram Channel:  https://t.me/pythontrader
Developer Telegram ID : https://t.me/pythontrader_admin
Gmail ID:   mnkumar2020@gmail.com 
Whatsapp : 9470669031 

Disclaimer: The information provided by the Python Traders channel is for educational purposes only, so please contact your financial adviser before placing your trade. Developer is not responsible for any profit/loss happened due to coding, logical or any type of error.
"""

import warnings
warnings.filterwarnings("ignore")
from NorenRestApiPy.NorenApi import NorenApi
import os
import time
import json
import sys
import requests
import xlwings as xw
import pandas as pd
from datetime import datetime
from time import sleep
import logging
import pyotp
from datetime import datetime
from threading import Thread

# logging.basicConfig(level=logging.DEBUG)

ins_df = pd.DataFrame()

OptionChain_template = []
subs_lst = []
subs_pending_lst = []

IndexList = ["NIFTY", "BANKNIFTY", "FINNIFTY"]

IndexList_token = [
    {"Name": "NIFTY", "Token": 26000},
    {"Name": "BANKNIFTY", "Token": 26009},
    {"Name": "FINNIFTY", "Token": 26037},
    {"Name": "INDIAVIX", "Token": 26017},
]


def Shoonya_login():
    global api
    isConnected = 0
    excel_name = xw.Book("Finvasia_Trade_Terminal.xlsx")
    Credential_sheet = excel_name.sheets["User_Credential"]


    try:

        try:
            class ShoonyaApiPy(NorenApi):
                def __init__(self):
                    NorenApi.__init__(self, host='https://api.shoonya.com/NorenWClientTP/', websocket='wss://api.shoonya.com/NorenWSTP/', eodhost='https://api.shoonya.com/chartApi/getdata/')
            api = ShoonyaApiPy()
        except Exception as e:
            class ShoonyaApiPy(NorenApi):
                def __init__(self):
                    NorenApi.__init__(self, host='https://api.shoonya.com/NorenWClientTP/', websocket='wss://api.shoonya.com/NorenWSTP/')
            api = ShoonyaApiPy()

        

        userid = Credential_sheet.range("B2").value.strip()
        password = Credential_sheet.range("B3").value.strip()
        TotpKey = str(Credential_sheet.range("B4").value)
        pin = pyotp.TOTP(TotpKey).now()
        twoFA = f"{int(pin):06d}" if len(pin) <= 5 else pin
        vendor_code = Credential_sheet.range("B5").value.strip()
        api_secret = Credential_sheet.range("B6").value.strip()
        imei = "abcd1234"

        print(
            f"userid={userid},password={password},twoFA={twoFA},vendor_code={vendor_code},api_secret={api_secret}, imei={imei}"
        )
        login_status = api.login(
            userid=userid,
            password=password,
            twoFA=twoFA,
            vendor_code=vendor_code,
            api_secret=api_secret,
            imei=imei,
        )

        client_name = login_status.get("uname")
        print(login_status)
        Credential_sheet.range("c2").value = "Login Successful, Welcome " + client_name
        isConnected = 1

    except Exception as e:
        print(f"Error : {e}")
        Credential_sheet.range("c2").value = "Wrong credential"

    return isConnected


feed_opened = False
SYMBOLDICT = {}
live_data = {}


def event_handler_quote_update(inmessage):
    global live_data

    global SYMBOLDICT
    # e   Exchange
    # tk  Token
    # lp  LTP
    # pc  Percentage change
    # v   volume
    # o   Open price
    # h   High price
    # l   Low price
    # c   Close price
    # ap  Average trade price

    fields = [
        "ts",
        "lp",
        "pc",
        "c",
        "o",
        "h",
        "l",
        "v",
        "ltq",
        "ltp",
        "bp1",
        "sp1",
        "ap",
        "oi",
        "ap",
        "poi",
        "toi",
    ]

    message = {field: inmessage[field] for field in set(fields) & set(inmessage.keys())}
    # print(message)
    key = inmessage["e"] + "|" + inmessage["tk"]

    if key in SYMBOLDICT:
        symbol_info = SYMBOLDICT[key]
        symbol_info.update(message)
        SYMBOLDICT[key] = symbol_info
        live_data[key] = symbol_info
    else:
        SYMBOLDICT[key] = message
        live_data[key] = message


def event_handler_order_update(tick_data):
    print(f"Order update {tick_data}")


def open_callback():
    global feed_opened
    feed_opened = True


def order_status(orderid):
    AverageExecutedPrice = 0
    try:
        order_book = get_order_book()
        order_book = order_book[order_book.norenordno == str(orderid)]

        status = order_book.iloc[0]["status"]
        if status == "COMPLETE":
            AverageExecutedPrice = order_book.iloc[0]["avgprc"]
    except Exception as e:
        Message = str(e) + " : Exception occur in order_status"
        print(Message)
    return AverageExecutedPrice


def place_trade(symbol, quantity, buy_or_sell):
    global api
    tradingsymbol = symbol[4:]
    exchange = symbol[:3]
    price_type = "MKT"
    price = 0.0

    if exchange == "NSE":
        product_type = "C"
        # price = round(float(price),1)
    else:
        product_type = "M"
        
    #remove below line if you want to take positional trade
    product_type = "I"
    
    ret = api.place_order(
        buy_or_sell=buy_or_sell[0],
        product_type=product_type,
        exchange=exchange,
        tradingsymbol=tradingsymbol,
        quantity=quantity,
        discloseqty=0,
        price_type=price_type,
        price=price,
        trigger_price=None,
        retention="DAY",
        remarks="Python_Trader",
    ).get("norenordno")

    ExecutedPrice = order_status(ret)

    Message = "Placed order id :" + ret + ", Executed @ " + str(ExecutedPrice)
    print(Message)

    return ExecutedPrice


def get_order_book():

    global api
    order_book = api.get_order_book()
    order_book = pd.DataFrame(order_book)
    order_book = order_book.sort_values(by=["norenordno"]).reset_index(drop=True)
    return order_book


def GetToken(exchange, tradingsymbol):
    global api
    Token = (
        api.searchscrip(exchange=exchange, searchtext=tradingsymbol)
        .get("values")[0]
        .get("token")
    )
    return Token


def subscribe_new_token(exchange, Token):
    global api
    symbol = []
    symbol.append(f"{exchange}|{Token}")
    api.subscribe(symbol)


def start_Trade_Terminal():
    global api, live_data
    global SYMBOLDICT
    excel_name = xw.Book("Finvasia_Trade_Terminal.xlsx")
    dt = excel_name.sheets("Trade_Terminal")
    ob = excel_name.sheets("OrderBook")
    ob.range("a:az").value = dt.range("n:t").value = None
    dt.range(f"a1:t1").value = [
        "Symbol",
        "Open",
        "High",
        "Low",
        "Close",
        "VWAP",
        "Best Buy Price",
        "Best Sell Price",
        "Volume",
        "LTP",
        "Percentage change",
        "Qty",
        "Direction",
        "Entry Signal",
        "Exit Signal",
        "Entry Price",
        "Exit Price",
        "Target",
        "SL" ,
        "Trade Status"
    ]

    subs_lst = []
    Symbol_Token = {}

    while True:
        try:
            time.sleep(0.5)
            # print(datetime.now())
            symbols = dt.range(f"a{2}:a{1000}").value
            trading_info = dt.range(f"l{2}:t{1000}").value
            main_list = []

            idx = 0
            for i in symbols:
                lst = [None, None, None, None, None, None, None, None, None, None]
                if i:
                    if i not in subs_lst:
                        subs_lst.append(i)
                        try:
                            exchange = i[:3]
                            tradingsymbol = i[4:]
                            Token = GetToken(exchange, tradingsymbol)
                            Symbol_Token[i] = exchange + "|" + str(Token)
                            subscribe_new_token(exchange, Token)
                            print(f"Symbol = {i}, Token={Token} subscribed")

                        except Exception as e:
                            print(f"Subscribe error {i} : {e}")
                    if i in subs_lst:
                        try:
                            TokenKey = Symbol_Token[i]

                            lst = [
                                live_data[TokenKey].get("o", "-"),
                                live_data[TokenKey].get("h", "-"),
                                live_data[TokenKey].get("l", "-"),
                                live_data[TokenKey].get("c", "-"),
                                live_data[TokenKey].get("ap", "-"),
                                live_data[TokenKey].get("bp1", "-"),
                                live_data[TokenKey].get("sp1", "-"),
                                live_data[TokenKey].get("v", "-"),
                                live_data[TokenKey].get("lp", "-"),
                                live_data[TokenKey].get("pc", "-"),
                            ]
                            trade_info = trading_info[idx]

                            if trade_info[0] is not None and trade_info[1] is not None:
                                if type(trade_info[0]) is float and type(trade_info[1]) is str:
                                    if trade_info[1].upper() == "BUY" and trade_info[2] is True:
                                        
                                        #0:Qty    1:Direction    2:Entry_Signal    3:Exit Signal 4:Entry_Price    5:Exit_Price    6:Target    7:SL    8:Trade_status

                                        if trade_info[2] is True and trade_info[3] is not True and trade_info[4] is None and trade_info[5] is None and trade_info[8] is None:
                                    
                                            dt.range(f"p{idx + 2}").value = place_trade(i, int(trade_info[0]), "BUY")
                                            dt.range(f"t{idx + 2}").value = 'Active'
                                        
                                        elif trade_info[2] is True and  trade_info[4] is not None and trade_info[5] is None and trade_info[8] == 'Active':
                                            LTP = float(live_data[TokenKey].get("lp", 0))
                                            #print(f"LTP = {LTP}, target {trade_info[6]} SL {trade_info[7]}")
                                            if trade_info[3] is True:
                                                dt.range(f"q{idx + 2}").value = place_trade(i, int(trade_info[0]), "SELL")
                                                dt.range(f"t{idx + 2}").value = 'Closed'
                                            
                                            elif type(trade_info[6]) is float and trade_info[6] <= LTP and LTP != 0 and trade_info[8] == 'Active':
                                                dt.range(f"q{idx + 2}").value = place_trade(i, int(trade_info[0]), "SELL")
                                                dt.range(f"t{idx + 2}").value = 'Closed'
                                            
                                            elif type(trade_info[7]) is float and trade_info[7] >= LTP and LTP != 0:
                                                dt.range(f"q{idx + 2}").value = place_trade(i, int(trade_info[0]), "SELL")
                                                dt.range(f"t{idx + 2}").value = 'Closed'
                                                
                                    if trade_info[1].upper() == "SELL" and trade_info[2] is True:
                                    
                                    #0:Qty    1:Direction    2:Entry_Signal    3:Exit Signal 4:Entry_Price    5:Exit_Price    6:Target    7:SL    8:Trade_status

                                        if trade_info[2] is True and trade_info[3] is not True and trade_info[4] is None and trade_info[5] is None and trade_info[8] is None:
                                            dt.range(f"p{idx + 2}").value = place_trade(i, int(trade_info[0]), "SELL")
                                            dt.range(f"t{idx + 2}").value = 'Active'
                                        
                                        elif trade_info[2] is True and  trade_info[4] is not None and trade_info[5] is None and trade_info[8] == 'Active':
                                            LTP = float(live_data[TokenKey].get("lp", 0))
                                            
                                            if trade_info[3] is True:
                                            
                                                dt.range(f"q{idx + 2}").value = place_trade(i, int(trade_info[0]), "BUY")
                                                dt.range(f"t{idx + 2}").value = "Closed"
                                                
                                            elif type(trade_info[6]) is float and trade_info[6] >= LTP and LTP != 0 and trade_info[8] == 'Active':
                                                dt.range(f"q{idx + 2}").value = place_trade(i, int(trade_info[0]), "BUY")
                                                dt.range(f"t{idx + 2}").value = 'Closed'
                                            
                                            elif type(trade_info[7]) is float and trade_info[7] <= LTP and LTP != 0:
                                                dt.range(f"q{idx + 2}").value = place_trade(i, int(trade_info[0]), "BUY")
                                                dt.range(f"t{idx + 2}").value = 'Closed'
                        except Exception as e:
                            # print(str(e))
                            pass
                main_list.append(lst)

                idx += 1

            dt.range("b2:k1000").value = main_list
            if excel_name.sheets.active.name == "OrderBook":
                ob.range("a1").value = get_order_book()
        except Exception as e:
            # print(str(e))
            pass


def LoadInstrument_token():
    global ins_df
    global api

    excel_name = xw.Book("Finvasia_Trade_Terminal.xlsx")
    print("Downloading master intrument")
    zip_file = "NFO_symbols.txt.zip"
    url = f"https://shoonya.finvasia.com/{zip_file}"
    r = requests.get(f"{url}", allow_redirects=True)
    open(zip_file, "wb").write(r.content)
    ins_df = pd.read_csv(zip_file)

    # ins_df= pd.read_csv("NFO_symbols.csv")
    ins_df = ins_df.sort_values(by="Symbol", ascending=True)
    ins_df = ins_df.astype({"StrikePrice": int})
    ins_df = ins_df.astype({"StrikePrice": str})

    List_Of_Symbols = ins_df["Symbol"].unique()

    List_Of_Symbols = pd.DataFrame(List_Of_Symbols)
    List_Of_Symbols = List_Of_Symbols.set_axis(["FNO Symbol"], axis=1, inplace=False)
    # List_Of_Symbols = List_Of_Symbols.reset_index(drop=True, inplace=True)

    Symbol_Selection = excel_name.sheets("Symbol_Selection")

    Symbol_Selection.range("a1").options(index=False).value = List_Of_Symbols


def Clear_optionchain():
    excel_name = xw.Book("Finvasia_Trade_Terminal.xlsx")
    Option_Chain = excel_name.sheets("Option_Chain")
    #Additional_Detail = excel_name.sheets("Additional_Detail")

    Option_Chain.range("a4:z500").value = None
    

    #Additional_Detail.range("B10:D11").value = None
    #Additional_Detail.range("B14").value = None
    #Additional_Detail.range("B16:C17").value = None


def start_optionchain():
    global subscribe_symbol
    global live_data
    global ins_df
    excel_name = xw.Book("Finvasia_Trade_Terminal.xlsx")
    Symbol_Selection = excel_name.sheets("Symbol_Selection")
    Option_Chain = excel_name.sheets("Option_Chain")
    
    Option_Chain.range("I1").value = None
    Option_Chain.range("L1").value = None
    Option_Chain.range("N1").value = None
    Option_Chain.range("P1").value = None
    Option_Chain.range("R1").value = None
    
    Additional_Detail = excel_name.sheets("Additional_Detail")

    Symbol_Selection.range("L6").value = None
    Symbol_Selection.range("L7").value = None
    Symbol_Selection.range("b2:b100").value = None
    Symbol_Selection.range("c2:c100").value = None

    Clear_optionchain()

    IterationSleep = 5
    while True:
        
        input_symbol = Symbol_Selection.range("J3").value
        if input_symbol != None:

            ins_df_temp = ins_df[ins_df.Symbol == input_symbol]
            if len(ins_df_temp) > 0:
                Symbol_Selection.range("L6").value = None
                input_symbol = input_symbol.strip()

                expiry_input = Symbol_Selection.range("J4").value

                print(
                    f"Option Chain Details: input_symbol={input_symbol},expiry_input={expiry_input}"
                )
                if expiry_input != None:

                    ins_df_temp = ins_df[ins_df.Expiry == expiry_input]
                    if len(ins_df_temp) > 0:

                        Symbol_Selection.range("L7").value = None
                        Symbol_Selection.range("b2:b100").value = None
                        Symbol_Selection.range("c2:c100").value = None
                        try:
                            IterationSleep = Symbol_Selection.range("J6").value
                            if IterationSleep != None:
                                IterationSleep = int(IterationSleep)
                                Symbol_Selection.range("L8").value = None
                        except:
                            IterationSleep = 5
                            Message = "Itegartion should be number"
                            print(Message)
                            Symbol_Selection.range("L8").value = Message

                        symbol_in_template = [
                            itr
                            for itr in OptionChain_template
                            if itr["symbol"] == input_symbol
                        ]
                        if len(symbol_in_template) == 0:
                            print("Symbol Not found, so append the details")

                            ind_df_specific_symbol = ins_df[
                                ins_df.Symbol == input_symbol
                            ]
                            # print(ind_df_specific_symbol)

                            List_of_Expiry = ind_df_specific_symbol["Expiry"].unique()
                            # print(List_of_Expiry)

                            Expiry_strikelist_list = []

                            for expiry in List_of_Expiry:
                                # print(expiry)
                                ind_df_specific_symbol_expiry = ind_df_specific_symbol[
                                    ind_df_specific_symbol.Expiry == expiry
                                ]
                                # print(ind_df_specific_symbol_expiry)

                                List_of_strikes = ind_df_specific_symbol_expiry[
                                    "StrikePrice"
                                ].unique()

                                LotSize = ind_df_specific_symbol_expiry.iloc[0][
                                    "LotSize"
                                ]
                                # print(LotSize)
                                # print(List_of_strikes)
                                strike_pe_ce_list = []

                                for strike in List_of_strikes:
                                    # print(f"\n\nsymbol:{input_symbol},Expiry:{expiry},strike:{strike}")
                                    ind_df_specific_symbol_expiry_pe = ind_df_specific_symbol_expiry[
                                        (
                                            ind_df_specific_symbol_expiry.StrikePrice
                                            == str(strike)
                                        )
                                        & (
                                            ind_df_specific_symbol_expiry.OptionType
                                            == "PE"
                                        )
                                    ]
                                    if len(ind_df_specific_symbol_expiry_pe) > 0:
                                        pe_token = (
                                            ind_df_specific_symbol_expiry_pe.iloc[0][
                                                "Token"
                                            ]
                                        )
                                    else:
                                        pe_token = "NA"

                                    ind_df_specific_symbol_expiry_ce = ind_df_specific_symbol_expiry[
                                        (
                                            ind_df_specific_symbol_expiry.StrikePrice
                                            == str(strike)
                                        )
                                        & (
                                            ind_df_specific_symbol_expiry.OptionType
                                            == "CE"
                                        )
                                    ]
                                    if len(ind_df_specific_symbol_expiry_ce) > 0:
                                        ce_token = (
                                            ind_df_specific_symbol_expiry_ce.iloc[0][
                                                "Token"
                                            ]
                                        )
                                    else:
                                        ce_token = "NA"

                                    # print(f"symbol:{input_symbol},Expiry:{expiry},strike:{strike},pe_token={pe_token},ce_token={ce_token}")

                                    strike_pe_ce_dictionary = dict(
                                        {
                                            "strike": strike,
                                            "PE_Token": pe_token,
                                            "CE_Token": ce_token,
                                        }
                                    )

                                    strike_pe_ce_list.append(strike_pe_ce_dictionary)

                                # print(strike_pe_ce_list)

                                expiry_stikelist_dict = dict(
                                    {
                                        "Expiry": expiry,
                                        "LotSize": LotSize,
                                        "Strike_list": strike_pe_ce_list,
                                    }
                                )

                                Expiry_strikelist_list.append(expiry_stikelist_dict)

                            # print("\n\n")
                            # print(Expiry_strikelist_list)

                            Final_dic = dict(
                                {
                                    "symbol": input_symbol,
                                    "Expiry_Strike_token": Expiry_strikelist_list,
                                }
                            )

                            OptionChain_template.append(Final_dic)
                            # print("\n\n")
                            # print(OptionChain_template)
                        else:
                            Message = (
                                "symbol already available in option chain template"
                            )

                        List_of_Expiry_Strike_token = [
                            itr["Expiry_Strike_token"]
                            for itr in OptionChain_template
                            if itr["symbol"] == input_symbol
                        ][0]
                        # print(f"\n\n\n{List_of_Expiry_Strike_token}")

                        abc = 2
                        for expiry_strike in List_of_Expiry_Strike_token:
                            # print(expiry_strike['Expiry'])

                            Symbol_Selection.range(
                                "B" + str(abc)
                            ).value = expiry_strike["Expiry"]
                            Symbol_Selection.range(
                                "C" + str(abc)
                            ).value = expiry_strike["LotSize"]

                            abc = abc + 1

                            if input_symbol not in subs_lst:

                                List_of_particular_expiry_strike = [
                                    itr["Strike_list"]
                                    for itr in List_of_Expiry_Strike_token
                                    if itr["Expiry"] == expiry_strike["Expiry"]
                                ][0]

                                for strike_dict in List_of_particular_expiry_strike:
                                    print(
                                        f"Going to subscribe strike {strike_dict.get('strike')}"
                                    )
                                    PE_Token = strike_dict.get("PE_Token")
                                    # print(PE_Token)
                                    CE_Token = strike_dict.get("CE_Token")
                                    # print(CE_Token)
                                    if PE_Token != "NA":
                                        subscribe_new_token("NFO", PE_Token)
                                    if CE_Token != "NA":
                                        subscribe_new_token("NFO", CE_Token)

                        if input_symbol not in subs_lst:
                            subs_lst.append(input_symbol)
                            print(f"{input_symbol} subscription completed")

                        pd_oc = pd.DataFrame(
                            columns=[
                                "CE_token",
                                "CE_oi",
                                "CE_poi",
                                "CE_toi",
                                "CE_lp",
                                "CE_pc",
                                "CE_bq1",
                                "CE_bp1",
                                "CE_sq1",
                                "CE_sp1",
                                "strike",
                                "PE_bq1",
                                "PE_bp1",
                                "PE_sq1",
                                "PE_sp1",
                                "PE_pc",
                                "PE_lp",
                                "PE_toi",
                                "PE_poi",
                                "PE_oi",
                                "PE_token",
                            ]
                        )

                        # prepare option chain
                        List_of_Expiry_Strike_token = [
                            itr["Expiry_Strike_token"]
                            for itr in OptionChain_template
                            if itr["symbol"] == input_symbol
                        ][0]

                        try:
                            List_of_particular_expiry_strike = [
                                itr["Strike_list"]
                                for itr in List_of_Expiry_Strike_token
                                if itr["Expiry"] == expiry_input
                            ][0]

                            # print(f"****{live_data}")
                            for strike_dict in List_of_particular_expiry_strike:

                                Strike = strike_dict.get("strike")
                                # print(Strike)
                                PE_Token = strike_dict.get("PE_Token")
                                PE_Token = "NFO|" + str(PE_Token)
                                # print(PE_Token)
                                CE_Token = strike_dict.get("CE_Token")
                                CE_Token = "NFO|" + str(CE_Token)
                                # print(CE_Token)

                                try:
                                    CE_oi = live_data[str(CE_Token)].get("oi", 0)
                                except:
                                    CE_oi = 0
                                try:
                                    CE_poi = live_data[str(CE_Token)].get("poi", "-")
                                except:
                                    CE_poi = "-"
                                try:
                                    CE_toi = live_data[str(CE_Token)].get("toi", "-")
                                except:
                                    CE_toi = "-"
                                try:
                                    CE_lp = live_data[str(CE_Token)].get("lp", "-")
                                except:
                                    CE_lp = "-"
                                try:
                                    CE_pc = live_data[str(CE_Token)].get("pc", "-")
                                except:
                                    CE_pc = "-"
                                try:
                                    CE_bq1 = live_data[str(CE_Token)].get("bq1", "-")
                                except:
                                    CE_bq1 = "-"
                                try:
                                    CE_bp1 = live_data[str(CE_Token)].get("bp1", "-")
                                except:
                                    CE_bp1 = "-"
                                try:
                                    CE_sq1 = live_data[str(PE_Token)].get("sq1", "-")
                                except:
                                    CE_sq1 = "-"
                                try:
                                    CE_sp1 = live_data[str(PE_Token)].get("sp1", "-")
                                except:
                                    CE_sp1 = "-"

                                try:
                                    PE_oi = live_data[str(PE_Token)].get("oi", 0)
                                except:
                                    PE_oi = 0
                                try:
                                    PE_poi = live_data[str(PE_Token)].get("poi", "-")
                                except:
                                    PE_poi = "-"
                                try:
                                    PE_toi = live_data[str(PE_Token)].get("toi", "-")
                                except:
                                    PE_toi = "-"
                                try:
                                    PE_lp = live_data[str(PE_Token)].get("lp", "-")
                                except:
                                    PE_lp = "-"
                                try:
                                    PE_pc = live_data[str(PE_Token)].get("pc", "-")
                                except:
                                    PE_pc = "-"
                                try:
                                    PE_bq1 = live_data[str(PE_Token)].get("bq1", "-")
                                except:
                                    PE_bq1 = "-"
                                try:
                                    PE_bp1 = live_data[str(PE_Token)].get("bp1", "-")
                                except:
                                    PE_bp1 = "-"
                                try:
                                    PE_sq1 = live_data[str(PE_Token)].get("sq1", "-")
                                except:
                                    PE_sq1 = "-"
                                try:
                                    PE_sp1 = live_data[str(PE_Token)].get("sp1", "-")
                                except:
                                    PE_sp1 = "-"

                                pd_oc = pd_oc.append(
                                    {
                                        "CE_token": CE_Token,
                                        "CE_oi": CE_oi,
                                        "CE_poi": CE_poi,
                                        "CE_toi": CE_toi,
                                        "CE_lp": CE_lp,
                                        "CE_pc": CE_pc,
                                        "CE_bq1": CE_bq1,
                                        "CE_bp1": CE_bp1,
                                        "CE_sq1": CE_sq1,
                                        "CE_sp1": CE_sp1,
                                        "strike": Strike,
                                        "PE_bq1": PE_bq1,
                                        "PE_bp1": PE_bp1,
                                        "PE_sq1": PE_sq1,
                                        "PE_sp1": PE_sp1,
                                        "PE_pc": PE_pc,
                                        "PE_lp": PE_lp,
                                        "PE_toi": PE_toi,
                                        "PE_poi": PE_poi,
                                        "PE_oi": PE_oi,
                                        "PE_token": PE_Token,
                                    },
                                    ignore_index=True,
                                )

                            pd_oc = pd_oc.astype({"strike": int})
                            pd_oc = pd_oc.sort_values(by="strike", ascending=True)

                            pd_oc = pd_oc.astype({"CE_oi": int})
                            pd_oc = pd_oc.astype({"PE_oi": int})

                            pd_oc["OI_SUm"] = pd_oc["CE_oi"] + pd_oc["PE_oi"]

                            # print(pd_oc)

                            df_maxPut = pd_oc[["strike", "PE_lp", "PE_oi"]][
                                pd_oc.PE_oi == pd_oc["PE_oi"].max()
                            ]

                            

                            if len(df_maxPut) == 1:
                                strike = df_maxPut.iloc[0]["strike"]
                                PE_lp = df_maxPut.iloc[0]["PE_lp"]
                                PE_oi = df_maxPut.iloc[0]["PE_oi"]

                                Additional_Detail.range("B10").value = strike
                                Additional_Detail.range("C10").value = PE_oi
                                Additional_Detail.range("D10").value = PE_lp

                            df_maxCall = pd_oc[["strike", "CE_lp", "CE_oi"]][
                                pd_oc.CE_oi == pd_oc["CE_oi"].max()
                            ]

                            if len(df_maxCall) == 1:
                                strike = df_maxCall.iloc[0]["strike"]
                                CE_lp = df_maxCall.iloc[0]["CE_lp"]
                                CE_oi = df_maxCall.iloc[0]["CE_oi"]

                                Additional_Detail.range("B11").value = strike
                                Additional_Detail.range("C11").value = CE_oi
                                Additional_Detail.range("D11").value = CE_lp

                            df_maxPain = pd_oc[
                                ["strike", "CE_lp", "PE_lp", "CE_oi", "PE_oi"]
                            ][pd_oc.OI_SUm == pd_oc["OI_SUm"].max()]

                            if len(df_maxPain) == 1:
                                strike = df_maxPain.iloc[0]["strike"]
                                CE_lp = df_maxPain.iloc[0]["CE_lp"]
                                PE_lp = df_maxPain.iloc[0]["PE_lp"]
                                CE_oi = df_maxPain.iloc[0]["CE_oi"]
                                PE_oi = df_maxPain.iloc[0]["PE_oi"]
                                # print(f"strike={strike},CE_lp={CE_lp},PE_lp={PE_lp}")

                                Additional_Detail.range("B14").value = strike
                                Additional_Detail.range("B16").value = CE_oi
                                Additional_Detail.range("B17").value = PE_oi
                                Additional_Detail.range("C16").value = CE_lp
                                Additional_Detail.range("C17").value = PE_lp

                                Nifty_LTP = api.get_quotes(
                                    "NSE", str(IndexList_token[0]["Token"])
                                ).get("lp")

                                BANKNIFTY_LTP = api.get_quotes(
                                    "NSE", str(IndexList_token[1]["Token"])
                                ).get("lp")

                                FINNIFTY_LTP = api.get_quotes(
                                    "NSE", str(IndexList_token[2]["Token"])
                                ).get("lp")

                                IndiaVix = api.get_quotes(
                                    "NSE", str(IndexList_token[3]["Token"])
                                ).get("lp")


                                Option_Chain.range("L1").value = Nifty_LTP
                                Option_Chain.range("N1").value = BANKNIFTY_LTP
                                Option_Chain.range("P1").value = FINNIFTY_LTP
                                Option_Chain.range("R1").value = IndiaVix

                                if input_symbol in IndexList:
                                    Message = "data already available in terminal"
                                else:
                                    symbol = input_symbol + "-EQ"
                                    Token = (
                                        api.searchscrip("NSE", searchtext=symbol)
                                        .get("values")[0]
                                        .get("token")
                                    )
                                    symbol_ltp = api.get_quotes("NSE", str(Token)).get(
                                        "lp"
                                    )

                                    Option_Chain.range("I1").value = symbol_ltp

                            pd_oc = pd_oc.drop(
                                ["CE_token", "PE_token", "OI_SUm"], axis=1
                            )
                            
                            Clear_optionchain()
                            Option_Chain.range("a4").options(
                                index=False, header=False
                            ).value = pd_oc

                        except Exception as e:
                            Message = (
                                "Please enter correct expiry in dd-MON-YYYY format"
                            )
                            print(Message)
                            Symbol_Selection.range("L7").value = Message
                            Clear_optionchain()
                    else:
                        Message = "Please enter correct expiry in dd-MON-YYYY format"
                        print(Message)
                        Symbol_Selection.range("L7").value = Message
                        Clear_optionchain()
                else:
                    Message = "Please enter the expiry"
                    print(Message)
                    Symbol_Selection.range("L7").value = Message
                    Clear_optionchain()
            else:
                Message = "Please enter correct symbol"
                print(Message)
                Symbol_Selection.range("L6").value = Message
                Clear_optionchain()
        else:
            Message = "Please enter the symbol"
            print(Message)
            Symbol_Selection.range("L6").value = Message
            Clear_optionchain()

        sleep(int(IterationSleep))


def StartThread():

    try:
        # Define the threads and put them in an array
        threads = [
            Thread(target=start_optionchain),
            Thread(target=start_Trade_Terminal),
        ]

        # Func1 and Func2 run in separate threads
        for thread in threads:
            thread.start()

        # Wait until both Func1 and Func2 have finished
        for thread in threads:
            thread.join()
    except Exception as e:
        Message = str(e) + " : Exception occur"
        print(Message)


if __name__ == "__main__":
    if Shoonya_login() == 1:

        LoadInstrument_token()

        api.start_websocket(
            order_update_callback=event_handler_order_update,
            subscribe_callback=event_handler_quote_update,
            socket_open_callback=open_callback,
        )

        while feed_opened == False:
            print(feed_opened)
            pass

        print("Connected to WebSocket...")

        # start_optionchain()

        # start_Trade_Terminal()
        StartThread()
        print("Enjoy the automation...")
    else:
        print("\n\nAlgo is not able to login using your given credential. Please follow below steps in matrix wise.\n\n1. Check entered userid/password/apikey/otp is correct or not. Try to login your finvasia account using same credential.\n2. If issue still exist please regenerate your password and api key and update the sheet.\n3. If you are using algo first time, please wait for 24 hours to activate your api.\n4. If issue still exist please contact to finvasia support team.")
