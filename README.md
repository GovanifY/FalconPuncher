FalconPuncher
=============

Send CIA files to FBI via network
---------------------------------

This is a fork of [blockfeed/FalconPunch](https://github.com/blockfeed/FalconPunch.git) with support for Python 3 (Python 2 is still supported), better user interface (including a simple GUI, see screenshot below) and better error handling. This program can be used with a 3DS with [Steveice10/FBI](https://github.com/Steveice10/FBI) installed to transfer CIA files to 3DS using network instead of manually copying files to SD card. This is somewhat slower, however it has the advantage of not using double the space to install.

![Screenshot](/screenshot.png?raw=true "FalconPuncher GUI")

Usage
-----

FalconPuncher does not have any requirements besides a basic Python 2/3 installation. You can just download it ([direct link](https://raw.githubusercontent.com/m45t3r/FalconPuncher/master/FalconPuncher.py)) and run:

    $ python FalconPuncher.py

This will open the GUI (Graphical User Interface). Open FalconPuncher inside the directory containing the CIAs, since it does not offer any option to change directories.

If you want to use FalconPuncher via command-line, you can start by running:

    $ python FalconPuncher.py -h

This will show the program help. To transfer a CIA to 3DS:

    $ python FalconPuncher.py some/cia/file.cia

The program will ask target 3DS IP before transfering the file. You can skip this step (useful for scripts or something) by passing `-i` option:

    $ python FalconPuncher.py -i 192.168.1.5 /some/cia/file.cia # change "192.168.1.5" to the IP of your 3DS!

You can pass multiple CIA files too:

    $ python FalconPuncher.py -i 192.168.1.5 /some/cia/file.cia /another/cia/file.cia

It is tested in Python 3.5.1, however it should work from Python 2.6 and above, and from Python 3.2 and above. At least I hope so.
