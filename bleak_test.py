"""
Scan/Discovery
--------------
Example showing how to scan for BLE devices.
Updated on 2019-03-25 by hbldh <henrik.blidh@nedomkull.com>
"""

import asyncio

from bleak import BleakScanner


async def main():
  print("scanning for 5 seconds, please wait...")

  devices = await BleakScanner.discover(return_adv=True, timeout=3)

  for d, a in devices.values():
    is_airpods = False

    print("-" * len(str(d)))
    if a.manufacturer_data.get(76) is not None:
      if b"\x07\x19\x01" in a.manufacturer_data.get(76):
        is_airpods = True

    print(f"Name: {d.name if not is_airpods else 'AirPods'} | Address: {d.address} | Metadata: {d.metadata}")


if __name__ == "__main__":
  asyncio.run(main())