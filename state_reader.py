"""Scan for iBeacons.

Copyright (c) 2022 Koen Vervloesem

SPDX-License-Identifier: MIT
"""
import asyncio
from uuid import UUID
import time
import json

from construct import Array, Byte, Const, Int8sl, Int16ub, Struct
from construct.core import ConstError

from bleak import BleakScanner
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData

from utils import parse_struct, raw_packet_to_str

apple_company_id = 'ff4c00'
phones = {}
resolved_devs = []
resolved_macs = []
resolved_numbers = []
victims = []
verb_messages = []
phone_number_info = {}
hash2phone = {}
dictOfss = {}
proxies = {}

phone_states = {
    '01': 'Disabled',
    '03': 'Idle',
    '05': 'Music',
    '07': 'Lock screen',
    '09': 'Video',
    '0a': 'Home screen',
    '0b': 'Home screen',
    '0d': 'Driving',
    '0e': 'Incoming call',
    '11': 'Home screen',
    '13': 'Off',
    '17': 'Lock screen',
    '18': 'Off',
    '1a': 'Off',
    '1b': 'Home screen',
    '1c': 'Home screen',
    '23': 'Off',
    '47': 'Lock screen',
    '4b': 'Home screen',
    '4e': 'Outgoing call',
    '57': 'Lock screen',
    '5a': 'Off',
    '5b': 'Home screen',
    '5e': 'Outgoing call',
    '67': 'Lock screen',
    '6b': 'Home screen',
    '6e': 'Incoming call',
}

