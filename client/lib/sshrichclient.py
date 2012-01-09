import socket
import select
import SocketServer
import threading

import paramiko

#Generic functions
def verbose(s):
    try:
        if g_verbose:
            print s
    except:
        pass

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

def handleRemote(chan, host, port):
    sock = socket.socket()
    try:
        sock.connect((host, port))
    except Exception, e:
        verbose('Forwarding request to %s:%d failed: %r' % (host, port, e))
        return
    
    verbose('Connected!  Tunnel open %r -> %r -> %r' % (chan.origin_addr,
                                                        chan.getpeername(), (host, port)))
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

    def remote_forward_loop(self, server_port, remote_host, remote_port):
        transport = self.get_transport()
        transport.request_port_forward('', server_port)
        while True:
            chan = transport.accept(1000)
            if chan is None:
                continue
            thr = threading.Thread(target=handleRemote, args=(chan, remote_host, remote_port))
            thr.setDaemon(True)
            thr.start()

    def remote_forward(self, server_port, remote_host, remote_port):
        thr = threading.Thread(target=self.remote_forward_loop, args=(server_port, remote_host, remote_port))
        thr.setDaemon(True)
        thr.start()


