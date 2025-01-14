import hashlib
from kivy.uix.screenmanager import  FadeTransition
from kivy.properties import NumericProperty
from wallet_func import *
from kivy.uix.screenmanager import ScreenManager
from kivymd.app import MDApp
from kivy.uix.screenmanager import Screen
from kivy.core.clipboard import Clipboard
import json
import webbrowser
import pyperclip
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivymd.uix.label import  MDIcon
from kivy.uix.label import Label
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.filechooser import FileChooserIconView
from kivy.uix.popup import Popup
from kivy.properties import StringProperty
from kivy.core.window import Window
from kivy.uix.image import Image
import os
from kivy.clock import Clock

import os
import json
from kivy.utils import platform
from kivymd.app import MDApp
from kivy.uix.screenmanager import ScreenManager, FadeTransition
from kivy.core.window import Window

# Define dynamic paths as public variables
json_file_path = "data/wallets.json"
json_keys_file_path ="data/keys.json"
wallet_name = None


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def generate_passphrase():
    mnemo = Mnemonic()
    return mnemo.generate()

def show_popup(title, message):
    popup = Popup(
        title=title,
        content=Label(text=message, halign='center', valign='middle', text_size=(1000, None)),
        size_hint=(0.8, 0.4),
    )
    popup.open()

def show_popup_master_pk():
    """
    Displays a popup to generate and display a master public key with improved styling.
    """
    def generate_keys(instance=None):
        """Generate the key and display it in the popup."""
        input_text = name_input.text.strip()
        if input_text:
            generated_message = generate_master_pub_key(input_text)  # Generate the key
            output_label.text = f"[b]Generated Key:[/b] {generated_message}"
        else:
            output_label.text = "[color=ff0000]Please enter a valid key name.[/color]"

    def copy_to_clipboard(instance=None):
        """Copy the displayed key to the clipboard."""
        if output_label.text.startswith("[b]Generated Key:[/b]"):
            key_to_copy = output_label.text.replace("[b]Generated Key:[/b] ", "").strip()
            pyperclip.copy(key_to_copy)
            output_label.text = "[color=00ff00]Key copied to clipboard![/color]"

    def close_popup(instance):
        """Close the popup."""
        popup.dismiss()

    # Input for the key name with larger text size
    name_input = TextInput(
        hint_text="Enter key name",
        size_hint=(1, None),
        height=50,
        multiline=False,
        padding=[10, 10],  # Padding inside the text input
        font_size=24,  # Increased font size for better readability
    )

    # "Generate" button with larger text size
    generate_button = Button(
        text="Generate",
        size_hint=(0.2, None),
        height=50,
        background_color=(0.2, 0.6, 1, 1),  # Blue background
        color=(1, 1, 1, 1),  # White text
        font_size=20,  # Increased font size for button text
        on_release=generate_keys,
    )

    # Horizontal layout for input and button
    input_layout = BoxLayout(
        orientation="horizontal",
        size_hint_y=None,
        height=60,
        spacing=10,
        padding=[10, 0],  # Horizontal padding for the layout
    )
    input_layout.add_widget(name_input)
    input_layout.add_widget(generate_button)

    # Label to display the generated key with larger text size
    output_label = Label(
        text="Generated key will appear here.",
        markup=True,  # Enable markup for styled text
        size_hint=(1, None),
        height=80,
        halign="center",
        valign="middle",
        font_size=20,  # Increased font size for key display
        color=(0.9, 0.9, 0.9, 1),  # Light gray text
    )
    output_label.bind(size=lambda *args: output_label.setter('text_size')(output_label, (output_label.width, None)))

    # "Copy" button with centered alignment and larger width
    copy_button = Button(
        text="Copy",
        size_hint=(None, None),
        size=(300, 60),  # Increased width and height for the Copy button
        background_color=(0.2, 0.8, 0.2, 1),  # Green background
        color=(1, 1, 1, 1),  # White text
        font_size=22,  # Larger font size for button text
        on_release=copy_to_clipboard,
    )

    # "Close" button with red background
    close_button = Button(
        text="Close",
        size_hint=(None, None),
        size=(300, 60),  # Similar width as Copy button
        background_color=(1, 0, 0, 1),  # Red background
        color=(1, 1, 1, 1),  # White text
        font_size=22,  # Larger font size for button text
        on_release=close_popup,
    )

    # Horizontal layout for the Copy and Close buttons
    button_layout = BoxLayout(
        orientation="horizontal",
        size_hint_y=None,
        height=70,
        spacing=10,
        padding=[10, 10],  # Padding around the buttons
    )
    button_layout.add_widget(copy_button)
    button_layout.add_widget(close_button)

    # Layout for the popup content
    layout = BoxLayout(
        orientation="vertical",
        spacing=20,
        padding=[20, 20, 20, 20],  # Padding: [left, top, right, bottom]
    )
    layout.add_widget(input_layout)
    layout.add_widget(output_label)
    layout.add_widget(button_layout)

    # Popup setup
    popup = Popup(
        title="Retrieve Public Key",
        title_size=24,  # Increased title font size
        title_align="center",
        content=layout,
        size_hint=(0.8, None),
        height=400,  # Increased height for better spacing with larger text
        auto_dismiss=False,  # Prevent closing the popup by tapping outside
    )
    popup.open()