airpods_states = {
    '00': 'Case:Closed',
    '01': 'Case:All out',
    '02': 'L:out',
    '03': 'L:out',
    '05': 'R:out',
    '09': 'R:out',
    '0b': 'LR:in',
    '11': 'R:out',
    '13': 'R:in',
    '15': 'R:in case',
    '20': 'L:out',
    '21': 'Case:All out',
    '22': 'Case:L out',
    '23': 'R:out',
    '29': 'L:out',
    '2b': 'LR:in',
    '31': 'Case:L out',
    '33': 'Case:L out',
    '50': 'Case:open',
    '51': 'L:out',
    '53': 'L:in',
    '55': 'Case:open',
    '70': 'Case:open',
    '71': 'Case:R out',
    '73': 'Case:R out',
    '75': 'Case:open',
}
devices_models = {
    "i386": "iPhone Simulator",
    "x86_64": "iPhone Simulator",
    "iPhone1,1": "iPhone",
    "iPhone1,2": "iPhone 3G",
    "iPhone2,1": "iPhone 3GS",
    "iPhone3,1": "iPhone 4",
    "iPhone3,2": "iPhone 4 GSM Rev A",
    "iPhone3,3": "iPhone 4 CDMA",
    "iPhone5,1": "iPhone 5 (GSM)",
    "iPhone4,1": "iPhone 4S",
    "iPhone5,2": "iPhone 5 (GSM+CDMA)",
    "iPhone5,3": "iPhone 5C (GSM)",
    "iPhone5,4": "iPhone 5C (Global)",
    "iPhone6,1": "iPhone 5S (GSM)",
    "iPhone6,2": "iPhone 5S (Global)",
    "iPhone7,1": "iPhone 6 Plus",
    "iPhone7,2": "iPhone 6",
    "iPhone8,1": "iPhone 6s",
    "iPhone8,2": "iPhone 6s Plus",
    "iPhone8,3": "iPhone SE (GSM+CDMA)",
    "iPhone8,4": "iPhone SE (GSM)",
    "iPhone9,1": "iPhone 7",
    "iPhone9,2": "iPhone 7 Plus",
    "iPhone9,3": "iPhone 7",
    "iPhone9,4": "iPhone 7 Plus",
    "iPhone10,1": "iPhone 8",
    "iPhone10,2": "iPhone 8 Plus",
    "iPhone10,3": "iPhone X Global",
    "iPhone10,4": "iPhone 8",
    "iPhone10,5": "iPhone 8 Plus",
    "iPhone10,6": "iPhone X GSM",
    "iPhone11,2": "iPhone XS",
    "iPhone11,4": "iPhone XS Max",
    "iPhone11,6": "iPhone XS Max Global",
    "iPhone11,8": "iPhone XR",
    "MacBookPro15,1": "MacBook Pro 15, 2019",
    "MacBookPro15,2": "MacBook Pro 13, 2019",
    "MacBookPro15,1": "MacBook Pro 15, 2018",
    "MacBookPro15,2": "MacBook Pro 13, 2018",
    "MacBookPro14,3": "MacBook Pro 15, 2017",
    "MacBookPro14,2": "MacBook Pro 13, 2017",
    "MacBookPro14,1": "MacBook Pro 13, 2017",
    "MacBookPro13,3": "MacBook Pro 15, 2016",
    "MacBookPro13,2": "MacBook Pro 13, 2016",
    "MacBookPro13,1": "MacBook Pro 13, 2016",
    "MacBookPro11,4": "MacBook Pro 15, mid 2015",
    "MacBookPro11,5": "MacBook Pro 15, mid 2015",
    "MacBookPro12,1": "MacBook Pro 13, ear 2015",
    "MacBookPro11,2": "MacBook Pro 15, mid 2014",
    "MacBookPro11,3": "MacBook Pro 15, mid 2014",
    "MacBookPro11,1": "MacBook Pro 13, mid 2014",
    "MacBookPro11,2": "MacBook Pro 15, end 2013",
    "MacBookPro11,3": "MacBook Pro 15, end 2013",
    "MacBookPro10,1": "MacBook Pro 15, ear 2013",
    "MacBookPro11,1": "MacBook Pro 13, end 2013",
    "MacBookPro10,2": "MacBook Pro 13, ear 2013",
    "MacBookPro10,1": "MacBook Pro 15, mid 2012",
    "MacBookPro9,1": "MacBook Pro 15, mid 2012",
    "MacBookPro10,2": "MacBook Pro 15, mid 2012",
    "MacBookPro9,2": "MacBook Pro 15, mid 2012",
    "MacBookPro8,3": "MacBook Pro 17, end 2011",
    "MacBookPro8,3": "MacBook Pro 17, ear 2011",
    "MacBookPro8,2": "MacBook Pro 15, end 2011",
    "MacBookPro8,2": "MacBook Pro 15, ear 2011",
    "MacBookPro8,1": "MacBook Pro 13, end 2011",
    "MacBookPro8,1": "MacBook Pro 13, ear 2011",
    "MacBookPro6,1": "MacBook Pro 17, mid 2010",
    "MacBookPro6,2": "MacBook Pro 15, mid 2010",
    "MacBookPro7,1": "MacBook Pro 13, mid 2010",
    "MacBookPro5,2": "MacBook Pro 17, mid 2009",
    "MacBookPro5,2": "MacBook Pro 17, ear 2009",
    "MacBookPro5,3": "MacBook Pro 15, mid 2009",
    "MacBookPro5,3": "MacBook Pro 15, mid 2009",
    "MacBookPro5,5": "MacBook Pro 13, mid 2009",
    "MacBookPro5,1": "MacBook Pro 15, end 2008",
    "MacBookPro4,1": "MacBook Pro 17, ear 2008",
    "MacBookPro4,1": "MacBook Pro 15, ear 2008",
    "iPod1,1": "1st Gen iPod",
    "iPod2,1": "2nd Gen iPod",
    "iPod3,1": "3rd Gen iPod",
    "iPod4,1": "4th Gen iPod",
    "iPod5,1": "5th Gen iPod",
    "iPod7,1": "6th Gen iPod",
    "iPad1,1": "iPad",
    "iPad1,2": "iPad 3G",
    "iPad2,1": "2nd Gen iPad",
    "iPad2,2": "2nd Gen iPad GSM",
    "iPad2,3": "2nd Gen iPad CDMA",
    "iPad2,4": "2nd Gen iPad New Revision",
    "iPad3,1": "3rd Gen iPad",
    "iPad3,2": "3rd Gen iPad CDMA",
    "iPad3,3": "3rd Gen iPad GSM",
    "iPad2,5": "iPad mini",
    "iPad2,6": "iPad mini GSM+LTE",
    "iPad2,7": "iPad mini CDMA+LTE",
    "iPad3,4": "4th Gen iPad",
    "iPad3,5": "4th Gen iPad GSM+LTE",
    "iPad3,6": "4th Gen iPad CDMA+LTE",
    "iPad4,1": "iPad Air (WiFi)",
    "iPad4,2": "iPad Air (GSM+CDMA)",
    "iPad4,3": "1st Gen iPad Air (China)",
    "iPad4,4": "iPad mini Retina (WiFi)",
    "iPad4,5": "iPad mini Retina (GSM+CDMA)",
    "iPad4,6": "iPad mini Retina (China)",
    "iPad4,7": "iPad mini 3 (WiFi)",
    "iPad4,8": "iPad mini 3 (GSM+CDMA)",
    "iPad4,9": "iPad Mini 3 (China)",
    "iPad5,1": "iPad mini 4 (WiFi)",
    "iPad5,2": "4th Gen iPad mini (WiFi+Cellular)",
    "iPad5,3": "iPad Air 2 (WiFi)",
    "iPad5,4": "iPad Air 2 (Cellular)",
    "iPad6,3": "iPad Pro (9.7 inch, WiFi)",
    "iPad6,4": "iPad Pro (9.7 inch, WiFi+LTE)",
    "iPad6,7": "iPad Pro (12.9 inch, WiFi)",
    "iPad6,8": "iPad Pro (12.9 inch, WiFi+LTE)",
    "iPad6,11": "iPad (2017)",
    "iPad6,12": "iPad (2017)",
    "iPad7,1": "iPad Pro 2nd Gen (WiFi)",
    "iPad7,2": "iPad Pro 2nd Gen (WiFi+Cellular)",
    "iPad7,3": "iPad Pro 10.5-inch",
    "iPad7,4": "iPad Pro 10.5-inch",
    "iPad7,5": "iPad 6th Gen (WiFi)",
    "iPad7,6": "iPad 6th Gen (WiFi+Cellular)",
    "iPad8,1": "iPad Pro 3rd Gen (11 inch, WiFi)",
    "iPad8,2": "iPad Pro 3rd Gen (11 inch, 1TB, WiFi)",
    "iPad8,3": "iPad Pro 3rd Gen (11 inch, WiFi+Cellular)",
    "iPad8,4": "iPad Pro 3rd Gen (11 inch, 1TB, WiFi+Cellular)",
    "iPad8,5": "iPad Pro 3rd Gen (12.9 inch, WiFi)",
    "iPad8,6": "iPad Pro 3rd Gen (12.9 inch, 1TB, WiFi)",
    "iPad8,7": "iPad Pro 3rd Gen (12.9 inch, WiFi+Cellular)",
    "iPad8,8": "iPad Pro 3rd Gen (12.9 inch, 1TB, WiFi+Cellular)",
    "Watch1,1": "Apple Watch 38mm case",
    "Watch1,2": "Apple Watch 38mm case",
    "Watch2,6": "Apple Watch Series 1 38mm case",
    "Watch2,7": "Apple Watch Series 1 42mm case",
    "Watch2,3": "Apple Watch Series 2 38mm case",
    "Watch2,4": "Apple Watch Series 2 42mm case",
    "Watch3,1": "Apple Watch Series 3 38mm case (GPS+Cellular)",
    "Watch3,2": "Apple Watch Series 3 42mm case (GPS+Cellular)",
    "Watch3,3": "Apple Watch Series 3 38mm case (GPS)",
    "Watch3,4": "Apple Watch Series 3 42mm case (GPS)",
    "Watch4,1": "Apple Watch Series 4 40mm case (GPS)",
    "Watch4,2": "Apple Watch Series 4 44mm case (GPS)",
    "Watch4,3": "Apple Watch Series 4 40mm case (GPS+Cellular)",
    "Watch4,4": "Apple Watch Series 4 44mm case (GPS+Cellular)",
}

