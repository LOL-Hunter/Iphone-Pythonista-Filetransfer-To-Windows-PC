import pysettings.tk as tk
from pysettings import Queue
from pysettings.geometry import Rect, Location2D
from threading import Thread
import os, socket as s
from time import sleep
import numpy
from PIL.Image import fromarray, open as open_
import win32clipboard as clip
from io import BytesIO
from tempfile import gettempdir
import tracemalloc
import enum

def printSnapshot(s1, s2):
    top_stats = s2.compare_to(s1, 'lineno')

    for stat in top_stats[:10]:
        print(stat)


DATA_PATH = os.path.join(gettempdir(), "tempImage.png")


class Server:
    def __init__(self, port):
        self.queue = Queue()
        self.port = port
        self.connected = False

    def connect(self):
        self.socket = s.socket(s.AF_INET, s.SOCK_STREAM)
        self.socket.setsockopt(s.SOL_SOCKET, s.SO_REUSEADDR, 1)
        self.socket.bind(("", self.port))
        self.socket.listen(1)
        self._clientSocket, self._clientAddress = self.socket.accept()
        self.connected = True
        print("terminate Connect")

    def getResponse(self):
        return self._clientSocket.recv(2048)

    def isConnected(self):
        return self.connected

    def send(self, param):
        self._clientSocket.send(bytes(param, "utf8"))

    def close(self):
        if not self.connected: return
        self.connected = False
        try:
            self._clientSocket.close()
        except:
           pass


class FileTransferPlugin(tk.Tk):
    def __init__(self):
        super().__init__()
        self.hide()
        self.onEnable()
        tracemalloc.start()
        self.mainloop()

    def onEnable(self):
        self.server = Server(25565)

        self.proc = tk.Toplevel(self)
        self.proc.setCloseable(False)
        self.proc.setWindowSize(250, 50)
        self.proc.centerWindowOnScreen()
        self.proc.hide()
        self.proc.setTitle("Receiving File...")

        self.bar = tk.Progressbar(self.proc)
        self.bar.placeRelative(fixHeight=20, changeWidth=-40, changeX=20)

        self.info = tk.Label(self.proc)
        self.info.placeRelative(fixHeight=25, stickDown=True)

        Thread(target=self.server.connect).start()
        Thread(target=self.update).start()

    def restartSocket(self):
        self.server.close()
        Thread(target=self.server.connect).start()

    def update(self):
        length_recved = False
        canClose = False
        receiving = False
        index = 0
        length = 0

        while True:
            if not receiving:
                sleep(1)
            if self.server.isConnected():
                anw = self.server.getResponse()
                if anw != b"":
                    receiving = True
                    if not length_recved:
                        out = str(anw, "utf8")
                        length = int(out.split(":")[1])
                        self.proc.show()
                        self.server.send(".")
                        length_recved = True
                        continue
                    if not canClose:
                        file = open(DATA_PATH, "wb")
                    file.write(anw)
                    if index % 10 == 0:
                        perc = (2048*index) / length
                        if perc*100 > 100:
                            self.bar.setPercentage(100)
                        else:
                            self.bar.setPercentage(perc)
                        perc = perc if perc < 1 else 1
                        self.info.setText(f"{round(perc*100, 1)} %")
                    index += 1
                    canClose = True
                if anw == b"" and canClose:
                    file.close()
                    self.proc.hide()
                    index = 0
                    receiving = False
                    canClose = False
                    length_recved = False
                    self.server.close()
                    self.openImageShower(fromarray(numpy.load(DATA_PATH)))
                    Thread(target=self.server.connect).start()

    def openImageShower(self, image):
        print("#"*20,"BEFORE")
        snap1 = tracemalloc.take_snapshot()
        def send_to_clipboard(clip_type, data):
            clip.OpenClipboard()
            clip.EmptyClipboard()
            clip.SetClipboardData(clip_type, data)
            clip.CloseClipboard()
        def copy(e):
            output = BytesIO()
            image2 = image.convert("RGB")
            image2.save(output, "BMP")
            image.close()
            image2.close()
            send_to_clipboard(clip.CF_DIB, output.getvalue()[14:])
            output.close()
            master.destroy()
            print("#" * 20, "AFTER")
            snap2 = tracemalloc.take_snapshot()
            printSnapshot(snap1, snap2)
            print("##################SILGLE#######################")
            top_stats = snap2.statistics("lineno")
            for stat in top_stats[:10]:
                print(stat)


        def save(e):
            master.destroy()
            path = tk.FileDialog.saveFile(master, "Save as...", initialpath=os.path.join(os.path.join(os.path.expanduser('~')), 'Desktop'),types=[".png"])
            if path is None:
                tk.SimpleDialog.askError(master, "Invalid Path! [None]\nSend Image again!")
                return
            path = path if path.endswith(".png") else path+".png"
            image.save(path)

        master = tk.Toplevel(self)
        master.setTitle("PyImageSend v1.0")
        master.setWindowSize(1000, 800)
        master.centerWindowOnScreen(True)

        imgLabel = tk.Label(master)
        imgObj = tk.PILImage.loadImageFromPIL(image)

        rect = Rect.fromLocWidthHeight(Location2D(0, 0), imgObj.getWidth(), imgObj.getHeight())

        rect.resizeToRectWithRatio(
            Rect.fromLocWidthHeight(Location2D(0, 0), 1000, 800-50)
        )

        imgObj.resizeTo(rect.getWidth(), rect.getHeight())
        imgLabel.setImage(imgObj)
        imgLabel.placeRelative(changeHeight=-50)

        copyB = tk.Button(master)
        copyB.setText("Copy Image")
        copyB.setCommand(copy)
        copyB.placeRelative(stickDown=True, fixHeight=50, xOffsetLeft=50)

        saveB = tk.Button(master)
        saveB.setText("Save as")
        saveB.setCommand(save)
        saveB.placeRelative(stickDown=True, fixHeight=50, xOffsetRight=50)

        master.show()


FileTransferPlugin()