def show_multi_Sig_popup(title,icon,message,transaction_id):

    # Create the layout for the popup
    layout = BoxLayout(
        orientation='vertical',
        spacing=20,  # Spacing between widgets
        padding=(20, 20, 20, 20)  # Padding: left, top, right, bottom
    )

    # Add an image to the popup
    layout.add_widget(Image(source=icon, size_hint=(1, 0.6)))  # Replace 'success_icon.png' with your image

    # Add a success message
    message_label = Label(
        text=message,
        size_hint=(1, 0.4),
        halign='center',  # Align text horizontally
        valign='middle',  # Align text vertically
    )
    # Set text wrapping
    message_label.text_size = (None, None)  # Allow size to adapt to parent
    message_label.bind(size=lambda lbl, sz: setattr(lbl, 'text_size', (sz[0], None)))

    layout.add_widget(message_label)
    # Create the popup
    popup = Popup(title=title,
                  content=layout,
                  size_hint=(0.8, 0.4),
                  auto_dismiss=False)

    # Schedule the popup to dismiss after 2 seconds
    Clock.schedule_once(lambda dt: popup.dismiss(), 2)

    # Open the popup
    popup.open()


def get_bitcoin_wallet_data_json():
    """
    Retrieves Bitcoin wallet details from a JSON file by wallet name.

    Parameters:
        wallet_name (str): Name of the wallet to retrieve.

    Returns:
        dict: Wallet details if found.
        str: Error message if the wallet or file is not found.
    """
    if not wallet_name:
        return "No wallet name provided."

    try:
        with open(json_file_path, 'r') as file:
            data = json.load(file)

        # Check if the data is a list (list of wallets)
        if isinstance(data, list):
            for wallet_details in data:
                if wallet_details.get("wallet_name", "").strip().lower() == wallet_name.strip().lower():
                    return wallet_details
            return "Wallet not found."

        return "Error: The data in the file is not structured correctly."

    except FileNotFoundError:
        return f"Error: File not found at '{json_file_path}'."
    except json.JSONDecodeError:
        return f"Error: Failed to decode JSON from the file '{json_file_path}'."
    except Exception as e:
        return f"An unexpected error occurred: {str(e)}"

class MainMenu(Screen):
    def create_new_wallet(self):
        self.manager.current = "create_new_wallet"

    def create_multi_sig_wallet(self):
        self.manager.current = "multi_sig_screen"

    def login_or_open_wallet(self):
        # Navigate to Wallet List Screen
        wallet_list_screen = self.manager.get_screen("wallet_list_screen")
        wallet_list_screen.load_wallets()  # Load wallets before navigating
        self.manager.current = "wallet_list_screen"

    def load_Wallet_from_seed_phrase(self):
        self.manager.current = "load_wallet_from_seedphrase"