proximity_dev_models = {
    '0220': 'AirPods',
    '0320': 'Powerbeats3',
    '0520': 'BeatsX',
    '0620': 'Beats Solo3'
}

proximity_colors = {
    '00': 'White',
    '01': 'Black',
    '02': 'Red',
    '03': 'Blue',
    '04': 'Pink',
    '05': 'Gray',
    '06': 'Silver',
    '07': 'Gold',
    '08': 'Rose Gold',
    '09': 'Space Gray',
    '0a': 'Dark Blue',
    '0b': 'Light Blue',
    '0c': 'Yellow',
}

homekit_category = {
    '0000': 'Unknown',
    '0100': 'Other',
    '0200': 'Bridge',
    '0300': 'Fan',
    '0400': 'Garage Door Opener',
    '0500': 'Lightbulb',
    '0600': 'Door Lock',
    '0700': 'Outlet',
    '0800': 'Switch',
    '0900': 'Thermostat',
    '0a00': 'Sensor',
    '0b00': 'Security System',
    '0c00': 'Door',
    '0d00': 'Window',
    '0e00': 'Window Covering',
    '0f00': 'Programmable Switch',
    '1000': 'Range Extender',
    '1100': 'IP Camera',
    '1200': 'Video Doorbell',
    '1300': 'Air Purifier',
    '1400': 'Heater',
    '1500': 'Air Conditioner',
    '1600': 'Humidifier',
    '1700': 'Dehumidifier',
    '1c00': 'Sprinklers',
    '1d00': 'Faucets',
    '1e00': 'Shower Systems',
}

