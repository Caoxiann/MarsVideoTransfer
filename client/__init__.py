import json
import socket
import cv2
import numpy
import struct
import sys


IP = "192.168.10.118"
PORT = 3310
ADDR = (IP, PORT)
VIDEO_IP = "192.168.10.118"
VIDEO_PORT = 9510
VIDEO_ADDR = (VIDEO_IP, VIDEO_PORT) 

reg_dict = {
    "path": "/csebase",
    "name": "camera7",
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
                "    <mni>" + "1" + "</mni>\n" +
                "    <mbs>" + "999999" + "</mbs>\n" +
                "    <mia>" + "111111" + "</mia>\n" +
                "    <li>//IN-CSEID.m2m.myoperator.org/1112</li>\n" +
                "    <or>http://tempuri.org/ontologies/xyz</or>\n" +
                "</m2m:cnt>",
    "queryString": reg_dict
}

write_dict = {
    "path": "/csebase/camera1",
    "name": "video0.c_vi",
    "size": "666",
    "type": "video"
}

write_entity = {
    "method": "POST",
    "path": "/write",
    "content": "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>"
               "<ns2:video xmlns:ns2=\"http://www.onem2m.org/xml/protocols\">"
               "<id>i0997</id>"
               "<longitude>65.42390508836665</longitude>"
               "<latitude>63.75465019330827</latitude>"
               "<size>735</size>"
               "<duration>707</duration>"
               "<resolution>448X336</resolution>"
               "<note>notenotenotenotenotenote</note>"
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
    print("length->", length)
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
    reg_resp = send_entity(reg_entity, ADDR)
    print("reg_resp->", reg_resp)
    if reg_resp["content"]["success"] is True:
        write_entity["queryString"]["path"] = reg_resp["content"]["data"]
        write_resp = send_entity(write_entity, ADDR)
        print("write_resp->", write_resp)
        if write_resp["content"]["success"] is True:
            video_entity["path"] = write_resp["content"]["data"]["path"]
            video_entity["name"] = write_resp["content"]["data"]["name"]
            video_entity["query"]["cert"] = write_resp["content"]["data"]["cert"]
            send_video_req(video_entity)


def send_video_req(video_entity):
    address = VIDEO_ADDR
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
    print("length->", length)
    data = recvall(sock, length)
    data = data.decode()
    video_resp = json.loads(data)
    if video_resp["success"] is True:
        send_video(sock)


def send_video(sock):
    capture = cv2.VideoCapture(0)
    ret, frame = capture.read()
    encode_param=[int(cv2.IMWRITE_JPEG_QUALITY),90]

    while ret:
        result, imgencode = cv2.imencode('.jpg', frame, encode_param)
        data = numpy.array(imgencode)
        stringData = data.tobytes()
        length = str(len(stringData)).ljust(16)
        t_len = int(length) + 17
        has_next = struct.pack('!b',1)

        sock.send(struct.pack('!i', t_len))
        sock.send(has_next)
        sock.send(length.encode())
        sock.send(stringData)
 
        print("length->", length)
        print("t_len->", t_len)
        ret, frame = capture.read()
        if cv2.waitKey(10) == 27:
            break
    print("end")
    sock.close()


def initial():
    if len(sys.argv)!=2:
        print("Please input Register name...")
        exit()
    reg_dict["name"] = sys.argv[1]

if __name__ == "__main__":
    initial()
    send_request()
