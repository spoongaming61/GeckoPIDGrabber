# GeckoPIDGrabber by Shadow Doggo. No rights reserved, do whatever you want.

import sys
import xml.etree.ElementTree as ET
from datetime import datetime
from tcpgecko import TCPGecko
from urllib.request import Request, urlopen

gecko = TCPGecko(sys.argv[1])  # Your Wii U's LAN IP address goes here (eg. "192.168.1.1").

print("\nGeckoPIDGrabber 1.0 by Shadow Doggo\n")

player_ptr = int.from_bytes(
    gecko.readmem(int.from_bytes(gecko.readmem(0x106E0330, 4), "big") + 0x10, 4), "big"
)  # Load pointer-in-pointer.
session_ptr = int.from_bytes(gecko.readmem(0x106EB980, 4), "big")

for offset in range(0x0, 0x1D, 0x4):
    player = int.from_bytes(gecko.readmem(player_ptr + offset, 4), "big")
    player_pid = int.from_bytes(gecko.readmem(player + 0xD0, 4), "big")
    player_pnid = ""
    player_name = (
        gecko.readmem(player + 0x6, 32)
        .decode("utf-16-be").split("\u0000")[0].replace("\n", "").replace("\r", "")
    )
    epic_fail = False

    if player_pid != 0:
        req = Request(
        f"http://account.pretendo.cc/v1/api/miis?pids={player_pid}",
        headers = {"X-Nintendo-Client-ID": "a2efa818a34fa16b8afbc8a74eba3eda",
        "X-Nintendo-Client-Secret": "c91cdb5658bd4954ade78533a339cf9a"}
        )

        try:
            response = ET.fromstring(urlopen(req).read().decode("utf-8"))
            player_pnid = response[0].find("user_id").text
        except Exception:
            epic_fail = True

    print(
        f"Player {offset // 0x4 + 1} | PID: {player_pid:X} ({player_pid}) | "
        f"PNID: {player_pnid} {" " * (16 - len(player_pnid))}| Name: {player_name}"
        )

if epic_fail: print("Failed to get PNID for one or more players.")

if session_ptr != 0:
    session_idx = int.from_bytes(gecko.readmem(session_ptr + 0xBD, 1), "big")
    session_id = int.from_bytes(gecko.readmem(session_ptr + session_idx + 0xCC, 4), "big")

    print(f"\nSession ID: {session_id:X} ({session_id})")
else:
    print("\nSession ID: None")

print(f"\nFetched at: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}")
