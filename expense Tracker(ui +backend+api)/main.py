import json
import re
from collections import defaultdict

import requests
from kivy.animation import Animation
from kivy.config import Config
from kivy.factory import Factory
from kivy.uix.modalview import ModalView

# Set window size to mobile dimensions BEFORE importing kivy
Config.set('graphics', 'width', '360')
Config.set('graphics', 'height', '640')
Config.set('graphics', 'resizable', True)

from kivymd.uix.screen import MDScreen
from kivymd.app import MDApp
from kivy.lang.builder import Builder
from kivymd.uix.label import MDLabel
from kivymd.uix.list import MDList
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.relativelayout import MDRelativeLayout
from kivymd.uix.selectioncontrol import MDCheckbox
from kivymd.uix.button import MDFabButton, MDButton, MDButtonText
from kivy.metrics import dp
from kivy.utils import get_color_from_hex as hex_colors
from kivy.storage.jsonstore import JsonStore
from kivymd.uix.pickers import MDModalDatePicker
from babel.numbers import get_currency_symbol
from babel.core import Locale
import uuid
from datetime import date, timedelta, datetime
from kivy.clock import Clock
from kivy.uix.scrollview import ScrollView
from kivymd.uix.menu import MDDropdownMenu
import threading
from kivy.properties import StringProperty
from kivy.uix.widget import Widget
from kivy.storage.jsonstore import JsonStore
from kivy.utils import get_color_from_hex as hex_color
from kivymd.uix.dialog import MDDialog, MDDialogHeadlineText, MDDialogSupportingText, MDDialogButtonContainer
from cryptography.fernet import Fernet
import os
import webbrowser
import matplotlib
import matplotlib.pyplot as plt
from datetime import datetime
from kivy.uix.screenmanager import Screen, NoTransition
from kivy.clock import Clock
from kivy.core.image import Image as CoreImage
from kivy.uix.image import Image
from io import BytesIO
import requests
matplotlib.use('Agg')
class SecureJsonStore:
    def __init__(self, filename="user_session.json"):
        self.filename = filename
        self.key_file = "session_key.key"
        self._load_or_generate_key()

    def _load_or_generate_key(self):
        """Generate encryption key if it doesn't exist"""
        if not os.path.exists(self.key_file):
            key = Fernet.generate_key()
            with open(self.key_file, "wb") as keyfile:
                keyfile.write(key)
        else:
            with open(self.key_file, "rb") as keyfile:
                key = keyfile.read()

        self.cipher = Fernet(key)

    def encrypt(self, data):
        """Encrypt data before saving"""
        json_data = json.dumps(data).encode()
        return self.cipher.encrypt(json_data)

    def decrypt(self, encrypted_data):
        """Decrypt data when retrieving"""
        decrypted_data = self.cipher.decrypt(encrypted_data)
        return json.loads(decrypted_data.decode())

    def put(self, key, value):
        """Save encrypted session data"""
        encrypted_value = self.encrypt(value)
        store = JsonStore(self.filename)
        store.put(key, value=encrypted_value.decode())  # Save as string

    def get(self, key):
        """Retrieve decrypted session data"""
        store = JsonStore(self.filename)
        if store.exists(key):
            encrypted_value = store.get(key)["value"].encode()
            return self.decrypt(encrypted_value)
        return None

    def delete(self, key):
        """Remove session data"""
        store = JsonStore(self.filename)
        if store.exists(key):
            store.delete(key)






