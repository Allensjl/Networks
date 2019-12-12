from socket import socket, AF_INET, SOCK_DGRAM, SOCK_STREAM
from MsgBox import MsgBox
import time
import random
import collections
import _thread
import threading
import os

from UserInfo import UserInfo, STATUS_ONLINE, STATUS_OFFLINT
from AckInfo import AckInfo
from TextLine import TextLine


USER_INFO_FILENAME = 'userinfo.txt'
BUFFSIZE = 1024

# Check the ack timeout period. 
# Packets that do not respond after this time 
# need to be retransmitted
MAX_ACK_TIMEOUT = 4

# The user's maximum standby time. 
# If this time is exceeded, 
# the user is considered offline.
USER_MAX_KEEPTIME = 60

# a path to Save picture information sent by users
DEFAULT_FILE_HOUE = './PIC/'

class Server():
    '''
    The main class of the server, accepting udp and tcp packages
    '''
    def __init__(self, ip, port, tcp_port):
        self.ip = ip
        self.port = port
        self.tcp_port = tcp_port
        self.address = (self.ip, self.port)
        self.udp_socket = None      # Listen for requests sent by the client and process them
        self.tcp_socket = None      # Accept photos from clients and process them
        self.userlist = {}          # Store user's id and password
        self.userstatus = {}        # Store the user's status
        self.tokenlist = {}
        self.text_list = []

        # This messageid is only used in the forward message, 
        # forward ack, and in the retrieve ack. 
        # For other messages, this is always zero.
        self._msg_id = 0
        self._ack_list = {}


        # Read the user's id and password from 
        # a file and save it to a dictionary
        self.get_userlist(USER_INFO_FILENAME)

        # Save the picture name in the current server
        self.pic_list = {}

    def get_msgid(self):
        '''
        Get the message id, the value represents the id 
        that has been used, you need to add 1 next time
        '''
        self._msg_id += 1
        return self._msg_id

    def add_msgbox_to_acklist(self, clientid, address, msgbox):
        self._ack_list[msgbox.messageid] = AckInfo(clientid, address, msgbox)


    def verify_ack(self, messageid):
        if messageid in self._ack_list.keys():
            del self._ack_list[messageid]

    def check_acklist(self):
        '''
        Check if there are unacknowledged packets 
        that timed out, then resend
        '''
        while True:
            time.sleep(MAX_ACK_TIMEOUT)
            for messageid, ackinfo in self._ack_list.items():
                if ackinfo.check_outtime(MAX_ACK_TIMEOUT) is True:
                    ackinfo.re_send(self.udp_socket)


    def get_userlist(self, filename):
        '''
        Read the user's id and password from a file
        '''
        with open(filename, 'r') as f:
            # read data
            for line in f.readlines():
                # remove '\n' and use ' ' split string, to get userid and password
                userid, password = line.replace('\n', '').split(' ')
                # store in the dict
                self.userlist[userid] = password
                self.userstatus[userid] = UserInfo(userid, '', '', '', STATUS_OFFLINT)


    def gen_token(self):
        '''
        Randomly generated token
        '''
        token = random.randint(2**31, 2**32)
        # Make sure tokens are not duplicated
        while token in self.tokenlist.keys():
            token = random.randint(2**31, 2**32)
        return token

    def forward_text(self, clientid, textline):
        '''
        Forward message
        '''
        remsg = {'sourceid': clientid, 'text': textline.text}
        for _, userinfo in self.userstatus.items():
            if clientid in userinfo.subscribe_list:
                # If there is a user following this message user
                remsgbox = MsgBox(0xB1, '', '', self.get_msgid(), remsg)
                # Add messages to the waiting queue, 
                # waiting for the client to confirm acceptance
                self.add_msgbox_to_acklist(clientid, userinfo.address, remsgbox)
                self.udp_socket.sendto(remsgbox.pack_message(), userinfo.address)

    def deal_msg(self, msg, address):
        msgbox = MsgBox()
        msgbox.umpack_message(msg)
        print(msgbox.make_message())
        try:
            if msgbox.opcode == 0x10:
                userid, password = msgbox.message.split('$')
                if userid in self.userlist.keys() and password == self.userlist[userid]:
                    # The user is on the server list and the password is correct
                    # Generate token
                    token = self.gen_token()
                    # Save token to online list
                    self.tokenlist[token] = userid
                    print(address)
                    self.userstatus[userid].online(token, address)
                    remsgbox = MsgBox(0x80, '', token, 0, '')
                else:
                    # failed to login
                    remsgbox = MsgBox(0x81, '', '', 0, '')
            else:
                # Verify user is online with token
                ctoken = msgbox.token
                if ctoken in self.tokenlist.keys():
                    # Get the client id of the sending request
                    clientid = self.tokenlist[ctoken]
                    if msgbox.opcode == 0x20:
                        userid = msgbox.message
                        if userid in self.userlist.keys() and userid not in self.userstatus[clientid].subscribe_list:
                            # subscribe successfully
                            self.userstatus[clientid].subscribe_list.append(userid)
                            remsgbox = MsgBox(0x90, '', '', 0, '')
                        else:
                            # subscribe failed
                            remsgbox = MsgBox(0x91, '', '', 0, '')
                    elif msgbox.opcode == 0x21:
                        userid = msgbox.message
                        if userid in self.userlist.keys() and userid in self.userstatus[clientid].subscribe_list:
                            # unsubscribe successfully
                            self.userstatus[clientid].subscribe_list.remove(userid)
                            remsgbox = MsgBox(0xA0, '', '', 0, '')
                        else:
                            # unsubscribe failed
                            remsgbox = MsgBox(0xA1, '', '', 0, '')
                    elif msgbox.opcode == 0x30:
                        text = msgbox.message
                        textline = TextLine(clientid, text)
                        # Adding messages to the server's storage, 
                        self.text_list.insert(0, textline)
                        # 转发消息
                        self.forward_text(clientid, textline)
                        remsgbox = MsgBox(0xB0, '', '', 0, '')
                    elif msgbox.opcode == 0x40:
                        n = int(msgbox.message)
                        i = 0
                        while n > 0 and i < len(self.text_list):
                            # 遍历用户发送的消息队列，按时间倒序排列，从中检索出n条消息
                            if self.text_list[i].userid in self.userstatus[clientid].subscribe_list:
                                remsg = {'sourceid': self.text_list[i].userid, 'text': self.text_list[i].text}
                                remsgbox = MsgBox(0xC0, '', '', self.get_msgid(), remsg)
                                self.udp_socket.sendto(remsgbox.pack_message(), address)
                                n -= 1
                            i += 1
                        remsgbox = MsgBox(0xC1, '', '', self.get_msgid(), '')
                    elif msgbox.opcode == 0x1F:
                        # The user logs out and then puts the status offline
                        del self.tokenlist[ctoken]
                        self.userstatus[clientid].offline()
                        remsgbox = MsgBox(0x8F, '', '', 0, '')
                    elif msgbox.opcode == 0x50:
                        # User requests photo upload
                        picname = msgbox.message
                        last_index = picname.rfind('/')
                        picname = picname[last_index + 1:]
                        self.pic_list[picname] = clientid
                        # Returns the local tcp server address to the user, and confirms the picture to be uploaded
                        remsgbox = MsgBox(0xD0, '', '', 0, {'tcpip':self.ip, 'tcpport': self.tcp_port, 'picname':picname})
                    elif msgbox.opcode == 0x51:
                        # 用户请求下载照片
                        picname = msgbox.message
                        if picname in self.pic_list.keys():
                            # 向用户返回本地tcp服务器地址，并且确认要接受的图片
                            remsgbox = MsgBox(0xD1, '', '', 0, {'tcpip':self.ip, 'tcpport': self.tcp_port, 'picname':picname, 'clientid':clientid})
                        else:
                            remsgbox = MsgBox(0xD2, '', '', 0, '')
                    elif msgbox.opcode == 0x00:
                        # The client actively requests a session reset
                        del self.tokenlist[ctoken]
                        self.userstatus[clientid].offline()
                        return
                    elif msgbox.opcode == 0x31:
                        #  Receive the packet and confirm the ack
                        ack_id = msgbox.messageid
                        if ack_id in self._ack_list.keys():
                            del self._ack_list[ack_id]
                            print('get info')
                        return
                    else:
                        return
                else:
                    # User is not logged in to perform these operations
                    remsgbox = MsgBox(0xF0, '', '', 0, '')
            
            self.udp_socket.sendto(remsgbox.pack_message(), address)
        except:
            pass
    
    def check_user(self):
        while True:
            time.sleep(USER_MAX_KEEPTIME)
            now_time = int(round(time.time() * 1000))
            for _, userinfo in self.userstatus.items():
                # The user exceeds the maximum standby time, and the user is taken offline
                if userinfo.status == STATUS_ONLINE and now_time - userinfo.last_act > USER_MAX_KEEPTIME * 1000:
                    ctoken = userinfo.token
                    # Notify the user and reset the session
                    remsgbox = MsgBox(0x00, '', '', 0, '')
                    self.udp_socket.sendto(remsgbox.pack_message(), userinfo.address)
                    # Clear customer information saved on the server
                    del self.tokenlist[ctoken]
                    userinfo.offline()

    def tcp_socket_service(self):
        self.tcp_socket.setblocking(0)
        self.tcp_socket.bind((self.ip, self.tcp_port))
        self.tcp_socket.listen(5)

        while True:
            time.sleep(4)
            try:
                self.tcp_socket.setblocking(0)
                conn, addr = self.tcp_socket.accept()
                # Received a user request
                print('get tcp')
                msg = conn.recv(256).decode('utf-8').rstrip()
                print(len(msg))
                if msg == 'upload':
                    picname = conn.recv(256).decode('utf-8').rstrip()
                    # Get the actual file name
                    last_index = picname.rfind('/')
                    picname = DEFAULT_FILE_HOUE + picname[last_index + 1:]
                    picsize = int(conn.recv(256).decode('utf-8').rstrip())
                    conn.send('ok'.ljust(256).encode('utf-8'))
                    with open(picname, "ab") as f:
                        while picsize > 0:
                            if picsize > BUFFSIZE:
                                cursize = BUFFSIZE
                            else:
                                cursize = picsize
                            data = conn.recv(cursize)
                            f.write(data)
                            picsize -= cursize
                elif msg == 'download':
                    picname = conn.recv(256).decode('utf-8').rstrip()
                    if picname in self.pic_list:
                        conn.send('ok'.ljust(256).encode('utf-8'))
                        picsize = os.path.getsize(picname)
                        conn.send(str(picsize).ljust(256).encode('utf-8'))
                        with open(picname, 'rb') as f:
                            for data in f:
                                print(data)
                                conn.send(data)
                    else:
                        # Cannot send
                        conn.send('fail'.ljust(256).encode('utf-8'))
                    pass
                else:
                    pass
            except Exception as e:
                pass
        
    def start(self):
        self.udp_socket = socket(AF_INET, SOCK_DGRAM)
        self.tcp_socket = socket(AF_INET, SOCK_STREAM)
        _thread.start_new_thread(self.tcp_socket_service, ())
        # Start server listening
        # Regularly check user online status thread
        _thread.start_new_thread(self.check_user, ())
        # Timeout retransmission thread
        _thread.start_new_thread(self.check_acklist, ())
        self.udp_socket.bind(self.address)
        while True:
            # Get client messages
            print('wait.....')
            msg, addr = self.udp_socket.recvfrom(BUFFSIZE)
            self.deal_msg(msg, addr)

server = Server('127.0.0.1', 9999, 10001)
server.start()
