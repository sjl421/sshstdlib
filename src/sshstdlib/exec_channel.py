import functools
import socket


def check_active_timeout(func):
    @functools.wraps(func)
    def wrapper(channel, *args, **kwargs):
        if channel._direct:
            return func(channel, *args, **kwargs)
        if channel.exec_channel is not None:
            channel.exec_channel.settimeout(channel.client.timeout)
        while True:
            try:
                rv = func(channel, *args, **kwargs)
                return rv
            except socket.timeout:
                if not channel.client.ping():
                    raise
    return wrapper


class ExecChannel(object):

    def __init__(self, client, _direct=False):
        self._direct = _direct
        self.client = client
        self.exec_channel = None

    @check_active_timeout
    def start(self, command):
        self.exec_channel = self.client.transport.open_session()
        self.exec_channel.settimeout(self.client.timeout)
        self.exec_channel.exec_command(command)

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

    @check_active_timeout
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

    @property
    def closed(self):
        return self.exec_channel.closed

    @check_active_timeout
    def close(self):
        if self.exec_channel is not None and not self.exec_channel.closed:
            self.exec_channel.shutdown(2)       

    def get_stderr(self):
        return self.exec_channel.in_stderr_buffer.empty()

    def communicate(self, data=""):
        if data != "":
            self.write(data)
            self.close_stdin()
        exit_code = self.recv_exit_status()
        return (exit_code, 
                self.exec_channel.in_buffer.empty(), 
                self.exec_channel.in_stderr_buffer.empty())

    def __enter__(self):
        return  self

    def __exit__(self, *args, **kwargs):
        self.close()
