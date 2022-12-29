import sys, socket

from Server import Server


class ServerStart:

    def main(self):
        try:
            SERVER_PORT = int(sys.argv[1])
        except:
            print("[NACIN KORISTENJA: ServerStart.py Server_port (npr ServerStart.py 1600)]\n")
        rtspSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        rtspSocket.bind(('', SERVER_PORT))
        print("RTSP ceka na sljedeci zahtjev...")
        rtspSocket.listen(5)

        # Dibijanje informacija o klijentu (adresa,port) kroz RTSP/TCP sesiju
        while True:
            clientInfo = {}
            clientInfo['rtspSocket'] = rtspSocket.accept()
            Server(clientInfo).pokreni()


if __name__ == "__main__":
    (ServerStart()).main()


