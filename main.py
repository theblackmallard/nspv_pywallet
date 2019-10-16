#!/usr/bin/env python3
# komodod -nSPV=1 -ac_reward=100000000  -ac_name=NSPV -ac_supply=10000000000 -ac_cc=2 -addressindex=1 -spentindex=1 -connect=5.9.102.210 &
# ./komodod -nSPV=1 -addnode=5.9.253.195 &

import platform, os
from tkinter import ttk
import ttkthemes as tkT
import tkinter as tk
from tkinter import PhotoImage
from lib import nspvwallet
import sys, subprocess, time, csv, json
from slickrpc import Proxy
import requests
from fake_useragent import UserAgent

if 'lib' in os.listdir(os.curdir):
    libPath = (os.getcwd()+'\lib')
    with open('{}\wallet_build.json'.format(libPath)) as json_file:
        data = json.load(json_file)
        icon = data['Icon_logo'] # ex: "lib/kmd.png"
        pngLogo = data['Main_logo'] # ex:  'lib/KMD_Horiz_Dark.png'
        coin = data['Coin'] # ex:  'KMD-komodo'
        appTitle = data['App_title'] # ex: "Komodo nSPV pywallet"
else:
    print('lib path not found')
    sys.exit()


# daemon initialization
try:
    ac_name = sys.argv[1]
    rpc_proxy = nspvwallet.def_credentials(ac_name)
except IndexError:
    print("Please use chain ticker as first start argument. For example: ./main.py KMD")
    sys.exit()

# checking if daemon connected
connect_attempts_counter = 0
while True:
    if connect_attempts_counter < 5:
        connect_attempts_counter += 1
        try:
            get_info_output = rpc_proxy.nspv_getinfo()
            print("nspv_getinfo")
            print(get_info_output)
            if "nSPV" in get_info_output and get_info_output["nSPV"] == "superlite":
                print(sys.argv[1] + " daemon is running. Welcome to nSPV pywallet!")
                break
            else:
                print("Please restart " + sys.argv[1] + " daemon in nSPV client mode (-nSPV=1 param)")
                sys.exit()
        except Exception as e:
            print(e)
            print(sys.argv[1] +" daemon is not started! Lets try to start")
            # TODO: have to parse json with params
            if sys.argv[1] == "KMD":
                subprocess.call(['./komodod', '-nSPV=1', '-connect=23.254.165.16', '-listen=0', '-daemon'])
                time.sleep(1)
            elif sys.argv[1] == "ILN":
                subprocess.call(['./komodod', '-ac_name=ILN', '-ac_supply=10000000000', '-ac_cc=2', '-nSPV=1',
                                 '-connect=5.9.102.210', '-listen=0', '-daemon'])
                time.sleep(1)
            else:
                print("I don't know params for this chain. Exiting")
                sys.exit()
    else:
        print("daemon for " + sys.argv[1] + " not started and can't start it. Exiting.")
        sys.exit()

# main window
root = tkT.ThemedTk()
root.title(appTitle)
root.resizable(False, False)
addressBook = {}
ua = UserAgent()
currency_symbols = {'BTC':'₿','USD':'$','EUR':'€','KRW':'₩','GBP':'£','CAD':'$',
                    'JPY':'¥','RUB':'₽','AUD':'$','CNY':'¥','INR':'₹'}

# Styling and Functions
style = ttk.Style()


class StyleTheme:
    def equilux(self):
        root.set_theme('equilux', background=True)
        style.map("TButton", background=[('pressed', 'darkslategray4')])
    def black(self):
        root.set_theme('black', background=True)
        style.map("TButton", background=[('pressed', 'darkslategray4')])
    def radiance(self):
        root.set_theme('radiance', background=True)
        style.map("TButton", background=[('pressed', 'orange red')])
    def scidGreen(self):
        root.set_theme('scidgreen', background=True)
        style.map("TButton", background=[('pressed', 'green2')])
    def arc(self):
        root.set_theme('arc', background=True)
        style.map("TButton", background=[('pressed', 'purple1')])
    def kroc(self):
        root.set_theme('kroc', background=True)
        style.map("TButton", background=[('pressed', 'gray15')])

        
def save_style():
    style_pack = {}
    style_pack['default_style_choice'] = style.theme_use()
    style_pack['default_tor'] = default_tor
    style_pack['default_tor_port'] = default_tor_port
    style_pack['default_price_request'] = default_price_request
    style_pack['default_currency'] = default_currency
    with open('lib/style_choice.txt', 'w') as text_file:
        json.dump(style_pack, text_file)

        
