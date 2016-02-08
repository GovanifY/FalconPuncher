#!/usr/bin/python

from __future__ import unicode_literals, print_function, division

import argparse
import glob
import os
import socket
import sys
import struct
import time
from contextlib import closing

try:
    import tkinter as tk
    from tkinter import messagebox as tkMessageBox
    from tkinter import ttk
except ImportError:
    import Tkinter as tk
    import tkMessageBox
    import ttk

try:
    input = raw_input
except NameError:
    pass

DEBUG = True
FBI_PORT = 5000
KB = 1024
CHUNK_SIZE = 128 * KB
WAIT_TIME = 2

class GUI(tk.Tk):
    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)
        self.title("FalconPuncher")

        # Create a listbox to show user filelist
        self.lb_filelist = tk.Listbox(selectmode=tk.SINGLE)
        self.lb_filelist.pack(side=tk.LEFT)
        self.populate_filelist("*.cia")
        self.lb_filelist.bind("<Double-Button-1>", self.add_file_to_sendlist)
        # Create a scrollbar to allow filelist to an arbitrary number of files
        self.sb_filelist = tk.Scrollbar(orient=tk.VERTICAL)
        self.sb_filelist.pack(side=tk.LEFT, fill=tk.Y)
        # Bind listbox and scrollbar together
        self.sb_filelist.configure(command=self.lb_filelist.yview)
        self.lb_filelist.configure(yscrollcommand=self.sb_filelist.set)

        # Create a listbox to show user the files selected to send
        self.lb_sendlist = tk.Listbox(selectmode=tk.SINGLE)
        self.lb_sendlist.pack(side=tk.LEFT)
        self.lb_sendlist.bind("<Double-Button-1>", self.remove_file_from_sendlist)
        # Create a scrollbar to allow filelist to an arbitrary number of files
        self.sb_sendlist = tk.Scrollbar(orient=tk.VERTICAL)
        self.sb_sendlist.pack(side=tk.LEFT, fill=tk.Y)
        # Bind listbox and scrollbar together
        self.sb_sendlist.configure(command=self.lb_sendlist.yview)
        self.lb_sendlist.configure(yscrollcommand=self.sb_sendlist.set)

        # Textbox to allow user to change IP
        self.label_ip = tk.Label(text="IP:")
        self.label_ip.pack()
        self.ip = tk.StringVar()
        self.ent_ip = tk.Entry(textvariable=self.ip)
        self.ent_ip.pack()

        # Button to start file transferring
        self.btn_start = tk.Button(text="Start", command=self.start_transfer)
        self.btn_start.pack()

        # Progress bar for send progress
        self.prg_send = ttk.Progressbar(orient="horizontal", mode="determinate")
        self.prg_send.pack()

    def populate_filelist(self, regex="/*"):
        for filename in sorted(glob.glob(regex)):
            self.lb_filelist.insert(tk.END, filename)
        debug("filelist:", self.get_files_from_filelist())

    def get_files_from_filelist(self):
        return self.lb_filelist.get(0, tk.END)

    def get_files_from_sendlist(self):
        return self.lb_sendlist.get(0, tk.END)

    def add_file_to_sendlist(self, event):
        position = self.lb_filelist.curselection()[0]
        selection = self.lb_filelist.get(position)
        if selection not in self.get_files_from_sendlist():
            self.lb_sendlist.insert(tk.END, selection)
        debug("sendlist:", self.get_files_from_sendlist())

    def remove_file_from_sendlist(self, event):
        position = self.lb_sendlist.curselection()[0]
        self.lb_sendlist.delete(position)
        debug("sendlist:", self.get_files_from_sendlist())

    def start_transfer(self):
        if not self.get_files_from_sendlist():
            tkMessageBox.showerror("Error", "No files selected")
            return
        if not self.ip.get():
            tkMessageBox.showerror("Error", "Did not set an IP")
            return

        for i, filename in enumerate(self.get_files_from_sendlist()):
            for speed, progress in send_file(filename, self.ip.get()):
                self.prg_send.step(progress)
                self.update_idletasks()
            self.lb_sendlist.delete(0)
            self.update_idletasks()
            time.sleep(WAIT_TIME)

def debug(value, *args, **kwargs):
    if DEBUG:
        if not "file" in kwargs:
            kwargs.update({"file": sys.stderr})
        print("DEBUG:", value, *args, **kwargs)

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
                        return
                    bytes_transferred = sock.send(chunk)
                    total_transferred += bytes_transferred

                    speed = bytes_transferred / KB ** 2 / (time.clock() - start)
                    progress = bytes_transferred / statinfo.st_size * 100
                    yield speed, progress

            except ConnectionResetError:
                sys.exit("\nConnection closed by FBI. Check FBI for errors.")

def send_file_cli(filename, dest_ip):
    basename = os.path.basename(filename)
    total_progress = 0
    for speed, progress in send_file(filename, dest_ip):
        total_progress += progress
        sys.stdout.write("\r{} - Speed: {:.1f}KB/s / Progress: {:3.1f}%"
                .format(basename, speed, total_progress))
    sys.stdout.write("\n")

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
        if not os.path.isfile(filename):
            sys.exit("{} not found or is not a file.".format(filename))

    for filename in args.file[:-1]:
        send_file_cli(filename, dest_ip)
        print("Waiting {}s until the next transfer.".format(WAIT_TIME))
        time.sleep(WAIT_TIME)
    # We don't need to wait in the last transfer of the list
    send_file_cli(args.file[-1], dest_ip)


if __name__ == "__main__":
    gui = GUI()
    gui.mainloop()
    #try:
    #   main()
    #except KeyboardInterrupt:
    #    pass
