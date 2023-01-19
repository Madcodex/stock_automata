1. Below files should available in current working directory
kiteext.pyc
Zerodha_Core_V3_001.pye
Zerodha_Trade_Terminal_V3_001.pyc
Zerodha_Trade_Terminal_V3.xlsm

2. Update ur credential, trade mode (real/paper), required feature in excel sheet before starting algo.

3. To run the command

Python Zerodha_Trade_Terminal_V3_001.pyc

Note : V3_001 may change if any latest version comes like V3_002, V3_003 so use that available file name.


List of newly added features:

1. Paper trade / Real trade
2. User can enable/disable feature as per his requirement
3. Added second option chain with pro feature
	3.1 Support all segment e.g. MCX, CDS, NFO, BDS
	3.2 Integrated NSE / Sesnsibull matching greeks
4. Limit entry has been added 
	True_Market : Market order will be placed
	True_LIMIT_LTP : Limit order will place with current LTP
	Limit_Below : Limit order will be with low price in buy and higher pricer in case of selling in entry
	Limit_Above : Limit order will be with higher price in buy and lower pricer in case of selling in entry useful to trade breakout system
5. User will get telegram notification
6. Voice alert is also enabled
7. User can cancel any open order which is pending to execute.
8. User can squareoff any running position, earlier we have all squareoff feature.

Improvement:
1. System will show correct executed price, useful if broker api is slow .