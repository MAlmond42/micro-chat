__author__ = "Mats Mandelkow"
__version__ = "1.1"

"""
Micro:bit V2 messaging service (MicroPython)

This is an implementation of a simple chat application for the BBC micro:bit V2.
Features:
 - Write and send messages over the micro:bit radio
 - Read incoming messages
 - Change the radio group (channel) at runtime
 - A very small Vigenère-style cipher is used to "encrypt" messages on send
   and to decrypt incoming messages. The sender name (before ": ") is used
   as the Vigenère keyword.

Usage:
 - The Chat class is instantiated with an initial radio group (0-255) and a
   sender name (string).
 - The run() method selects a mode depending on the internal mode value:
   mode 0: send (default)  -> displays north arrow
   mode 1: get/read         -> displays south arrow
   mode 2: group settings   -> displays settings image
 - The logo touch sensor is used to cycle modes at many points; pressing both
   buttons A and B confirms or finalizes certain actions (e.g. finishing a
   message or applying a channel change).
 - The alphabet used includes A-Z and space. Messages are composed from these
   characters and are case-insensitive (the name is uppercased on init).

Notes:
 - Uses microbit and radio modules for hardware and radio functionality.
 - No structural changes were made — only comments and docstrings were added
   to clarify behavior.
"""

import microbit as mb
import radio
from time import sleep

# A small image used for the settings mode display
SETTINGS: mb.Image = mb.Image("90909:09990:99099:09990:90909:")


