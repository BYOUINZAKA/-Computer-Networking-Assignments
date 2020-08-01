from socket import *
import os


def BuildHeader(outputdata: str) -> str:
    return ('HTTP/1.1 200 OK\nConnection: close\nContent-Type: text/html\nContent-Length: %d\n\n' % (
        len(outputdata))).encode()


with socket(AF_INET, SOCK_STREAM) as server_socket:
    server_port = 8001

    server_socket.bind(('', server_port))
    server_socket.listen(8)

    while True:
        print('Ready to serve...')
        connection = server_socket.accept()
        with connection[0] as connection_socket:
            msg = connection_socket.recv(1024)
            print('Received from %s' % connection[1][0])
            try:
                file_name = os.path.dirname(
                    __file__) + msg.decode('utf-8').split()[1]
                with open(file_name, encoding='utf-8') as data:
                    outputdata = data.read().encode()

                    header = BuildHeader(outputdata)

                    connection_socket.sendall(header)
                    connection_socket.sendall(outputdata)

                    print('Send %s to %s\n' % (file_name, connection[1][0]))

            except FileNotFoundError:
                header = 'HTTP/1.1 404 Found\n'
                print(header)
                connection_socket.send(header.encode())

            except IndexError:
                continue
