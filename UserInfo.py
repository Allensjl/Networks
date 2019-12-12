import time

# Variable used to indicate whether the user is online
STATUS_ONLINE = 1
STATUS_OFFLINT = 2

class UserInfo():
    '''
    Used to save the client's capital information, mainly including 
    the user's id, user's ip, user's port, user's status,
    user's token
    '''
    def __init__(self, userid, token, ip, port, status):
        self.userid = userid
        self.token = token
        self.ip = ip
        self.port = port
        self.address = (self.ip, self.port)
        self.status = status
        self.last_act = 0               # Save the user's last operation time
        self.subscribe_list = []        # User list to save subscriptions

    def online(self, token, address):
        '''
        Users are back online, updating user status
        '''
        self.token = token
        self.ip = address[0]
        self.port = address[1]
        self.address = address
        self.last_act = int(round(time.time() * 1000))  # Write timestamp
        self.status = STATUS_ONLINE
    
    def offline(self):
        '''
        The user goes offline, deletes the user's various statuses, 
        sets it as offline, and thereafter the message is no longer 
        forwarded to the user
        '''
        self.token = ''
        self.ip = ''
        self.port = ''
        self.address = (self.ip, self.port)
        self.status = STATUS_OFFLINT

    def update_act(self):
        '''
        User action, update timestamp of last operation
        '''
        self.last_act = int(round(time.time() * 1000))