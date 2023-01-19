# -*- coding: utf-8 -*-
"""
Created on Fri Oct 21 09:13:23 2022

Here i coded how to trade in zerodha broker using excel, all the trading data (o,h,l,c,..) will stream in excel.

Contact details :
Telegram Channel:  https://t.me/pythontrader
Developer Telegram ID : https://t.me/pythontrader_admin
Gmail ID:   mnkumar2020@gmail.com 
Whatsapp : 9470669031 

Disclaimer: The information provided by the Python Traders channel is for educational purposes only, so please contact your financial adviser before placing your trade. Developer is not responsible for any profit/loss happened due to coding, logical or any type of error.
"""

from kiteext import KiteExt
import os, time, json, sys
import xlwings as xw
import pandas as pd
from datetime import datetime
from time import sleep
import logging
import pyotp

excel_name = xw.Book('Zerodha_Trade_Terminal.xlsx')

#logging.basicConfig(level=logging.DEBUG)

def Zerodha_login():
    global kite
    isConnected = 0
    try:
        kite = KiteExt()
        
        Credential_sheet = excel_name.sheets['User_Credential']

        UserID = Credential_sheet.range('B2').value.strip()
        Password = Credential_sheet.range('B3').value.strip()
        Totp = str(Credential_sheet.range('B4').value)
        pin = pyotp.TOTP(Totp).now()
        twoFA = f"{int(pin):06d}" if len(pin) <=5 else pin    
        
        print(f"UserID={UserID},Password={Password},Totp={Totp},twoFA={twoFA}")
        
        kite.login_with_credentials(userid=UserID, password=Password, twofa=twoFA)

        Profile = kite.profile()
        print(Profile)
        
        client_name = Profile.get('user_name')
        
        Credential_sheet.range('c2').value = 'Login Successful, Welcome ' + client_name
        isConnected = 1
        
    except Exception as e:
        print(f"Error : {e}")
        Credential_sheet.range('c2').value = 'Wrong credential'

    return isConnected
    
SYMBOLDICT = {}
live_data = {}
Token_yet_to_subscribe = []
 
def on_ticks(ws, ticks):
    # Callback to receive ticks.
    global Token_yet_to_subscribe, live_data
    #print("Ticks data: {}".format(ticks))
    
    for stock in ticks:
        #print(f"inside tick for loop : {stock}")
        try:
            volume = stock["volume_traded"]
        except:
            volume = 0
        try:
            Vwap = stock["average_traded_price"]
        except:
            Vwap = 0
        try:
            bp1 = stock["depth"]["buy"][0]["price"]
        except:
            bp1 = 0
        try:
            sp1 = stock["depth"]["sell"][0]["price"]
        except:
            sp1 = 0        
        live_data[stock['instrument_token']] = {"Open": stock["ohlc"]["open"],
                                                                      "High": stock["ohlc"]["high"],
                                                                      "Low": stock["ohlc"]["low"],
                                                                      "Close": stock["ohlc"]["close"],
                                                                      "LTP": stock["last_price"],
                                                                      "Volume": volume,
                                                                      "Vwap": Vwap,
                                                                      "change" : stock["change"],
                                                                      "bp1":bp1,
                                                                      "sp1":sp1}
        #print(f"after appending live data became : {live_data}")
    if(len(Token_yet_to_subscribe) > 0):
        try:
            #print(f"New symbol found, so going to subscribe, token= {Token_yet_to_subscribe}")
            kws.subscribe(Token_yet_to_subscribe)
            kws.set_mode(ws.MODE_FULL, Token_yet_to_subscribe)
            Token_yet_to_subscribe = []
        except Exception as e:
            print(str(e)+":Exception in on_ticks")
            
def on_connect(ws, response):
    # Callback on successful connect.
    #mode available MODE_FULL,MODE_LTP,MODE_QUOTE
    TokenList = [256265] #subscribe Nifty 50
    ws.subscribe(TokenList)
    ws.set_mode(ws.MODE_FULL, TokenList)

def on_error(ws, code, reason):
    logging.error('Ticker errored out. code = %d, reason = %s', code, reason)

def on_close(ws, code, reason):
    # On connection close stop the event loop.
    # Reconnection will not happen after executing `ws.stop()`
    ws.stop()

def on_order_update(ws, data):
    logging.info('Ticker: order update %s', data)

def stop_ticker():
    logging.info('Ticker: stopping..')
    kws.close(1000, "Manual close")

def on_max_reconnect_attempts(ws):
    logging.error('Ticker max auto reconnects attempted and giving up..')

def GetToken(exchange,tradingsymbol):
    global ins_df
    
    Token = ins_df[(ins_df.tradingsymbol == tradingsymbol) & (ins_df.exchange == exchange)].iloc[0]['instrument_token']
    
    return Token

