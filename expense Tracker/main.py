
from kivy.config import Config
from kivy.utils import get_color_from_hex as hex_color
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
from kivymd.uix.button import MDFabButton
from kivy.metrics import dp
from kivy.utils import get_color_from_hex as hex_colors
from kivy.storage.jsonstore import JsonStore
from kivymd.uix.pickers import MDModalDatePicker

import uuid
from datetime import date, timedelta, datetime
from kivy.clock import Clock
from kivy.uix.scrollview import ScrollView
from kivymd.uix.menu import MDDropdownMenu
class SettingsScreen(MDScreen):
    def go_back(self):
        self.manager.transition.direction = 'right'
        self.manager.current = self.manager.current = 'expense'



class ExpenseScreen(MDScreen):
    def on_kv_post(self, base_widget):
        self.menu = None  # Initialize menu reference

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
        self.manager.current = self.manager.current = 'expense'


class AddTransaction(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.date_dialog = None  # Store picker once

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

    def go_back(self):
        self.manager.transition.direction = 'right'
        self.manager.current = self.manager.current = 'expense'



class Transactions(MDScreen):
    def on_enter(self):
        self.ids.loader_overlay.opacity = 1
        self.ids.loader_overlay.disabled = True  # Allow interaction with overlay if needed
        Clock.schedule_once(self.stop_loader, 1.5)  # simulate loading delay

    def stop_loader(self, *args):
        self.ids.loader_overlay.opacity = 0
        self.ids.loader_overlay.disabled = False

    def go_back(self):
        self.manager.transition.direction = 'right'
        self.manager.current = self.manager.current = 'expense'


class MyApp(MDApp):
    def build(self):

        kv = Builder.load_file('expense.kv')
        return kv



if __name__ == "__main__":
    MyApp().run()
