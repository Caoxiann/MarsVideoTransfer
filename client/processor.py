import json
import socket
import cv2
import numpy
import struct
import sys
import time
import threading
import os
import logging
import random
import uuid
from queue import Queue


IP = "192.168.10.109"
PORT = 3310
ADDR = (IP, PORT)
VIDEO_IP = "192.168.10.109"
VIDEO_PORT = 9510
VIDEO_ADDR = (VIDEO_IP, VIDEO_PORT)
SERVER_IP = "127.0.0.1"
SERVER_PORT = 9980
SERVER_ADDR = (SERVER_IP, SERVER_PORT)
BUFFER_LEN = 1024
QUEUE_LEN = 16

reg_dict = {
    "path": "/csebase",
    "name": "waitKey",
    "type": "container"
}

reg_entity = {
    "method": "POST",
    "path": "/new",
    "content": "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n" +
                "<m2m:cnt xmlns:m2m=\"http://www.onem2m.org/xml/protocols\">\n" +
                "    <lbl>label1 label2</lbl>\n" +
                "    <acpi>\n" +
                "        //IN-CSEID.m2m.myoperator.org/" + "111111" + "\n" +
                "    </acpi>\n" +
                "    <cr>//IN-CSEID.m2m.myoperator.org/" + "1111" + "</cr>\n" +
                "    <mni>" + str(random.randint(0, 10)) + "</mni>\n" +
                "    <mbs>" + str(random.randint(100000, 999999)) + "</mbs>\n" +
                "    <mia>" + str(random.randint(100000, 999999)) + "</mia>\n" +
                "    <li>//IN-CSEID.m2m.myoperator.org/1112</li>\n" +
                "    <or>http://tempuri.org/ontologies/xyz</or>\n" +
                "</m2m:cnt>",
    "queryString": reg_dict
}

write_dict = {
    "path": "/csebase/camera1",
    "name": "video" + time.strftime("%Y%m%d%H%M%S") + ".c_vi",
    "size": str(random.randint(100, 1000)),
    "type": "video"
}

write_entity = {
    "method": "POST",
    "path": "/write",
    "content": "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>"
               "<ns2:video xmlns:ns2=\"http://www.onem2m.org/xml/protocols\">"
               "<id>" + str(write_dict["name"]) + "</id>"
               "<longitude>" + str(random.uniform(10, 100)) + "</longitude>"
               "<latitude>" + str(random.uniform(10, 100)) + "</latitude>"
               "<size>" + str(random.randint(100, 1000)) + "</size>"
               "<duration>" + str(random.randint(100, 100)) + "</duration>"
               "<resolution>" + str(uuid.uuid1()).split("-").pop() + "</resolution>"
               "<note>" + str(uuid.uuid1()) + "</note>"
               "</ns2:video>",
    "queryString": write_dict
}

video_dict = {
    "cert": ""
}

video_entity = {
    "id": "0xxxxxx",
    "op": "op-stream",
    "path": "",
    "name": "",
    "query": video_dict
}


class MyQueue(Queue):

    def __init__(self, *args, **kwargs):
        super(MyQueue, self).__init__(*args, **kwargs)

    def put(self, item, block=True, timeout=None):
        """
        如果队列已满，将队首元素弹出，再将最新元素压入
        :param item:
        :param block:
        :param timeout:
        :return:
        """
        if self.full():
            super().get()
        super().put(item=item, block=block, timeout=timeout)


class VideoPack(object):

    def __init__(self, t_len=None, has_next=None, length=None, stringData=None):
        """
        用来打包一帧视频字节流数据
        :param t_len:
        :param has_next:
        :param length:
        :param stringData:
        """
        self.t_len = t_len
        self.has_next = has_next
        self.length = length
        self.stringData = stringData

myqueue = MyQueue(QUEUE_LEN)


def recvall(sock, count):
    buf = b''
    while count:
        newbuf = sock.recv(count)
        if not newbuf: return None
        buf += newbuf
        count -= len(newbuf)
    return buf


def send_adata(data, ADDR):
    address = ADDR
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(address)
    #length = str(len(data)).ljust(4)
    length = len(data)
    length = struct.pack("!i", length)
    s.send(length)
    s.send(data.encode())
    length = recvall(s, 4)
    length = struct.unpack("!i", length)
    length = length[0]
    data = recvall(s, length)
    s.close()
    return data.decode()


def send_entity(entity, ADDR):
    json_entity = json.dumps(entity)
    resp_entity = send_adata(json_entity, ADDR)
    try:
        resp = json.loads(resp_entity)
    except:
        resp = resp_entity
    return resp


def send_cert(cert, resp_write_dict):
    cert["cert"] = resp_write_dict["cert"]
    cert["length"] = 0
    json_cert = json.dumps(cert)
    send_adata(json_cert)


def send_request():
    """
    往1m2m平台发送存储视频请求，请求成功后开始发送视频数据
    :return:
    """
    try:
        reg_resp = send_entity(reg_entity, (IP, PORT))
        logging.info("reg_resp->", reg_resp)
        if reg_resp["content"]["success"] is True:
            write_entity["queryString"]["path"] = reg_resp["content"]["data"]
            write_resp = send_entity(write_entity, (IP, PORT))
            logging.info("write_resp->", write_resp)
            if write_resp["content"]["success"] is True:
                video_entity["path"] = write_resp["content"]["data"]["path"]
                video_entity["name"] = write_resp["content"]["data"]["name"]
                video_entity["query"]["cert"] = write_resp["content"]["data"]["cert"]
                send_video_req(video_entity)
            else:
                logging.exception("send write request fail...")
                os._exit(0)
        else:
            logging.exception("send register request fail, maybe Container Resource name is duplicate...")
            os._exit(0)
    except ConnectionResetError as e:
        logging.error("error:" + str(e))
        os._exit(0)


