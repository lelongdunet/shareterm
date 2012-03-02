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
import sshrichclient
import paramiko
import system

cmdNetLink = "sudo -u shareterm /usr/share/shareterm/createlink"
VNCBASEPORT = 5900

config = system.Config(sys.argv[1:])
hostname = config.SHARESERV
port = int(config.SSHPORT)
username = config.NETUSER
password = ''

if hasattr(config, 'COMMAND'):
    cmdNetLink = config.COMMAND

import logging
logging.basicConfig(filename='/tmp/shareterm.log',level=logging.DEBUG)
paramiko.util.log_to_file('/tmp/shareterm_ssh.log')

def printError(msg):
    print 'MSG=%s' % msg
    logging.error(msg)


#Try to connect to the server
try:
    client = sshrichclient.SSHRichClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.WarningPolicy)
    client.connect(hostname, port, username)
except Exception, e:
    printError("Can\'t connect to server : %s: %s" % (e.__class__, e))
    try:
        client.close()
    except:
        pass
    sys.exit(1)

#First connection, send the private key to server and get ports
try:
    fkey = open(config.SSHKEYFILE)
    pkey = fkey.read()
    fkey.close()
except Exception, e:
    printError('Error while sending key : %s: %s' % (e.__class__, e))
    sys.exit(2)

try:
    fvncpw = open(os.path.expanduser('~/.vnc/passwd'))
    vncpw64 = system.myEncod(fvncpw.read())
    fvncpw.close()
    logging.info('VNC password encoded: %s' % vncpw64)
except Exception, e:
    logging.warning('No VNC password available. : %s: %s' % (e.__class__, e))

stdin, stdout, stderr = client.exec_command(cmdNetLink)
stdin.write(pkey + '\n')
try:
    stdin.write('VNCPW=%s\n' % vncpw64)
except:
    pass
stdin.channel.shutdown_write()
params = {}
for l in stdout:
    m = l.split('=')
    if len(m) == 2:
        params[m[0].strip()] = m[1].strip()
stdin.close()
client.close()

#Then detach the process, the tunnel is kept open
system.detach()

client.connect(hostname, port, username)

logging.info('Remote forward %(r)s to %(l)i', {'r' : params['NEWPORT'], 'l' : 22})
try:
    client.remote_forward(params['NEWPORT'], 'localhost', 22)
except Exception, e:
    logging.error('Error while forwarding SSH port %s, %s' % (e.__class__, e))

#Open remote connection
try:
    vncport = int(config.VNC_XID)
except Exception, e:
    logging.warning('No valid VNC X session number provided. %s, %s' % (e.__class__, e))
    vncport = 0

try:
    if vncport > 0:
        vncport = vncport + VNCBASEPORT
        logging.info('Remote forward %(r)s to %(l)i', {'r' : params['NEWGPORT'], 'l' : vncport})
        client.remote_forward(params['NEWGPORT'], 'localhost', vncport)
except Exception, e:
    logging.error('Error while forwarding VNC port %s, %s' % (e.__class__, e))

while True:
    pass