siri_dev = {'0002': 'iPhone',
            '0003': 'iPad',
            '0009': 'MacBook',
            '000a': 'Watch',
            }

magic_sw_wrist = {
    '03': 'Not on wrist',
    '1f': 'Wrist detection disabled',
    '3f': 'On wrist',
}

hotspot_net = {
    '01': '1xRTT',
    '02': 'GPRS',
    '03': 'EDGE',
    '04': '3G (EV-DO)',
    '05': '3G',
    '06': '4G',
    '07': 'LTE',
}
ble_packets_types = {
    'airprint': '03',
    'airdrop': '05',
    'homekit': '06',
    'airpods': '07',
    'siri': '08',
    'airplay': '09',
    'nearby': '10',
    'watch_c': '0b',
    'handoff': '0c',
    'wifi_set': '0d',
    'hotspot': '0e',
    'wifi_join': '0f',
}

titles = ['Mac', 'State', 'Device', 'WI-FI', 'OS', 'Phone', 'Time', 'Notes']
dev_sig = {'02010': 'MacBook', '02011': 'iPhone'}
dev_types = ["iPad", "iPhone", "MacOS", "AirPods", "Powerbeats3", "BeatsX", "Beats Solo3"]

def parse_nearby(mac, header, data):
    # 0        1        2                                 5
    # +--------+--------+--------------------------------+
    # |        |        |                                |
    # | status | wifi   |           authTag              |
    # |        |        |                                |
    # +--------+--------+--------------------------------+
    nearby = {'status': 1,
              'wifi': 1,
              'authTag': 999}
    result = parse_struct(data, nearby)
    print("Nearby:{}".format(json.dumps(result)), mac)
    state = os_state = wifi_state = unkn = '<unknown>'
    if result['status'] in phone_states.keys():
        state = phone_states[result['status']]
    dev_val = unkn
    for dev in dev_sig:
        if dev in header:
            dev_val = dev_sig[dev]
    os_state, wifi_state = parse_os_wifi_code(result['wifi'], dev_val)
    if os_state == 'WatchOS':
        dev_val = 'Watch'
    if mac in resolved_macs or mac in resolved_devs:
        phones[mac]['state'] = state
        phones[mac]['wifi'] = wifi_state
        phones[mac]['os'] = os_state
        phones[mac]['time'] = int(time.time())
        if mac not in resolved_devs:
            phones[mac]['device'] = dev_val
    else:
        phones[mac] = {'state': unkn, 'device': unkn, 'wifi': unkn, 'os': unkn, 'phone': '', 'time': int(time.time()),
                       'notes': ''}
        phones[mac]['device'] = dev_val
        resolved_macs.append(mac)

def parse_nandoff(mac, data):
    # 0       1          3       4                                   14
    # +-------+----------+-------+-----------------------------------+
    # |       |          |       |                                   |
    # | Clbrd | seq.nmbr | Auth  |     Encrypted payload             |
    # |       |          |       |                                   |
    # +-------+----------+-------+-----------------------------------+
    handoff = {'clipboard': 1,
               's_nbr': 2,
               'authTag': 1,
               'encryptedData': 10}
    result = parse_struct(data, handoff)
    print("Handoff:{}".format(json.dumps(result)), mac)
    notes = f"Clbrd:True" if result['clipboard'] == '08' else ''
    if mac in resolved_macs:
        phones[mac]['time'] = int(time.time())
        phones[mac]['notes'] = notes
    else:
        phones[mac] = {'state': 'Idle', 'device': 'AppleWatch', 'wifi': '', 'os': '', 'phone': '',
                       'time': int(time.time()), 'notes': notes}
        resolved_macs.append(mac)

def parse_os_wifi_code(code, dev):
  # print(code)
  if code == '1c':
    if dev == 'MacBook':
      return ('Mac OS', 'On')
    else:
      return ('iOS12', 'On')
  elif code == '18':
    if dev == 'MacBook':
      return ('Mac OS', 'Off')
    else:
      return ('iOS12', 'Off')
  elif code == '10':
      return ('iOS11', '<unknown>')
  elif code == '1e':
      return ('iOS13', 'On')
  elif code == '1a':
      return ('iOS13', 'Off')
  elif code == '0e':
      return ('iOS13', 'Connecting')
  elif code == '0c':
      return ('iOS12', 'On')
  elif code == '04':
      return ('iOS13', 'On')
  elif code == '00':
      return ('iOS10', '<unknown>')
  elif code == '09':
      return ('Mac OS', '<unknown>')
  elif code == '14':
      return ('Mac OS', 'On')
  elif code == '98':
      return ('WatchOS', '<unknown>')
  else:
      return ('', '')

