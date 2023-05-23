# Python RTSP Server for Video Player
This project represents a client-server application that works on the principle of RTSP. 
This is a desktop application and allows the client to choose a specific movie from the server and control the video reproduction. 
Video/movie is not fully downloaded immediately, but using rtsp protocol, video is downloaded in chunks and displayed to the end user.
User can start/stop the video player, speed up and slow down the video reproduction. 

Network protocol analyzer that is used is Wireshark. It allowed us to capture and analyze network traffic in real-time, providing detailed insights into the communication between client and server.

More detailed documentation (in Bosnian) is written in file "Sistemska dokumentacija - Bosflix".

## Table of Contents
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Usage](#usage)
- [Configuration](#configuration)
- [Technologies](#technologies)

## Prerequisites
Python - version 3 (https://www.python.org/downloads/)
Wireshark (https://www.wireshark.org/download.html)

## Installation
Pillow - latest version - python library (pip install Pillow - https://pypi.org/project/Pillow/)

## Usage
When all prerequisites are installed, the application can be easily started.

Server can be started on port 1700 using the next command:  python ServerStart.py 1700

Client desktop application can be launched on port 1025 using the next command: python KlijentStart.py localhost 1700 1025

When the client app is launced, the video player is displayed. In this project version, only one movie can be chosen and loaded using the button "Učitaj film".
User can start the reproduction using button "Pokreni" once when the movie is loaded. It is possible to speed up ("Ubrzaj"), slow down ("Uspori"), and stop ("Zaustavi") the movie that is being reproduced.

If the wireshark is launced at the time of application usage, the user can track network on TCP and UDP protocols.
Every request to the server is made via the TCP protocol. It is possible to read the time required to send the packet, which is the source (its IP address) and which is the destination (its IP address). It is also possible to see the length of the transmitted packet.
After starting the video reproduction, data packets via the RTP protocol are sent using the UDP protocol.

## Configuration
RTP protocol only supports MPEG and MJPEG video formats. (video filename can be changed in Klijent.py file).

This desktop application can be launched on different ports, if needed (1024 - 65535).

## Technologies
The programming language that is used is Python. Python features that are represented through this project are:
 - Python OOP (using classes with their constructors and specific methods)
 - Exception handling (using try-except blocks)
 - Python built-in functions for string manipulation
 - Python sockets for network communication
 - Python GUI (Graphical User Interface) toolkit  Tkinter
 - RTP (Real-time Transport Protocol) packets in Python

## Contact
Dika Bošnjak - dika.bosnjak2018@size.ba 

Hajrija Bajrić - hajrija.bajric2018@size.ba
