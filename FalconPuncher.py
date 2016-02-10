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

DEFAULT_IP = "192.168.1."
FBI_PORT = 5000
KB = 1024
CHUNK_SIZE = 128 * KB
WAIT_TIME = 2

class GUI(tk.Tk):
    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)
        self.title("FalconPuncher")
        self.geometry("400x600")

        # Create a listbox to show user filelist
        self.lbl_filelist = tk.Label(
                text="CIA list (double click to add to queue):",
                anchor=tk.W)
        self.lbl_filelist.pack(side=tk.TOP, fill=tk.X)
        self.lb_filelist = tk.Listbox(selectmode=tk.SINGLE)
        self.lb_filelist.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.populate_filelist("*.cia")
        self.lb_filelist.bind("<Double-Button-1>", self.add_file_to_sendlist)
        # Create a scrollbar to allow filelist to an arbitrary number of files
        self.sb_filelist = tk.Scrollbar(self.lb_filelist, orient=tk.VERTICAL)
        self.sb_filelist.pack(side=tk.RIGHT, fill=tk.Y)
        # Bind listbox and scrollbar together
        self.sb_filelist.configure(command=self.lb_filelist.yview)
        self.lb_filelist.configure(yscrollcommand=self.sb_filelist.set)

        # Create a listbox to show user the files selected to send
        self.lbl_sendlist = tk.Label(
                text="CIA's in queue (double click to remove from queue):",
		anchor=tk.W)
        self.lbl_sendlist.pack(side=tk.TOP, fill=tk.X, expand=False)
        self.lb_sendlist = tk.Listbox(selectmode=tk.SINGLE)
        self.lb_sendlist.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.lb_sendlist.bind("<Double-Button-1>", self.remove_file_from_sendlist)
        # Create a scrollbar to allow filelist to an arbitrary number of files
        self.sb_sendlist = tk.Scrollbar(self.lb_sendlist, orient=tk.VERTICAL)
        self.sb_sendlist.pack(side=tk.RIGHT, fill=tk.Y)
        # Bind listbox and scrollbar together
        self.sb_sendlist.configure(command=self.lb_sendlist.yview)
        self.lb_sendlist.configure(yscrollcommand=self.sb_sendlist.set)

        # Textbox to allow user to change IP
        self.lbl_ip = tk.Label(text="IP (press Y in FBI to show 3DS IP):",
                anchor=tk.W)
        self.lbl_ip.pack(side=tk.TOP, fill=tk.X)
        self.ip = tk.StringVar()
        self.ip.set(DEFAULT_IP)
        self.ent_ip = tk.Entry(textvariable=self.ip)
        self.ent_ip.pack(side=tk.TOP, fill=tk.X)

        # Button to start file transferring
        self.btn_start = tk.Button(text="Send", command=self.start_transfer)
        self.btn_start.pack(side=tk.TOP, fill=tk.X)

        # Progress bar for send progress
        self.prg_send = ttk.Progressbar(orient="horizontal", mode="determinate")
        self.prg_send.pack(side=tk.TOP, fill=tk.X)

    def populate_filelist(self, regex="/*"):
        for filename in sorted(glob.glob(regex)):
            self.lb_filelist.insert(tk.END, filename)

    def get_files_from_filelist(self):
        return self.lb_filelist.get(0, tk.END)

    def get_files_from_sendlist(self):
        return self.lb_sendlist.get(0, tk.END)

    def add_file_to_sendlist(self, event):
        position = self.lb_filelist.curselection()[0]
        selection = self.lb_filelist.get(position)
        if selection not in self.get_files_from_sendlist():
            self.lb_sendlist.insert(tk.END, selection)

    def remove_file_from_sendlist(self, event):
        position = self.lb_sendlist.curselection()[0]
        self.lb_sendlist.delete(position)

    def start_transfer(self):
        if not self.get_files_from_sendlist():
            tkMessageBox.showerror("Error", "No files selected")
            return

        dest_ip = self.ip.get()
        if not dest_ip:
            tkMessageBox.showerror("Error", "Did not set an IP")
            return
        if not valid_ip(dest_ip):
            tkMessageBox.showerror("Error", "Invalid IP")
            return

        try:
            for i, filename in enumerate(self.get_files_from_sendlist()):
                for progress in send_file(filename, dest_ip):
                    self.prg_send.step(progress)
                    self.update_idletasks()
                self.lb_sendlist.delete(0)
                self.update_idletasks()
                time.sleep(WAIT_TIME)
        except ConnectionRefusedError:
            tkMessageBox.showerror("Error",
                    "Connection error. Is FBI running?")
        except ConnectionResetError:
            tkMessageBox.showerror("Error",
                    "Connection closed by FBI. Check FBI for errors.")
        except OSError:
            tkMessageBox.showerror("Error",
                    "No route to host. Is IP correct?")
        finally:
            self.prg_send.config(value=0)
            return

def send_file(filename, dest_ip):
    statinfo = os.stat(filename)
    fbiinfo = struct.pack("!q", statinfo.st_size)

    with open(filename, "rb") as f:
        with closing(socket.socket()) as sock:
            sock.connect((dest_ip, FBI_PORT))
            sock.send(fbiinfo)
            while True:
                start = time.clock()
                chunk = f.read(CHUNK_SIZE)
                if not chunk:
                    return
                yield sock.send(chunk) / statinfo.st_size * 100


def send_file_cli(filename, dest_ip):
    try:
        total_progress = 0
        for progress in send_file(filename, dest_ip):
            total_progress += progress
            sys.stdout.write("\r{} - {:3.1f}%".format(filename, total_progress))
        sys.stdout.write("\n")
    except ConnectionRefusedError:
        sys.exit("Connection error. Is FBI running?")
    except ConnectionResetError:
        sys.exit("\nConnection closed by FBI. Check FBI for errors.")
    except OSError:
        sys.exit("No route to host. Is IP correct?")

def valid_ip(ip):
    try:
        socket.inet_aton(ip)
        return True
    except socket.error:
        return False

def argparser():
    parser = argparse.ArgumentParser(description="Send CIA files to FBI via network.")
    parser.add_argument("file", nargs="*", help="CIA file to send to FBI")
    parser.add_argument("-i", "--ip", help="IP from target 3DS")
    parser.add_argument("--gui", action="store_true", help="force GUI mode")
    return parser

def main():
    parser = argparser()
    args = parser.parse_args()

    if args.gui or not args.file:
        gui = GUI()
        gui.mainloop()
        sys.exit()

    if args.ip:
        dest_ip = args.ip
    else:
        dest_ip = input("Enter IP: ")

    for filename in args.file:
        if not os.path.isfile(filename):
            sys.exit("{} not found or is not a file.".format(filename))

    if not valid_ip(dest_ip):
        sys.exit("IP {} is invalid.".format(dest_ip))

    for filename in args.file[:-1]:
        send_file_cli(filename, dest_ip)
        print("Waiting {}s until the next transfer.".format(WAIT_TIME))
        time.sleep(WAIT_TIME)
    # We don't need to wait in the last transfer of the list
    send_file_cli(args.file[-1], dest_ip)


if __name__ == "__main__":
    try:
       main()
    except KeyboardInterrupt:
        pass
