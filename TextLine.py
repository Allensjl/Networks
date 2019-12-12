import time

class TextLine():
    '''
    Save the message sent by the user to the server. 
    It will be used when other users need to retrieve 
    the latest message.
    '''
    def __init__(self, userid, text):
        self.userid = userid
        self.text = text
        self.timestamp = int(round(time.time() * 1000))