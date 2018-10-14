import json
from tweepy import API, OAuthHandler, Cursor

def create_twitter_client():
    consumer_key = 'sOQmiBbFHCDCEWBPnA0kHhD2C'
    consumer_secret ='6WYPnPgcCnuXbws4b8RiC3Qp6TRg0omOA3JiWJz0kvmnvMcbYx'
    access_token ='864707595243671552-BvpllHZJkpb2qMFTOtsBybASzLiQnxp'
    access_secret =   'KXtpDbTzsfCZWAb1jKifdpOS2sdq1AKLKtOBYaX6ZFGD2'

    auth = OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_secret)

    client = API(auth, wait_on_rate_limit=True)
    

    return client