def check_style():
    global default_tor, default_tor_port, default_price_request, default_currency
    try:
        with open('lib/style_choice.txt') as json_file:
            data = json.load(json_file)
            style_choice = data['default_style_choice']
            default_tor = data['default_tor']
            default_price_request = data['default_price_request']
            default_currency = data['default_currency']
            default_tor_port = data['default_tor_port']
            root.set_theme(style_choice, background=True)
            style.map("TButton", background=[('pressed', 'purple1')])
            if default_tor == 0:
                running_tor.configure(text='Running Tor...  ')
            return default_tor, default_price_request, default_currency, style_choice
    except:
        root.set_theme('equilux', background=True)
        default_tor = 1
        default_price_request = 1
        default_currency = 'USD'
        default_tor_port = 9150
        style_choice = 'equilux'
        return default_tor, default_tor_port, default_price_request, default_currency, style_choice

# Icon
root.iconphoto(True, PhotoImage(file=icon))

# Logo
img = PhotoImage(file=pngLogo).subsample(3,3)
lbl_img = ttk.Label(root, image=img)

# Tabbed Notebook
nb = ttk.Notebook(root)
tab1 = ttk.Frame(nb)
tab2 = ttk.Frame(nb)
tab3 = ttk.Frame(nb)
tab4 = ttk.Frame(nb)
nb.add(tab1, text='Interaction Info')
nb.add(tab2, text='New Wallet Info')
nb.add(tab3, text='Transaction History')
nb.add(tab4, text='Address Book')
nb.grid(row=3, column=0, rowspan=3, columnspan=2, sticky='NEWS', padx=(10,10), pady=(5,5))


# widgets creation
wallet_interact_messages = tk.Text(tab1, height=8, width=85, bg='gray22')
wallet_create_messages = tk.Text(tab2, height=8, width=85, bg='gray22')
transaction_history_messages = tk.Text(tab3, height=8, width=85, bg='gray22')
address_book_messages = ttk.Treeview(tab4, columns=('Name', 'Address'), show='headings', height=5)

get_new_address_button = ttk.Button(root, text="Get new address")
nspv_login_button = ttk.Button(root, text="Login")
nspv_logout_button = ttk.Button(root, text="Logout")
refresh_button = ttk.Button(root, text="Refresh")

# prices
price_text = ttk.Label(root, width=50)
price_change_text = ttk.Label(root, width=50)


wif_input = ttk.Entry(root, width=50)
nspv_login_text = ttk.Label(root, text="Input WIF to login:")
nspv_spend_text = ttk.Label(root, text="Send to address:")
amount_text = ttk.Label(root, text="Amount:")
amount_input = ttk.Entry(root, width=50)
nspv_spend_button = ttk.Button(root, text="Send")
address_input = ttk.Entry(root, width=50)
current_address_text = ttk.Label(root, text="Address: please login first!")
current_balance_text = ttk.Label(root, text="Balance: please login first!")
current_balance_fiat = ttk.Label(root, text="")
running_tor = ttk.Label(root, text="")
logout_timer_text = ttk.Label(root, text="Logout in: please login first!")

# buttons bindings
def get_new_address(event):
    new_address_info = rpc_proxy.getnewaddress()
    print("getnewaddress")
    print(new_address_info)
    new_address_info_string = "wif: " + new_address_info["wif"] + "\n" \
                              + "address: " + new_address_info["address"] + "\n" \
                              + "pubkey: " + new_address_info["pubkey"] + "\n"
    wallet_create_messages.replace('1.0', '100.0', new_address_info_string)


def nspv_login(event):
    login_info = rpc_proxy.nspv_login(wif_input.get())
    print("nspv_login " + wif_input.get())
    print(login_info)
    wallet_interact_messages.replace('1.0', '100.0', login_info)
    current_address_text["text"] = "Address: " + login_info["address"]
    listunspent_output = rpc_proxy.nspv_listunspent(login_info["address"])
    print(listunspent_output)
    if "error" in listunspent_output and listunspent_output["error"] == "no utxos result":
        current_balance_text["text"] = "Balance: 0 " + ac_name
    else:
        if len(listunspent_output["utxos"]) < 10:
            for utxo in listunspent_output["utxos"]:
                print(utxo)
                rpc_proxy.nspv_txproof(utxo["txid"], str(utxo["height"]))
        current_balance_text["text"] = "Balance: " + str(listunspent_output["balance"]) + " " + ac_name
    logout_timer_text["text"] = "Logout in: " + str(rpc_proxy.nspv_getinfo()["wifexpires"]) + " seconds"


