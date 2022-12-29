from random import randint
import threading, socket

from VideoStream import VideoStream
from RtpPacket import RtpPacket


class Server:
    #moguce akcije na strani klijenta
    SETUP = 'SETUP'
    PLAY = 'PLAY'
    PAUSE = 'PAUSE'
    EXIT = 'EXIT'

    #stanja programa
    INIT = 0
    READY = 1
    PLAYING = 2
    state = INIT

    #status kod 200, 4/4 i 500
    OK_200 = 0
    FILE_NOT_FOUND_404 = 1
    CON_ERR_500 = 2

    clientInfo = {}

    def __init__(self, clientInfo):
        self.clientInfo = clientInfo

    def pokreni(self):
        threading.Thread(target=self.preuzmiRTSPZahtjev).start()

    def preuzmiRTSPZahtjev(self):
        #preuzmi rtso zahtjev od klijenta
        connSocket = self.clientInfo['rtspSocket'][0]
        while True:
            data = connSocket.recv(256)
            if data:
                print("Dobijeni podaci:\n" + data.decode("utf-8"))
                self.procesirajRTSPZahtjev(data.decode("utf-8"))

    def procesirajRTSPZahtjev(self, data):
        #procesiranje rtsp zahtjeva
        # dobijanje tipa zahtjeva
        request = data.split('\n')
        line1 = request[0].split(' ')
        requestType = line1[0]

        # dobijanje naziva videa koji se treba reproducirati
        filename = line1[1]

        # dobijanje RTSP broja sekvence
        seq = request[1].split(' ')

        # procesiranje SETUP zahtjeva
        if requestType == self.SETUP:
            if self.state == self.INIT:
                # azuriranje trenutnog stanja
                print("processing SETUP\n")

                try:
                    self.clientInfo['videoStream'] = VideoStream(filename)
                    self.state = self.READY
                except IOError:
                    self.odgovoriRTSP(self.FILE_NOT_FOUND_404, seq[1])

                # generisanje nasumicnog broja za id sesije
                self.clientInfo['session'] = randint(100000, 999999)

                # slanje RTSP odgovora
                self.odgovoriRTSP(self.OK_200, seq[1])

                # Koristenje RTP ili UDP porta iz posljednje linije
                self.clientInfo['rtpPort'] = request[2].split(' ')[3]

        # procesiranje PLAY zahtjeva
        elif requestType == self.PLAY:
            if self.state == self.READY:
                print("processing PLAY\n")
                self.state = self.PLAYING

                # kreiranje novog socketa za RTP/UDP
                self.clientInfo["rtpSocket"] = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

                self.odgovoriRTSP(self.OK_200, seq[1])

                # Kreiranje novog thread-a i slanje RTP paketa
                self.clientInfo['event'] = threading.Event()
                self.clientInfo['worker'] = threading.Thread(target=self.posaljiRTP)
                self.clientInfo['worker'].start()

        # procesiranje PAUSE zahtjeva
        elif requestType == self.PAUSE:
            if self.state == self.PLAYING:
                print("processing PAUSE\n")
                self.state = self.READY
                self.clientInfo['event'].set()
                self.odgovoriRTSP(self.OK_200, seq[1])

        # procesiranje EXIT zahtjeva
        elif requestType == self.EXIT:
            print("processing EXIT\n")
            self.clientInfo['event'].set()
            self.odgovoriRTSP(self.OK_200, seq[1])
            # zatvaranje rtp socketa
            self.clientInfo['rtpSocket'].close()


    def posaljiRTP(self):
        #slanje RTP paketa preko UDP
        while True:
            self.clientInfo['event'].wait(0.05)

            # Zaustavljanje slanja ako je dobijen PAUSE ili EXIT zahtjev
            if self.clientInfo['event'].isSet():
                break

            data = self.clientInfo['videoStream'].nextFrame()
            if data:
                frameNumber = self.clientInfo['videoStream'].frameNbr()
                try:
                    address = self.clientInfo['rtspSocket'][1][0]
                    port = int(self.clientInfo['rtpPort'])
                    self.clientInfo['rtpSocket'].sendto(self.kreirajRTP(data, frameNumber), (address, port))
                except:
                    print("...")

    def kreirajRTP(self, payload, frameNbr):
        #RTP paketiziranje podataka
        version = 2
        padding = 0
        extension = 0
        cc = 0
        marker = 0
        pt = 26  # MJPEG
        seqnum = frameNbr
        ssrc = 0

        rtpPacket = RtpPacket()
        rtpPacket.encode(version, padding, extension, cc, seqnum, marker, pt, ssrc, payload)
        return rtpPacket.getPacket()

    def odgovoriRTSP(self, code, seq):
        #slanje rtsp odgovora klijentu
        if code == self.OK_200:
            reply = 'RTSP/1.0 200 OK\nCSeq: ' + seq + '\nSession: ' + str(self.clientInfo['session'])
            connSocket = self.clientInfo['rtspSocket'][0]
            connSocket.send(reply.encode())

        # Poruke o greškama
        elif code == self.FILE_NOT_FOUND_404:
            print("404 NOT FOUND")
        elif code == self.CON_ERR_500:
            print("500 CONNECTION ERROR")
