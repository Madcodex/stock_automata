import json 


def load_config():
    with open('config.json', 'r') as file:
        return json.load(file)
    

def variable_assign():
    config = load_config()
    
    # Access the variables from the config
    strike_price_ce = config["strike_price"]["ce"]
    strike_price_pe = config["strike_price"]["pe"]
    symbol_ce = f"NFO:NIFTY24FEB{strike_price_ce}CE"
    symbol_pe = f"NFO:NIFTY24FEB{strike_price_pe}PE"

    support_ce = config["support"]["ce"]
    support_pe = config["support"]["pe"]
    resistance_ce = config["resistance"]["ce"]
    resistance_pe = config["resistance"]["pe"]


    call_side = config["side"]["call"]
    put_side = config["side"]["put"]
    breakout = config["breakout"]


    range_ce = config["range"]["ce"]
    range_pe = config["range"]["pe"]
    stop_loss_ce = config["stop_loss"]["ce"]
    stop_loss_pe = config["stop_loss"]["pe"]
    breakout_target = config["breakout_target"]
    breakout_stop_loss = config["stop_loss"]["breakout"]
    return  (strike_price_ce, strike_price_pe, symbol_ce, symbol_pe, support_ce, support_pe, resistance_ce, 
         resistance_pe, call_side, put_side, breakout, range_ce, range_pe, stop_loss_ce, stop_loss_pe, breakout_target, breakout_stop_loss,
             )
    


def buy_sell_order(kite,strike_price = None,ce_pe = None, price = None, trans_type = None,order_type = "MARKET",quantity = 50):
    print(strike_price, ce_pe, price,trans_type, order_type)
    order = kite.place_order(
        variety = kite.VARIETY_REGULAR,
        exchange = kite.EXCHANGE_NFO,
        tradingsymbol = f"NIFTY24FEB{strike_price}{ce_pe}",
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
        tag="TradeviaPython",
    )
    return order



# Assuming 'kite' object is already defined and has necessary methods to fetch option prices
# strike_price_ce = 22300
# strike_price_pe = 22300
# symbol_ce = f"NFO:NIFTY24FEB{strike_price_ce}CE"
# symbol_pe = f"NFO:NIFTY24FEB{strike_price_pe}PE"

# support_ce = 135
# resistance_ce = 150
# support_pe = 153
# resistance_pe = 172

# position_call  = 0 
# position_put = 0 
# call_side = True
# put_side= False
# breakout = False
# position_put_breakout = 0
# position_call_breakout = 0

# sl_ce_hit = 0
# sl_pe_hit = 0
# range_ce = .01
# range_pe = .01
# stop_loss_ce = .05
# stop_loss_pe = .05
# breakout_target = .5
# breakout_stop_loss = .10