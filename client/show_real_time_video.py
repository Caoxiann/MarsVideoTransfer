import socket
import cv2
import numpy
import struct
import sys
import logging


class RealTimeClient(object):

    def __init__(self, ip=None, port=9980):
        self.ip = ip
        self.port = port

    def start(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.ip, self.port))
        self.recv_video(s)
        pass

    def recvall(self, sock, count):
        buf = b''
        while count:
            print("count->" + str(count))
            newbuf = sock.recv(count)
            if not newbuf: return None
            buf += newbuf
            count -= len(newbuf)
        return buf

    def recv_video(self, s):
        stringData = b""
        while 1:
            int_length = self.recvall(s, 4)
            int_length = struct.unpack("!i", int_length)
            int_length = int_length[0]
            int_length = int_length - 1
            has_next = self.recvall(s, 1)
            new_data = self.recvall(s, int_length)
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
                    cv2.imshow('real time video', decimg)
                    if cv2.waitKey(25) == 27:
                        break

        s.close()
        cv2.destroyAllWindows()


def main():
    ip = str()
    port = 9980
    logging.getLogger().setLevel(logging.INFO)
    if len(sys.argv) == 2:
        if sys.argv[1] == "--help":
            logging.warning("Please input Video Server ip at lease...")
            logging.info("Usage: python3 " + sys.argv[0] + " ip port")
            logging.info("    ip:   Real Time Server ip")
            logging.info("    port: Real Time Server port, default value is " + str(port))
            exit()
        ip = sys.argv[1]
        logging.info("default port: " + str(port))
    elif len(sys.argv) == 3:
        ip = sys.argv[1]
        port = int(sys.argv[2])
    else:
        logging.warning("Please input Video Server ip at lease...")
        logging.info("Usage: python3 " + sys.argv[0] + " ip port")
        logging.info("    ip:   Real Time Server ip")
        logging.info("    port: Real Time Server port, default value is " + str(port))
        exit()
    real_time_client = RealTimeClient(ip=ip, port=port)
    real_time_client.start()

if __name__ == "__main__":
    main()
