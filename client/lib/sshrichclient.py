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

import socket
import select
import SocketServer
import threading
import mutex

import paramiko

import logging

#Generic functions
def verbose(s):
    try:
        if g_verbose:
            print s
    except:
        pass
    logging.info(s)

#Local port forwarding
class ForwardServer (SocketServer.ThreadingTCPServer):
    daemon_threads = True
    allow_reuse_address = True

class HandleLocal (SocketServer.BaseRequestHandler):

    def handle(self):
        try:
            chan = self.ssh_transport.open_channel('direct-tcpip',
                                                   (self.chain_host, self.chain_port),
                                                   self.request.getpeername())
        except Exception, e:
            verbose('Incoming request to %s:%d failed: %s' % (self.chain_host,
                                                              self.chain_port,
                                                              repr(e)))
            return
        if chan is None:
            verbose('Incoming request to %s:%d was rejected by the SSH server.' %
                    (self.chain_host, self.chain_port))
            return

        verbose('Connected!  Tunnel open %r -> %r -> %r' % (self.request.getpeername(),
                                                            chan.getpeername(), (self.chain_host, self.chain_port)))
        while True:
            r, w, x = select.select([self.request, chan], [], [])
            if self.request in r:
                data = self.request.recv(1024)
                if len(data) == 0:
                    break
                chan.send(data)
            if chan in r:
                data = chan.recv(1024)
                if len(data) == 0:
                    break
                self.request.send(data)
        chan.close()
        verbose('Tunnel closed from %r' % (self.request.getpeername(),))
        self.request.close()

class HandleRemote:
    def __init__(self):
        self.port_assoc = {}

    def assoc(self, server_port, remote_host, remote_port):
        self.port_assoc[int(server_port)] = (remote_host, remote_port)

    def __call__(self, chan, origin, server):
        try:
            server_port = int(server[1])
            dest_host = self.port_assoc[server_port]
        except:
            verbose('Forwarding from %r failed (available assoc are %r)' % (server,self.port_assoc))
            chan.close()
            return
        verbose('Forwarding %r to %r.' % (server, dest_host))
        thr = threading.Thread(target=self.loop, args=(chan, dest_host))
        thr.start()

    def loop(self, chan, dest_host):
        sock = socket.socket()
        try:
            sock.connect(dest_host)
        except Exception, e:
            verbose('Forwarding request to %r failed: %s, %s' % (dest_host, e.__class__, e))
            chan.close()
            return

        verbose('Connected!  Tunnel open %r -> %r' % (chan.getpeername(), dest_host))
        while True:
            r, w, x = select.select([sock, chan], [], [])
            if sock in r:
                data = sock.recv(1024)
                if len(data) == 0:
                    break
                chan.send(data)
            if chan in r:
                data = chan.recv(1024)
                if len(data) == 0:
                    break
                sock.send(data)
        chan.close()
        sock.close()
        verbose('Tunnel closed from %r' % (chan.origin_addr,))


class SSHRichClient(paramiko.SSHClient):
    """ Provide some additional features to the paramiko SSHClient
    Added methods allows to easily add port forwarding
    """
    def local_forward_loop(self, local_port, remote_host, remote_port):
        # this is a little convoluted, but lets me configure things for the HandleLocal
        # object.  (SocketServer doesn't give Handlers any way to access the outer
        # server normally.)
        class SubHander (HandleLocal):
            chain_host = remote_host
            chain_port = remote_port
            ssh_transport = self.get_transport()
        ForwardServer(('', local_port), SubHander).serve_forever()

    def local_forward(self, local_port, remote_host, remote_port):
        thr = threading.Thread(target=self.local_forward_loop, args=(local_port, remote_host, remote_port))
        thr.setDaemon(True)
        thr.start()

    def remote_forward(self, server_port, remote_host, remote_port):
        if(not hasattr(self, 'handleRemote')):
            self.handleRemote = HandleRemote()
        self.handleRemote.assoc(server_port, remote_host, remote_port)
        transport = self.get_transport()
        transport.request_port_forward('', server_port, self.handleRemote)


