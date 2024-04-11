from kite_trade import *


def get_kite():
    enctoken = "ajVhMcU6Ml6ccfgT1bfUnr/THN8Pt+GJHqJB0IjviUi0sJ9Jc96Y1FkmvaEFFwqTGINOp6CFlCaimqXH9CL7V8+OhBNvVNB/teMRnWp8UQkHwArnVB7uyQ=="
    kite = KiteApp(enctoken=enctoken)
    return kite