def send_video_req(video_entity):
    address = (VIDEO_IP, VIDEO_PORT)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(address)
    json_entity = json.dumps(video_entity)
    length = len(json_entity)
    length = struct.pack("!i", length)
    sock.send(length)
    sock.send(json_entity.encode())
    length = recvall(sock, 4)
    length = struct.unpack("!i", length)
    length = length[0]
    data = recvall(sock, length)
    data = data.decode()
    video_resp = json.loads(data)
    if video_resp["success"] is True:
        logging.info("success: " + str(video_resp["msg"]))
        logging.info("video name:" + str(write_dict["name"]))
        send_video(sock)
    else:
        logging.exception("Error: " + str(video_resp["msg"]))
        logging.exception("video resp:" + str(video_resp["success"]))


def send_video(sock):
    """
    往socket连接:param sock 中发送发送视频数据
    :param sock:
    :return:
    """
    capture = cv2.VideoCapture(0)
    ret, frame = capture.read()
    encode_param=[int(cv2.IMWRITE_JPEG_QUALITY),90]

    while ret:
        cv2.imshow("upload", frame)
        result, imgencode = cv2.imencode('.jpg', frame, encode_param)
        data = numpy.array(imgencode)
        stringData = data.tobytes()
        length = str(len(stringData)).ljust(16)
        t_len = int(length) + 17
        has_next = struct.pack('!b', 1)

        sock.send(struct.pack('!i', t_len))
        sock.send(has_next)
        sock.send(length.encode())
        sock.send(stringData)
        # 将当前视频帧的字节数据打包成VideoPack，存放在同步队列myqueue中，myqueue用来实现实时视频服务器
        pack = VideoPack(t_len=struct.pack('!i', t_len), has_next=has_next, length=length.encode(), stringData=stringData)
        myqueue.put(pack)

        ret, frame = capture.read()
        if cv2.waitKey(10) == 27:
            break
    logging.info("end")
    sock.close()


def test_cap_video():
    capture = cv2.VideoCapture(0)
    ret, frame = capture.read()
    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]

    while ret:
        cv2.imshow("init", frame)
        result, imgencode = cv2.imencode('.jpg', frame, encode_param)
        data = numpy.array(imgencode)
        stringData = data.tobytes()
        length = str(len(stringData)).ljust(16)
        t_len = int(length) + 17
        has_next = struct.pack('!b', 1)

        pack = VideoPack(t_len=struct.pack('!i', t_len), has_next=has_next, length=length.encode(),
                         stringData=stringData)
        myqueue.put(pack)

        ret, frame = capture.read()
        if cv2.waitKey(10) == 27:
            break
    print("end")


class RealTimeServer(object):

    def __init__(self, ip=None, port=None, ADDR=None):
        self.ip = ip
        self.port = port
        self.ADDR = ADDR

    def start(self):
        """
        启动实时视频服务器
        :return:
        """
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(self.ADDR)
            sock.listen(True)
            logging.info("Real Time Video Server start...")
            logging.info("Real Time Video ip: " + self.ADDR[0])
            logging.info("Real Time Video port: " + str(self.ADDR[1]))
            while True:
                conn, addr = sock.accept()
                logging.info("recv a connect. " + "addr:" + str(addr))
                try:
                    client_thread = threading.Thread(target=self.send_video, args=(conn, ))
                    client_thread.start()
                except BrokenPipeError as e:
                    logging.error("Error:" + str(e))
            logging.info("server close...")
            sock.close()
        except Exception as e:
            logging.error("Real Time Server Error: " + str(e))
            os._exit(0)

    def send_video(self, conn):
        """
        往一个新的socket连接发送视频数据
        :param conn: 客户端连接
        :return:
        """
        try:
            while True:
                video_pack = myqueue.get()
                if isinstance(video_pack, VideoPack):
                    try:
                        conn.send(video_pack.t_len)
                        conn.send(video_pack.has_next)
                        conn.send(video_pack.length)
                        conn.send(video_pack.stringData)
                    except ConnectionResetError as e:
                        logging.error("connect reset...")
                        logging.error("Error:" + str(e))
        except BrokenPipeError as e:
            logging.error("error:" + str(e))

        conn.close()


def initial():
    logging.getLogger().setLevel(logging.INFO)
    global IP, VIDEO_IP
    if len(sys.argv) == 2:
        reg_dict["name"] = sys.argv[1]
        logging.info("default 1m2m ip: " + IP)
    elif len(sys.argv) == 3:
        reg_dict["name"] = sys.argv[1]
        IP = sys.argv[2]
        VIDEO_IP = sys.argv[2]
    else:
        logging.warning("Please input Container Resource name at lease...")
        logging.info("Usage: python3 " + sys.argv[0] + " name ip")
        logging.info("    name : Container Resource name")
        logging.info("    ip   : 1m2m ip, default is " + IP)
        exit()


def use_threading():
    server = RealTimeServer(ADDR=SERVER_ADDR)
    send_request_thread = threading.Thread(target=send_request)
    server_thread = threading.Thread(target=server.start)

    send_request_thread.start()
    server_thread.start()


def main():
    initial()
    use_threading()


if __name__ == "__main__":
    main()