def order_status (orderid):
    print(f"I am at order_status function with order id {orderid}")
    filled_quantity = 0
    AverageExecutedPrice = 0
    global kite
    try:
        order_history = kite.order_history(orderid)
        filled_quantity = order_history[-1].get('filled_quantity')
        AverageExecutedPrice = order_history[-1].get('average_price')
    except Exception as e:
        Message = str(e) + " : Exception occur in order_status"
        print(Message)
    return filled_quantity, AverageExecutedPrice
    
def place_trade(tradingsymbol_exchange,quantity,transaction_type ):
    
    print(f"place_trade called with parameter {tradingsymbol_exchange} {quantity} {transaction_type}")
    global kite
    
    try:
        exchange = tradingsymbol_exchange[:3]
        tradingsymbol = tradingsymbol_exchange[4:]
              
        if(exchange in ['NSE','BSE']):
            product = kite.PRODUCT_CNC
        else:
            product = kite.PRODUCT_NRML
                
        variety =  kite.VARIETY_REGULAR
        order_type = 'MARKET'
        
        price = 0
        
        AverageExecutedPrice =0
        
        
        order_id = kite.place_order(tradingsymbol = tradingsymbol,
                                exchange = exchange,
                                transaction_type = transaction_type,
                                quantity = int(quantity),
                                price = price,
                                variety = variety,
                                order_type = order_type,
                                product = product)
        print(f"Order id = {order_id}")
        filled_quantity, AverageExecutedPrice = order_status (order_id)
       
    except Exception as e:
        Message = str(e) + " : Exception occur in order_place. "
        print(Message)
    return AverageExecutedPrice


 
