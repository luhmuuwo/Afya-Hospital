import requests
import json
from requests.auth import HTTPBasicAuth
from datetime import datetime
import base64


class MpesaC2bCredential:
    consumer_key ='rx0PsL2fcf9q8R73UUrTCPB8AjQW9oOc8xUFD6jv4PreRkb4'
    consumer_secret = 'w2a4t4m283Uda7ExOsGbAV7LWfi6e6pR80xGAPEfroQDGzrRJjuXvIqnhfNGIxNA'
    api_URL = 'https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'


class MpesaAccessToken:
    @staticmethod
    def fetch():
        response = requests.get(
            MpesaC2bCredential.api_URL,
            auth=HTTPBasicAuth(MpesaC2bCredential.consumer_key, MpesaC2bCredential.consumer_secret),
        )
        response.raise_for_status()
        token_data = response.json()
        return token_data.get('access_token')


class LipanaMpesaPpassword:
    lipa_time = datetime.now().strftime('%Y%m%d%H%M%S')
    business_short_code = "174379"
    OffSetValue = '0'
    passkey = 'bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919'

    data_to_encode = business_short_code + passkey + lipa_time

    online_password = base64.b64encode(data_to_encode.encode())
    decode_password = online_password.decode('utf-8')
