import os

from multiprocessing import Process, Queue
from socket import *


class ProxyServer:
    def __init__(self, port: int, server: tuple, consumer_nums=1, socketpair=(AF_INET, SOCK_STREAM)) -> None:
        self.__server_socket = socket(socketpair)
        self.__server_socket.bind(('', port))
        self.__server_socket.listen(256)

        self.__client_socket = socket(socketpair)
        self.__client_socket.connect(server)

        self.__queue = Queue()

        self.__process_pool = []

        root = os.path.dirname(__file__)

        producer = Process(target=ProxyServer._producer,
                           args=(self.__queue, self.__server_socket))

        consumer = Process(target=ProxyServer._consumer,
                           args=(self.__queue, self.__client_socket, root))

    def __del__(self):
        self.__client_socket.close()
        self.__server_socket.close()

    def _producer(queue: Queue, server: socket):
        while True:
            connection, addr = server.accept()
            message = connection.recv(4096)
            queue.put((connection, addr, message))

    def _consumer(queue: Queue, client: socket, root: str):
        def build_response(data: bytes) -> str:
            return ('HTTP/1.1 200 OK\nConnection: close\nContent-Type: text/html\nContent-Length: %d\n\n' % (
                len(data))).encode()+data

        while True:
            connect_socket, addr, message = queue.get()
            file_name = root+message.decode('utf-8').split()[1]
            try:
                with open(file_name, mode='r', encoding='uft-8') as data:
                    response = data.read().encode()
                    connect_socket.sendall(build_response(response))

            except FileNotFoundError:
                client.sendall(message)
                buffer = client.recv(4096)

                with open(file_name, mode='w', encoding='utf-8') as target:
                    target.write(buffer.decode('utf-8'))

            connect_socket.close()
