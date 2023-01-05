from tkinter import *
import tkinter.messagebox
from PIL import Image, ImageTk
import socket, threading, os
import time

from RtpPacket import RtpPacket

CACHE_FILE_NAME = "cache-"
CACHE_FILE_EXT = ".jpg"
SESSION_FILE = "session.txt"


class Klijent:
    #Moguca stanja programa
    INIT = 0
    READY = 1
    PLAYING = 2
    state = INIT

    #Moguce akcije na strani klijenta
    SETUP = 0
    PLAY = 1
    PAUSE = 2
    EXIT = 3
    SLOWER = 4
    FASTER = 5

    #Inicijalizacija aplikacije
    def __init__(self, master, serveraddr, serverport, rtpport):
        self.master = master
        self.master.protocol("WM_DELETE_WINDOW", self.handler)
        self.kreiranjeGUI()
        self.serverAddr = serveraddr
        self.serverPort = int(serverport)
        self.rtpPort = int(rtpport)
        self.rtspSeq = 0
        self.sessionId = 0
        self.requestSent = -1
        self.exitAcked = 0
        self.konekcijaNaServer()
        self.frameNbr = 0

        self.mode = "normal"

        self.bytesReceived = 0
        self.startTime = 0
        self.lossCounter = 0

    def kreiranjeGUI(self):
        self.setup1 = Button(self.master, width=15, padx=3, pady=3)
        self.setup1["text"] = "Učitaj film"
        self.setup1["command"] = self.postaviVideo1
        self.setup1.grid(row=2, column=0, padx=2, pady=2)
        self.setup1["state"] = "normal"

        self.start = Button(self.master, width=15, padx=3, pady=3)
        self.start["text"] = "Pokreni"
        self.start["command"] = self.pokreniVideo
        self.start.grid(row=3, column=0, padx=2, pady=2)
        self.start["state"] = "disabled"

        self.rewindback = Button(self.master, width=15, padx=3, pady=3)
        self.rewindback["text"] = "Uspori"
        self.rewindback["command"] = self.usporiVideo
        self.rewindback.grid(row=3, column=1, padx=2, pady=2)
        self.rewindback["state"] = "disabled"

        self.rewindforward = Button(self.master, width=15, padx=3, pady=3)
        self.rewindforward["text"] = "Ubrzaj"
        self.rewindforward["command"] = self.ubrzajVideo
        self.rewindforward.grid(row=3, column=2, padx=2, pady=2)
        self.rewindforward["state"] = "disabled"

        self.pause = Button(self.master, width=15, padx=3, pady=3)
        self.pause["text"] = "Zaustavi"
        self.pause["command"] = self.zaustaviVideo
        self.pause.grid(row=3, column=3, padx=2, pady=2)
        self.pause["state"] = "disabled"

        self.exit = Button(self.master, width=15, padx=3, pady=3)
        self.exit["text"] = "Izađi"
        self.exit["command"] = self.zatvori
        self.exit.grid(row=3, column=4, padx=2, pady=2)
        self.exit["state"] = "disabled"

        self.label = Label(self.master, height=18, bg="black")
        self.label.grid(row=0, column=0, columnspan=5, sticky=W + E + N + S, padx=5, pady=5)

        self.timeBox = Label(self.master, width=12, text="00:00")
        self.timeBox.grid(row=1, column=2, sticky=W + E + N + S, padx=5, pady=5)

    def postaviVideo1(self):
        if self.state == self.INIT:
            self.fileName = "movie.Mjpeg"
            self.posaljiRTSPZahtjev(self.SETUP)

    def zatvori(self):
        self.posaljiRTSPZahtjev(self.EXIT)

        if self.frameNbr != 0:
            lossRate = self.lossCounter / self.frameNbr
            print("Gubitak paketa: " + str(lossRate) + "\n")

        self.master.destroy()
        os.remove(CACHE_FILE_NAME + str(self.sessionId) + CACHE_FILE_EXT)

    def zaustaviVideo(self):
        if self.state == self.PLAYING:
            self.posaljiRTSPZahtjev(self.PAUSE)

    def pokreniVideo(self):
        if self.state == self.READY:
            threading.Thread(target=self.slusajRtp).start()
            self.playEvent = threading.Event()
            self.playEvent.clear()
            self.posaljiRTSPZahtjev(self.PLAY)
    
    def usporiVideo(self):
        if self.state == self.PLAYING:
            self.mode = "slow"
            self.posaljiRTSPZahtjev(self.SLOWER)
    
    def ubrzajVideo(self):
        if self.state == self.PLAYING:
            self.mode = "fast"
            self.posaljiRTSPZahtjev(self.FASTER)

    def slusajRtp(self):
        while True:
            try:
                data = self.rtpSocket.recv(20480)
                if data:
                    rtpPacket = RtpPacket()
                    rtpPacket.decode(data)

                    # Ako se brojevi sekvenci ne poklapaju, dolazi do gubitka paketa
                    if self.frameNbr + 1 != rtpPacket.seqNum():
                        self.lossCounter += (rtpPacket.seqNum() - (self.frameNbr + 1))

                    currFrameNbr = rtpPacket.seqNum()

                    if currFrameNbr > self.frameNbr:
                        # Preracunavanje dobavljenih bajtova
                        self.bytesReceived += len(rtpPacket.getPayload())

                        self.frameNbr = currFrameNbr
                        self.azurirajVideo(self.upisiFrame(rtpPacket.getPayload()))

                        # Trenutno trajanje stream-a
                        currentTime = int(currFrameNbr * 0.05)
                        self.timeBox.configure(text="%02d:%02d" % (currentTime // 60, currentTime % 60))
                    
                                    #provjera u kojem modu se treba prikazivati video
                    if self.mode == "normal" and self.state != self.READY:
                        time.sleep(0.1)
                    if self.mode == "slow" and self.state != self.READY:
                        time.sleep(0.3)
                    if self.mode == "fast" and self.state != self.READY:
                        time.sleep(0.001)
                    if self.state == self.READY:
                        break

            except:
                # prestanak oslusivanja u slucaju pauze ili izlaska iz programa
                if self.playEvent.isSet():
                    break

                # Zatvranje RTP socketa u slucaju izlaska iz programa
                if self.exitAcked == 1:
                    self.rtpSocket.shutdown(socket.SHUT_RDWR)
                    self.rtpSocket.close()
                    break

    def upisiFrame(self, data):
        #upisivanje trenutnog okvira u cache fajl
        cachename = CACHE_FILE_NAME + str(self.sessionId) + CACHE_FILE_EXT
        file = open(cachename, "wb")
        file.write(data)
        file.close()
        return cachename

    def azurirajVideo(self, imageFile):
        #azuriranje slike kao video frejma u GUI-ju
        photo = ImageTk.PhotoImage(Image.open(imageFile))
        self.label.configure(image=photo, height=288)
        self.label.image = photo

    def konekcijaNaServer(self):
        #Konekcija na server kroz RTSP TCP sesiju
        self.rtspSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.rtspSocket.connect((self.serverAddr, self.serverPort))
        except:
            tkinter.messagebox.showwarning('Prekinuta konekcija', 'Konekcija na adresi \'%s\' je prekinuta.' % self.serverAddr)

    def posaljiRTSPZahtjev(self, requestCode):
        #slanje rtsp zahtjeva serveru

        # kreiranje zahtjeva
        if requestCode == self.SETUP and self.state == self.INIT:
            threading.Thread(target=self.preuzmiRTSPOdgovor).start()
            self.rtspSeq = 1

            request = "SETUP " + str(self.fileName) + " RTSP/1.0\n"
            request += "CSeq: " + str(self.rtspSeq) + "\n"
            request += "Transport: RTP/UDP; client_port= " + str(self.rtpPort)
            self.requestSent = self.SETUP

        elif requestCode == self.PLAY and self.state == self.READY:
            self.rtspSeq += 1
            request = "PLAY " + str(self.fileName) + " RTSP/1.0\n"
            request += "CSeq: " + str(self.rtspSeq) + "\n"
            request += "Session: " + str(self.sessionId)
            self.requestSent = self.PLAY

        elif requestCode == self.PAUSE and self.state == self.PLAYING:
            self.rtspSeq += 1
            request = "PAUSE " + str(self.fileName) + " RTSP/1.0\n"
            request += "CSeq: " + str(self.rtspSeq) + "\n"
            request += "Session: " + str(self.sessionId)
            self.requestSent = self.PAUSE


        elif requestCode == self.SLOWER:
            self.rtspSeq += 1
            request = "SLOW DOWN " + str(self.fileName) + " RTSP/1.0\n"
            request += "CSeq: " + str(self.rtspSeq) + "\n"
            request += "Session: " + str(self.sessionId)
        
        elif requestCode == self.FASTER:
            self.rtspSeq += 1
            request = "SPEED UP " + str(self.fileName) + " RTSP/1.0\n"
            request += "CSeq: " + str(self.rtspSeq) + "\n"
            request += "Session: " + str(self.sessionId)

        elif requestCode == self.EXIT and not self.state == self.INIT:
            self.rtspSeq += 1
            request = "EXIT " + str(self.fileName) + " RTSP/1.0\n"
            request += "CSeq: " + str(self.rtspSeq) + "\n"
            request += "Session: " + str(self.sessionId)
            self.requestSent = self.EXIT

        else:
            return

        # slanje rtsp zahtjeva koristeci rtsp socket
        self.rtspSocket.send(request.encode())
        print('\nPoslani podaci:\n' + request)

    def preuzmiRTSPOdgovor(self):
        #dobavljanje rtsp odgovora sa servera
        while True:
            reply = self.rtspSocket.recv(1024)
            if reply:
                self.procitajRTSPOdgovor(reply.decode("utf-8"))
            if self.requestSent == self.EXIT:
                self.rtspSocket.shutdown(socket.SHUT_RDWR)
                self.rtspSocket.close()
                break

    def procitajRTSPOdgovor(self, data):
       #parsiranje odgovora
        lines = data.split('\n')
        seqNum = int(lines[1].split(' ')[1])

        # procesiranje samo ako je isti broj sekvence
        if seqNum == self.rtspSeq:
            session = int(lines[2].split(' ')[1])
            # Postavljanje id sesije
            if self.sessionId == 0:
                self.sessionId = session

            # procesiranje samo ako je isti id sesije
            if self.sessionId == session:
                if int(lines[0].split(' ')[1]) == 200:
                    if self.requestSent == self.SETUP:
                        self.state = self.READY
                        self.otvoriRTPPort()
                        self.setup1["state"] = "disabled"
                        self.start["state"] = "normal"
                        self.pause["state"] = "disabled"
                        self.rewindforward["state"] = "disabled"
                        self.rewindback["state"] = "disabled"
                        self.exit["state"] = "normal"

                    elif self.requestSent == self.PLAY:
                        self.state = self.PLAYING
                        self.startTime = time.time()
                        self.bytesReceived = 0
                        self.setup1["state"] = "disabled"
                        self.start["state"] = "disabled"
                        self.rewindforward["state"] = "normal"
                        self.rewindback["state"] = "normal"
                        self.pause["state"] = "normal"
                        self.exit["state"] = "normal"

                    elif self.requestSent == self.PAUSE:
                        self.state = self.READY
                        self.playEvent.set()
                        dataRate = int(self.bytesReceived / (time.time() - self.startTime))
                        print("Brzina prenosa podataka je: " + str(dataRate) + " bytes/sec\n")
                        self.setup1["state"] = "disabled"
                        self.start["state"] = "normal"
                        self.pause["state"] = "disabled"
                        self.exit["state"] = "normal"
                        self.rewindforward["state"] = "disabled"
                        self.rewindback["state"] = "disabled"

                    elif self.requestSent == self.EXIT:
                        self.state = self.INIT
                        self.exitAcked = 1

    def otvoriRTPPort(self):
        #otvaranje rtp socketa na portu
        self.rtpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # timeout socketa je 0.5 sec
        self.rtpSocket.settimeout(0.5)

        try:
            # postavljanje rtp porta uz adresu
            self.rtpSocket.bind(("0.0.0.0", self.rtpPort))
        except:
            tkinter.messagebox.showwarning('Nemoguce povezati port', 'Nemoguce povezati port PORT=%d' % self.rtpPort)

    def handler(self):
        #Zatvaranje prozora
        self.zaustaviVideo()
        if tkinter.messagebox.askokcancel("Zatvoriti?", "Da li ste sigurni da zelite prekinuti rad programa?"):
            self.zatvori()
        else:
            self.pokreniVideo()