class Chat:
    """
    Chat provides simple radio-based messaging for the micro:bit.

    Constructor:
      Chat(group: int, name: str)
        - group: initial radio group (0-255)
        - name: sender name (will be uppercased and prepended to sent messages)

    Public methods:
      run() - main loop handler; decides which mode to run (send/get/group_config)
      send() - interactively build a message and send it (uses Vigenère encrypt)
      get() - display and manage incoming messages (uses Vigenère decrypt)
      group_config() - change radio group interactively
    """

    def __init__(self, group, name):
        # Radio group (channel) used for communication
        self.group: int = group

        # The outgoing message being composed
        self.message: str = ""

        # Mode: 0=send, 1=get, 2=group_config
        self.mode: int = 0

        # Current letter index when composing a message
        self.letter: int = 0

        # Sender name is stored in uppercase for the keyword/encryption
        self.name: str = name.upper()

        # Queue of incoming raw messages received from radio.receive()
        self.incoming: list = []

        # Alphabet used for the Vigenère-like cipher (A-Z plus space)
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

        # Initialize radio hardware and set the configured group
        radio.on()
        radio.config(group=self.group)

    def run(self):
        """
        Main mode dispatcher. Called repeatedly in the top-level loop.
        Shows a small indicator on the display, executes the selected mode,
        and collects any newly received radio messages into the incoming queue.
        """
        if self.mode == 0:
            # Send mode (compose and send messages)
            mb.display.show(mb.Image.ARROW_N)
            self.send()
        elif self.mode == 1:
            # Read/receive mode (view incoming messages)
            mb.display.show(mb.Image.ARROW_S)
            self.get()
        elif self.mode == 2:
            # Radio group configuration mode
            mb.display.show(SETTINGS)
            self.group_config()
        else:
            # Any unknown mode resets to send mode
            self.mode = 0

        # Always check for new radio messages and queue them for later reading.
        # radio.receive() returns a string or None.
        new = radio.receive()
        if new is not None:
            self.incoming.append(new)

    def send(self):
        """
        Compose a message interactively and send it.
        Controls:
         - Button A cycles through characters when pressed (advance after B)
         - Button B selects the currently shown character (appends it)
         - Pressing both A and B together ends composition and sends
         - Touching the logo acts as a mode switch (skips sending and advances)
        Behavior:
         - The sender's name is prepended (NAME: ) automatically.
         - If no characters were appended (only the name), nothing is sent.
         - Message is encrypted with encrypt() before radio.send().
        """
        self.message = ""
        # Start message with sender name and colon-space as convention
        self.message += "%s: " % self.name

        # Clear previous button states
        mb.button_a.was_pressed()
        mb.button_b.was_pressed()

        # Wait for user to finish composing. Finishing condition is pressing
        # both A and B (was_pressed checks for a press event).
        while not (mb.button_a.was_pressed() and mb.button_b.was_pressed()):
            # Loop to select a single character. User holds A to pause on a char,
            # presses B to move to the next char, and touches logo to change mode.
            while not mb.button_a.was_pressed():
                # Display current letter choice without blocking the runtime loop
                mb.display.show(self.ALPHABET[self.letter], wait=False)

                # If B is pressed, move to the next letter option
                if mb.button_b.was_pressed():
                    self.letter += 1

                # Wrap-around (alphabet has 27 entries: 0..26)
                if self.letter > 26:
                    self.letter = 0

                # Logo touch switches to the next mode immediately
                if mb.pin_logo.is_touched():
                    self.mode += 1
                    # small debounce/safety delay so that mode change isn't re-triggered
                    sleep(0.5)
                    return

                # Note: optional small sleep could be added here to reduce CPU usage:
                # sleep(0.1)

            # When A is pressed, accept the currently shown character into the message
            self.message += self.ALPHABET[self.letter]
            # reset letter selection for the next character
            self.letter = 0

        # If only the name prefix exists (no message), do not send
        if self.message == ("%s: " % self.name):
            return

        # Encrypt the composed message (the last character appended handling in
        # the original code expects slicing [0:-1], preserving intended text).
        send: str = self.encrypt(self.message[0:-1])
        radio.send(send)

    def get(self):
        """
        Display and manage incoming messages.
        Controls:
         - Incoming messages are decrypted and scrolled on the display.
         - Press Button B to advance to the next incoming message.
         - Touch the logo to change mode and return immediately.
        Notes:
         - Messages are taken from self.incoming list and removed after showing.
        """
        # Reset button state so first presses are detected cleanly
        mb.button_a.was_pressed()
        mb.button_b.was_pressed()

        # Iterate over queued incoming messages
        for i in range(len(self.incoming)):
            # Decrypt the message before showing it
            mb.display.scroll(self.decrypt(self.incoming[i]), wait=False)

            # Wait until the user presses B to move to the next message,
            # or touches the logo to change mode immediately.
            while 1:
                if mb.button_b.was_pressed():
                    # Move to next message in the queue
                    break

                if mb.pin_logo.is_touched():
                    # Switch mode and return to the main loop
                    self.mode += 1
                    sleep(0.5)
                    return

            # Remove the message we just displayed from the queue
            self.incoming.pop(i)

        # If no more messages and the logo is touched, change mode
        if mb.pin_logo.is_touched():
            self.mode += 1
            sleep(0.5)
            return

    def group_config(self):
        """
        Interactive radio group (channel) configuration.
        Controls:
         - Button A decreases the group number (wraps at 0 -> 255)
         - Button B increases the group number (wraps at 255 -> 0)
         - Press both A and B to confirm and apply the new group via radio.config()
         - Touch logo to cancel/advance mode without applying
        Display:
         - The current numeric group is scrolled on the display whenever it changes.
        """
        # Clear previous button states
        mb.button_a.was_pressed()
        mb.button_b.was_pressed()

        # Loop until both buttons are pressed together (confirmation)
        while not (mb.button_a.is_pressed() and mb.button_b.is_pressed()):
            if mb.button_a.was_pressed():
                # Decrement group (wrap around below 0 to 255)
                self.group -= 1
                if self.group < 0:
                    self.group = 255
                mb.display.scroll(self.group, wait=False)
            elif mb.button_b.was_pressed():
                # Increment group (wrap around above 255 to 0)
                self.group += 1
                if self.group > 255:
                    self.group = 0
                mb.display.scroll(self.group, wait=False)

            # Logo touch acts as immediate mode switch (cancel config)
            if mb.pin_logo.is_touched():
                self.mode += 1
                sleep(0.5)
                return

        # When both buttons pressed, apply the new radio group
        radio.config(group=self.group)

    def key_gen(self, message: str) -> tuple:
        """
        Prepare encryption/decryption key and message body from a full message string.

        Expects messages in the format "NAME: TEXT". Splits on ': ' into:
          - key_base: NAME (used as the keyword)
          - message_text: TEXT

        The returned tuple is (key, message_text, key_base) where key is expanded
        (repeated/truncated) to match the length of message_text so it can be used
        as a Vigenère key.

        Example:
          input: "MATS: HELLO"
          output: ("MATSMA...", "HELLO", "MATS")
        """
        split: list = message.split(": ")
        key_base: str = split[0]
        key: str = key_base

        # Expand the key so it matches the message length if necessary
        if len(key_base) != len(split[1]):
            for i in range(len(split[1]) - len(key_base)):
                key += key_base[i % len(key_base)]

        return (key, split[1], split[0])

    def encrypt(self, msg_plain: str) -> str:
        """
        Encrypt message text using a Vigenère-like cipher with the sender name
        as the keyword. The function expects the full message string including
        the 'NAME: ' prefix (it calls key_gen internally to split it).
        Returns a string in the "NAME: ENCRYPTED_TEXT" format.
        """
        encrypted: str = ""
        prepare: tuple = self.key_gen(msg_plain)
        msg: str = prepare[1]

        # For each character, shift by the alphabet index of the corresponding
        # key character. Wrap around using modulo arithmetic on the alphabet size.
        for i in range(len(msg)):
            encrypted += self.ALPHABET[
                (self.ALPHABET.index(msg[i]) + self.ALPHABET.index((prepare[0])[i]))
                % len(self.ALPHABET)
            ]

        # Prepend original name so receivers can reconstruct the key
        return prepare[2] + ": " + encrypted

    def decrypt(self, msg_encrypted: str) -> str:
        """
        Decrypt a message that was encrypted with encrypt().
        Expects a string in the "NAME: ENCRYPTED_TEXT" format and returns
        "NAME: PLAINTEXT".
        """
        decrypted: str = ""
        prepare: tuple = self.key_gen(msg_encrypted)
        key: str = prepare[0]
        encrypted: str = prepare[1]

        # Reverse the Vigenère-like shift by subtracting key indices
        for i in range(len(encrypted)):
            decrypted += self.ALPHABET[
                (self.ALPHABET.index(encrypted[i]) - self.ALPHABET.index(key[i]))
                % len(self.ALPHABET)
            ]

        return prepare[2] + ": " + decrypted


if __name__ == "__main__":
    # Example startup: group 0, name "MATS"
    device: Chat = Chat(0, "MATS")

    # Main event loop: repeatedly call run() which handles the current mode
    while 1:
        device.run()
