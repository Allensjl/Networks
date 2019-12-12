import json
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
import base64

# Keys used for encryption
DEFAULT_KEY = b'\x19\x1bf\x86N\x14\xd4\x00\xfc\x10%\xc6\x8eA\xda\x90'
DEFAULT_KEY_LEN = 16
PADDING_CHAR = '\0'

class AESMsgTool():
    '''
    Use AES encryption
    '''
    def __init__(self, key=DEFAULT_KEY):
        self.key = key
        self.mode = AES.MODE_CBC
    
    def pad_text(self, text):
        '''
        Padding string, multiples of length 16
        '''
        # For UTF-8 encoding, English takes 1 byte, while Chinese takes 3 bytes
        if len(bytes(text, encoding='utf-8')) == len(text):
            totlength = len(text)
        else:
            totlength = len(bytes(text, encoding='utf-8'))
        p_num = AES.block_size - totlength % AES.block_size
        padding_text = PADDING_CHAR * p_num
        return text + padding_text
    
    def unpad_text(self, text):
        '''
        Remove padding string
        '''
        return text.rstrip('\0')
    

    def encrypt(self, text):
        '''
        Encryption function, if text is not a multiple of 16,
        then make up a multiple of 16
        '''
        cipher = AES.new(self.key, AES.MODE_CBC, self.key)
        # Handle plaintext
        after_pad_text = self.pad_text(text)
        # Encrypts and returns a re-encoded string
        encrypt_bytes = cipher.encrypt(bytes(after_pad_text, encoding='utf-8'))
        return str(base64.b64encode(encrypt_bytes), encoding='utf-8')
    
    
    def decrypt(self, text):
        '''
        After decryption, remove the supplementary 
        space and remove it with strip ()
        '''
        cipher = AES.new(self.key, AES.MODE_CBC, self.key)
        # base64解码
        encrypt_bytes = base64.b64decode(text)
        # base64 decoding
        decrypt_bytes = cipher.decrypt(encrypt_bytes)
        # Re-encode, go out and fill in content
        result = str(decrypt_bytes, encoding='utf-8')
        return self.unpad_text(result)

class MsgBox():
    '''
    Message format that requires interaction 
    between client and server
    '''

    def __init__(self, opcode=0, payload='', token='', messageid=0, message=''):
        '''
        Initialize the messages that need to be sent
        '''
        self.opcode = opcode
        self.payload = payload
        self.token = token
        self.messageid = messageid
        self.message = message

        self.tool = AESMsgTool()

    def make_message(self):
        '''
        Convert dictionary to dictionary format for easy use
        '''
        return {'opcode': self.opcode,
                'payload': self.payload,
                'token': self.token,
                'messageid': self.messageid,
                'message': self.message,
                }

    def pack_message(self):
        '''
        Convert messages to json format, and encode it
        '''
        json_msg = json.dumps(self.make_message())
        # Encrypt message before sending
        return self.tool.encrypt(json_msg).encode('utf-8')

    def umpack_message(self, messages):
        '''
        decode frist, and parse information from json package
        '''
        messages = messages.decode('utf-8')
        # Decrypt the message after receiving it
        messages = self.tool.decrypt(messages)
        infos = json.loads(messages)
        self.opcode = infos['opcode']
        self.payload = infos['payload']
        self.token = infos['token']
        self.messageid = infos['messageid']
        self.message = infos['message']
