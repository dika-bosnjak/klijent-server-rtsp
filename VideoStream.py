class VideoStream:
    def __init__(self, filename):
        self.filename = filename
        try:
            self.file = open(filename, 'rb')
        except:
            raise IOError
        self.frameNum = 0

    def nextFrame(self):
        #Pronadji sljedeci frame i procitaj 5 bita
        data = self.file.read(5)
        if data:
            try:
                framelength = int(data)

                #Procitaj trenutni sadrzaj frame-a
                data = self.file.read(framelength)
                self.frameNum += 1
            except Exception as e:
                print(e)
        return data

    def frameNbr(self):
        #broj frameova
        return self.frameNum

