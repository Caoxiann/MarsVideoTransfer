import socket
import cv2
import numpy
import struct
import json
import sys
import logging


class HistoryClient(object):

    def __init__(self, ip='192.168.10.109', port=9510):
        self.ip = ip
        self.port = port
        self.video_entity = {
            "id": "0xxxxxx",
            "op": "op-tail-on",
            "path": "/hadoop/rdnfile-1",
            "name": "rdnfile-1"
        }

    def start(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.ip, self.port))
        self.send_video_req(s)
        self.recv_video(s)

    def set_video_name(self, name):
        self.video_entity["path"] = "/hadoop/" + name
        self.video_entity["name"] = name

    def send_video_req(self, s):
        json_entity = json.dumps(self.video_entity).encode()
        s.send(struct.pack("!i", len(json_entity)))
        s.send(json_entity)

    def recvall(self, sock, count):
        buf = b''
        while count:
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
                    cv2.imshow('history video', decimg)
                    if cv2.waitKey(25) == 27:
                        break

        s.close()
        cv2.destroyAllWindows()


def main():
    history_client = HistoryClient()
    logging.getLogger().setLevel(logging.INFO)
    if (len(sys.argv)) == 2:
        history_client.set_video_name(sys.argv[1])
        logging.info("video path:" + history_client.video_entity["path"])
        logging.info("default operation: " + history_client.video_entity["op"] + " ip: " + history_client.ip + " port:" + str(history_client.port))
    elif (len(sys.argv)) == 3:
        history_client.set_video_name(sys.argv[1])
        history_client.video_entity["op"] = sys.argv[2]
        logging.info("video path:" + history_client.video_entity["path"])
        logging.info("default ip:" + history_client.ip + " port:" + str(history_client.port))
    elif (len(sys.argv)) == 4:
        history_client.set_video_name(sys.argv[1])
        history_client.video_entity["op"] = sys.argv[2]
        history_client.ip = sys.argv[3]
        logging.info("video path:" + history_client.video_entity["path"])
        logging.info("default port:" + str(history_client.port))
    elif (len(sys.argv)) == 5:
        history_client.set_video_name(sys.argv[1])
        history_client.video_entity["op"] = sys.argv[2]
        history_client.ip = sys.argv[3]
        history_client.port = int(sys.argv[4])
        logging.info("video path:" + history_client.video_entity["path"])
    else:
        logging.info("Usage: python3 " + sys.argv[0] + " name" + " op" + " ip" + " port")
        logging.info("    name: video name")
        logging.info("    op:   operation, default value is " + history_client.video_entity["op"])
        logging.info("    ip:   1m2m ip, default value is " + history_client.ip)
        logging.info("    port: 1m2m port, default value is " + str(history_client.port))
        exit()
    history_client.start()


if __name__ == "__main__":
    main()