def start_excel():
    global live_data , kws
    global SYMBOLDICT
    global Token_yet_to_subscribe
    tt = excel_name.sheets("Trade_Terminal")
    ob = excel_name.sheets("OrderBook")
    op = excel_name.sheets("OpenPosition")
    ob.range("a:az").value = op.range("a:az").value = tt.range("n:t").value = None
    tt.range(f"a1:t1").value = [ "Symbol", "Open", "High", "Low", "Close", "VWAP", "Best Buy Price",
                                "Best Sell Price","Volume", "LTP","Percentage change", "Qty", "Direction", "Entry Signal", "Exit Signal", "Entry Price",
                                "Exit Price", "Target","SL" ,"Trade Status"]
                

    subs_lst = []
    Symbol_Token = {}

    while True:
        try:
            time.sleep(.5)
            
            #print(live_data)
            symbols = tt.range(f"a{2}:a{1000}").value
            trading_info = tt.range(f"l{2}:t{1000}").value
            main_list = []
            
            idx = 0
            for i in symbols:
                lst = [None, None, None, None,None, None, None, None, None,None]
                if i:
                    if i not in subs_lst:
                        subs_lst.append(i)
                        try:
                            exchange = i[:3]
                            tradingsymbol = i[4:]
                            Token = GetToken(exchange,tradingsymbol)
                            Symbol_Token[i] =  int(Token)
                            Token_yet_to_subscribe.append(int(Token))
                            print(f"Symbol = {i}, Token={Token} subscribed")
                            
                        except Exception as e:
                            print(f"Subscribe error {i} : {e}")
                    if i in subs_lst:
                        try:
                            TokenKey = Symbol_Token[i]
                            
                            lst = [live_data[TokenKey].get("Open", "-"),
                                   live_data[TokenKey].get("High", "-"),
                                   live_data[TokenKey].get("Low", "-"),
                                   live_data[TokenKey].get("Close", "-"),
                                   live_data[TokenKey].get("Vwap", "-"),
                                   live_data[TokenKey].get("bp1", "-"),
                                   live_data[TokenKey].get("sp1", "-"),
                                   live_data[TokenKey].get("Volume", "-"),
                                   live_data[TokenKey].get("LTP", "-"),
                                   live_data[TokenKey].get("change", "-")]
                            trade_info = trading_info[idx]
                            #print(trade_info)
                            if trade_info[0] is not None and trade_info[1] is not None:
                                if type(trade_info[0]) is float and type(trade_info[1]) is str:
                                    if trade_info[1].upper() == "BUY" and trade_info[2] is True:
                                        
                                        #0:Qty    1:Direction    2:Entry_Signal    3:Exit Signal 4:Entry_Price    5:Exit_Price    6:Target    7:SL    8:Trade_status

                                        if trade_info[2] is True and trade_info[3] is not True and trade_info[4] is None and trade_info[5] is None and trade_info[8] is None:
                                    
                                            tt.range(f"p{idx + 2}").value = place_trade(i, int(trade_info[0]), "BUY")
                                            tt.range(f"t{idx + 2}").value = 'Active'
                                        
                                        elif trade_info[2] is True and  trade_info[4] is not None and trade_info[5] is None and trade_info[8] == 'Active':
                                            LTP = live_data[TokenKey].get("LTP", 0)
                                            if trade_info[3] is True:
                                                tt.range(f"q{idx + 2}").value = place_trade(i, int(trade_info[0]), "SELL")
                                                tt.range(f"t{idx + 2}").value = 'Closed'
                                            
                                            elif type(trade_info[6]) is float and trade_info[6] <= LTP and LTP != 0 and trade_info[8] == 'Active':
                                                tt.range(f"q{idx + 2}").value = place_trade(i, int(trade_info[0]), "SELL")
                                                tt.range(f"t{idx + 2}").value = 'Closed'
                                            
                                            elif type(trade_info[7]) is float and trade_info[7] >= LTP and LTP != 0:
                                                tt.range(f"q{idx + 2}").value = place_trade(i, int(trade_info[0]), "SELL")
                                                tt.range(f"t{idx + 2}").value = 'Closed'
                                                
                                    if trade_info[1].upper() == "SELL" and trade_info[2] is True:
                                    
                                    #0:Qty    1:Direction    2:Entry_Signal    3:Exit Signal 4:Entry_Price    5:Exit_Price    6:Target    7:SL    8:Trade_status

                                        if trade_info[2] is True and trade_info[3] is not True and trade_info[4] is None and trade_info[5] is None and trade_info[8] is None:
                                            tt.range(f"p{idx + 2}").value = place_trade(i, int(trade_info[0]), "SELL")
                                            tt.range(f"t{idx + 2}").value = 'Active'
                                        
                                        elif trade_info[2] is True and  trade_info[4] is not None and trade_info[5] is None and trade_info[8] == 'Active':
                                            LTP = live_data[TokenKey].get("LTP", 0)
                                            
                                            if trade_info[3] is True:
                                            
                                                tt.range(f"q{idx + 2}").value = place_trade(i, int(trade_info[0]), "BUY")
                                                tt.range(f"t{idx + 2}").value = "Closed"
                                                
                                            elif type(trade_info[6]) is float and trade_info[6] >= LTP and LTP != 0 and trade_info[8] == 'Active':
                                                tt.range(f"q{idx + 2}").value = place_trade(i, int(trade_info[0]), "BUY")
                                                tt.range(f"t{idx + 2}").value = 'Closed'
                                            
                                            elif type(trade_info[7]) is float and trade_info[7] <= LTP and LTP != 0:
                                                tt.range(f"q{idx + 2}").value = place_trade(i, int(trade_info[0]), "BUY")
                                                tt.range(f"t{idx + 2}").value = 'Closed'
                        except Exception as e:
                            #print('Exception occur in trade terminal:' + str(e))
                            pass
                main_list.append(lst)
                
                idx += 1

            tt.range("b2:k1000").value = main_list
            if excel_name.sheets.active.name == "OrderBook":
                ob.range("a:az").value = None
                ob.range("a1").value = get_order_book()
            elif excel_name.sheets.active.name == "OpenPosition":
                op.range("a:az").value = None
                op.range("a1").value = get_position()
                
        except Exception as e:
            print('Exception occur in while :' + str(e))
            pass

def get_position():
    #print(f"I am inside get_position")
    global kite
    position = kite.positions()
    df_position_net = pd.DataFrame(position['net'])
    return df_position_net
    
def get_order_book():
    #print(f"I am inside get_order_book")
    global kite
    order_book = pd.DataFrame()
    order_book = kite.orders()
    if(len(order_book) > 0):
        order_book = pd.DataFrame(order_book)
        order_book = order_book.drop(['meta'], axis=1)
    return order_book
    
def Zerodha_Token():
    global kite, ins_df
    print("Zerodha intrument token download started, may take upto 2-3 minutes ..")
    instruments = kite.instruments()
    ins_df = pd.DataFrame(instruments, index=None)
    
    ins = excel_name.sheets("Instrument")
    ins.range("a1:az100000").value = None
    
    ins.range("a1").value = ins_df
    print("Zerodha intrument token download completed")
    
if __name__ == '__main__':
    if(Zerodha_login() == 1 ):   
        try:
            Zerodha_Token()
            
            kws = kite.kws()

            # Assign the callbacks.
            kws.on_ticks = on_ticks
            kws.on_order_update = on_order_update
            kws.on_connect = on_connect
            #kws.on_close = on_close

            kws.connect(threaded=True)
        
            start_excel()
            
        except Exception as e:
            print("Exception : " + str(e))
    else:
        print("Credential is not correct")