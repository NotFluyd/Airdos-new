from ast import arg
from concurrent.futures import thread
import ipaddress
import json
import logging
import plistlib
import random
import threading
import time

from colorama import Fore, Back, Style

from opendrop.server import AirDropServer
from opendrop.config import AirDropConfig, AirDropReceiverFlags

def server(i):
  config = AirDropConfig(
      email="lol",
      phone="0fff",
      computer_name=f"Epic name {i}",
      computer_model="lolll",
      debug=False,
      interface="awdl0"
  )
  server = None
  client = None
  browser = None
  sending_started = False
  discover = []
  lock = threading.Lock()

  server = AirDropServer(config)
  # server.start_service()
  server.start_server()

if __name__ == "__main__":
  for i in range(2):
    threading.Thread(target=server, args=(i,)).start()