def nspv_logout(event):
    logout_info = rpc_proxy.nspv_logout()
    print("nspv_logout")
    print(logout_info)
    wallet_interact_messages.replace('1.0', '100.0', logout_info)
    current_address_text["text"] = "Address: please login first!"
    current_balance_text["text"] = "Balance: please login first!"
    logout_timer_text["text"] = "Logout in: please login first!"


def nspv_send_tx(event):
    nspv_spend_output = rpc_proxy.nspv_spend(str(address_input.get()), str(amount_input.get()))
    print("nspv_spend " + str(address_input.get() + " "  + str(amount_input.get())))
    print(nspv_spend_output)
    if "vout" in nspv_spend_output:
        confirmation_popup(nspv_spend_output)
    else:
        wallet_interact_messages.replace('1.0', '100.0', nspv_spend_output)


def refresh(event):
    get_price(price_text.cget('text')[-3:])
    current_address = current_address_text["text"][-34:]
    listunspent_output = rpc_proxy.nspv_listunspent(current_address)
    print("nspv_listunspent " + current_address)
    print(listunspent_output)
    nspv_getinfo_output = rpc_proxy.nspv_getinfo()
    print("nspv_getinfo")
    print(nspv_getinfo_output)
    main_address_book()
    transaction_history_messages.replace('1.0', '100.0', 'Need to add tx history RPC')
    if "wifexpires" in nspv_getinfo_output:
        logout_timer_text["text"] = "Logout in: " + str(rpc_proxy.nspv_getinfo()["wifexpires"]) + " seconds"
        if "error" in listunspent_output and listunspent_output["error"] == "no utxos result":
            current_balance_text["text"] = "Balance: 0 " + ac_name
        else:
            try:
                current_balance_text["text"] = "Balance: " + str(listunspent_output["balance"]) + " " + ac_name
            except KeyError:
                current_balance_text["text"] = "Balance: 0 " + ac_name
    else:
        current_address_text["text"] = "Address: please login first!"
        current_balance_text["text"] = "Balance: please login first!"
        logout_timer_text["text"] = "Logout in: please login first!"


def confirm_broadcasting(spend_output, popup_window):
    try:
        nspv_broadcast_output = rpc_proxy.nspv_broadcast(spend_output["hex"])
        print("nspv_broadcast " + spend_output["hex"])
        print(nspv_broadcast_output)
        wallet_interact_messages.replace('1.0', '100.0', nspv_broadcast_output)
    except Exception as e:
        wallet_interact_messages.replace('1.0', '100.0', spend_output)
    finally:
        refresh("test")
        popup_window.destroy()


def confirmation_popup(spend_output):
    popup = ttk.Tk()
    popup.iconbitmap(ico)
    popup.wm_title("Please confirm your transaction")
    label = ttk.Label(popup, text="You're about to spend: " + str(spend_output["vout"][0]["value"]) + " " + ac_name)
    label2 = ttk.Label(popup, text="Destination address: " + str(spend_output["vout"][0]["scriptPubKey"]["addresses"][0]))
    label3 = ttk.Label(popup, text="Input txid: " + str(spend_output["vin"][0]["txid"]))
    if spend_output["retcodes"][0] == 0:
        label4 = ttk.Label(popup, text="Input notarized")
    else:
        label4 = ttk.Label(popup, text="Input NOT notarized")
    label5 = ttk.Label(popup, text="Tx fee: 0.0001 " + ac_name)
    label6 = ttk.Label(popup, text="Rewards: " + str(spend_output["rewards"]) + " " + ac_name)
    label.pack(side="top", fill="x", pady=10)
    label2.pack(side="top", fill="x", pady=10)
    label3.pack(side="top", fill="x", pady=10)
    label4.pack(side="top", fill="x", pady=10)
    label5.pack(side="top", fill="x", pady=10)
    label6.pack(side="top", fill="x", pady=10)
    button1 = ttk.Button(popup, text="Confirm", command=lambda: confirm_broadcasting(spend_output, popup))
    button2 = ttk.Button(popup, text="Cancel", command=popup.destroy)
    button1.pack()
    button2.pack()
    popup.mainloop()


def custom_paste(event):
    try:
        event.widget.delete("sel.first", "sel.last")
    except:
        pass
    event.widget.insert("insert", event.widget.clipboard_get())
    return "break"

