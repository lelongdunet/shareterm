# This file is part of the shareterm project
# Copyright (C) 2011-2012  Adrien LELONG
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import sys, os
import logging
import binascii

def logFileHandler(filename, level):
    logFile = logging.FileHandler(filename)
    logFile.setLevel(level)
    logFile.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    return logFile

def logOutHandler(level):
    logOut = logging.StreamHandler()
    logOut.setLevel(level)
    logOut.setFormatter(logging.Formatter('%(message)s'))
    return logOut

def myEncod(s):
    return binascii.b2a_base64(s).replace('=', ':')

def myDecod(s):
    return binascii.a2b_base64(s.replace(':', '='))

def toFile(filename, text, mode='w'):
    print 'Open\n'
    f = open(filename, mode)
    print 'Read\n'
    f.write(text)
    print 'Close\n'
    f.close()
    print 'closed\n'

class Config:
    def __init__(self, argList):
        for l in argList:
            m = l.split('=')
            if len(m) == 2:
                setattr(self, m[0].strip(), m[1].strip())

def detach (stdin='/dev/null', stdout='/dev/null', stderr='/dev/null', wd='/'):
    ''' Fork the current process as a daemon, redirecting standard file
        descriptors (by default, redirects them to /dev/null).
    '''
    # Perform first fork.
    try:
        pid = os.fork( )
        if pid > 0:
            print "CPID=" + str(pid)
            sys.exit(0) # Exit first parent.
    except OSError, e:
        sys.stderr.write("fork #1 failed: (%d) %s\n" % (e.errno, e.strerror))
        sys.exit(1)
    # Decouple from parent environment.
    os.chdir(wd)

    for f in sys.stdout, sys.stderr: f.flush( )
    si = file(stdin, 'r')
    so = file(stdout, 'a+')
    se = file(stderr, 'a+', 0)
    os.dup2(si.fileno( ), sys.stdin.fileno( ))
    os.dup2(so.fileno( ), sys.stdout.fileno( ))
    os.dup2(se.fileno( ), sys.stderr.fileno( ))

def _example_main ( ):
    ''' Example main function: print a count & timestamp each second '''
    import time
    sys.stdout.write('Daemon started with pid %d\n' % os.getpid( ) )
    sys.stdout.write('Daemon stdout output\n')
    sys.stderr.write('Daemon stderr output\n')
    c = 0
    while True:
        sys.stdout.write('%d: %s\n' % (c, time.ctime( )))
        sys.stdout.flush( )
        c = c + 1
        time.sleep(1)

if __name__ == "__main__":
    detach('/dev/null','/tmp/daemon.log','/tmp/daemon.log')
    _example_main( )

