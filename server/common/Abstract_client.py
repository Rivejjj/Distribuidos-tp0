import multiprocessing as mp
import logging
from .comms import Comms
from .utils import Bet, store_bets


class Abstract_client:
    def __init__(self,socket, file,lock):
        self.parent_conn, self.child_conn = mp.Pipe()
        self.file = file
        self.lock = lock
        self.sock = socket
        self.process = mp.Process(target=run, args=(self.child_conn,self.sock, self.lock))
        #return self.parent_conn

def run(conn,socket,lock):
    """
    Read message from a specific client socket and closes the socket

    If a problem arises in the communication with the client, the
    client socket will also be closed
    """
    comms = Comms(socket)
    msg, last_batch = comms.full_read()
    msg = msg.rstrip().decode('utf-8')
    if not msg: #client disconnected
        return #??
    
    addr = socket.getpeername()
    logging.info(f'action: receive_message | result: success | ip: {addr[0]} | msg: {msg}')

    if msg.startswith("winners"):
        conn.send(msg)
        return

    bets, batch_size = comms.parse_bet(msg)
    print("len bets: ", len(bets))
    if not last_batch and len(bets) < int(batch_size):
        comms.full_write(socket, "err\n")
        return
    else:
        comms.full_write(socket, "ok\n")

    with lock:
        store_bets(bets)

    for bet in bets:
        logging.info(f"action: apuesta_almacenada | result: success | dni: {bet.document} | numero: {bet.number}")

    socket.close()


def get_client_id(self):
    return self.client_id
