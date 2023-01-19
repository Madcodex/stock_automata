import sys, os

try:
    Version = sys.version[:4]
except Exception as e:
    print(f"{e}")
    pass
    
if Version != "3.11":
    Message = "This trade tool will work with python latest version 3.11 only, so please upgrade python from installed version " + str(Version) + "to python 3.11"
    print(Message)
    sys.exit()
    
try:
    from kiteconnect import KiteConnect, KiteTicker
except (ModuleNotFoundError, ImportError):
    print("KiteConnect module not found")
    os.system(f"{sys.executable} -m pip install -U kiteconnect")
    print(f"Please follow the steps as mentioned in video for microsoft c++ build tool error : https://www.youtube.com/watch?v=EV8quw1-cJA")
finally:
    from kiteconnect import KiteConnect, KiteTicker 
    
try:
    import numpy as np 
except (ModuleNotFoundError, ImportError):
    print("numpy module not found")
    os.system(f"{sys.executable} -m pip install -U numpy")
finally:
    import numpy as np 
    
try:
    import requests
except (ModuleNotFoundError, ImportError):
    print("requests module not found")
    os.system(f"{sys.executable} -m pip install -U requests")
finally:
    import requests

try:
    import pyotp
except (ModuleNotFoundError, ImportError):
    print("pyotp module not found")
    os.system(f"{sys.executable} -m pip install -U pyotp")
finally:
    import pyotp
    
try:
    import xlwings as xw
except (ModuleNotFoundError, ImportError):
    print("xlwings module not found")
    os.system(f"{sys.executable} -m pip install -U xlwings")
finally:
    import xlwings as xw

try:
    import pyttsx3
except (ModuleNotFoundError, ImportError):
    #print("pyttsx3 module not found")
    os.system(f"{sys.executable} -m pip install -U pyttsx3")
finally:
    import pyttsx3
    
try:
    import pandas as pd
except (ModuleNotFoundError, ImportError):
    print("pandas module not found")
    os.system(f"{sys.executable} -m pip install -U pandas")
finally:
    import pandas as pd
    
try:
    from py_vollib.black_scholes.implied_volatility import implied_volatility 
    from py_vollib.black_scholes.greeks.analytical import delta, gamma, rho, theta, vega
except (ModuleNotFoundError, ImportError):
    print("py_vollib module not found")
    os.system(f"{sys.executable} -m pip install -U py_vollib")
finally:
    from py_vollib.black_scholes.implied_volatility import implied_volatility 
    from py_vollib.black_scholes.greeks.analytical import delta, gamma, rho, theta, vega

try:
    import sourcedefender
except (ModuleNotFoundError, ImportError):
    print("sourcedefender module not found")
    os.system(f"{sys.executable} -m pip install -U sourcedefender")
finally:
    import sourcedefender

try:    
    import Zerodha_Core_V3_001
except (ModuleNotFoundError, ImportError):
    print("Zerodha_Core_V3_001.pye file not found/corrupted, please download the latest file from tinyurl.com/pythontrader")