class WalletListScreen(Screen):
    def load_wallets(self):
        # Clear the list of wallets
        self.ids.wallet_list.clear_widgets()

        # Load wallets from the JSON file
        if os.path.exists(json_file_path):
            with open(json_file_path, 'r') as file:
                data = json.load(file)

            # Iterate over the wallet data
            for wallet_details in data:  # Assuming data is a list of wallet dictionaries
                global wallet_name
                wallet_name = wallet_details.get("wallet_name", "Unnamed Wallet")  # Get wallet name safely
                # Create a button for each wallet with increased height and padding
                wallet_button = Button(
                    text=wallet_name,
                    font_size=38,
                    size_hint_y=None,
                    background_color= (0.0, 1.0, 0.0, 0.5),
                    height=90,  # Increased height for each item
                    on_press=self.select_wallet,  # Bind the click event to `select_wallet`
                    padding=(10, 10)  # Add padding inside the button
                )
                self.ids.wallet_list.add_widget(wallet_button)
        else:
            # Display a message if no wallets are found
            self.ids.wallet_list.add_widget(
                Label(
                    text="No wallets found.",
                    font_size=20,
                    size_hint_y=None,
                    height=50
                )
            )

    def go_back(self):

        """Handle the "Go Back" button press."""
        self.manager.current = "main_menu"

    def select_wallet(self, instance):
        global wallet_name
        wallet_name = instance.text  # Get the wallet name from the button text
        print(f"Selected wallet: {wallet_name}")  # Debugging: Check the selected wallet

        # Optionally navigate to another screen
        self.manager.current = "home_screen"

