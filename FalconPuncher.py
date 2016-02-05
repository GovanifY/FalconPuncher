#!/usr/bin/python

from __future__ import unicode_literals, print_function, division

import argparse
import os
import socket
import sys
import struct
import time
from contextlib import closing

try:
    input = raw_input
except NameError:
    pass

FBI_PORT = 5000
KB = 1024
CHUNK_SIZE = 128 * KB
WAIT_TIME = 2

def send_file(filename, dest_ip):
    statinfo = os.stat(filename)
    fbiinfo = struct.pack("!q", statinfo.st_size)

    with open(filename, "rb") as f:
        with closing(socket.socket()) as sock:
            try:
                sock.connect((dest_ip, FBI_PORT))
            except ConnectionRefusedError:
                sys.exit("Connection error with IP {}. Is FBI running?"
                        .format(dest_ip))
            try:
                sock.send(fbiinfo)
                total_transferred = 0
                while True:
                    bytes_transferred = 0
                    start = time.clock()
                    chunk = f.read(CHUNK_SIZE)
                    if not chunk:
                        break  # EOF
                    bytes_transferred = sock.send(chunk)
                    total_transferred += bytes_transferred
                    sys.stdout.write("\r{}: Speed: {:.1f}KB/s / Progress: {:3.1f}%".format(
                                filename,
                                bytes_transferred / KB ** 2 / (time.clock() - start),
                                total_transferred / statinfo.st_size * 100))
                sys.stdout.write("\n")
            except ConnectionResetError:
                sys.exit("\nConnection closed by FBI. Check FBI for errors.")

def check_and_send_file(filename, dest_ip):
    if os.path.isfile(filename):
        send_file(filename, dest_ip)
    else:
        sys.exit("{} not found or is not a file.".format(filename))

def argparser():
    parser = argparse.ArgumentParser(description="Send CIA files to FBI via network.")
    parser.add_argument("file", nargs="+", help="CIA file to send to FBI")
    parser.add_argument("-i", "--ip", help="IP from target 3DS")
    return parser

def main():
    parser = argparser()
    args = parser.parse_args()
    if args.ip:
        dest_ip = args.ip
    else:
        dest_ip = input("Enter IP: ")
    try:
        socket.inet_aton(dest_ip)
    except socket.error:
        sys.exit("IP {} is invalid.".format(dest_ip))

    for filename in args.file[:-1]:
        check_and_send_file(filename, dest_ip)
        print("Waiting {}s until the next transfer.".format(WAIT_TIME))
        time.sleep(WAIT_TIME)
    # We don't need to wait in the last transfer of the list
    check_and_send_file(args.file[-1], dest_ip)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