def transaction_info(event):
    message = 'Need to get tx history from RPC'
    transaction_history_messages.replace('1.0', '100.0', message)

# Address Book
def address_book_popup():
    popup = tkT.ThemedTk()
    popup_style = ttk.Style()
    popup_style.map("TButton", background=[('pressed', 'purple1')])
    popup.set_theme('{}'.format(style.theme_use()), background=True)
    popup.iconbitmap(ico)
    popup.wm_title("Edit Your Address Book")
    label = ttk.Label(popup, text="Edit your Address Book by adding or deleting a contact below")
    label.pack(side="top", fill="x", pady=10, padx=10)

    popup_tree = ttk.Treeview(popup, columns=('Name', 'Address'), show='headings')
    popup_tree.heading('#1', text='Name')
    popup_tree.heading('#2', text='Address')
    for name in addressBook.items():
        popup_tree.insert('', 'end', values=[(name[0]), (name[1])])
    popup_tree.pack(padx=10)

    label2 = ttk.Label(popup, text="Contact Name: ")
    label2.pack()
    name = ttk.Entry(popup, width=50)
    name.pack()
    label3 = ttk.Label(popup, text="Contact Address: ")
    label3.pack()
    address = ttk.Entry(popup, width=50)
    address.pack()

    def select_item(event):
        name.delete(0, 'end')
        address.delete(0, 'end')
        try:
            curItem = popup_tree.focus()
            curName = popup_tree.item(curItem)['values'][0]
            curAddress = popup_tree.item(curItem)['values'][1]
            name.insert(0, curName)
            address.insert(0, curAddress)
        except:
            pass

    def reload_book():
        popup_tree.delete(*popup_tree.get_children())
        for name in addressBook.items():
            popup_tree.insert('', 'end', values=[(name[0]), (name[1])])

    button1 = ttk.Button(popup, text="Add Contact", command=lambda: add_address_book(name.get(), address.get()))
    button2 = ttk.Button(popup, text="Delete Contact", command=lambda: delete_address_book_entry(name.get()))
    button3 = ttk.Button(popup, text="Refresh", command=reload_book)
    button4 = ttk.Button(popup, text="Exit", command=popup.destroy)
    popup_tree.bind('<ButtonRelease-1>', select_item)
    button1.pack(anchor='n')
    button2.pack(anchor='n')
    button3.pack(anchor='n')
    button4.pack(anchor='se')

    popup.mainloop()

    
# loads address book into Dictionary
def load_address_book():
    try:
        with open('lib/address_book.csv', 'r') as csvAddresses:
            read = csv.reader(csvAddresses)
            for row in read:
                new = list(row)
                name = str(new[0])
                address = str(new[1])
                addressBook[name] = address
                main_address_book()
    except:
        print("Could not open address book")

        
# adds entry to address book
def add_address_book(name, address):
    load_address_book()
    if name not in addressBook:
        add_name = str(name)
        add_address = str(address)
        addressBook[add_name] = add_address
        save_address_book(addressBook)
    else:
        print('{} is already in address book, please use different name'.format(name))

        
# saves address book to CSV
def save_address_book(addressBook):
    with open('lib/address_book.csv', 'w') as f:
        writer = csv.writer(f, delimiter=',', lineterminator='\n')
        for name in addressBook.items():
            entry = [name[0], name[1]]
            writer.writerow(entry)
            load_address_book()  # reloads address book

            
# delete entry from address book
def delete_address_book_entry(name):
    if name in addressBook:
        delete_name = str(name)
        addressBook.pop(delete_name)
        save_address_book(addressBook)
    else:
        print('{} was not found in address book'.format(name))

        
# fills 'send to address' with click from address book
def select_item_book(event):
    address_input.delete(0, 'end')
    curItem = address_book_messages.focus()
    curAddress = address_book_messages.item(curItem)['values'][1]
    address_input.insert(0, curAddress)

    
# updates address book on main page
def main_address_book():
    address_book_messages.delete(*address_book_messages.get_children())
    address_book_messages.heading('#1', text='Name')
    address_book_messages.column('#1', width=350)
    address_book_messages.heading('#2', text='Address')
    address_book_messages.column('#2', width=350)
    for name in addressBook.items():
        address_book_messages.insert('', 'end', values=[(name[0]), (name[1])])

        
