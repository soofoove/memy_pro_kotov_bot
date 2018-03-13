from socket import *

s = socket()
s.bind(("", 8000))

s.listen(5)


while(True):
    conn, addr = s.accept()

    data = conn.recv(1024)
    print(data.decode())

    conn.send("""HTTP/1.1 200 OK\n\r\n\rHello, World!!!\n\r""".encode())