class LoginScreen(MDScreen):
    def link_to_get_api_key(self):
        threading.Thread(target=webbrowser.open, args=("https://nexpenz.nexapytechnologies.com/expense_tracker_api",), daemon=True).start()
    def show_alert(self, title, message):
        self.dialog = MDDialog(
            MDDialogHeadlineText(
                text=title,
                halign="left",
            ),
            MDDialogSupportingText(
                text=message,
                halign="left",

            ),
            MDDialogButtonContainer(
                Widget(),

                MDButton(
                    MDButtonText(text="Ok"),
                    on_release=lambda x: self.dismiss_dialog()
                ),
                spacing="8dp",
            ),
        )
        self.dialog.open()

    def dismiss_dialog(self):
        """Dismiss the active dialog"""
        if self.dialog:
            self.dialog.dismiss()
    def process_login(self):
        store = SecureJsonStore("user_session.json")
        loader_overlay = self.ids.loader_overlay
        username = self.ids.API_KEY.text
        MDApp.get_running_app().API_KEY = username

        if not username:
            loader_overlay.disabled = False
            Clock.schedule_once(lambda dt: self.show_alert("Error", "api key is required!"), 0)
            Clock.schedule_once(lambda dt: setattr(loader_overlay, "opacity", 0), 0)
            return

        url = "https://nexpenz.nexapytechnologies.com/api/login_securely"
        headers = {
            "Authorization": f"Api-Key {username}",
            "Content-Type": "application/json"
        }


        try:
            response = requests.post(url, headers=headers)
            result = response.json()

            if response.status_code == 200:
                print("Successfully logged in")
                session_data = {

                    "api_key": result['api_key'],

                }


                Clock.schedule_once(lambda dt: store.put("session", session_data), 0)

                Clock.schedule_once(lambda dt: setattr(self.manager, "current", "expense"), 2)

            else:
                Clock.schedule_once(lambda dt: self.show_alert("Error", "Invalid API KEY Provided."), 0)

        except Exception:
            Clock.schedule_once(lambda dt: self.show_alert("Error", "Network Error! Check connection."), 0)

        finally:
            loader_overlay.disabled = False
            Clock.schedule_once(lambda dt: setattr(loader_overlay, "opacity", 0), 2)

    # Run API request in a separate thread
    def login_with_api_key(self):
        loader_overlay = self.ids.loader_overlay  # Get the overlay
        loader_overlay.opacity = 1  # Show loading overlay
        loader_overlay.disabled = True
        threading.Thread(target=self.process_login, daemon=True).start()



class SettingsScreen(MDScreen):
    API_URL = "https://nexpenz.nexapytechnologies.com/api/settings"
    def on_pre_enter(self):
        self.API_KEY = MDApp.get_running_app().API_KEY
        """Call this when the screen or app starts."""
        threading.Thread(
            target=self.fetch_currency,
            daemon=True
        ).start()

    def fetch_currency(self):
        headers = {
            "Authorization": f"Api-Key {self.API_KEY}",
            "Content-Type": "application/json"
        }

        try:
            response = requests.get(self.API_URL, headers=headers)

            if response.status_code == 200:
                data = response.json()
                currency = data.get("currency", "NGN")  # Fallback if not present

                # Update the UI on the main thread
                Clock.schedule_once(lambda dt: self.update_currency_ui(currency))

            else:
                print("API Error:", response.status_code)


        except requests.exceptions.RequestException as e:
            print("Network error:", e)


    def update_currency_ui(self, currency):
        manual_symbols = {'NGN': '₦'}
        try:

            if currency == 'NGN':
                self.ids.curency_symbol.text = str(manual_symbols.get(str(currency)))
            else:
                symbol = get_currency_symbol(currency, locale='en')
                self.ids.curency_symbol.text = symbol


        except:
            self.ids.curency_symbol.text = currency
    def on_kv_post(self, base_widget):
        self.menu = None  # Initialize menu reference

    def open_menu(self, caller):
        try:
            # Dismiss any open menu first
            if self.menu:
                self.menu.dismiss()
                self.menu = None

            currency_code = ['NGN', 'USD', 'CAD', 'GBP', 'JPY', 'EUR', 'GBP', 'INR']
            menu_items = [
                    {
                        "text": code,
                        "height": dp(48),
                        "on_release": lambda x=code: self.set_item(x),
                    }

                    for code in currency_code

            ]



            self.menu = MDDropdownMenu(
                caller=caller,
                items=menu_items,
                width_mult=4,
                pos_hint={'right': 1, "top": 1, },
            )
            self.menu.bind(on_dismiss=self.on_menu_dismiss)
            self.menu.open()
        except:
            pass

    def update_currency(self, API_URL,  currency):
        headers = {
            "Authorization": f"Api-Key {self.API_KEY}",
            "Content-Type": "application/json"
        }

        data = {
            "currency": currency
        }

        try:
            response = requests.post(API_URL, json=data, headers=headers)

            if response.status_code == 200:
                print("Currency updated:", response.json())
            else:
                print("Error:", response.status_code, response.json())

        except requests.exceptions.RequestException as e:
            print("Network error:", e)
    def set_item(self, item_text):
        manual_symbols = {
            'NGN': '₦'
        }
        try:
            symbol = get_currency_symbol(item_text, locale='en')
            if item_text == 'NGN':
                self.ids.curency_symbol.text = str(manual_symbols.get(str(item_text)))
                MDApp.get_running_app().currency_symbol = str(manual_symbols.get(str(item_text)))

            else:
                self.ids.curency_symbol.text = symbol
                MDApp.get_running_app().currency_symbol = symbol

            # 🔁 Only change: move update_currency call into a background thread
            threading.Thread(
                target=self.update_currency,
                args=(self.API_URL, item_text),
                daemon=True
            ).start()




        except:
            self.ids.curency_symbol.text = item_text


        if self.menu:
            Clock.schedule_once(lambda dt: self.menu.dismiss(), 0.1)

    def on_menu_dismiss(self, *args):
        # Cleanup so it doesn't reopen
        self.menu = None

    def go_back(self):
        self.manager.transition.direction = 'right'
        self.manager.current = self.manager.current = 'expense'





