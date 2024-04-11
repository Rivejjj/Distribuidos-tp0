import logging
from .utils import Bet

class Comms:
    def __init__(self, sock):
        self.message = b''
        self.sock = sock

    def full_read(self):
        read = self.sock.recv(1024)
        if len(read) <= 0:
            logging.error("action: read in socket | result: fail | error: {e}")
            return None
        self.message += read

        finished = self.test_message(self.message)
        if finished:
            return read
        else:
            while not finished:
                read += self.sock.recv(1024)
                if len(read) <= 0:
                    logging.error("action: read in socket | result: fail | error: {e}")
                    return None
                self.message += read
                finished = self.test_message(self.message)
        print(read)
        return read

    def test_message(self, msg):
        message = msg.decode('utf-8')
        header = ""
        for i in range(len(message)):
            header += message[i]
            if message[i] == '|':
                break

        header = header.split(" ")
        total_len = int(header[0])
        if len(message) < total_len:
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
        """
        The message received from the client is a string with the following format:
        <len> | <agencia> | <nombre>|<apellido>|<documento>|<nacimiento>|<numero>
          0         1          2          3          4           5          6
        """        
        categorias = msg.split("|")
        agencia = categorias[1]
        nombre = categorias[2]
        apellido = categorias[3]
        documento = categorias[4]
        nacimiento = categorias[5]
        numero = categorias[6]

        bet = Bet(agencia, nombre, apellido, documento, nacimiento, numero)
        bets = [bet]
        logging.info(f"action: apuesta_almacenada | result: success | dni: {documento} | numero: {numero}")
        return bets
        
