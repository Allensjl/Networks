import time

class AckInfo():
    '''
    Ack information temporarily saved for timeout retransmission
    '''
    def __init__(self, clientid, address, msgbox):
        self.clientid = clientid
        self.address = address
        self.msgbox = msgbox
        self.timestramp = int(round(time.time() * 1000))
    
    def check_outtime(self, outtime):
        '''
        Check if repackaging is retransmitted
        '''
        now_time = int(round(time.time() * 1000))
        if now_time - self.timestramp > outtime * 1000:
            return True
        return False
    
    def re_send(self, ssocket):
        '''
        Resend packet, change timestamp
        '''
        ssocket.sendto(self.msgbox.pack_message(), self.address)
        self.timestramp = int(round(time.time() * 1000))