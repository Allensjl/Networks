from socket import socket, AF_INET, SOCK_DGRAM, SOCK_STREAM
from MsgBox import MsgBox
import time
import _thread
import threading
import os

BUFFSIZE = 1024
DEFAULT_OPSODE = {
    'login'         :   0x10,
    'subscribe'     :   0x20,
    'unsubscribe'   :   0x21,
    'post'          :   0x30,
    'retrieve'      :   0x40,
    'logout'        :   0x1F,

    'reset'         :   0x00,

    # 发送图片
    'sendpic'       :   0x50,
    # 拉取图片
    'getpic'        :   0x51,
    }

class Client():
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.address = (self.ip, self.port)
        self.socket = None
        self.token = ''         # Before the user logs in, no token
    
    def is_login(self):
        '''
        Verify if the user is logged in
        '''
        if self.token == '':
            return False
        return True


    def verify_datas(self, opcode, datas):
        if opcode in ('logout', 'reset') and len(datas) == 0:
            return True
        elif opcode in ('login', 'subscribe', 'unsubscribe', 'post', 'retrieve') and len(datas) > 0:
            return True
        elif opcode in ('sendpic') and len(datas) >  0:
            # See if the currently uploaded picture can be opened
            try:
                f = open(datas, 'rb')
                f.close()
                return True
            except:
                print('Please check if the picture path can be opened!')
                return False
        else:
            return False
        
    def inputproc(self):
        '''
        Thread listening for user input
        '''
        while True:
            # get user input and store in userinput
            try:
                opcode, datas = input().split('#')
                if opcode in DEFAULT_OPSODE.keys() and self.verify_datas(opcode, datas):
                    msgbox = MsgBox(DEFAULT_OPSODE[opcode], '', self.token, 0, datas)
                    self.socket.sendto(msgbox.pack_message(), self.address)

                    # The client actively requests a session reset
                    if opcode == 'reset':
                        self.token = ''
                else:
                    print('Error message, please log in again')
            except:
                print('Error message, please log in again')


    def deal_msg(self, msg, addr):
        msgbox = MsgBox()
        msgbox.umpack_message(msg)
        if msgbox.opcode == 0xF0:
            print('erro#must_login_frist')
        elif msgbox.opcode == 0x80:
            # store the token gived by server
            self.token = msgbox.token
            # login successfully
            print('login_ack#success')
        elif msgbox.opcode == 0x81:
            # failed to login
            print('login_ack#failed')
        elif msgbox.opcode == 0x8F:
            self.token = ''
            # logout successfully
            print('logout_ack#success')
        elif msgbox.opcode == 0x90:
            print('subscribe_ack# successful')
        elif msgbox.opcode == 0x91:
            print('subscribe_ack#failed')
        elif msgbox.opcode == 0xA0:
            print('unsubscribe_ack# successful')
        elif msgbox.opcode == 0xA1:
            print('unsubscribe_ack#failed')
        elif msgbox.opcode == 0xB1:
            sclientid , text = msgbox.message['sourceid'], msgbox.message['text']
            print('<%s> %s' % (sclientid, text))
            # forward ack
            remsgbox = MsgBox(0x31, '', self.token, msgbox.messageid, '')
            self.socket.sendto(remsgbox.pack_message(), self.address)
        elif msgbox.opcode == 0xC0:
            # Get the information returned by the retrieval
            sclientid , text = msgbox.message['sourceid'], msgbox.message['text']
            print('<%s> %s' % (sclientid, text))
        elif msgbox.opcode == 0xC1:
            # Get all search information,
            print('Get all retrieve text!')
        elif msgbox.opcode == 0x00:
            # Reset session state and clear client content
            self.token = ''
            print('Has not been operated for a long time, offline!')
        elif msgbox.opcode == 0xD0:
            # The server agrees to upload the picture
            tcp_ip, tcp_port, picname = msgbox.message['tcpip'], msgbox.message['tcpport'], msgbox.message['picname']
            print('ready upload', tcp_ip, tcp_port)
            # Establish a TCP connection to the server
            tcpsocket = socket(AF_INET,SOCK_STREAM)
            tcpsocket.connect((tcp_ip, tcp_port))
            # Send flag, picture name, and picture size
            fsize = os.path.getsize(picname)
            tcpsocket.send('upload'.ljust(256).encode('utf-8'))
            tcpsocket.send(picname.ljust(256).encode('utf-8'))
            tcpsocket.send(str(fsize).ljust(256).encode('utf-8'))
            #
            start = tcpsocket.recv(256).decode('utf-8').rstrip()
            print(start)
            # Open image and send data
            with open(picname, 'rb') as f:
                for data in f:
                    print(data)
                    tcpsocket.send(data)
            tcpsocket.close()

            # Send complete
            print('%s send success' % picname)
        elif msgbox.opcode == 0xD1:
            # 服务器同意拉取图片
            tcp_ip, tcp_port, picname, clientid = msgbox.message['tcpip'], msgbox.message['tcpport'], msgbox.message['picname'], msgbox.message['clientid']
            # 建立tcp链接,链接到服务器上
            tcpsocket = socket(AF_INET,SOCK_STREAM)
            tcpsocket.connect((tcp_ip, tcp_port))
            # 发送标志位， 文件名称
            tcpsocket.send('download'.ljust(256).encode('utf-8'))
            tcpsocket.send(picname.ljust(256).encode('utf-8'))
            # 接受文件大小
            picsize = int(tcpsocket.recv(256).decode('utf-8').rstrip())

            with open(picname,"ab") as f:
                while picsize > 0:
                    if picsize > BUFFSIZE:
                        cursize = BUFFSIZE
                    else:
                        cursize = picsize
                    data = tcpsocket.recv(cursize)
                    f.write(data)
                    picsize -= cursize
            tcpsocket.close()
            # 接受完成，
            print('success get pic')
        

    def serverproc(self):
        '''
        Listen for threads returned by the server
        '''
        while True:
            try:
                self.socket.setblocking(0)
                msg, addr = self.socket.recvfrom(BUFFSIZE)
                self.deal_msg(msg, addr)
            except:
                self.socket.setblocking(1)
                time.sleep(1)


    def start(self):
        self.socket = socket(AF_INET, SOCK_DGRAM)
            # User input thread
        _thread.start_new_thread(self.inputproc, ())
        # Accept server information thread
        _thread.start_new_thread(self.serverproc, ())

client = Client('127.0.0.1', 9999)
client.start()
while True:
    pass