def read_packet(mac, data_str):
  # if apple_company_id in data_str:
  header = data_str[:data_str.find(apple_company_id)]
  data = data_str[data_str.find(apple_company_id) + len(apple_company_id):]
  packet = parse_ble_packet(data)
  if ble_packets_types['nearby'] in packet.keys():
      parse_nearby(mac, header, packet[ble_packets_types['nearby']])
  if ble_packets_types['handoff'] in packet.keys():
      parse_nandoff(mac, packet[ble_packets_types['handoff']])
  if ble_packets_types['watch_c'] in packet.keys():
      parse_watch_c(mac, packet[ble_packets_types['watch_c']])
  if ble_packets_types['wifi_set'] in packet.keys():
      parse_wifi_set(mac, packet[ble_packets_types['wifi_set']])
  # if ble_packets_types['hotspot'] in packet.keys():
  #     parse_hotspot(mac, packet[ble_packets_types['hotspot']])
  # if ble_packets_types['wifi_join'] in packet.keys():
  #     parse_wifi_j(mac, packet[ble_packets_types['wifi_join']])
  # if ble_packets_types['airpods'] in packet.keys():
  #     parse_airpods(mac, packet[ble_packets_types['airpods']])
  # if ble_packets_types['airdrop'] in packet.keys():
  #     parse_airdrop_r(mac, packet[ble_packets_types['airdrop']])
  # if ble_packets_types['airprint'] in packet.keys():
  #     parse_airprint(mac, packet[ble_packets_types['airprint']])
  # if ble_packets_types['homekit'] in packet.keys():
  #     parse_homekit(mac, packet[ble_packets_types['homekit']])
  # if ble_packets_types['siri'] in packet.keys():
  #     parse_siri(mac, packet[ble_packets_types['siri']])
  # if ble_packets_types['airplay'] in packet.keys():
  #     parse_siri(mac, packet[ble_packets_types['airplay']])

def parse_watch_c(mac, data):
    # 0          2       3
    # +----------+-------+
    # |          |       |
    # |  Data    | Wrist |
    # |          |       |
    # +----------+-------+
    magic_switch = {'data': 2,
                    'wrist': 1
                    }
    result = parse_struct(data, magic_switch)
    print("MagicSwitch:{}".format(json.dumps(result)), mac)
    notes = f"{magic_sw_wrist[result['wrist']]}"
    if mac in resolved_macs:
        phones[mac]['state'] = 'MagicSwitch'
        phones[mac]['time'] = int(time.time())
        phones[mac]['notes'] = notes
    else:
        phones[mac] = {'state': 'MagicSwitch', 'device': 'AppleWatch', 'wifi': '', 'os': '', 'phone': '',
                       'time': int(time.time()), 'notes': notes}
        resolved_macs.append(mac)



def parse_ble_packet(data):
  parsed_data = {}
  tag_len = 2
  i = 0
  while i < len(data):
    tag = data[i:i + tag_len]
    val_len = int(data[i + tag_len:i + tag_len + 2], 16)
    value_start_position = i + tag_len + 2
    value_end_position = i + tag_len + 2 + val_len * 2
    parsed_data[tag] = data[value_start_position:value_end_position]
    i = value_end_position
  return parsed_data

def device_found(device: BLEDevice, advertisement_data: AdvertisementData):
  # print(device)
  """Decode iBeacon."""
  try:
    data_str = raw_packet_to_str(advertisement_data.manufacturer_data[0x004C])
    read_packet(device.address, data_str)

  except KeyError:
    # Apple company ID (0x004c) not found
    pass

def parse_wifi_set(mac, data):
    # 0                                         4
    # +-----------------------------------------+
    # |                                         |
    # |             iCloud ID                   |
    # |                                         |
    # +-----------------------------------------+
    wifi_set = {'icloudID': 4}
    result = parse_struct(data, wifi_set)
    print("WiFi settings:{}".format(json.dumps(result)), mac)
    unkn = '<unknown>'
    if mac in resolved_macs or mac in resolved_devs:
        phones[mac]['state'] = 'WiFi screen'
    else:
        phones[mac] = {'state': unkn, 'device': unkn, 'wifi': unkn, 'os': unkn, 'phone': '', 'time': int(time.time())}
        resolved_macs.append(mac)

async def main():
  """Scan for devices."""
  scanner = BleakScanner()
  scanner.register_detection_callback(device_found)

  while True:
    await scanner.start()
    await asyncio.sleep(1.0)
    await scanner.stop()

asyncio.run(main())
