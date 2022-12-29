import sys
from tkinter import Tk
from Klijent import Klijent

if __name__ == "__main__":
    try:
        serverAddr = sys.argv[1]
        serverPort = sys.argv[2]
        rtpPort = sys.argv[3]
        fileName = sys.argv[4]
    except:
        print("[NACIN KORISTENJA: KlijentStart.py Naziv_servera Server_port RTP_port (KlijentStart.py localhost 1600 1025)]\n")

    root = Tk()

    # Kreiranje novog klijenta
    app = Klijent(root, serverAddr, serverPort, rtpPort)
    app.master.title("BOSFLIX-RTPClient")
    root.mainloop()
