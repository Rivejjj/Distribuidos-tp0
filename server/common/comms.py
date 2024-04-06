import logging
from .utils import Bet

MAX_BLOCK_SIZE = 1024

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

        finished = self.test_message(self.message)
        if finished:
            return read
        else:
            while not finished:
                read += self.sock.recv(MAX_BLOCK_SIZE)
                if len(read) <= 0:
                    logging.error("action: read in socket | result: fail | error: {e}")
                    return None
                self.message += read
                finished = self.test_message(self.message)
        return read


    def test_message(self, msg):
        message = msg.decode('utf-8')
        header = ""
        for i in range(len(message)):
            if message[i] == '|':
                break
            header += message[i]

        header = header.split(" ")
        total_len = int(header[1])
        if len(self.message) < total_len:
            print("len message: ", len(message))
            print("total len: ", total_len) 
            return False
        return True



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
        header,payload = split_message(msg)
        batch_size = header.split(" ")[0]

        messages = payload.split("$")
        messages.pop(-1)
        bets = []
        
        for message in messages:
            categorias = message.split("|")
            agencia = categorias[1]
            nombre = categorias[2]
            apellido = categorias[3]
            documento = categorias[4]
            nacimiento = categorias[5]
            numero = categorias[6]
            bet = Bet(agencia, nombre, apellido, documento, nacimiento, numero)
            bets.append(bet)

        logging.info(f"action: apuesta_almacenada | result: success | dni: {documento} | numero: {numero}")
        return bets, batch_size
        
def split_message(msg):
    header = ""
    for i in range(len(msg)):
        header += msg[i]
        if msg[i] == '|':
            break
    return header, msg[len(header):]