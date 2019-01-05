#!/usr/bin/python3
import os
import requests
import configparser


class Venmo:
    def __init__(self):
        self.session = requests.session()
        self.username = None
        self.phone_number = None
        self.name = None
        self.access_token = None
        self.balance = None
        self.id = None
        self.email = None
        self.external_id = None
        self.device_id = 'EFF75587-5CB7-432B-BB59-639820DFD2DD'

    def login(self, username, password):
        headers = {
            'Host':             'venmo.com',
            'Content-Type':     'application/json; charset=utf-8',
            'Connection':       'keep-alive',
            'device-id':        self.device_id,
            'Accept':           'application/json; charset=utf-8',
            'User-Agent':       'Venmo/7.8.1 (iPhone; iOS 10.2; Scale/2.0)',
            'Accept-Language':  'en-US;q=1.0',
            'Accept-Encoding':  'gzip;q=1.0,compress;q=0.5'
        }
        payload = {
            "client_id": "1",
            "password": password,
            "phone_email_or_username": username
        }
        # TODO handle new devices and 2fa - Venmo-Otp-Secret in response headers
        response = self.session.post('https://venmo.com/api/v5/oauth/access_token', json=payload, headers=headers)
        if response.status_code == 401:
            self.two_factor_auth(response.headers['Venmo-Otp-Secret'], response.headers['Set-Cookie'].split('csrftoken2=')[-1].split(';')[0])
        # TODO need to class variable declarations if 2fa needed - 'response'
        self.username = response.json()['username']
        self.phone_number = response.json()['phone']
        self.name = response.json()['name']
        self.access_token = response.json()['access_token']
        self.balance = response.json()['balance']
        self.id = response.json()['id']
        self.email = response.json()['email']
        # Call method to set external id
        self.get_me()

    def two_factor_auth(self, otp_secret, csrftoken):
        # TODO I'm in Canada will flesh this out when I'm back state-side
        headers = {
            'Host':              'venmo.com',
            'Accept-Encoding':   'gzip, deflate',
            'Connection':        'keep-alive',
            'device-id':         self.device_id,
            'Accept':            'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'User-Agent':        'Venmo/7.8.1 (iPhone; iOS 10.2; Scale/2.0)',
            'Accept-Language':   'en-us',
            'Referer':           'https://venmo.com/',
            'Venmo-Otp-Secret':  otp_secret,
            'Venmo-User-Agent':  'Venmo/7.8.1 (iPhone; iOS 10.2; Scale/2.0)'
        }
        # Need to go here first otherwise api call results in 400 Client error
        response = self.session.get('https://venmo.com/two-factor', headers=headers)
        response.raise_for_status()

        del headers['device-id']
        del headers['Venmo-User-Agent']
        del headers['Venmo-Otp-Secret']
        headers['Accept'] = 'application/json'
        headers['venmo-otp-secret'] = otp_secret
        response = self.session.get('https://venmo.com/api/v5/two_factor/token', headers=headers)
        response.raise_for_status()
        response.json()  # braintree stuff and security

        # send sms
        headers = {
            'Host':              'venmo.com',
            'Accept':            'application/json',
            'Accept-Language':   'en-us',
            'Accept-Encoding':   'gzip, deflate',
            'Content-Type':      'application/json',
            'Origin':            'https://venmo.com',
            'User-Agent':        'Venmo/7.8.1 (iPhone; iOS 10.2; Scale/2.0)',
            'Connection':        'keep-alive',
            'Referer':           'https://venmo.com/',
            'venmo-otp-secret':  otp_secret
        }
        payload = {
            "csrftoken2": csrftoken,  # should get from the set-cookie in the response headers
            "via": "sms"
        }
        response = self.session.post('https://venmo.com/api/v5/two_factor/token', json=payload, headers=headers)
        response.raise_for_status()  # response['data']['status'] == 'sent'

        # Require manual input for sms - integrate automation with google voice maybe if venmo short code supported?
        sms_code_received = input('SMS code received: ')
        headers['venmo-otp'] = sms_code_received
        payload = {
            "csrftoken2": csrftoken,  # should get from the set-cookie in the response headers
        }
        response = self.session.post('https://venmo.com/login', json=payload, headers=headers)
        response.raise_for_status()

    def get_account(self):
        headers = {
            'Host':             'api.venmo.com',
            'Connection':       'keep-alive',
            'device-id':        self.device_id,
            'Accept':           'application/json; charset=utf-8',
            'User-Agent':       'Venmo/7.8.1 (iPhone; iOS 10.2; Scale/2.0)',
            'Accept-Language':  'en-US;q=1.0',
            'Authorization':    f'Bearer {self.access_token}',
            'Accept-Encoding':  'gzip;q=1.0,compress;q=0.5'
        }
        response = self.session.get('https://api.venmo.com/v1/account', headers=headers)
        response.raise_for_status()
        return response.json()

    def get_alerts(self):
        headers = {
            'Host':             'api.venmo.com',
            'Connection':       'keep-alive',
            'device-id':        self.device_id,
            'Accept':           'application/json; charset=utf-8',
            'User-Agent':       'Venmo/7.8.1 (iPhone; iOS 10.2; Scale/2.0)',
            'Accept-Language':  'en-US;q=1.0',
            'Authorization':    f'Bearer {self.access_token}',
            'Accept-Encoding':  'gzip;q=1.0,compress;q=0.5'
        }
        response = self.session.get('https://api.venmo.com/v1/alerts', headers=headers)
        response.raise_for_status()
        return response.json()

    def get_me(self):
        headers = {
            'Host':             'venmo.com',
            'Connection':       'keep-alive',
            'device-id':        self.device_id,
            'Accept':           'application/json; charset=utf-8',
            'User-Agent':       'Venmo/7.8.1 (iPhone; iOS 10.2; Scale/2.0)',
            'Accept-Language':  'en-US;q=1.0',
            'Authorization':    f'Bearer {self.access_token}',
            'Accept-Encoding':  'gzip;q=1.0,compress;q=0.5'
        }
        response = self.session.get('https://venmo.com/api/v5/users/me', headers=headers)
        response.raise_for_status()
        self.external_id = response.json()['external_id']
        return response.json()

    def get_suggested(self):
        headers = {
            'Host':             'api.venmo.com',
            'Connection':       'keep-alive',
            'device-id':        self.device_id,
            'Accept':           'application/json; charset=utf-8',
            'User-Agent':       'Venmo/7.8.1 (iPhone; iOS 10.2; Scale/2.0)',
            'Accept-Language':  'en-US;q=1.0',
            'Authorization':    f'Bearer {self.access_token}',
            'Accept-Encoding':  'gzip;q=1.0,compress;q=0.5'
        }
        response = self.session.get('https://api.venmo.com/v1/suggested', headers=headers)
        response.raise_for_status()
        return response.json()

    def get_authorizations(self, limit=20):
        headers = {
            'Host':             'api.venmo.com',
            'Connection':       'keep-alive',
            'device-id':        self.device_id,
            'Accept':           'application/json; charset=utf-8',
            'User-Agent':       'Venmo/7.8.1 (iPhone; iOS 10.2; Scale/2.0)',
            'Accept-Language':  'en-US;q=1.0',
            'Authorization':    f'Bearer {self.access_token}',
            'Accept-Encoding':  'gzip;q=1.0,compress;q=0.5'
        }
        query_string_params = {
            'acknowledged': False,
            'status':       'active,captured',
            'limit':        limit
        }
        response = self.session.get('https://api.venmo.com/v1/authorizations', params=query_string_params, headers=headers)
        response.raise_for_status()
        return response.json()

    def get_stories(self):
        headers = {
            'Host':             'api.venmo.com',
            'Connection':       'keep-alive',
            'device-id':        self.device_id,
            'Accept':           'application/json; charset=utf-8',
            'User-Agent':       'Venmo/7.8.1 (iPhone; iOS 10.2; Scale/2.0)',
            'Accept-Language':  'en-US;q=1.0',
            'Authorization':    f'Bearer {self.access_token}',
            'Accept-Encoding':  'gzip;q=1.0,compress;q=0.5'
        }
        response = self.session.get('https://api.venmo.com/v1/stories/target-or-actor/friends', headers=headers)
        response.raise_for_status()
        return response.json()

    def get_merchant_views(self):
        headers = {
            'Host':             'api.venmo.com',
            'Connection':       'keep-alive',
            'device-id':        self.device_id,
            'Accept':           'application/json; charset=utf-8',
            'User-Agent':       'Venmo/7.8.1 (iPhone; iOS 10.2; Scale/2.0)',
            'Accept-Language':  'en-US;q=1.0',
            'Authorization':    f'Bearer {self.access_token}',
            'Accept-Encoding':  'gzip;q=1.0,compress;q=0.5'
        }
        response = self.session.get('https://api.venmo.com/v1/users/merchant-payments-activation-views', headers=headers)
        response.raise_for_status()
        return response.json()

    def get_hermes_whitelist(self):
        headers = {
            'Host':             'api.venmo.com',
            'Connection':       'keep-alive',
            'device-id':        self.device_id,
            'Accept':           'application/json; charset=utf-8',
            'User-Agent':       'Venmo/7.8.1 (iPhone; iOS 10.2; Scale/2.0)',
            'Accept-Language':  'en-US;q=1.0',
            'Authorization':    f'Bearer {self.access_token}',
            'Accept-Encoding':  'gzip;q=1.0,compress;q=0.5'
        }
        response = self.session.get('https://api.venmo.com/v1/hermes-whitelist', headers=headers)
        response.raise_for_status()
        return response.content

    def search_user(self, user):
        headers = {
            'Host':             'api.venmo.com',
            'Connection':       'keep-alive',
            'device-id':        self.device_id,
            'Accept':           'application/json; charset=utf-8',
            'User-Agent':       'Venmo/7.8.1 (iPhone; iOS 10.2; Scale/2.0)',
            'Accept-Language':  'en-US;q=1.0',
            'Authorization':    f'Bearer {self.access_token}',
            'Accept-Encoding':  'gzip;q=1.0,compress;q=0.5'
        }
        response = self.session.get('https://api.venmo.com/v1/users', params={'query':user}, headers=headers)
        response.raise_for_status()
        return response.json()

    def get_back_accounts(self):
        headers = {
            'Host':             'venmo.com',
            'Connection':       'keep-alive',
            'device-id':        self.device_id,
            'Accept':           'application/json; charset=utf-8',
            'User-Agent':       'Venmo/7.8.1 (iPhone; iOS 10.2; Scale/2.0)',
            'Accept-Language':  'en-US;q=1.0',
            'Authorization':    f'Bearer {self.access_token}',
            'Accept-Encoding':  'gzip;q=1.0,compress;q=0.5'
        }
        response = self.session.get('https://venmo.com/api/v5/bankaccounts', headers=headers)
        response.raise_for_status()
        return response.json()

    def get_payment_methods(self):
        headers = {
            'Host':             'api.venmo.com',
            'Connection':       'keep-alive',
            'device-id':        self.device_id,
            'Accept':           'application/json; charset=utf-8',
            'User-Agent':       'Venmo/7.8.1 (iPhone; iOS 10.2; Scale/2.0)',
            'Accept-Language':  'en-US;q=1.0',
            'Authorization':    f'Bearer {self.access_token}',
            'Accept-Encoding':  'gzip;q=1.0,compress;q=0.5'
        }
        response = self.session.get('https://api.venmo.com/v1/payment-methods', headers=headers)
        response.raise_for_status()
        return response.json()

    def get_incomplete_requests(self):
        headers = {
            'Host':             'api.venmo.com',
            'Connection':       'keep-alive',
            'device-id':        self.device_id,
            'Accept':           'application/json; charset=utf-8',
            'User-Agent':       'Venmo/7.8.1 (iPhone; iOS 10.2; Scale/2.0)',
            'Accept-Language':  'en-US;q=1.0',
            'Authorization':    f'Bearer {self.access_token}',
            'Accept-Encoding':  'gzip;q=1.0,compress;q=0.5'
        }
        query_string_params = {
            'action': 'charge',
            'actor':  self.external_id,
            'limit':  '20',
            'status': 'pending,held'
        }
        response = self.session.get('https://api.venmo.com/v1/payments', params=query_string_params, headers=headers)
        response.raise_for_status()
        return response.json()

    def get_incomplete_payments(self):
        headers = {
            'Host':             'api.venmo.com',
            'Connection':       'keep-alive',
            'device-id':        self.device_id,
            'Accept':           'application/json; charset=utf-8',
            'User-Agent':       'Venmo/7.8.1 (iPhone; iOS 10.2; Scale/2.0)',
            'Accept-Language':  'en-US;q=1.0',
            'Authorization':    f'Bearer {self.access_token}',
            'Accept-Encoding':  'gzip;q=1.0,compress;q=0.5'
        }
        query_string_params = {
            'action': 'pay',
            'actor':  self.external_id,
            'limit':  '20',
            'status': 'pending,held'
        }
        response = self.session.get('https://api.venmo.com/v1/payments', params=query_string_params, headers=headers)
        response.raise_for_status()
        return response.json()

    def change_password(self, old_password, new_password):
        headers = {
            'Host':             'api.venmo.com',
            'Connection':       'keep-alive',
            'device-id':        self.device_id,
            'Accept':           'application/json; charset=utf-8',
            'User-Agent':       'Venmo/7.8.1 (iPhone; iOS 10.2; Scale/2.0)',
            'Accept-Language':  'en-US;q=1.0',
            'Authorization':    f'Bearer {self.access_token}',
            'Accept-Encoding':  'gzip;q=1.0,compress;q=0.5'
        }
        payload = {
            "old_password": old_password,
            "password": new_password
        }
        response = self.session.put(f'https://api.venmo.com/v1/users/{self.external_id}', json=payload, headers=headers)
        response.raise_for_status()
        return response.json()

    def get_remembered_devices(self):
        headers = {
            'Host':             'api.venmo.com',
            'Connection':       'keep-alive',
            'device-id':        self.device_id,
            'Accept':           'application/json; charset=utf-8',
            'User-Agent':       'Venmo/7.8.1 (iPhone; iOS 10.2; Scale/2.0)',
            'Accept-Language':  'en-US;q=1.0',
            'Authorization':    f'Bearer {self.access_token}',
            'Accept-Encoding':  'gzip;q=1.0,compress;q=0.5'
        }
        response = self.session.get('https://venmo.com/api/v5/devices', headers=headers)
        response.raise_for_status()
        return response.json()

    def forget_device(self, device_id):
        """
        :param device_id: int - user_device_id key in response of get_remembered_devices method for a given device
        """
        headers = {
            'Host':             'venmo.com',
            'Connection':       'keep-alive',
            'device-id':        self.device_id,
            'Accept':           'application/json; charset=utf-8',
            'User-Agent':       'Venmo/7.8.1 (iPhone; iOS 10.2; Scale/2.0)',
            'Accept-Language':  'en-US;q=1.0',
            'Authorization':    f'Bearer {self.access_token}',
            'Accept-Encoding':  'gzip;q=1.0,compress;q=0.5'
        }
        response = self.session.delete(f'https://venmo.com/api/v5/devices/{device_id}', headers=headers)
        response.raise_for_status()
        return response.json()

    def change_number(self, new_number):
        """
        :params new_number: str eg. "(123) 456-7890"
        """
        # TODO I'm in Canada will flesh this out when I'm back state-side
        headers = {
            'Host':             'venmo.com',
            'Connection':       'keep-alive',
            'device-id':        self.device_id,
            'Accept':           'application/json; charset=utf-8',
            'User-Agent':       'Venmo/7.8.1 (iPhone; iOS 10.2; Scale/2.0)',
            'Accept-Language':  'en-US;q=1.0',
            'Authorization':    f'Bearer {self.access_token}',
            'Accept-Encoding':  'gzip;q=1.0,compress;q=0.5'
        }
        payload = {
            "phone": new_number
        }
        response = self.session.post('https://venmo.com/api/v5/phones', json=payload, headers=headers)
        response.raise_for_status()
        return response.json()

    def get_blocked_users(self):
        headers = {
            'Host':             'api.venmo.com',
            'Connection':       'keep-alive',
            'device-id':        self.device_id,
            'Accept':           'application/json; charset=utf-8',
            'User-Agent':       'Venmo/7.8.1 (iPhone; iOS 10.2; Scale/2.0)',
            'Accept-Language':  'en-US;q=1.0',
            'Authorization':    f'Bearer {self.access_token}',
            'Accept-Encoding':  'gzip;q=1.0,compress;q=0.5'
        }
        response = self.session.get('https://api.venmo.com/v1/blocks', headers=headers)
        response.raise_for_status()
        return response.json()

    def make_all_past_transactions_private(self):
        headers = {
            'Host':             'venmo.com',
            'Connection':       'keep-alive',
            'device-id':        self.device_id,
            'Accept':           'application/json; charset=utf-8',
            'User-Agent':       'Venmo/7.8.1 (iPhone; iOS 10.2; Scale/2.0)',
            'Accept-Language':  'en-US;q=1.0',
            'Authorization':    f'Bearer {self.access_token}',
            'Accept-Encoding':  'gzip;q=1.0,compress;q=0.5'
        }
        payload = {
            "audience": "private"
        }
        response = self.session.post('https://venmo.com/api/v5/stories/each', json=payload, headers=headers)
        response.raise_for_status()
        return response.json()

    def make_all_past_transactions_viewable_by_friends(self):
        headers = {
            'Host':             'venmo.com',
            'Connection':       'keep-alive',
            'device-id':        self.device_id,
            'Accept':           'application/json; charset=utf-8',
            'User-Agent':       'Venmo/7.8.1 (iPhone; iOS 10.2; Scale/2.0)',
            'Accept-Language':  'en-US;q=1.0',
            'Authorization':    f'Bearer {self.access_token}',
            'Accept-Encoding':  'gzip;q=1.0,compress;q=0.5'
        }
        payload = {
            "audience": "friends"
        }
        response = self.session.post('https://venmo.com/api/v5/stories/each', json=payload, headers=headers)
        response.raise_for_status()
        return response.json()

    def edit_profile(self, first_name=None, last_name=None, username=None, email=None):
        # TODO fetch currents so that we only pass through new/updated param to the payload
        headers = {
            'Host':             'venmo.com',
            'Connection':       'keep-alive',
            'device-id':        self.device_id,
            'Accept':           'application/json; charset=utf-8',
            'User-Agent':       'Venmo/7.8.1 (iPhone; iOS 10.2; Scale/2.0)',
            'Accept-Language':  'en-US;q=1.0',
            'Authorization':    f'Bearer {self.access_token}',
            'Accept-Encoding':  'gzip;q=1.0,compress;q=0.5'
        }
        payload = {
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
            "username": username
        }
        response = self.session.put('https://venmo.com/api/v5/users/me', json=payload, headers=headers)
        response.raise_for_status()
        return response.json()

    def get_friends(self, limit=1337):
        headers = {
            'Host':             'api.venmo.com',
            'Connection':       'keep-alive',
            'device-id':        self.device_id,
            'Accept':           'application/json; charset=utf-8',
            'User-Agent':       'Venmo/7.8.1 (iPhone; iOS 10.2; Scale/2.0)',
            'Accept-Language':  'en-US;q=1.0',
            'Authorization':    f'Bearer {self.access_token}',
            'Accept-Encoding':  'gzip;q=1.0,compress;q=0.5'
        }
        response = self.session.get(f'https://api.venmo.com/v1/users/{self.external_id}/friends', params={'limit':limit}, headers=headers)
        response.raise_for_status()
        return response.json()

    def sign_out(self):
        headers = {
            'Host':             'venmo.com',
            'Connection':       'keep-alive',
            'device-id':        self.device_id,
            'Accept':           'application/json; charset=utf-8',
            'User-Agent':       'Venmo/7.8.1 (iPhone; iOS 10.2; Scale/2.0)',
            'Accept-Language':  'en-US;q=1.0',
            'Authorization':    f'Bearer {self.access_token}',
            'Accept-Encoding':  'gzip;q=1.0,compress;q=0.5'
        }
        response = self.session.delete('https://venmo.com/api/v5/oauth/access_token', headers=headers)
        response.raise_for_status()
        return response.json()


root_directory = os.getcwd()
cfg = configparser.ConfigParser()
configFilePath = os.path.join(root_directory, 'config.cfg')
cfg.read(configFilePath)

venmo = Venmo()
venmo.login(cfg.get('login', 'username'), cfg.get('login', 'password'))
print(venmo.get_friends())
