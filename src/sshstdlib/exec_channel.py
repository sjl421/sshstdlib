import functools
import socket


def check_active_timeout(func):
    @functools.wraps(func)
    def wrapper(channel, *args, **kwargs):
        channel.updatetimeout()
        while True:
            try:
                rv = func(channel, *args, **kwargs)
                return rv
            except socket.timeout:
                if not channel.ping():
                    raise
    return wrapper


class ExecChannel(object):

    def __init__(self, client):
        self.client = client
        self.check_channel = None
        self.exec_channel = None

    def start(self, command):
        if self.client.timeout:
            self.check_channel = self.client.transport.open_session()
        self.exec_channel = self.client.transport.open_session()
        self.updatetimeout()
        if self.check_channel is not None:
            self.check_channel.exec_command("/bin/cat")
        self.exec_channel.exec_command(command)

    def updatetimeout(self):
        if self.exec_channel is not None:
            self.exec_channel.settimeout(self.client.timeout)
        if self.check_channel is not None:
            self.check_channel.settimeout(self.client.timeout)

    @check_active_timeout
    def recv_exit_status(self):
        event = self.exec_channel.status_event
        status = event.wait(self.client.timeout)
        if status == False:
            raise socket.timeout()
        return self.exec_channel.exit_status

    @check_active_timeout
    def _send(self, data):
        return self.exec_channel.send(data)

    @check_active_timeout
    def _recv(self, nbytes):
        return self.exec_channel.recv(nbytes)

    @check_active_timeout
    def _recv_stderr(self, nbytes):
        return self.exec_channel.recv(nbytes)

    def close_stdin(self):
        self.exec_channel.shutdown_write()

    def write(self, data):
        self.exec_channel.settimeout(self.client.timeout)
        while len(data):
            bytes_sent = self._send(data)
            data = data[bytes_sent:]

    def read_exact(self, n):
        to_read = n
        data = ""
        while to_read:
            read_bytes = self._recv(to_read)
            if read_bytes == "":
                raise Exception("EOF")
            data += read_bytes
            to_read -= len(read_bytes)
        return data

    def _get_ping_response(self):
        to_read = len("ping\n")
        data = ""
        while to_read:
            assert not self.check_channel.closed, "Ping channel closed prematurely"
            read_bytes = self.check_channel.recv(to_read)
            to_read -= len(read_bytes)
            data += read_bytes
        return data

    def ping(self):
        if self.check_channel is None:
            return True
        self.check_channel.settimeout(self.client.timeout)
        try:
            self.check_channel.send("ping\n")
            data = self._get_ping_response()
            assert data == "ping\n", "Received unexpected ping reply: %r" % (data, )
        except socket.timeout:
            return False
        return True

    @property
    def closed(self):
        return self.exec_channel.closed

    def close(self):
        if self.check_channel is not None and not self.check_channel.closed:
            self.check_channel.shutdown(2)
        if self.exec_channel is not None and not self.exec_channel.closed:
            self.exec_channel.shutdown(2)       

    def get_stderr(self):
        return self.exec_channel.in_stderr_buffer.empty()

    def communicate(self, data=""):
        if data != "":
            self.write(data)
            self.close_stdin()
        exit_code = self.recv_exit_status()
        return exit_code, self.exec_channel.in_buffer.empty(), self.exec_channel.in_stderr_buffer.empty()

    def __enter__(self):
        return  self

    def __exit__(self, *args, **kwargs):
        self.close()