class ExpenseScreen(MDScreen):

    API_URL = "https://nexpenz.nexapytechnologies.com/api/get_currency"
    amount_text = StringProperty("null")
    balance =0
    total_income = 0
    total_expense = 0

    def format_currency(self, amount):
        try:
            return "{:,.2f}".format(float(amount))
        except (ValueError, TypeError):
            return str(amount)


    def on_enter(self):

        Clock.schedule_once(lambda dt:self.load_monthly_expense_chart_threaded(), timeout=0.1)


    def load_monthly_expense_chart_threaded(self):
        def fetch_and_plot():
            target_month = datetime.now().strftime("%Y-%m")
            headers = {
                "Authorization": f"Api-Key {self.API_KEY}",
                "Content-Type": "application/json"
            }
            try:
                response = requests.get("https://nexpenz.nexapytechnologies.com/api/get_transaction", headers=headers)
                if response.status_code != 200:
                    print("Failed to fetch data:", response.status_code)
                    Clock.schedule_once(lambda dt: self.clear_chart())
                    return

                transactions = response.json()
                expenses = [
                    t for t in transactions
                    if t["type"] == "expense" and t["date"].startswith(target_month)
                ]

                if not expenses:
                    #print("No expense transactions for this month.")
                    Clock.schedule_once(lambda dt: self.clear_chart(),0.1)
                    Clock.schedule_once(lambda dt: self.create_no_data_image(),0.2)
                    return

                category_totals = defaultdict(float)
                for t in expenses:
                    category_totals[t["category"]] += float(t["amount"])

                if not category_totals:
                    print("No categorized expense data.")
                    Clock.schedule_once(lambda dt: self.clear_chart())
                    return

                labels = list(category_totals.keys())
                sizes = list(category_totals.values())
                colors = ['#ffb347', '#4682B4', '#9370DB', '#3CB371', '#FF6347', '#FFD700'][:len(labels)]

                fig, ax = plt.subplots(figsize=(5, 3), dpi=110)
                wedges, _, _ = ax.pie(
                    sizes,
                    colors=colors,
                    startangle=90,
                    autopct='%1.0f%%',
                    wedgeprops={'width': 0.7, 'edgecolor': 'white'},
                    textprops={'color': 'white', 'fontsize': 11}
                )
                ax.axis('equal')
                plt.title("Monthly Spending", fontsize=15, fontweight='bold', loc='left')
                plt.legend(
                    wedges,
                    [f"{label}  {self.format_currency(amount)}" for label, amount in zip(labels, sizes)],
                    loc='center left',
                    bbox_to_anchor=(1, 0.5),
                    fontsize=12
                )

                buf = BytesIO()
                plt.tight_layout()
                plt.savefig(buf, format='png')
                plt.close(fig)
                buf.seek(0)

                image = CoreImage(buf, ext='png')

                # Schedule the GUI update on the main thread
                Clock.schedule_once(lambda dt: self.update_chart_texture(image.texture))

            except Exception as e:
                print("Error loading chart:", e)
                Clock.schedule_once(lambda dt: self.clear_chart())
                Clock.schedule_once(lambda dt: self.create_no_data_image())

        threading.Thread(target=fetch_and_plot).start()

    def update_chart_texture(self, texture):

        self.ids.chart_image.texture = texture

    def clear_chart(self):
        self.ids.chart_image.texture = None

    def create_no_data_image(self):
        fig, ax = plt.subplots(figsize=(5, 3), dpi=110)
        ax.text(0.5, 0.5, "No chart to display", fontsize=20, color='gray',
                ha='center', va='center', alpha=0.7)
        ax.axis('off')  # Hide axes

        buf = BytesIO()
        plt.title("Monthly Spending", fontsize=15, fontweight='bold', loc='left')
        plt.tight_layout()

        plt.savefig(buf, format='png', bbox_inches='tight')
        plt.close(fig)
        buf.seek(0)
        image = CoreImage(buf, ext='png')
        Clock.schedule_once(lambda dt: self.update_chart_texture(image.texture))

    def fetch_total_balance(self):
        headers = {
            "Authorization": f"Api-Key {self.API_KEY}",
            "Content-Type": "application/json"
        }

        try:
            response = requests.get("https://nexpenz.nexapytechnologies.com/api/get_balance", headers=headers)
            if response.status_code == 200:
                data = response.json()
                all_total_expense = data.get("total_expense", 0)
                all_total_income = data.get("total_income", 0)
                all_total_balance = data.get("total_balance", 0)

                self.total_expense =  self.format_currency(all_total_expense)
                self.total_income = self.format_currency(all_total_income)
                self.balance = self.format_currency(all_total_balance)




            else:
                print("API Error:", response.status_code)
        except Exception as e:
            print("Network error:", e)


    def on_kv_post(self, base_widget):
        self.menu = None  # Initialize menu reference

    def on_pre_enter(self, *args):
        self.API_KEY = MDApp.get_running_app().API_KEY
        threading.Thread(
            target=self.fetch_dashboard_currency,
            daemon=True
        ).start()


    def fetch_dashboard_currency(self, currency='₦'):
        headers = {
            "Authorization": f"Api-Key {self.API_KEY}",
            "Content-Type": "application/json"
        }

        try:

            response = requests.get(self.API_URL, headers=headers)

            if response.status_code == 200:
                data = response.json()
                currency = data.get("currency", "NGN")  # Fallback if not present

                # Update the UI on the main thread
                self.fetch_total_balance()



            else:
                print("API Error:", response.status_code)


        except requests.exceptions.RequestException as e:
            print("Network error:", e)
        finally:
            Clock.schedule_once(lambda dt: self.update_currency_ui(currency),0)

    def update_currency_ui(self, currency):
        manual_symbols = {'NGN': '₦'}
        try:

            if currency == 'NGN':
                symbol = str(manual_symbols.get(str(currency)))
                self.ids.amount_label.text = f"{symbol} {self.amount}" or '0'
                self.ids.total_income.text =  f"{symbol} {self.total_income}" or '0'
                self.ids.total_expense.text = f"{symbol} {self.total_expense}"  or '0'
                self.manager.get_screen('addtransaction').currency = f"{symbol}"  or '0'
            else:
                symbol = get_currency_symbol(currency, locale='en')
                self.ids.amount_label.text = f"{symbol} {self.balance}"  or '0'
                self.ids.total_income.text = f"{symbol} {self.total_income}"  or '0'
                self.ids.total_expense.text = f"{symbol} {self.total_expense}"  or '0'
                self.manager.get_screen('addtransaction').currency= f"{symbol}"  or '0'

        except:
            symbol = str(manual_symbols.get(str(currency)))
            self.ids.amount_label.text = f"{symbol} {self.balance}"  or '0'
            self.ids.total_income.text = f"{symbol} {self.total_income}"  or '0'
            self.ids.total_expense.text = f"{symbol} {self.total_expense}"  or '0'
            self.manager.get_screen('addtransaction').currency = f"{symbol}"  or '0'



    def open_menu(self, caller):
        # Dismiss any open menu first
        if self.menu:
            self.menu.dismiss()
            self.menu = None

        menu_items = [
            {
                "text": item,
                "height": dp(48),
                "on_release": lambda x=item: self.set_item(x),
            }
            for item in ["Add Transaction", "Transactions", "Settings"]
        ]

        self.menu = MDDropdownMenu(
            caller=caller,
            items=menu_items,
            width_mult=4,
            pos_hint={'right':1, "top": 1,},
        )
        self.menu.bind(on_dismiss=self.on_menu_dismiss)
        self.menu.open()

    def set_item(self, item_text):
        if self.menu:
            Clock.schedule_once(lambda dt: self.menu.dismiss(), 0.1)

        screen_map = {
            "Add Transaction": "addtransaction",
            "Transactions": "transactions",
            "Settings": "settings",
        }
        screen_name = screen_map.get(item_text)
        if screen_name:
            self.manager.transition.direction = 'left'

            self.manager.current = screen_name

    def on_menu_dismiss(self, *args):
        self.menu = None

    def go_back(self):
        self.manager.transition.direction = 'right'
        self.manager.current  = 'expense'

    def transaction_screen(self):
        self.manager.transition.direction = 'up'
        self.manager.current  = 'addtransaction'