# Price information
def get_price(fiat):
    default_currency = fiat
    if default_price_request == 0:
        print('updating prices...')
        url = 'https://api.coinpaprika.com/v1/tickers/{0}?quotes={1}'.format(coin, fiat)
        useragent = {'User-Agent': ua.random}
        if default_tor == 0:
            try:
                session = requests.session()
                session.proxies = {'http':  'socks5://127.0.0.1:{}'.format(default_tor_port), 'https': 'socks5://127.0.0.1:{}'.format(default_tor_port)}  # 9150
                response = session.get(url, headers=useragent)
                print(session.get('https://httpbin.org/ip').json())  # checking IP address to ensure its Tor
                print('price requested through Tor')
                wallet_interact_messages.replace('1.0', '100.0',"")
            except:
                wallet_interact_messages.replace('1.0', '100.0', "Sorry that Tor port isn't open! please change port number in settings")
        else:
            response = requests.get(url, headers=useragent)
        if response.status_code == 200:
            data = response.json()
            login_info = rpc_proxy.nspv_login(wif_input.get())
            listunspent_output = rpc_proxy.nspv_listunspent(login_info["address"])
            balance = listunspent_output['balance']
            if fiat == 'BTC':
                price = format(data['quotes'][fiat]['price'], '.8f')
                balance_fiat = format(balance * data['quotes'][fiat]['price'], '.8f')
            else:
                price = round(data['quotes'][fiat]['price'], 3)
                balance_fiat = round(balance * price, 3)
            change = data['quotes'][fiat]['percent_change_24h']
            price_text.configure(text="Current Price: {0} {1} {2}".format(currency_symbols[fiat], price, fiat))
            price_change_text.configure(text="Change in past 24/hrs: {}%".format(change))
            current_balance_fiat.configure(text="Balance Value: {0} {1} {2}".format(currency_symbols[fiat], str(balance_fiat), fiat))
        else:
            print('price status code {}'.format(response.status_code))
        root.after(300000, get_price) # refresh every 5 minutes, 300000 ms
    else:
        price_text.configure(text="Prices are Disabled")
        price_change_text.configure(text="24hr Price Changes are Disabled")
        current_balance_fiat.configure(text="Prices are Disabled")


def disable_prices():
    global default_price_request
    if default_price_request == 1:
        default_price_request = 0
        print('price enabled')
        get_price(default_currency)
    else:
        default_price_request = 1
        print('price disabled')

        
def select_tor_port():
    tor_popup = tkT.ThemedTk()
    tor_popup_style = ttk.Style()
    tor_popup_style.map("TButton", background=[('pressed', 'purple1')])
    tor_popup.set_theme('{}'.format(style.theme_use()), background=True)
    tor_popup.iconbitmap(ico)
    tor_popup.wm_title("Tor Port Number")

    def select():
        global default_tor_port
        default_tor_port = port.get()
        tor_popup.destroy()

    label = ttk.Label(tor_popup, text="Input what port number your Tor Browser is running on")
    label.pack(side="top", fill="x", pady=10, padx=10)
    port = ttk.Entry(tor_popup, width=50)
    port.delete(0)
    port.insert(0, '{}'.format(default_tor_port))
    port.pack()
    button1 = ttk.Button(tor_popup, text="Select", command=select)
    button2 = ttk.Button(tor_popup, text="Exit", command=tor_popup.destroy)
    button1.pack()
    button2.pack()


def enable_tor():
    global default_tor
    if default_tor == 1:
        default_tor = 0
        running_tor.configure(text='Running Tor...  ')
        print('Tor Enabled')
        get_price(default_currency)
    else:
        default_tor = 1
        running_tor.configure(text='')
        print('Tor disabled')

        
# exit button on toolbar logs out then closes app
def safe_close():
    nspv_logout(event=True)
    save_style()
    root.quit()

    
# Button bindings
nspv_login_button.bind('<Button-1>', nspv_login)
nspv_spend_button.bind('<Button-1>', nspv_send_tx)
nspv_logout_button.bind('<Button-1>', nspv_logout)
refresh_button.bind('<Button-1>', refresh)
amount_input.bind("<<Paste>>", custom_paste)
wif_input.bind("<<Paste>>", custom_paste)
address_input.bind("<<Paste>>", custom_paste)
address_book_messages.bind('<ButtonRelease-1>', select_item_book)


