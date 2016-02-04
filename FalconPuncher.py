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
WAIT_TIME = 1.5

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
                bytes_transferred = 0
                while True:
                    chunk = f.read(CHUNK_SIZE)
                    if not chunk:
                        break  # EOF
                    bytes_transferred += sock.send(chunk)
                    sys.stdout.write("\rProgress: {:.2f}KB of {:.2f}KB"
                            .format(bytes_transferred / KB, statinfo.st_size / KB))
                sys.stdout.write("\n")
            except ConnectionResetError:
                sys.exit("\nConnection closed by FBI. Check FBI for errors.")

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

    for filename in args.file:
        if os.path.isfile(filename):
            print("Sending file {}".format(filename))
            time.sleep(WAIT_TIME)  # Wait a while for the next transfer
            send_file(filename, dest_ip)
        else:
            sys.exit("{} is not a file.".format(filename))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
