import socket
import cv2
import numpy
import threading
import struct

from queue import Queue

myqueue = Queue(1000)


def recvall(sock, count):
    buf = b''
    while count:
        newbuf = sock.recv(count)
        if not newbuf: return None
        buf += newbuf
        count -= len(newbuf)
    return buf


def recv_video2():
    address = ('192.168.10.180', 9002)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(address)
    s.listen(True)
    conn, addr = s.accept()
    stringData = b""
    while 1:
        int_length = recvall(conn, 4)
        myqueue.put(int_length)
        int_length = struct.unpack("!i", int_length)
        int_length = int_length[0]
        int_length = int_length -1
        has_next = recvall(conn, 1)
        myqueue.put(has_next)
        new_data = recvall(conn, int_length)
        myqueue.put(new_data)
        stringData = stringData + new_data

        if stringData.__len__() > 16:
            length = stringData[0: 16]
            length = int(length)
            if stringData.__len__() > (length + 16):
                stringData = stringData[16:]
                img_data = stringData[0: length]
                stringData = stringData[length:]
                data = numpy.fromstring(img_data, dtype='uint8')
                decimg = cv2.imdecode(data, 1)
                cv2.imshow('server', decimg)
                if cv2.waitKey(10) == 27:
                    break
def recv_video():
    address = ('192.168.10.180', 9002)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(address)
    s.listen(True)
    conn, addr = s.accept()
    while 1:
        length = recvall(conn, 16)
        myqueue.put(length)
        stringData = recvall(conn, int(length))
        print(stringData)
        myqueue.put(stringData)
        data = numpy.fromstring(stringData, dtype='uint8')
        decimg = cv2.imdecode(data, 1)
        cv2.imshow('SERVER', decimg)
        print(type(decimg))
        if cv2.waitKey(10) == 27:
            break
    s.close()
    cv2.destroyAllWindows()

def send_video():
    show_address = ("192.168.10.180", 10000)
    show_s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    show_s.bind(show_address)
    show_s.listen(True)
    print("show thread")
    show_conn, show_addr = show_s.accept()
    while True:
        show_conn.send(myqueue.get())
        show_conn.send(myqueue.get())
        show_conn.send(myqueue.get())
    show_s.close()



if __name__ == "__main__":
    send_thread = threading.Thread(target=send_video)
    recv_thread = threading.Thread(target=recv_video2)
    send_thread.start()
    recv_thread.start()