class AddTransaction(MDScreen):
    selected_category = StringProperty("")
    def on_pre_enter(self, *args):
        self.API_KEY = MDApp.get_running_app().API_KEY
    def show_alert(self, title, message):
        self.dialog = MDDialog(
            MDDialogHeadlineText(
                text=title,
                halign="left",
            ),
            MDDialogSupportingText(
                text=message,
                halign="left",

            ),
            MDDialogButtonContainer(
                Widget(),

                MDButton(
                    MDButtonText(text="Ok"),
                    on_release=lambda x: self.dismiss_dialog()
                ),
                spacing="8dp",
            ),
        )
        self.dialog.open()

    def format_on_unfocus(self, textinput):
        # Remove spaces and non-numeric characters except dot and minus
        clean_input = re.sub(r"[^0-9,.]", "", textinput.text)

        # Format the cleaned input
        formatted = self.format_currency(clean_input)
        textinput.text = formatted

    def format_currency(self, amount):
        try:
            if amount in ("", "-", ".", "-.", ".0"):
                return amount

            # Convert to float and format
            num = float(str(amount).replace(",", ""))
            return "{:,.2f}".format(num)
        except (ValueError, TypeError):
            return ""

    def dismiss_dialog(self):
        """Dismiss the active dialog"""
        if self.dialog:
            self.dialog.dismiss()

    def loader_overlay(self, dt):
        loader_overlay = self.ids.loader_overlay  # Get the overlay
        loader_overlay.opacity = 1  # Show loading overlay
        loader_overlay.disabled = True

    def remove_loader(self, dt):
        loader_overlay = self.ids.loader_overlay  # Get the overlay
        self.ids.loader_overlay.opacity = 0
        self.ids.loader_overlay.disabled = False
    currency = StringProperty()
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.date_dialog = None  # Store picker once
        self.end_date_dialog = None


    def on_kv_post(self, base_widget):
        self.menu = None  # No menu yet


    def open_menu(self):
        # Fully destroy the old menu first
        if self.menu:
            self.menu.dismiss()
            self.menu = None  # Important: reset reference

        menu_items = [
            {
                "text": item,
                "height": dp(48),
                "on_release": lambda x=item: self.set_item(x),
            }
            for item in ["Food", "Bills", "Travel", "Others"]
        ]

        self.menu = MDDropdownMenu(
            caller=self.ids.category_field,
            items=menu_items,
            pos_hint={"right": 0.98},
        )

        self.menu.bind(on_dismiss=self.on_menu_dismiss)
        self.menu.open()

    def set_item(self, item_text):
        self.ids.category_field.text = item_text
        if self.menu:
            Clock.schedule_once(lambda dt: self.menu.dismiss(), 0.1)

    def on_menu_dismiss(self, *args):
        # Cleanup so it doesn't reopen
        self.menu = None


    def show_modal_date_picker(self):

            # Only create the picker once
            if not self.date_dialog:
                max_date = date.today()
                self.date_dialog = MDModalDatePicker(
                    min_date=date(2025, 1, 1,),
                    max_date=max_date,
                )
                self.date_dialog.bind(on_ok=self.on_date_selected)

            self.date_dialog.open()
    def on_date_selected(self, instance_date_picker):
        selected_date = instance_date_picker.get_date()[0]
        self.ids.date_field.text = str(selected_date)

        # Reset the dialog so it can be recreated safely later if needed
        self.date_dialog.dismiss()
        self.date_dialog = None  # optional: recreate next time

    def Category(self, name, is_active):
        self.ids.category_field.disabled= True
        self.ids.category_field.text = ''
        if is_active:
            self.selected_category = name

    def expense_category(self, name, is_active):
        self.ids.category_field.disabled = False
        if is_active:
            self.selected_category = name

    def remove_spaces(self, textfield):
        #textfield.text = textfield.text.replace(" ", "")  # Remove spaces
        if len(textfield.text) > 20:
            textfield.text = textfield.text[:20]  # Trim excess characters

    #----------------------add api authentication----------------------------------
    API_URL = "https://nexpenz.nexapytechnologies.com/api/add_transaction"  # Replace with your actual backend URL

    def clear_fields(self, dt):
        self.ids.amount.text = ""
        self.ids.note.text = ""
        self.ids.date_field.text = ""
        self.selected_category = ""
        self.ids.check_active.active = False
        self.ids.income_check_active.active = False

        self.ids.category_field.text =''

    def prepare_number_for_api(self, amount_str):
        # Remove commas before converting to float or sending
        cleaned = amount_str.replace(",", "")
        return float(cleaned)
    def submit_transaction(self):
        amount_text = self.prepare_number_for_api((self.ids.amount.text.strip()))
        transaction_type = self.selected_category  # example: 'income' or 'expense'
        date_text = self.ids.date_field.text.strip()
        note_text = self.ids.note.text.strip()
        category = self.ids.category_field.text.strip()



        try:
            amount = amount_text
            if amount <= 0:
                return
        except:
            return

        if not date_text or not note_text or not transaction_type:
            return


        Clock.schedule_once(self.loader_overlay, 0)
        headers = {
            "Authorization": f"Api-Key {self.API_KEY}",
            "Content-Type": "application/json"
        }

        data = {
            "amount": amount_text,
            "category": category,
            "type": transaction_type,
            "date": date_text,  # Format: YYYY-MM-DD
            "note": note_text
        }


        try:
            response = requests.post(self.API_URL, json=data, headers=headers)

            if response.status_code == 200:
                Clock.schedule_once(self.remove_loader, 1)
                Clock.schedule_once(self.clear_fields, 1)
                Clock.schedule_once(lambda dt: self.show_alert("Transaction", "Transaction added successfully!"), 1)
                #print("Transaction saved:", response.json())
            else:
                Clock.schedule_once(lambda dt: self.show_alert("FailedTransaction", str(response.json())), 1)

                print("Failed:", response.status_code, str(response.json()))
                Clock.schedule_once(self.remove_loader, 0)

        except requests.exceptions.RequestException as e:
            Clock.schedule_once(self.remove_loader, 0)
            print("Network error:", e)
            Clock.schedule_once(lambda dt: self.show_alert("FailedTransaction", str(e)), 1)

    def save_transaction(self):
        threading.Thread(target=self.submit_transaction, daemon=True).start()
    def go_back(self):
        self.manager.transition.direction = 'right'
        self.manager.current = self.manager.current = 'expense'