# widgets drawing
lbl_img.grid(row=0, sticky='e', padx=(10,10), pady=(10,0))
price_text.grid(row=0, sticky='w', padx=(10,10), pady=(0,0))
price_change_text.grid(row=1, sticky='w', padx=(10,10), pady=(0,10))
wallet_create_messages.grid(row=1, sticky='nesw', padx=(10,10), pady=(10,0))
nspv_login_text.grid(row=2, sticky='w', pady=(15,0), padx=(10,10))
wif_input.grid(row=2, sticky='w', pady=(15,0), padx=(160,10))
nspv_login_button.grid(row=2, sticky='e', pady=(15,0), padx=(160,10))
wallet_interact_messages.grid(row=4, sticky='nesw', padx=(10,10), pady=(10,0))
transaction_history_messages.grid(row=4, sticky='nesw', padx=(10,10), pady=(10,0))
address_book_messages.grid(row=4, sticky='nesw', padx=(10,10), pady=(10,0))
current_address_text.grid(row=6, sticky='w', pady=(15,0), padx=(10,10))
current_balance_text.grid(row=7, sticky='w', pady=(15,0), padx=(10,10))
current_balance_fiat.grid(row=7, sticky='e', pady=(15,0), padx=(5,400))
refresh_button.grid(row=7, column=0, sticky='w', pady=(15,0), padx=(630,10))
nspv_logout_button.grid(row=8, column=0, sticky='w', pady=(15,0), padx=(630,10))
logout_timer_text.grid(row=8, sticky='w', pady=(15,0), padx=(10,10))
nspv_logout_button.grid(row=8, column=0, sticky='w', pady=(15,0), padx=(630,10))
nspv_spend_text.grid(row=9, sticky='w', pady=(15,0), padx=(10,10))
address_input.grid(row=9, sticky='w', pady=(15,0), padx=(160,10))
amount_text.grid(row=10, sticky='w', pady=(15,0), padx=(10,10))
amount_input.grid(row=10, sticky='w', pady=(15,0), padx=(160,10))
nspv_spend_button.grid(row=11, sticky='W', pady=(5,10), padx=(160,10))
running_tor.grid(row=12, sticky='E', pady=(0,0), padx=(630,10))

# Menu Bar
menubar = tk.Menu(root, tearoff=0)
root.config(menu=menubar)

filemenu = tk.Menu(menubar, tearoff=0)
filemenu.add_command(label='Arc', command=StyleTheme.arc)
filemenu.add_command(label='Black', command=StyleTheme.black)
filemenu.add_command(label='Equilux', command=StyleTheme.equilux)
filemenu.add_command(label='Kroc', command=StyleTheme.kroc)
filemenu.add_command(label='Radiance', command=StyleTheme.radiance)
filemenu.add_command(label='Scid-Green', command=StyleTheme.scidGreen)

settingsmenu = tk.Menu(menubar, tearoff=0)
settingsmenu.add_command(label='Get New Address', command=get_new_address)
settingsmenu.add_command(label='Edit Address Book', command=address_book_popup)
settingsmenu.add_command(label='Disable/Enable Prices', command=disable_prices)
settingsmenu.add_command(label='Disable/Enable Tor', command=enable_tor)
settingsmenu.add_command(label='Select Other Tor Port', command=select_tor_port)

menubar.add_cascade(label="Settings", menu=settingsmenu)
menubar.add_cascade(label="Themes", menu=filemenu)
menubar.add_command(label="Exit", command=safe_close)

fiatmenu = tk.Menu(menubar, tearoff=0)
settingsmenu.add_cascade(label='Currency Choice', menu=fiatmenu)
fiatmenu.add_command(label='AUD', command=lambda: get_price('AUD'))
fiatmenu.add_command(label='BTC', command=lambda: get_price('BTC'))
fiatmenu.add_command(label='CAD', command=lambda: get_price('CAD'))
fiatmenu.add_command(label='CNY', command=lambda: get_price('CNY'))
fiatmenu.add_command(label='EUR', command=lambda: get_price('EUR'))
fiatmenu.add_command(label='GBP', command=lambda: get_price('GBP'))
fiatmenu.add_command(label='INR', command=lambda: get_price('INR'))
fiatmenu.add_command(label='JPY', command=lambda: get_price('JPY'))
fiatmenu.add_command(label='KRW', command=lambda: get_price('KRW'))
fiatmenu.add_command(label='RUB', command=lambda: get_price('RUB'))
fiatmenu.add_command(label='USD', command=lambda: get_price('USD'))


# lets go
root.eval('tk::PlaceWindow %s center' % root.winfo_pathname(root.winfo_id())) # center window
check_style()  # loads previous style theme
root.after(1000, load_address_book) # loads address book from CSV
root.after(1000, lambda: get_price(default_currency))  # Waits till after GUI loads and gets current price info
root.mainloop()
