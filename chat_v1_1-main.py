__author__ = "Mats Mandelkow"
__version__ = "1.1"

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

SETTINGS: mb.Image = mb.Image("90909:09990:99099:09990:90909:")


class Chat:
    def __init__(self, group, name):
        self.group: int = group
        self.message: str = ""
        self.mode: int = 0
        self.letter: int = 0
        self.name: str = name.upper()
        self.incoming: list = []
        self.ALPHABET: list = [
            "A",
            "B",
            "C",
            "D",
            "E",
            "F",
            "G",
            "H",
            "I",
            "J",
            "K",
            "L",
            "M",
            "N",
            "O",
            "P",
            "Q",
            "R",
            "S",
            "T",
            "U",
            "V",
            "W",
            "X",
            "Y",
            "Z",
            " ",
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
        if new is not None:
            self.incoming.append(new)

    def send(self):
        self.message = ""
        self.message += "%s: " % self.name
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

                # sleep(0.1)

            self.message += self.ALPHABET[self.letter]
            self.letter = 0

        if self.message == ("%s: " % self.name):
            return

        send: str = self.encrypt(self.message[0:-1])
        radio.send(send)

    def get(self):
        mb.button_a.was_pressed()
        mb.button_b.was_pressed()

        for i in range(len(self.incoming)):
            mb.display.scroll(self.decrypt(self.incoming[i]), wait=False)

            while 1:
                if mb.button_b.was_pressed():
                    break

                if mb.pin_logo.is_touched():
                    self.mode += 1
                    sleep(0.5)
                    return
            self.incoming.pop(i)

        if mb.pin_logo.is_touched():
            self.mode += 1
            sleep(0.5)
            return

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

    def key_gen(self, message: str) -> tuple:
        split: list = message.split(": ")
        key_base: str = split[0]
        key: str = key_base

        if len(key_base) != len(split[1]):
            for i in range(len(split[1]) - len(key_base)):
                key += key_base[i % len(key_base)]

        return (key, split[1], split[0])

    def encrypt(self, msg_plain: str) -> str:
        encrypted: str = ""
        prepare: tuple = self.key_gen(msg_plain)
        msg: str = prepare[1]

        for i in range(len(msg)):
            encrypted += self.ALPHABET[
                (self.ALPHABET.index(msg[i]) + self.ALPHABET.index((prepare[0])[i]))
                % len(self.ALPHABET)
            ]

        return prepare[2] + ": " + encrypted

    def decrypt(self, msg_encrypted: str) -> str:
        decrypted: str = ""
        prepare: tuple = self.key_gen(msg_encrypted)
        key: str = prepare[0]
        encrypted: str = prepare[1]

        for i in range(len(encrypted)):
            decrypted += self.ALPHABET[
                (self.ALPHABET.index(encrypted[i]) - self.ALPHABET.index(key[i]))
                % len(self.ALPHABET)
            ]

        return prepare[2] + ": " + decrypted


if __name__ == "__main__":
    device: Chat = Chat(0, "MATS")

    while 1:
        device.run()

