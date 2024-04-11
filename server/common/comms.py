import logging
from .utils import Bet

MAX_BLOCK_SIZE = 1024
LAST_BATCH = "1"
MSG_TYPE = 0
LAST_BATCH_POS = 2

class Comms:
    def __init__(self, sock):
        self.message = b''
        self.sock = sock

    def full_read(self):
        read = self.sock.recv(MAX_BLOCK_SIZE)
        if len(read) <= 0:
            logging.error("action: read in socket | result: fail | error: {e}")
            return None
        self.message += read
        finished_batch, last_batch = self.test_message(self.message)
        if finished_batch:
            return read, last_batch
        else:
            while not finished_batch:
                read += self.sock.recv(MAX_BLOCK_SIZE)
                if len(read) <= 0:
                    logging.error("action: read in socket | result: fail | error: {e}")
                    return None
                self.message += read
                finished_batch, last_batch = self.test_message(self.message)
        return read, last_batch


    def test_message(self, msg):
        #returns a tuple with two booleans, the first one indicates if the batch is finished, the second one indicates if it is the last batch
        finished_batch = True
        last_batch = False
        header = b""
        header_finished = False
        for byte in msg:
            if byte == ord(b'|'):
                header_finished = True

                break
            header += bytes([byte])

        if not finished_header:
            return finished_batch, last_batch
            
        if not header_finished:
            finished_batch = False
            return finished_batch, last_batch

        header = header.decode('utf-8')
        header = header.split(" ")

        if header[MSG_TYPE] == "exit":
            return True, True

        if header[MSG_TYPE] == "winners":
            return True, True

        if header[LAST_BATCH_POS] == LAST_BATCH:
            last_batch = True
        
        total_len = int(header[1])

        if len(self.message) < total_len:
            print("len message: ", len(self.message))
            print("total len: ", total_len)
            finished_batch = False 


        return finished_batch, last_batch



    def full_write(self,sock, msg):
        total_sent = 0
        msg_len = str(len(msg))
        msg = msg_len + "|" + msg
        while total_sent < len(msg):
            sent = sock.send("{}".format(msg[total_sent:]).encode('utf-8')) 
            if sent == 0:
                logging.error(f"action: write in socket | result: fail | error: {sent}")
                break
            total_sent += sent
        return total_sent      


    def parse_bet(self, msg):
        print("msg: ", msg)
        header,payload = split_message(msg)
        batch_size = header.split(" ")[0]

        messages = payload.split("$")
        messages.pop(-1)
        bets = []
        
        for message in messages:
            categorias = message.split("|")
            print(categorias)
            agencia = categorias[1]
            nombre = categorias[2]
            apellido = categorias[3]
            documento = categorias[4]
            nacimiento = categorias[5]
            numero = categorias[6]
            bet = Bet(agencia, nombre, apellido, documento, nacimiento, numero)
            bets.append(bet)

        return bets, batch_size
        
def split_message(msg):
    header = ""
    for i in range(len(msg)):
        header += msg[i]
        if msg[i] == '|':
            break
    return header, msg[len(header):]


