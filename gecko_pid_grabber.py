# GeckoPIDGrabber (c) Shadow Doggo.

import sys
import time
import urllib.error
import xml.etree.ElementTree as ET
from datetime import datetime
from tcpgecko import TCPGecko
from logger import Logger
from urllib.request import Request, urlopen


def main():
    player_ptr = int.from_bytes(
        gecko.readmem(int.from_bytes(gecko.readmem(0x106E0330, 4), "big") + 0x10, 4), "big"
    )  # Load pointer-in-pointer.
    session_ptr = int.from_bytes(gecko.readmem(0x106EB980, 4), "big")

    epic_fail = False

    if not auto_logging and logging_enabled:
        logger.new_match(gecko, auto_logging, session_ptr, 1)

    if not silent_logging:
        print()

    for offset in range(0x0, 0x1D, 0x4):
        player = int.from_bytes(
            gecko.readmem(player_ptr + offset, 4), "big"
        )  # [[0x106E0330] + 0x10] + offset.
        player_data = gecko.readmem(
            player, 0xD4
        )  # Read all the player data at once cause it's faster.
        player_pid = int.from_bytes(player_data[0xD0:0xD4], "big")

        if player_pid != 0:
            player_pnid = ""
            player_name = (
                player_data[0x6:0x26]
                .decode("utf-16-be")
                .split("\u0000")[0]
                .replace("\n", "")
                .replace("\r", "")
            )

            req = Request(
                f"http://account.pretendo.cc/v1/api/miis?pids={player_pid}",
                headers={
                    "X-Nintendo-Client-ID": "a2efa818a34fa16b8afbc8a74eba3eda",
                    "X-Nintendo-Client-Secret": "c91cdb5658bd4954ade78533a339cf9a",
                },
            )  # Get user data from account server.

            try:
                response = ET.fromstring(urlopen(req).read().decode("utf-8"))
                player_pnid = response[0].find("user_id").text
            except urllib.error.URLError:
                epic_fail = True

            if logging_enabled:
                logger.log(
                    gecko,
                    log_stats,
                    offset // 0x4 + 1,
                    player_data,
                    player_pid,
                    player_pnid,
                    player_name,
                )

            if not silent_logging:
                print(
                    f"Player {offset // 0x4 + 1} | "
                    f"PID: {player_pid:X} ({player_pid}) {' ' * 16 if player_pid == 0 else ''}| "
                    f"PNID: {player_pnid} {' ' * (16 - len(player_pnid))}| "
                    f"Name: {player_name}"
                )

    if epic_fail:
        print("Failed to get PNID for one or more players.")

    if not silent_logging and session_ptr != 0:
        session_idx = int.from_bytes(gecko.readmem(session_ptr + 0xBD, 1), "big")
        session_id = int.from_bytes(gecko.readmem(session_ptr + session_idx + 0xCC, 4), "big")

        print(f"\nSession ID: {session_id:X} ({session_id})")
    elif not silent_logging:
        print("\nSession ID: None")

    if not silent_logging:
        print(f"\nFetched at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    logging_enabled = False
    silent_logging = False
    log_stats = False
    auto_logging = False

    print("GeckoPIDGrabber by Shadow Doggo\n")

    try:
        gecko = TCPGecko(sys.argv[1])
    except IndexError:
        print("No IP address was provided")
        exit()
    except OSError as ex:
        print(f"Failed to connect: {ex}")
        exit()

    valid_args = ["log", "silent", "stats", "auto"]

    for arg in sys.argv[2:]:
        if arg not in valid_args:
            print(f"Invalid argument: {arg}")

    if len(sys.argv) > 2 and "log" in sys.argv[2:]:
        logging_enabled = True
        logger = Logger()
        logger.create_log()

    if len(sys.argv) > 2 and "silent" in sys.argv[2:]:
        silent_logging = True

    if len(sys.argv) > 2 and "stats" in sys.argv[2:]:
        log_stats = True

    if len(sys.argv) > 2 and "auto" in sys.argv[2:]:
        print("\nAuto logging enabled")

        if not logging_enabled:
            logging_enabled = True
            logger = Logger()
            logger.create_log()

        auto_logging = True
        match_in_progress = False
        count = 0

        while True:
            session_ptr = int.from_bytes(gecko.readmem(0x106EB980, 4), "big")
            scene_id = int.from_bytes(
                gecko.readmem(int.from_bytes(gecko.readmem(0x106E9770, 4), "big") + 0x162, 2), "big"
            )  # Scene ID ptr [[0x106E9770] + 0x160] + 0x2.

            if scene_id != 7:
                match_in_progress = False

            if (
                not match_in_progress and scene_id == 7
            ):  # Trigger logging when scence changes to a vs match.
                match_in_progress = True
                count += 1

                logger.new_match(gecko, auto_logging, session_ptr, count)

                if not silent_logging:
                    print(f"\nMatch {count}")

                main()

            time.sleep(10)

    main()
