import sys
import sshrichclient
import paramiko
import system

cmdNetLink = "sudo -u shareterm /usr/share/shareterm/createlink"

config = system.Config(sys.argv[1:])
hostname = config.SHARESERV
port = int(config.SSHPORT)
username = config.NETUSER
password = ''

if hasattr(config, 'COMMAND'):
    cmdNetLink = config.COMMAND

paramiko.util.log_to_file('/tmp/shareterm.log')

#Try to connect to the server
try:
    client = sshrichclient.SSHRichClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.WarningPolicy)
    client.connect(hostname, port, username)
except Exception, e:
    print 'MSG="Can\'t connect to server : %s: %s"' % (e.__class__, e)
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
    print 'MSG="Error while sending key : %s: %s"' % (e.__class__, e)

stdin, stdout, stderr = client.exec_command(cmdNetLink)
stdin.write(pkey)
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

#Open remote connection
client.remote_forward(params['NEWPORT'], 'localhost', 22)

while True:
    pass

