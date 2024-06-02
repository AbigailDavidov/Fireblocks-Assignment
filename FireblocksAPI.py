import json
import math
import secrets
import time
import urllib.parse
from hashlib import sha256
import configparser
import sys

import jwt
import requests

class TransferPeerPath:
    def __init__(self, peer_type, peer_id):
        """Defines a source or a destination for a transfer

        Args:
            peer_type (str): either VAULT_ACCOUNT, EXCHANGE_ACCOUNT, INTERNAL_WALLET, EXTERNAL_WALLET, FIAT_ACCOUNT, NETWORK_CONNECTION, ONE_TIME_ADDRESS or UNKNOWN_PEER
            peer_id (str): the account/wallet id
        """
        if peer_type not in PEER_TYPES:
            raise Exception("Got invalid transfer peer type: " + peer_type)

        self.type = peer_type
        if peer_id:
            self.id = str(peer_id)


class DestinationTransferPeerPath(TransferPeerPath):
    def __init__(self, peer_type, peer_id=None, one_time_address=None):
        """Defines a destination for a transfer

        Args:
            peer_type (str): either VAULT_ACCOUNT, EXCHANGE_ACCOUNT, INTERNAL_WALLET, EXTERNAL_WALLET, FIAT_ACCOUNT, NETWORK_CONNECTION, ONE_TIME_ADDRESS or UNKNOWN_PEER
            peer_id (str): the account/wallet id
            one_time_address (JSON object): The destination address (and tag) for a non whitelisted address.
        """
        TransferPeerPath.__init__(self, peer_type, peer_id)

        if one_time_address:
            self.oneTimeAddress = one_time_address

class TransactionDestination:
    def __init__(self, amount, destination):
        """Defines destinations for multiple outputs transaction

        Args:
          amount (double): The amount to transfer
          destination (DestinationTransferPeerPath): The transfer destination
        """

        self.amount = str(amount)
        self.destination = destination.__dict__

TRANSACTION_TYPES = (
    'TRANSFER',
    'MINT',
    'BURN',
    'SUPPLY_TO_COMPOUND',
    'REDEEM_FROM_COMPOUND',
    'RAW',
    'CONTRACT_CALL',
    'ONE_TIME_ADDRESS',
    'TYPED_MESSAGE'
)

PEER_TYPES = (
    'VAULT_ACCOUNT', 'EXCHANGE_ACCOUNT', 'INTERNAL_WALLET', 'EXTERNAL_WALLET', 'UNKNOWN_PEER', 'FIAT_ACCOUNT', 'NETWORK_CONNECTION',
    'COMPOUND', 'ONE_TIME_ADDRESS')

class FireblocksRequestHandler(object):
    def __init__(self):
        self.base_url = 'https://api.fireblocks.io'
        try:
            config = configparser.ConfigParser()
            config.read_file(open("config.cfg", "r"))
            self.api_key = config["Fireblocks"]["api_key"]
            self.private_key = open('fireblocks_secret.key', 'r').read()
        except FileNotFoundError:
            # Terminate the script if no config files are found
            print("CONFIG FILE(s) NOT FOUND. TERMINATING.")
            sys.exit()

    def _sign_jwt(self, path, body_json=""):

        timestamp = time.time()
        nonce = secrets.randbits(63)
        timestamp_secs = math.floor(timestamp)
        path = path.replace("[", "%5B")
        path = path.replace("]", "%5D")
        token = {
            "uri": path,
            "nonce": nonce,
            "iat": timestamp_secs,
            "exp": timestamp_secs + 55,
            "sub": self.api_key,
            "bodyHash": sha256(json.dumps(body_json).encode("utf-8")).hexdigest()
        }
        return jwt.encode(token, key=self.private_key, algorithm="RS256")

    def get_request(self, path):
        token = self._sign_jwt(path)
        headers = {
            "X-API-Key": self.api_key,
            "Authorization": f"Bearer {token}"
        }
        try:
            res = requests.get(urllib.parse.urljoin(self.base_url, path), headers=headers)
        except ValueError:
            res.raise_for_status()
            raise
        return res

    def post_request(self, path, body_json={}):
        token = self._sign_jwt(path, body_json)
        headers = {
            "X-API-Key": self.api_key,
            "Authorization": f"Bearer {token}"
        }
        # response = requests.post(urllib.parse.urljoin(self.base_url, path), json=body_json, headers=headers)
        # return response
        try:
           response = requests.post(urllib.parse.urljoin(self.base_url, path), json=body_json, headers=headers)
        except ValueError:
            response.raise_for_status()
            raise
        return response
# ------------------------------------------------------------------------------------------------------------

    def get_accounts(self):
        return self.get_request('/v1/vault/accounts_paged').json()

    def get_wallet_balance(self, vault_account_id, asset_id):
        return self.get_request(f'/v1/vault/accounts/{vault_account_id}/{asset_id}').json()

    def create_transaction(
            self,
            asset_id=None,
            amount=None,
            source=None,
            destination=None,
            fee=None,
            gas_price=None,
            wait_for_status=True,
            tx_type='TRANSFER',
            note=None,
            network_fee=None,
            customer_ref_id=None,
            replace_tx_by_hash=None,
            extra_parameters=None,
            destinations=None,
            fail_on_low_fee=None,
            max_fee=None,
            gas_limit=None,
            external_tx_id=None,
            treat_as_gross_amount=None,
            force_sweep=None,
            priority_fee=None,
    ):

        if tx_type not in TRANSACTION_TYPES:
            raise Exception("Got invalid transaction type: " + tx_type)

        if source:
            if not isinstance(source, TransferPeerPath):
                raise Exception(
                    "Expected transaction source of type TransferPeerPath, but got type: "
                    + type(source)
                )

        body = {
            "waitForStatus": wait_for_status,
            "operation": tx_type,
        }

        if asset_id:
            body["assetId"] = asset_id

        if source:
            body["source"] = source.__dict__

        if amount is not None:
            body["amount"] = amount

        if fee:
            body["fee"] = fee

        if max_fee:
            body["maxFee"] = max_fee

        if fail_on_low_fee:
            body["failOnLowFee"] = fail_on_low_fee

        if gas_price:
            body["gasPrice"] = str(gas_price)

        if gas_limit:
            body["gasLimit"] = str(gas_limit)

        if note:
            body["note"] = note

        if destination:
            if not isinstance(
                    destination, (TransferPeerPath, DestinationTransferPeerPath)
            ):
                raise Exception(
                    "Expected transaction destination of type DestinationTransferPeerPath or TransferPeerPath, but got type: "
                    + type(destination)
                )
            body["destination"] = destination.__dict__

        if network_fee:
            body["networkFee"] = network_fee

        if customer_ref_id:
            body["customerRefId"] = customer_ref_id

        if replace_tx_by_hash:
            body["replaceTxByHash"] = replace_tx_by_hash

        if treat_as_gross_amount:
            body["treatAsGrossAmount"] = treat_as_gross_amount

        if destinations:
            if any([not isinstance(x, TransactionDestination) for x in destinations]):
                raise Exception(
                    "Expected destinations of type TransactionDestination"
                )

            body["destinations"] = [dest.__dict__ for dest in destinations]

        if extra_parameters:
            body["extraParameters"] = extra_parameters

        if external_tx_id:
            body["externalTxId"] = external_tx_id

        if force_sweep:
            body["forceSweep"] = force_sweep

        if priority_fee:
            body["priorityFee"] = priority_fee

        try:
            res = self.post_request("/v1/transactions", body).json()
        except Exception:
            res = "not enough money in the wallet, couldn't procced"
        return res

