from flask import Flask, request
from FireblocksAPI import FireblocksRequestHandler, TransferPeerPath, DestinationTransferPeerPath
import time
import configparser
import sys

app = Flask(__name__)
request_handler = FireblocksRequestHandler()
threshold = 0.1

try:
    config = configparser.ConfigParser()
    config.read_file(open("config.cfg", "r"))
    epenses_id = config["Fireblocks"]["expenses_id"]
    treasury_id = config["Fireblocks"]["treasury_id"]
except FileNotFoundError:
    # Terminate the script if no config files are found
    print("CONFIG FILE(s) NOT FOUND. TERMINATING.")
    sys.exit()


@app.route('/initiate_trasnactions', methods=["POST"])
def initiate_trasnactions():
    balance_res = request_handler.get_wallet_balance(epenses_id, 'ETH_TEST5')
    balance = balance_res['total']
    print(f'balance is: {balance}')

    if float(balance) > threshold:
        print("transaction")
        request_handler.create_transaction('ETH_TEST5', '0.1', source=TransferPeerPath('VAULT_ACCOUNT', epenses_id),
                                                                destination=DestinationTransferPeerPath('VAULT_ACCOUNT',treasury_id))
    else:
        request_handler.create_transaction('ETH_TEST5', '0.1', source=TransferPeerPath('VAULT_ACCOUNT', treasury_id),
                                                                destination=DestinationTransferPeerPath('VAULT_ACCOUNT',epenses_id))
    return 'success', 200


@app.route('/', methods=["POST"])
def webook():
    req = request.json
    print(req)
    if req['notificationSubject'] == 'Transaction Signed':
        initiate_trasnactions()
    return 'success', 200


if __name__ == '__main__':
    app.run()
