import os
import shutil
from bitcoinlib.keys import HDKey
from bitcoinlib.mnemonic import Mnemonic
from bitcoinlib.services.services import *
from bitcoinlib.wallets import Wallet
from bitcoin.core.script import CScript, OP_RETURN
from bitcoinlib.transactions import Output
from bitcoinlib.wallets import Value
import requests
import json
from PIL import Image
import qrcode
import pickle
import threading

json_file_path = "data/wallets.json"
json_keys_file_path ="data/keys.json"

def wallet_info(wallet_name):
    w = Wallet(wallet_name)
    # Define tasks for threading

    w.balance_update_from_serviceprovider()

    w.utxos_update()

    w.transactions_update()

    accounts = w.accounts(network=w.name)
    if not accounts:
        accounts = [0]

    transactions_data = []  # List to hold transaction data for returning
    multisig_data = []  # List to hold multisig data for returning

    # Multisig data
    if w.multisig:
        print("\n= Multisig Public Master Keys =")
        if isinstance(w.cosigner, list):
            for cs in w.cosigner:
                is_primary = "*" if cs.cosigner_id == w.cosigner_id else ""
                role = "main" if cs.main_key.is_private else "cosigner"
                multisig_data.append({
                    "key_id": cs.main_key.key_id,
                    "wif": cs.wif(is_private=False),
                    "scheme": cs.scheme,
                    "role": role,
                    "is_primary": is_primary
                })
        else:
            print("Error: w.cosigner is not iterable.")
            multisig_data = None
    else:
        multisig_data = None

    # Transaction data
    for account_id in accounts:
        txs = w.transactions(account_id=account_id, as_dict=True)
        print("\n- - Transactions Account %d (%d)" % (account_id, len(txs)))

        for tx in reversed(txs):  # Process transactions in reverse order
            spent = " "
            address = tx['address'] or 'nulldata'
            if 'spent' in tx and not tx['spent']:
                spent = "U"
            status = tx['status'] if tx['status'] in ['confirmed', 'unconfirmed'] else ""

            transactions_data.append({
                "txid": tx['txid'],
                "address": address,
                "confirmations": tx['confirmations'],
                "amount": Value.from_satoshi(tx['value']),
                "spent": spent,
                "status": status
            })

    return w.balance(), w.wallet_id, w.name, w.scheme, w.multisig, w.witness_type, w.network.name, transactions_data, multisig_data

def external_send_transaction(recipient_address, amount, message, wallet_data):
    wallet_name= wallet_data.get("wallet_name")
    # Extract wallet details
    mnemonic_passphrase = wallet_data.get('mnemonic_passphrase')
    # Generate sender's key


    w = Wallet(wallet_name)
    w.balance_update_from_serviceprovider()  # This will update the wallet to make sure it syncs with the blockchain.
    w.utxos_update()
    w.transactions_update()
    message_bytes = message.encode('utf-8')  # Convert to bytes
    w.info()
    # Create OP_RETURN script
    op_return_script = CScript([OP_RETURN, message_bytes])

    # Create OP_RETURN output
    op_return_output = Output(value=0, lock_script=op_return_script)  # Value = 0 for OP_RETURN
    tx = w.transaction_create(output_arr=[(recipient_address,amount)],fee='normal')

    # Add the OP_RETURN output to the transaction
    tx.outputs.append(op_return_output)

    print("hex: " + tx.raw_hex())

    try:
        # Sign the transaction
        tx.sign(HDKey.from_passphrase(passphrase=mnemonic_passphrase))
        print("tx.info()")
        print(tx.info())
        return broadcast_transaction(tx)
    except ValueError as e:
        print(f"Transaction Error: {e}")
        return e

def broadcast_transaction(tx):
    """Broadcast the transaction."""
    if not tx.verify():
        print(tx.verify())
        raise ValueError("Transaction verification failed.")

    # Get raw transaction hex
    raw_tx = tx.raw_hex()
    print(f"Raw Transaction Hex: {raw_tx}")

    # Broadcast the transaction to the Bitcoin network
    url = "https://mempool.space/api/tx"
    headers = {
        "Content-Type": "text/plain"
    }

    response = requests.post(url, headers=headers, data=raw_tx)

    print(response.status_code)
    print("Broadcasted Transaction ID: ",response.text)


    return response.text

