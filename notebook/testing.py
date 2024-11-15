import kiteapp as kt
import pandas as pd
from time import sleep
with open('enctoken.txt', 'r') as rd:
	token = rd.read()
kite = kt.KiteApp("kite", "FC9764", token)
kws = kite.kws()  # For Websocket


'''
# Place Order
oid = kite.place_order(variety="amo", exchange='NSE',
		tradingsymbol='SBIN', transaction_type='BUY',
		quantity=5, product='MIS', order_type="LIMIT",
		price=820, validity="DAY")


print(oid)
order = kite.orders()

print(order)
'''

holding = kite.holdings()

print(holding)
