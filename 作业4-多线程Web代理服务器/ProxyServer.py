import os

from multiprocessing import Process, Queue
from socket import *


class ProxyServer:
    def __init__(self, external_port: int, main_server: tuple, consumer_count=1) -> None:
        self.__server_socket = socket(AF_INET, SOCK_STREAM)
        self.__server_socket.bind(('', external_port))
        self.__server_socket.listen(256)

        self.__queue = Queue()

        root = os.path.dirname(__file__)

        self.__process_pool = []

        producer = Process(target=ProxyServer._producer,
                           args=(self.__queue, self.__server_socket))

        self.__process_pool.append(producer)

        for _ in range(consumer_count):
            consumer = Process(target=ProxyServer._consumer,
                               args=(self.__queue, main_server, root))
            self.__process_pool.append(consumer)

    def __del__(self):
        self.__server_socket.close()

    def _producer(queue: Queue, server: socket):
        while True:
            print("生产者进程 等待请求……")
            connection, addr = server.accept()
            message = connection.recv(4096)
            queue.put((connection, addr, message))

    def _consumer(queue: Queue, server_msg: tuple, root: str):
        def build_response(buffer: bytes) -> str:
            return ('HTTP/1.1 200 OK\nConnection: close\nContent-Type: text/html\nContent-Length: %d\n\n' % (
                len(buffer))).encode()+buffer

        while True:
            connect_socket, addr, message = queue.get()
            print("消费者者进程 处理请求……")
            file_name = root+message.decode('utf-8').split()[1]
            try:
                with open(file_name, mode='r', encoding='uft-8') as data:
                    buffer = data.read().encode()
                    connect_socket.sendall(build_response(buffer))

            except FileNotFoundError:
                try:
                    with socket(AF_INET, SOCK_STREAM) as client:
                        client.connect(server_msg)

                        client.sendall(message)
                        buffer = client.recv(4096)

                        data = buffer.decode('utf-8')

                        if '200 OK\n' in data:
                            with open(file_name, mode='w', encoding='utf-8') as target:
                                target.write(buffer.decode('utf-8'))

                        connect_socket.send(buffer)

                except:
                    header = 'HTTP/1.1 404 Found\n'
                    print(header)
                    connect_socket.send(header.encode())

            connect_socket.close()

    def run(self):
        for p in self.__process_pool:
            p.start()


if __name__ == "__main__":
    server = ProxyServer(8008, ('127.0.0.1', 8001))
    server.run()
