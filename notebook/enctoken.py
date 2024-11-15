from kite_trade import *
from espressoApi.espressoConnect import EspressoConnect
import json 

def get_kite():
    enctoken = "m0MCz6UDDZ9fyeKsLa/xKTXFIrOd/Ywp714ZsH5xuT9OKNJzV0lDYindMx+bAV8cIj3Jj9+mtEHy8vLPPBwABqUNj6ElasUp8R6zWx9zygKSlrDvTDVZhA=="
    kite = KiteApp(enctoken=enctoken)
    return kite


def get_espersso_token():
    request_token_url = "https://api.myespresso.com/espressoapi/auth/www.test.com?request_token=9HIJWIIc4hyfN9VaLZ5mwdIVIFIeUoUcKfe-dJtkftJPNGZTaXLnW_wXb4IE_CaZ7BoKfiMhpHT3&state=12345"
    api_key = "txrMiRzR1ebw76Ns9r2KkOtsmr4TcK9M"
    """ vendor_key="Vendor Key" """
    state = 12345
    secret_key="A2MP3iTHgazspXxNpnkORm4Jho6N46Mh"

    espressoApi = EspressoConnect(api_key=api_key)
    print(espressoApi.login_url())

    request_token= request_token_url.split("request_token=")[1].split("&state")[0]

    """Use generate session method for decrypt and re-encrypt the request token value """
    session = espressoApi.generate_session(request_token,secret_key)

    """Use get_access_token for generating access token """
    access_token=espressoApi.get_access_token(api_key,session, state = '12345')
    access_token_dict = json.loads(access_token)

    access_token = access_token_dict['data']['token']
    espressoApi = EspressoConnect(api_key=api_key,access_token=access_token)
    print(espressoApi.requestHeaders()) 
    return espressoApi