from kite_trade import *


def get_kite():
    enctoken = "Dn2G5L1rxu05kpYF0S2A4dkospF+NVa8kVpbHBwR9/ds0JLvlw8z9G/oU8O0PHc62aYW+4E5CzRvtLFwegZ1bhf1XUOu/R9BBaEhmuZm7feUt2UQrSmweA=="
    kite = KiteApp(enctoken=enctoken)
    return kite