def address_qrcode(address,logo_path):
    # Create a QR code object
    qr = qrcode.QRCode(version=1, box_size=10, border=5)

    # Define the data to be encoded in the QR code
    data =address
    # Add the data to the QR code object
    qr.add_data(data)

    # Make the QR code
    qr.make(fit=True)

    # Create an image from the QR code
    img = qr.make_image(fill_color="black", back_color="white")

    # Open the logo or image file
    logo = Image.open(logo_path)

    # Resize the logo or image if needed
    logo = logo.resize((50, 50))

    # Position the logo or image in the center of the QR code
    img_w, img_h = img.size
    logo_w, logo_h = logo.size
    pos = ((img_w - logo_w) // 2, (img_h - logo_h) // 2)

    # Paste the logo or image onto the QR code
    img.paste(logo, pos)

    # Save the QR code image with logo or image
    path = f"assets/{address}.png"
    img.save(path)
    return path

def generate_master_pub_key(name_key):
    seed_phrase=Mnemonic().generate()
    print(seed_phrase)
    key2 = HDKey.from_passphrase(seed_phrase, key_type='single')

    # Prepare wallet data
    keys_data = {
        "name_key":name_key,
        "public_master_key": key2.wif(),
        "mnemonic_passphrase": seed_phrase,
    }

           # Handle missing, empty, or corrupted JSON file
    if os.path.exists(json_keys_file_path) and os.path.getsize(json_keys_file_path) > 0:
        try:
            with open(json_keys_file_path, 'r') as file:
                data = json.load(file)
                # If the data is not a list, reset it to an empty list
                if not isinstance(data, list):
                    data = []
        except json.JSONDecodeError:
            # Handle corrupted JSON file by initializing an empty list
            return "Error", "The wallet data file is corrupted. Initializing a new file."
            data = []
    else:
        # Initialize data as a list if file doesn't exist or is empty
        data = []


    data.append(keys_data)
    # Save updated data back to the file
    with open(json_keys_file_path, 'w') as file:
        json.dump(data, file, indent=4)

    print(key2.public_master)
    print(key2.wif())
    return key2.wif()

def Create_multi_sig_wallet(wallet_name, keys, sigs_required):
    # Generate a seed phrase for the wallet
    seed_phrase = Mnemonic().generate()
    passphrase = seed_phrase  # In this case, the passphrase is the seed phrase
    hd_key_private_hex = HDKey.from_passphrase(passphrase).private_hex

    # Create the list of keys for the wallet
    list_keys = [seed_phrase]  # Start the list with the seed phrase

    # Process the provided keys, expecting them to be space-separated
    for key in keys.split():  # Split the keys by spaces
        list_keys.append(HDKey(key, key_type='single'))  # Append each key to the list

    # Create the multi-sig wallet with the provided details
    w = Wallet.create(wallet_name,list_keys, sigs_required)
    WalletKeys = w.get_keys(number_of_keys=1)  # Get one key from the wallet (or change as needed)
    w.info()
    for k in WalletKeys:
        bech32_address = k.address  # Extract the Bech32 address from the wallet keys

    # Save wallet details in a dictionary
    wallet_data = {
        "wallet_name": wallet_name,
        "mnemonic_passphrase": passphrase,
        "private_hex": hd_key_private_hex,
        "bech32_address": bech32_address
    }

    # Handle missing, empty, or corrupted JSON file
    if os.path.exists(json_file_path) and os.path.getsize(json_file_path) > 0:
        try:
            with open(json_file_path, 'r') as file:
                data = json.load(file)
                # If the data is not a list, reset it to an empty list
                if not isinstance(data, list):
                    data = []
        except json.JSONDecodeError:
            return passphrase ,"error", "Handle corrupted JSON file by initializing an empty list"
            data = []
    else:
        data = []

    # Append the new wallet data to the list
    data.append(wallet_data)

    # Save updated data back to the file
    with open(json_file_path, 'w') as file:
        json.dump(data, file, indent=4)

    return passphrase ,"Success","Wallet created successfully! Proceed to view your wallet."

def load_wallet(wallet_name,passphrase):
    hd_key_private_hex = HDKey.from_passphrase(passphrase).private_hex
    w = Wallet.create(wallet_name, witness_type='segwit', keys=hd_key_private_hex, network='bitcoin')
    w.utxos_update()
    w.transactions_update()
    WalletKeys = w.get_keys(number_of_keys=1)
    for k in WalletKeys:
        bech32_address = k.address
    # Save wallet details
    wallet_data = {
        "wallet_name": wallet_name,
        "mnemonic_passphrase": passphrase,
        "private_hex":hd_key_private_hex,
        "bech32_address": bech32_address
    }

    # Handle missing, empty, or corrupted JSON file
    if os.path.exists(json_file_path) and os.path.getsize(json_file_path) > 0:
        try:
            with open(json_file_path, 'r') as file:
                data = json.load(file)
                # If the data is not a list, reset it to an empty list
                if not isinstance(data, list):
                    data = []
        except json.JSONDecodeError:
            return "Handle corrupted JSON file by initializing an empty list"
            data = []
    else:
        # Initialize data as a list if file doesn't exist or is empty
        data = []

    # Append the new wallet data to the list
    data.append(wallet_data)
    # Save updated data back to the file
    with open(json_file_path, 'w') as file:
        json.dump(data, file, indent=4)

def save_trx(recipient_address, amount, message, wallet_data):
    print(f"recipient_address {recipient_address}")
    print(f"amount {amount}")
    print(f"wallet_data {wallet_data}")
    wallet_name= wallet_data.get("wallet_name")
    # Extract wallet details
    mnemonic_passphrase = wallet_data.get('mnemonic_passphrase')
    # Generate sender's key
    w = Wallet(wallet_name)
    print(w.info())
    message_bytes = message.encode('utf-8')  # Convert to bytes

    # Create OP_RETURN script
    op_return_script = CScript([OP_RETURN, message_bytes])

    # Create OP_RETURN output
    op_return_output = Output(value=0, lock_script=op_return_script)  # Value = 0 for OP_RETURN

    try:

        tx = w.transaction_create(output_arr=[(recipient_address,amount)],fee='normal')
        # Add the OP_RETURN output to the transaction
        tx.outputs.append(op_return_output)

        print(f"transaction id {tx}")
        print("hex: " + tx.raw_hex())
        # Sign the transaction

        tx.sign(HDKey.from_passphrase(passphrase=mnemonic_passphrase))

        print("tx.info()")
        print(tx.info())
        print("transaction Id")
        print(tx)
        tx.save()
        return tx
    except ValueError as e:
        print(f"Transaction Error: {e}")
        return e

def find_and_download_transaction( txid, download_dir):
    """Find the transaction file by TXID and download it."""
    # Expand user paths
    bitcoinlib_dir = os.path.expanduser("~/.bitcoinlib")
    download_dir = os.path.expanduser(download_dir)
    print(f"BitcoinLib Directory: {bitcoinlib_dir}")

    # Check if the .bitcoinlib directory exists
    if not os.path.exists(bitcoinlib_dir):
        print(f"Error: No .bitcoinlib directory found at {bitcoinlib_dir}.")
        return
    if not os.path.exists(download_dir):
        print(f"Error: No .bitcoinlib directory found at {download_dir}.")
        return


    # List all files in the .bitcoinlib directory and filter for .tx files
    tx_files = [f for f in os.listdir(bitcoinlib_dir) if f.endswith('.tx')]
    print(f"Found transaction files: {tx_files}")
    print(os.access(download_dir, os.W_OK))
    for tx_file in tx_files:
        if txid in tx_file:
            source_path = os.path.join(bitcoinlib_dir, tx_file)
            destination_path = os.path.join(download_dir, tx_file)
            print(os.path.exists(destination_path))

            print(f"Attempting to copy {source_path} to {destination_path}")

            # Ensure the destination directory exists
            os.makedirs(download_dir, exist_ok=True)

            try:
                # Copy the transaction file to the download directory
                shutil.copy(source_path, destination_path)
                print(f"Transaction file '{tx_file}' downloaded to {destination_path}.")
                return
            except Exception as e:
                print(f"Error copying file: {e}")
                return

    print(f"No transaction file found for TXID: {txid}")

def load_transaction(transaction_file_path,key_passphrase):
    try:
        with open(transaction_file_path, 'rb') as file:
            tx = pickle.load(file)
        tx.sign(HDKey.from_passphrase(passphrase=key_passphrase))
        tx.save()

        return True,tx
    except Exception as e:
        return False,e

def read_and_broadcast_transaction_from_path(transaction_file_path):
    try:
        with open(transaction_file_path, 'rb') as file:
            tx = pickle.load(file)
        tx.verify()
        print( tx.verify())

        return True,broadcast_transaction(tx)
    except Exception as e:
        return False,e


# recipient_address="bc1qvszq9uh5eza3r5cnqyr0wzqrxwxgwaqcefma9q"
# amount=1001
# message=""
# wallet_data={
#         "wallet_name": "ahmed_testing",
#         "password_hash": "6b86b273ff34fce19d6b804eff5a3f5747ada4eaa22f1d49c01e52ddb7875b4b",
#         "mnemonic_passphrase": "bunker among rebel hello between action city below defy mass neither remove",
#         "bech32_address": "bc1qg8ccwyhpeupnwtvm3spv46xxthaaczkuh50js7"
#     }
# save_trx(recipient_address, amount, message, wallet_data)


