# Copyright (C) 2003-2007  Robey Pointer <robeypointer@gmail.com>
# Copyright (C) 2012  Adrien Lelong <contact@lelongdunet.com>
#
# This file is part of paramiko.
#
# Paramiko is free software; you can redistribute it and/or modify it under the
# terms of the GNU Lesser General Public License as published by the Free
# Software Foundation; either version 2.1 of the License, or (at your option)
# any later version.
#
# Paramiko is distrubuted in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Paramiko; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA.


import socket
import sys
import os
import array
import fcntl
import signal

# windows does not have termios...
try:
    import termios
    import tty
    has_termios = True
except ImportError:
    has_termios = False


def interactive_shell(chan):
    if has_termios:
        posix_shell(chan)
    else:
        windows_shell(chan)

def get_term_env():
    if not has_termios:
        return {}
    # Get the terminal size and type of the real terminal.
    buf = array.array('h', [0, 0, 0, 0])
    fcntl.ioctl(sys.stdin.fileno(), termios.TIOCGWINSZ, buf, True)
    env = {}
    env['term'] = os.environ['TERM']
    env['width'] = buf[1]
    env['height'] = buf[0]
    return env

def set_size(chan):
    # Get the terminal size of the real terminal, set it on the channel pty.
    buf = array.array('h', [0, 0, 0, 0])
    fcntl.ioctl(sys.stdin.fileno(), termios.TIOCGWINSZ, buf, True)
    chan.resize_pty(buf[1], buf[0])


def posix_shell(chan):
    import select
    
    class signal_winch:
        def __init__(self, chan):
            self.chan = chan
        def __call__(self, signum, frame):
            set_size(self.chan)

    oldtty = termios.tcgetattr(sys.stdin)
    old_handler = signal.signal(signal.SIGWINCH, signal_winch(chan))
    try:
        tty.setraw(sys.stdin.fileno())
        tty.setcbreak(sys.stdin.fileno())
        chan.settimeout(0.0)

        while True:
            try:
                r, w, e = select.select([chan, sys.stdin], [], [])
            except select.error, e:
                if e[0] == 4:   # Interrupted system call.
                    continue

            if chan in r:
                try:
                    x = chan.recv(1024)
                    if len(x) == 0:
                        print '\r\n*** EOF\r\n',
                        break
                    while x != '':
                        n = os.write(sys.stdout.fileno(), x)
                        x = x[n:]
                except socket.timeout:
                    pass
            if sys.stdin in r:
                x = os.read(sys.stdin.fileno(), 1)
                if len(x) == 0:
                    break
                chan.send(x)

    finally:
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, oldtty)
        signal.signal(signal.SIGWINCH, old_handler)

    
# thanks to Mike Looijmans for this code
def windows_shell(chan):
    import threading

    sys.stdout.write("Line-buffered terminal emulation. Press F6 or ^Z to send EOF.\r\n\r\n")
        
    def writeall(sock):
        while True:
            data = sock.recv(256)
            if not data:
                sys.stdout.write('\r\n*** EOF ***\r\n\r\n')
                sys.stdout.flush()
                break
            sys.stdout.write(data)
            sys.stdout.flush()
        
    writer = threading.Thread(target=writeall, args=(chan,))
    writer.start()
        
    try:
        while True:
            d = sys.stdin.read(1)
            if not d:
                break
            chan.send(d)
    except EOFError:
        # user hit ^Z or F6
        pass
