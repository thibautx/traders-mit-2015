__author__ = 'thibautxiong'

import numpy as np
import pandas as pd
import mibian as mb


def get_data():
    df = pd.DataFrame()

    # Index Prices
    f = open('data/idx_px.txt', 'r')
    index_prices = []
    for line in f:
        index_prices.append(float(line.rstrip()))
    f.close()
    df['underlying'] = index_prices

    # Futures Prices
    future_months = ['0', '1', '2', '3']
    future_prices = []
    for future_month in future_months:
        f = open('data/fut'+future_month+'_px.txt', 'r')
        # future_prices = []
        for line in f:
            future_prices.append(float(line.rstrip()))
        f.close()
    df['future'] = future_prices

    # Options Prices
    call_strikes = ['90', '95', '100', '105', '100']
    put_strikes = ['90', '95', '100', '105']
    for call_strike in call_strikes:
        f = open('data/opt_c_'+call_strike+'_px.txt', 'r')
        call_prices = []
        for line in f:
            call_prices.append(float(line.rstrip()))
        df[call_strike+'C'] = call_prices
        f.close()
    for put_strike in put_strikes:
        f = open('data/opt_p_'+put_strike+'_px.txt', 'r')
        put_prices = []
        for line in f:
            put_prices.append(float(line.rstrip()))
        df[put_strike+'P'] = put_prices
        f.close()

    # print df.head(5)
    df['ix'] = df.index
    return df


def connect_web_socket(local=False):
    import json
    from websocket import create_connection
    if local is False:
        ws = create_connection("ws://big.m.angocore.com/(actual username)/(actual password)")
    else:
        ws = create_connection("ws://localhost:10914/trader0/trader0")
    auth_msg = json.dumps({"message_type": "REGISTER", "token": "uiuc123"},
                          sort_keys=True, indent=4, separators=(',', ':'))

    print auth_msg
    ws.send(auth_msg)
    result = ws.recv()
    print result


def black_scholes(data, strike, type):
    call_price = data[str(strike)+type]
    underlying_price = data['underlying']
    strike_price = strike
    interest_rate = 0
    days_to_expiration = 120 - 120*(data['ix']/1800)
    c = mb.BS([underlying_price, strike_price, interest_rate, days_to_expiration],
              callPrice=call_price)
    return c.impliedVolatility*.001

if __name__ == "__main__":
    # df = get_data()

    connect_web_socket(local=True)

    # call_strikes = [90, 95, 100, 105, 100]
    # # put_strikes = ['90', '95', '100', '105']
    # for call_strike in call_strikes:
    #     vol = df.apply(lambda x: black_scholes(x, call_strike, 'C'), axis=1)
    #     df[str(call_strike)+'_vol'] = vol
    #
    # print df.head(5)