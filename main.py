__author__ = "Mats Mandelkow"
__version__ = "1.0"

"""
Dies ist eine Implementierung einer Chat Anwendung
für den BBC micro:bit mit MicroPython.

Die Klasse Chat nimmt bei der Instanzierung nur
einen Integer für den Start-Channel (0 - 83) und einen
String als Absender-Namen als Konstruktor-Variablen
entgegen.
Sie enthält die Funktionen send(), get() und
channel_config(), deren Aufruf von run() gehändelt
wird.
Die verschiedenen oben genannten Modi sind über das
Logo erreichbar. Standardmäßig ist send() eingestellt.
"""

import microbit as mb
import radio
from time import sleep

SETTINGS: mb.Image = mb.Image("90909:"
                              "09990:"
                              "99099:"
                              "09990:"
                              "90909:")

class Chat:
    def __init__(self, group, name):
        self.group: int = group
        self.message: str = ""
        self.mode: int = 0
        self.letter: int = 0
        self.name: str = name
        self.incoming: list = []
        self.ALPHABET: list = [
            "A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M",
            "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z",
            " "
        ]

        radio.on()
        radio.config(group=self.group)
        

    def run(self):
        if self.mode == 0:
            mb.display.show(mb.Image.ARROW_N)
            self.send()
        elif self.mode == 1:
            mb.display.show(mb.Image.ARROW_S)
            self.get()
        elif self.mode == 2:
            mb.display.show(SETTINGS)
            self.group_config()
        else:
            self.mode = 0

        new = radio.receive()
        if new != None:
            self.incoming.append(new)
            

    def send(self):
        self.message = ""
        self.message += ("%s: " % self.name)
        mb.button_a.was_pressed()
        mb.button_b.was_pressed()

        # send whole message
        while not (mb.button_a.was_pressed() and mb.button_b.was_pressed()):
            # append single character
            while not mb.button_a.was_pressed():
                mb.display.show(self.ALPHABET[self.letter], wait=False)

                if mb.button_b.was_pressed():
                    self.letter += 1

                if self.letter > 26:
                    self.letter = 0

                if mb.pin_logo.is_touched():
                    self.mode += 1
                    sleep(0.5)
                    return

                #sleep(0.1)

            self.message += self.ALPHABET[self.letter]
            self.letter = 0

        if self.message == ("%s: " % self.name):
            return

        radio.send(self.message[0:-1])
        

    def get(self):
        mb.button_a.was_pressed()
        mb.button_b.was_pressed()

        for i in self.incoming:
            while 1:
                mb.display.scroll(i, wait=False)
    
                if mb.button_b.was_pressed():
                    break

                if mb.pin_logo.is_touched():
                    self.mode += 1
                    sleep(0.5)
                    return

        if mb.pin_logo.is_touched():
                self.mode += 1
                sleep(0.5)
                return

        self.incoming = []
        

    def group_config(self):
        mb.button_a.was_pressed()
        mb.button_b.was_pressed()

        while not (mb.button_a.is_pressed() and mb.button_b.is_pressed()):
            if mb.button_a.was_pressed():
                self.group -= 1
                if self.group < 0:
                    self.group = 255
                mb.display.scroll(self.group, wait=False)
            elif mb.button_b.was_pressed():
                self.group += 1
                if self.group > 255:
                    self.group = 0
                mb.display.scroll(self.group, wait=False)

            if mb.pin_logo.is_touched():
                    self.mode += 1
                    sleep(0.5)
                    return

        radio.config(group=self.group)
        

if __name__ == '__main__':
    device: Chat = Chat(0, "Mats")

    while 1:
        device.run()