class Transactions(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.date_dialog = None  # Store picker once
        self.end_date_dialog = None

    API_URL = "https://nexpenz.nexapytechnologies.com/api/get_currency"

    def format_currency(self, amount):
        try:
            return "{:,.2f}".format(float(amount))
        except (ValueError, TypeError):
            return str(amount)

    def open_date_filter(self):
        self.filter_view = Factory.FilterDate()

        def slide_up(view):
            content = self.filter_view.ids.filter_boxlayout
            #content.y = -content.height


            #  Bind the icon button properly
            self.filter_view.ids.start_icon.on_release = self.show_modal_date_picker
            self.filter_view.ids.end_icon.on_release = self.show_modal_date_picker_end
            self.filter_view.ids.confirm_btn.on_release = self.on_confirm_date_filter


            import time
            anim = Animation(y=0, d=0.3, t='out_quad')
            anim.start(content)





        self.filter_view.bind(on_open=slide_up)
        self.filter_view.open()

    def stop_loader(self, *args):
        self.ids.loader_overlay.opacity = 0
        self.ids.loader_overlay.disabled = False

    def go_back(self):
        self.manager.transition.direction = 'right'
        self.manager.current = self.manager.current = 'expense'

    def fetch_transactions(self, limit=20, data=None):
        headers = {
            "Authorization": f"Api-Key {self.API_KEY}",
            "Content-Type": "application/json"
        }
        url = f"https://nexpenz.nexapytechnologies.com/api/get_transaction?limit={limit}"

        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
             data = response.json()
                # data is a list of transactions sorted by date desc


            else:
                print("API Error:", response.json())
        except requests.exceptions.RequestException as e:
            data = None
            print("Network error:", e)
        finally:
            Clock.schedule_once(lambda dt: self.stop_loader(), 2)
            Clock.schedule_once(lambda dt: self.update_transactions_ui(data), 2)





    def update_transactions_ui(self, transactions=None):

            symbol = MDApp.get_running_app().currency_symbol
            transaction_list = self.ids.transaction_list
            transaction_list.clear_widgets()
            if transactions:
                for transaction in transactions:

                    # Create a widget or list item for each transaction
                    # Example assuming you have a TransactionItem widget
                    item = {
                        "date": transaction['date'],
                        "amount": self.format_currency(transaction['amount']),
                        "type": transaction['type'],
                        "note": transaction.get('note', '')
                    }

                    if item["type"] == "income":
                        widget = Factory.MySalary()
                        widget.ids.income_text.text = item["note"]
                        widget.ids.income_amount.text = f"+ {symbol}{item['amount']}"
                        widget.ids.income_date.text = item["date"]
                    else:
                        widget = Factory.MyCategory()
                        widget.ids.expense_text.text = item["note"]
                        widget.ids.expense_amount.text = f"- {symbol}{item['amount']}"
                        widget.ids.expense_date.text = item["date"]

                    transaction_list.add_widget(widget)


    def load_transactions(self):
        threading.Thread(target=self.fetch_transactions, daemon=True).start()
    def on_pre_enter(self, *args):
        self.API_KEY = MDApp.get_running_app().API_KEY
        self.ids.loader_overlay.opacity = 1
        self.ids.loader_overlay.disabled = True  # Allow interaction with overlay if needed
        self.load_transactions()

    def show_modal_date_picker(self):

        # Only create the picker once
        if not self.date_dialog:
            max_date = date.today()
            self.date_dialog = MDModalDatePicker(
                min_date=date(2025, 1, 1, ),
                max_date=max_date,
            )
            self.date_dialog.bind(on_ok=self.on_date_selected)

        self.date_dialog.open()

    def on_date_selected(self, instance_date_picker):
        selected_date = instance_date_picker.get_date()[0]
        self.filter_view.ids.start_date_input.text = str(selected_date)

        # Reset the dialog so it can be recreated safely later if needed
        self.date_dialog.dismiss()
        self.date_dialog = None  # optional: recreate next time

    def show_modal_date_picker_end(self):
        # Only create the picker once
        if not self.end_date_dialog:
            max_date = date.today()
            self.end_date_dialog = MDModalDatePicker(
                min_date=date(2025, 1, 1, ),
                max_date=max_date,
            )
            self.end_date_dialog.bind(on_ok=self.on_date_selected_end)


        self.end_date_dialog.open()

    def on_date_selected_end(self, instance_date_picker):
        selected_date = instance_date_picker.get_date()[0]
        self.filter_view.ids.end_input_date.text = str(selected_date)

        # Reset the dialog so it can be recreated safely later if needed
        self.end_date_dialog.dismiss()
        self.end_date_dialog = None  # optional: recreate next time

    def on_confirm_date_filter(self):
        start_date = self.filter_view.ids.start_date_input.text
        end_date = self.filter_view.ids.end_input_date.text
        self.ids.loader_overlay.opacity = 1
        self.ids.loader_overlay.disabled = True
        self.filter_view.dismiss()


        headers = {
            "Authorization": f"Api-Key {self.API_KEY}",
            "Content-Type": "application/json"
        }

        url = (
            f"https://nexpenz.nexapytechnologies.com/api/filter_by_date_transaction?"
            f"start={start_date}&end={end_date}"
        )



        def fetch_filtered_transactions(data=None):
            try:

                    response = requests.get(url, headers=headers)
                    if response.status_code == 200:
                        data = response.json()
                        self.filter_view.dismiss()
                        # Update your UI

                        #Clock.schedule_once(lambda dt: self.stop_date_filter, 0.2)



                    else:
                        print("Error fetching filtered transactions:", response.status_code)
            except Exception as e:
              print("Network error:", e)
            finally:
                Clock.schedule_once(lambda dt: self.stop_loader(), 0.9)
                Clock.schedule_once(lambda dt: self.update_transactions_ui(data), 1)







        threading.Thread(target=fetch_filtered_transactions, daemon=True).start()


class MyApp(MDApp):
    API_KEY  =  StringProperty('')
    API_URL = "https://nexpenz.nexapytechnologies.com/api/get_currency"
    currency_symbol = StringProperty('')
    def build(self):

        kv = Builder.load_file('expense.kv')

        return kv


    def check_session(self):
        store = SecureJsonStore("user_session.json")

        session_data = store.get("session")
        if session_data:
            api_key = (session_data["api_key"])
            if api_key:
                self.API_KEY = api_key
                print("? Auto-login: Session is still valid")
                self.root.transition = NoTransition()
                self.root.current = "expense"

        else:
            self.root.transition = NoTransition()
            self.root.current = "login"


    def on_start(self):
        self.check_session()
        threading.Thread(
            target=self.fetch_currency,
            daemon=True
        ).start()

    def fetch_currency(self, currency ='₦'):

        headers = {
            "Authorization": f"Api-Key {self.API_KEY}",
            "Content-Type": "application/json"
        }

        try:
            response = requests.get(self.API_URL, headers=headers)

            if response.status_code == 200:
                data = response.json()
                currency = data.get("currency", "NGN")  # Fallback if not present

                # Update the UI on the main thread


            else:
                print("API Error:", response.status_code)


        except requests.exceptions.RequestException as e:
            print("Network error:", e)
        finally:
            Clock.schedule_once(lambda dt: self.update_currency_ui(currency))

    def update_currency_ui(self, currency):
        manual_symbols = {'NGN': '₦'}
        try:

            if currency == 'NGN':
                self.currency_symbol  = str(manual_symbols.get(str(currency)))
            else:
                symbol = get_currency_symbol(currency, locale='en')
                self.currency_symbol  = symbol


        except:
            self.currency_symbol  = currency


if __name__ == "__main__":
    MyApp().run()
