import socket
import cv2
import numpy
import struct
import json

address = ('192.168.10.118', 9510)
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(address)


video_entity = {
    "id": "0xxxxxx",
    "op": "op-download",
    "path": "/test/rdnfile-1",
    "name": "rdnfile-1"
}

def recvall(sock, count):
    buf = b''
    while count:
        newbuf = sock.recv(count)
        if not newbuf: return None
        buf += newbuf
        count -= len(newbuf)
    return buf


def recv_video(s):
    stringData = b""
    while 1:
        int_length = recvall(s, 4)
        int_length = struct.unpack("!i", int_length)
        int_length = int_length[0]
        int_length = int_length -1
        has_next = recvall(s, 1)
        new_data = recvall(s, int_length)
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
                cv2.imshow('client', decimg)
                if cv2.waitKey(25) == 27:
                    break

        # length = recvall(s, 16)
        # print length
        # stringData = recvall(s, int(length))
        # print stringData
        # data = numpy.fromstring(stringData, dtype='uint8')
        # decimg = cv2.imdecode(data, 1)
        # print decimg
        # cv2.imshow('client', decimg)
        # if cv2.waitKey(10) == 27:
        #     break

    s.close()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    json_entity = json.dumps(video_entity).encode()
    s.send(struct.pack("!i", len(json_entity)))
    s.send(json_entity)
    recv_video(s)