class CreateNewWallet(Screen):
    wallet_name = StringProperty('')
    password = StringProperty('')
    confirm_password = StringProperty('')
    passphrase = StringProperty('')  # To store the generated passphrase

    def submit_new_wallet(self):
        global wallet_name  # Update the global variable
        wallet_name = self.ids.wallet_name_input.text.strip()
        password = self.ids.password_input.text
        confirm_password = self.ids.confirm_password_input.text

        # Basic validation
        if not wallet_name:
            show_popup("Input Error", "Wallet name cannot be empty.")
            return
        if not password:
            show_popup("Input Error", "Password cannot be empty.")
            return
        if password != confirm_password:
            show_popup("Input Error", "Passwords do not match.")
            return

        # Generate passphrase and Bitcoin address
        passphrase = generate_passphrase()
        #wallet info
        self.passphrase = passphrase  # Save passphrase locally
        hd_key_private_hex = HDKey.from_passphrase(passphrase).private_hex
        w = Wallet.create(wallet_name, witness_type='segwit', keys=hd_key_private_hex, network='bitcoin')

        WalletKeys = w.get_keys(number_of_keys=1)
        for k in WalletKeys:
            bech32_address = k.address

        # Prepare wallet data
        wallet_data = {
            "wallet_name": wallet_name,
            "password_hash": hash_password(password),
            "mnemonic_passphrase": passphrase,
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
                # Handle corrupted JSON file by initializing an empty list
                show_popup("Error", "The wallet data file is corrupted. Initializing a new file.")
                data = []
        else:
            # Initialize data as a list if file doesn't exist or is empty
            data = []

        # Append the new wallet data to the list
        data.append(wallet_data)

        # Save updated data back to the file
        with open(json_file_path, 'w') as file:
            json.dump(data, file, indent=4)

        # Show a success popup
        show_popup("Success", "Wallet created successfully! Proceed to view your wallet.")

        # Pass data to WalletCreated screen
        wallet_created_screen = self.manager.get_screen("wallet_created")
        wallet_created_screen.passphrase = passphrase
        self.manager.current = "wallet_created"

        # Clear input fields
        self.ids.wallet_name_input.text = ""
        self.ids.password_input.text = ""
        self.ids.confirm_password_input.text = ""

    def go_back(self):
        """Navigate back to the home screen."""
        self.manager.current = "main_menu"

class WalletCreated(Screen):
    passphrase = StringProperty('')

    def copy_passphrase(self):
        Clipboard.copy(self.passphrase)
        show_popup("Copied", "Passphrase copied to clipboard.")

    def finish(self):
        # Navigate to HomeScreen
        self.manager.current = "home_screen"

class HomeScreen(Screen):
    bitcoin_address = StringProperty("")
    balance = NumericProperty(0)

    def copy_to_clipboard(self, text):
        """Copy the text to clipboard."""
        prefix = "bitcoin address: "

        address_part = text.split(prefix)[-1].strip()
        pyperclip.copy(address_part)
        print(f"Copied to clipboard: {text}")  # Optional: for debugging purposes

    def on_address_click(self, instance, touch):
        """Handle the click on the address label."""
        if instance.collide_point(*touch.pos):  # Check if the touch was on the label
            self.copy_to_clipboard(instance.text)  # Copy the label's text to clipboard

    def on_enter(self):
        try:
            # Fetch Bitcoin address and wallet data
            wallet_data = get_bitcoin_wallet_data_json()
            wallet_name_str = wallet_data.get("wallet_name")
            self.bitcoin_address =  wallet_data.get("bech32_address")


            # Update main labels
            self.ids.wallet_address_label.text = f"{self.bitcoin_address}"

            # Fetch additional wallet info, including transactions
            balance,wallet_id, name, scheme, multisig, witness_type, network, transactions,multisig_table = wallet_info(wallet_name_str)

            # Update wallet info labels
            self.ids.total_balance_label.text = f"{balance} Sats"

            self.ids.wallet_id_label.text = f"Wallet ID: {wallet_id}"
            self.ids.wallet_name_label.text = f"Wallet Name: {name}"
            self.ids.wallet_scheme_label.text = f"Scheme: {scheme}"
            self.ids.wallet_multisig_label.text = f"Multisig: {multisig}"
            self.ids.wallet_witness_label.text =  f"Witness Type: {witness_type}"
            self.ids.wallet_network_label.text = f"Network: {network}"

            # Fetch and display transactions (assets)
            self.update_transactions(transactions)
            self.update_multisig_keys(multisig_table)
            self.ids.wallet_address_label.text = f"{self.bitcoin_address}"




        except Exception as e:
            # Handle errors
            self.ids.wallet_name_label.text = "Error fetching address or balance"
            self.ids.total_balance_label.text = "Balance unavailable"
            print(f"Error: {e}")


    def update_transactions(self, transactions):
        try:
            # Get the scrollable GridLayout for transactions
            transaction_list_layout = self.ids.transactions_list
            transaction_list_layout.clear_widgets()  # Clear existing widgets

            # Add each transaction as a card
            for txn in transactions:
                # if txn["spent"] == 'U':
                #     sym="-"
                # else:
                #     sym="+"
                # Create the card layout with gray background
                card = MDCard(size_hint_y=None, height=120, padding=10, orientation='horizontal', spacing=10, md_bg_color="grey",)

                # Create a box layout for the left side with an icon at the start
                left_layout = MDBoxLayout(size_hint_x=0.8, orientation='horizontal', spacing=10)

                # Add the icon image (you can change the icon name or source path)
                icon = MDIcon(icon="input", size_hint_x=None, size_hint_y=None, size=(40, 40))
                left_layout.add_widget(icon)  # Add the icon to the left layout

                # Create the left-side text content
                text_layout = MDBoxLayout(orientation='vertical', spacing=10)
                txn_id_label = MDLabel(text=txn['txid'], size_hint_x=1, height=30)
                address_label = MDLabel(text=txn['address'], size_hint_x=1, height=30)
                text_layout.add_widget(txn_id_label)
                text_layout.add_widget(address_label)

                left_layout.add_widget(text_layout)  # Add the text content to the left layout

                # Right side: Amount and Confirmations
                right_layout = MDBoxLayout(size_hint_x=0.2, orientation='vertical', spacing=10)
                amount_label = MDLabel(text=f"Amount: {txn['amount']} ", size_hint_x=1, height=30)
                confirmations_label = MDLabel(text=f"Confirmations: {txn['confirmations']}", size_hint_x=1, height=30)
                right_layout.add_widget(amount_label)
                right_layout.add_widget(confirmations_label)

                # Add left and right layouts to the card
                card.add_widget(left_layout)
                card.add_widget(right_layout)

                # Add the card to the transaction list
                transaction_list_layout.add_widget(card)

        except Exception as e:
            print(f"Error fetching transactions: {e}")
            # Optionally, you can add a label stating no transactions found
            error_label = MDLabel(text="No transactions available", size_hint_y=None, height=40)
            transaction_list_layout.add_widget(error_label)



    def update_multisig_keys(self, multisig_table):
        try:
            # Get the scrollable GridLayout for multisig keys
            multisig_keys_layout = self.ids.multisig_keys_list
            multisig_keys_layout.clear_widgets()  # Clear existing widgets
            if multisig_table:
                # Add headers for the multisig keys table
                header = BoxLayout(size_hint_y=None, height=40)
                header.add_widget(Label(text="Key ID", bold=True,size_hint_x=0.1))
                header.add_widget(Label(text="Public Key (WIF)", bold=True,size_hint_x=0.6))
                header.add_widget(Label(text="Scheme", bold=True,size_hint_x=0.1))
                header.add_widget(Label(text="Role", bold=True,size_hint_x=0.1))
                header.add_widget(Label(text="Primary", bold=True,size_hint_x=0.1))
                multisig_keys_layout.add_widget(header)
                for row in multisig_table:
                    multisig_row = BoxLayout(size_hint_y=None, height=40)
                    multisig_row.add_widget(Label(text=str(row['key_id']),size_hint_x=0.1))
                    multisig_row.add_widget(Label(text=str(row['wif'][:10] + '...' + row['wif'][-19:]), size_hint_x=0.6))
                    multisig_row.add_widget(Label(text=str(row['key_id']),size_hint_x=0.1))
                    multisig_row.add_widget(Label(text=str(row['role']),size_hint_x=0.1))
                    multisig_row.add_widget(Label(text=str(row['is_primary']),size_hint_x=0.1))
                    multisig_keys_layout.add_widget(multisig_row)

            else:

                # Handle case if there's no multisig data
                error_label = Label(text="No multisig keys available", size_hint_y=None, height=40)
                multisig_keys_layout.add_widget(error_label)

        except Exception as e:
            print(f"Error updating multisig keys: {e}")
            # Optionally, you can add a label stating no multisig data available
            error_label = Label(text="Error fetching multisig keys", size_hint_y=None, height=40)
            multisig_keys_layout.add_widget(error_label)


    def go_back(self):
        """Navigate back to the home screen."""
        self.ids.wallet_address_label.text = ""
        self.ids.total_balance_label.text = ""

        self.ids.wallet_id_label.text = ""
        self.ids.wallet_name_label.text = ""
        self.ids.wallet_scheme_label.text = ""
        self.ids.wallet_multisig_label.text = ""
        self.ids.wallet_witness_label.text = ""

        self.ids.transactions_list.clear_widgets()
        self.ids.multisig_keys_list.clear_widgets()
        self.manager.current = "wallet_list_screen"

class CustomPopup(Popup):
    title = StringProperty("")
    message = StringProperty("")
    txid = StringProperty("")  # Make sure txid is dynamically updated

    def go_memepool(self):
        """Open the mempool URL in the browser using the transaction ID."""
        if self.txid:  # Make sure txid is not empty
            url = f"https://mempool.space/tx/{self.txid}"
            webbrowser.open(url)  # Opens the URL in the default web browser
        else:
            print("No TXID found.")
    def go_back(self):
        """Navigate back to the home screen."""
        Popup.dismiss(self)

class SendScreen(Screen):
    def go_back(self):
        """Navigate back to the home screen."""
        self.manager.current = "home_screen"


    def send_transaction(self):
        """Handle the transaction sending process."""
        # Get inputs from the TextInput fields
        recipient_address = self.ids.receiver_address_input.text.strip()
        amount = self.ids.amount_input.text.strip()
        message = self.ids.message_input.text.strip()

        # Validate inputs
        if not recipient_address:
            self.show_popup("Input Error", "Receiver's address is required.")
            return
        if not amount or not amount.isdigit():
            self.show_popup("Input Error", "Amount in sats must be a valid number.")
            return

        # Convert amount to integer (in satoshis)
        amount_sats = int(amount)

        # Fetch Bitcoin address and wallet data
        wallet_data = get_bitcoin_wallet_data_json()
        if not wallet_data:
            self.show_popup("Error", "Failed to load wallet data.")
            return

        # Pass data to the external function
        try:
            result = external_send_transaction(
                recipient_address=recipient_address,
                amount=amount_sats,
                message=message,
                wallet_data=wallet_data
            )
            print("result")
            print(result)
            # Show success popup with TXID
            self.show_popup("Success", "Transaction broadcasted!", txid=result)

        except Exception as e:
            # Show error popup
            self.show_popup("Error", f"Transaction failed:",txid=str(e))

        # Return to the home screen
        self.go_back()

    def save_transaction(self):
        """Handle the transaction sending process."""
        # Get inputs from the TextInput fields
        recipient_address = self.ids.receiver_address_input.text.strip()
        amount = self.ids.amount_input.text.strip()
        message = self.ids.message_input.text.strip()

        # Validate inputs
        if not recipient_address:
            self.show_popup("Input Error", "Receiver's address is required.")
            return
        if not amount or not amount.isdigit():
            self.show_popup("Input Error", "Amount in sats must be a valid number.")
            return

        # Convert amount to integer (in satoshis)
        amount_sats = int(amount)

        # Fetch Bitcoin address and wallet data
        wallet_data = get_bitcoin_wallet_data_json()
        if not wallet_data:
            self.show_popup("Error", "Failed to load wallet data.")
            return

        # Pass data to the external function
        try:

            result = save_trx(
                recipient_address=recipient_address,
                amount=amount_sats,
                message=message,
                wallet_data=wallet_data
            )
            print("result")
            print(result)

            # Show success popup with TXID
            find_and_download_transaction(txid=str(result),download_dir="~/downloads")
            self.show_popup("Success", f"Transaction created and saved in the download folder:", txid=str(result))

        except Exception as e:
            # Show error popup
            print(f"Exception {e}")
            self.show_popup("Error", f"Transaction failed:",txid=str(result))

        # Return to the home screen
        self.go_back()

    def show_popup(self, title, message, txid=None):
        """Show a popup with the given title, message, and optional TXID."""
        popup = CustomPopup(title=title, message=message, txid=txid)
        popup.open()

class LoadWalletFromSeedPhrase(Screen):
    wallet_name = StringProperty('')
    passphrase = StringProperty('')  # To store the generated passphrase

    def submit_new_wallet(self):
        global wallet_name  # Update the global variable
        wallet_name = self.ids.wallet_name_input.text.strip()
        passphrase = self.ids.wallet_passphrase_input.text
        print(f"Sanitized mnemonic: {passphrase}")
        # Basic validation
        if not wallet_name:
            show_popup("Input Error", "Wallet name cannot be empty.")
            return
        if not passphrase:
            show_popup("Input Error", "Passphrase cannot be empty.")
            return

        load_wallet(wallet_name, passphrase)

        # Show a success popup
        show_popup("Success", "Wallet Loaded successfully! Proceed to view your wallet.")

        # Pass data to WalletLoaded screen
        self.manager.current = "home_screen"

        # Clear input fields
        self.ids.wallet_name_input.text = ""
        self.ids.wallet_passphrase_input.text = ""

    def load_wallet_from_seedphrase(self):
        self.submit_new_wallet()  # Use the existing submit function to handle the logic

    def go_back(self):
        """Navigate back to the home screen."""
        self.manager.current = "main_menu"


class MultiSigScreen(Screen):

    def create_multisig_wallet(self):

        self.manager.current = "create_multisig_wallet"

    def get_public_key(self):
        """Handles fetching the public key."""
        print("Getting Public Key...")
        show_popup_master_pk()
        # Add your logic here to retrieve the public key

    def go_back(self):
        """Handle the 'Go Back' button press."""
        self.manager.current = 'main_menu'  # Replace 'home_screen' with your actual screen name

    def sign_transaction(self):
        """Handle the 'Go Back' button press."""
        self.manager.current = 'sign_trx'  # Replace 'home_screen' with your actual screen name

class ReceiveScreen(Screen):
    bitcoin_address = StringProperty("")  # Property for binding to the UI

    def on_enter(self):
        """Called when the screen is entered to generate and display a QR code."""
        # Fetch the Bitcoin address
        wallet_data = get_bitcoin_wallet_data_json()
        self.bitcoin_address = wallet_data.get("bech32_address")

        # Generate QR code with the logo and get the saved path
        qr_code_path = address_qrcode(self.bitcoin_address, "assets/bitcoin-btc-logo.png")

        # Update the source of the image widget
        self.ids.qr_image.source = qr_code_path
    def on_leave(self):
        """Called when the screen is left to clean up resources."""
        qr_code_path = self.ids.qr_image.source
        if os.path.exists(qr_code_path):
            os.remove(qr_code_path)  # Delete the QR code image

    def go_back(self, instance):
        """Handle the 'Go Back' button press."""
        self.manager.current = 'home_screen'  # Replace 'home_screen' with your actual screen name

class SignTrx(Screen):
    selected_key = StringProperty("")
    uploaded_file_path = StringProperty("")

    def load_keys(self):
        """Load keys from the JSON file."""
        self.keys = []  # Clear keys list to avoid duplicates
        if os.path.exists(json_keys_file_path):
            with open(json_keys_file_path, 'r') as file:
                data = json.load(file)

            for key_details in data:  # Assuming data is a list of dictionaries
                key_name = key_details.get("name_key", "Unnamed Key")
                public_master_key = key_details.get("public_master_key", "N/A")
                mnemonic_passphrase = key_details.get("mnemonic_passphrase", "N/A")
                # Store both key name + public key (for display) and mnemonic passphrase (for signing)
                self.keys.append(
                    {"display": f"{key_name} =>{public_master_key[:10]}...{public_master_key[-19:]}",
                     "mnemonic_passphrase": mnemonic_passphrase}
                )
        else:
            print("Key file not found.")
            self.ids.wallet_list.add_widget(
                Label(
                    text="No Keys found.",
                    multiline=True,
                    font_size=20,
                    size_hint_y=0.7,
                    height=50
                )
            )

    def populate_key_list(self, keys=None):
        """Populate the key list with filtered or all keys."""
        keys = keys or self.keys
        key_list = self.ids.key_list
        key_list.clear_widgets()

        for key in keys:
            # Create a button for each key
            button = Button(
                text=key["display"],
                size_hint_y=None,
                height=90,
                halign="center",
                valign="middle",
                text_size=(self.width - 40, None),  # Wrap text within button width
                on_press=lambda instance, k=key: self.on_key_select(k, instance)
            )
            key_list.add_widget(button)

    def filter_keys(self, search_text):
        """Filter keys based on the search text."""
        filtered_keys = [key for key in self.keys if search_text.lower() in key["display"].lower()]
        self.populate_key_list(filtered_keys)

    def on_key_select(self, key, button):
        """Triggered when a key is selected."""
        self.selected_key = key["display"]  # Assign the display name or key name to the StringProperty
        self.selected_key_data = key  # Store the whole key dictionary for later use (in case you need mnemonic)
        print(f"Selected key: {self.selected_key}")

        # Highlight the selected button
        for widget in self.ids.key_list.children:
            if isinstance(widget, Button):
                widget.background_color = (1, 1, 1, 1)  # Reset color
        button.background_color = (0, 1, 0, 1)  # Highlight selected button

    def open_file_chooser(self):
        """Open a popup to choose a file."""
        download_dir = os.path.expanduser('~/downloads')  # Path to Downloads directory

        # Check if the directory exists
        if not os.path.exists(download_dir):
            self.show_popup("Error", f"Directory {download_dir} not found.")
            return

        # Create file chooser with a filter for .tx files
        file_chooser = FileChooserIconView(path=download_dir, filters=['*.tx'])  # Show only .tx files
        popup = Popup(title="Choose a file", content=file_chooser, size_hint=(0.9, 0.9))

        def select_file(instance, selection, *args):  # Accept additional arguments
            if selection:
                self.uploaded_file_path = selection[0]
                popup.dismiss()

        file_chooser.bind(on_submit=select_file)
        popup.open()

    def sign_transaction(self):
        """Handle the signing of the transaction."""
        if self.uploaded_file_path and self.selected_key:
            print(f"Signing transaction for key: {self.selected_key_data['display']}, with file: {self.uploaded_file_path}")
            print(f"Mnemonic Passphrase for signing: {self.selected_key_data['mnemonic_passphrase']}")

            status, trx_id = load_transaction(self.uploaded_file_path, self.selected_key_data['mnemonic_passphrase'])
            find_and_download_transaction(txid=str(trx_id), download_dir="~/downloads")
            print(f"Transaction ID: {trx_id}")
            if not status:
                icon = "assets/logo_failed.png"
                message = f"{trx_id}"
                title = "Exception"
            else:
                icon = "assets/logo_success.png"
                message = f"Transaction signed and downloaded successfully!\nTransaction ID: {trx_id}.tx"
                title = "Success"
            show_multi_Sig_popup(title, icon, message, trx_id)
        else:
            print("Please select a key and upload a file first.")
            icon = "assets/logo_failed.png"
            message = "Please select a key and upload a file first."
            title = "Exception"
            result = ""
            show_multi_Sig_popup(title, icon, message, result)

    def go_back(self):
        print("Go back")
        self.manager.current = "multi_sig_screen"

    def broadcast_transaction(self):
        """Handle broadcasting of the transaction."""
        if self.uploaded_file_path:
            # Broadcasting logic here
            status, result = read_and_broadcast_transaction_from_path(self.uploaded_file_path)
            if not status:
                icon = "assets/logo_failed.png"
                message = f"{result}"
                title = "Exception"
            else:
                icon = "assets/logo_success.png"
                message = f"Transaction broadcasted successfully!\nTransaction ID: {result}.tx"
                title = "Success"
            show_multi_Sig_popup(title, icon, message, result)

        else:
            icon = "assets/logo_failed.png"
            message = "Please upload a file first."
            title = "Exception"
            result = ""
            show_multi_Sig_popup(title, icon, message, result)

    def on_enter(self):
        """Lifecycle event called when the screen is entered."""
        self.load_keys()
        self.populate_key_list()

class CreateMultiSigWallet(Screen):
    wallet_name = StringProperty('')
    nbsigs = StringProperty('')
    keys = StringProperty('')
    def save_multi_sig_wallet(self):  # Updated method name
        global wallet_name  # Update the global variable
        wallet_name = self.ids.wallet_name_input.text.strip()
        nbsigs = self.ids.sigs_required.text.strip()
        keys = self.ids.list_keys.text.strip()

        if not wallet_name or not keys or not nbsigs:
            show_popup("Error", "All fields are required!")
            return

        passphrase , status, response = Create_multi_sig_wallet(wallet_name, keys, int(nbsigs))
        show_popup(status, response)



        # Pass data to WalletCreated screen
        wallet_created_screen = self.manager.get_screen("wallet_created")
        wallet_created_screen.passphrase = passphrase
        self.manager.current = "wallet_created"
        self.ids.wallet_name_input.text = ""
        self.ids.sigs_required.text = "1"
        self.ids.list_keys.text = ""

    def go_back(self):
        self.manager.current = "main_menu"


class WalletCreatorApp(MDApp):
    def build(self):
        global json_keys_file_path, json_file_path, wallet_name
        wallet_name = None  # Initialize wallet_name as None or set dynamically if needed
        # App configuration
        self.title = "Z XWallet"
        self.icon = "assets/logo.png"
        Window.size = (800, 600)

        # Screen Manager setup
        sm = ScreenManager(transition=FadeTransition())
        sm.add_widget(MainMenu(name="main_menu"))
        sm.add_widget(CreateNewWallet(name="create_new_wallet"))
        sm.add_widget(WalletCreated(name="wallet_created"))
        sm.add_widget(HomeScreen(name="home_screen"))
        sm.add_widget(SendScreen(name="send_screen"))
        sm.add_widget(WalletListScreen(name="wallet_list_screen"))
        sm.add_widget(ReceiveScreen(name="recieve_screen"))
        sm.add_widget(LoadWalletFromSeedPhrase(name="load_wallet_from_seedphrase"))
        sm.add_widget(MultiSigScreen(name="multi_sig_screen"))
        sm.add_widget(CreateMultiSigWallet(name="create_multisig_wallet"))
        sm.add_widget(SignTrx(name="sign_trx"))

        return sm


if __name__ == "__main__":
    WalletCreatorApp().run()
