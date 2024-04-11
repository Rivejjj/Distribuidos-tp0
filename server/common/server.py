import socket
import logging
import signal
from .utils import Bet, store_bets
from .comms import Comms

class Server:
    def __init__(self, port, listen_backlog):
        # Initialize server socket
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(('', port))
        self._server_socket.listen(listen_backlog)
        self.active_clients = {}
        self.running = True
        
    def handle_sigterm(self):
        logging.info("HANDLING SIGTERM")
        self.running = False
        for client in self.active_clients.values():
            client.close()
        self._server_socket.close()

    def run(self):
        """
        Dummy Server loop

        Server that accept a new connections and establishes a
        communication with a client. After client with communucation
        finishes, servers starts to accept new connections again
        """
        signal.signal(signal.SIGTERM, self.handle_sigterm)

        while self.running:
            client_sock = self.__accept_new_connection()
            if client_sock:
                self.__handle_client_connection(client_sock)



    def __handle_client_connection(self, client_sock):
        """
        Read message from a specific client socket and closes the socket

        If a problem arises in the communication with the client, the
        client socket will also be closed
        """
        try:
            comms = Comms(client_sock)
            msg = comms.full_read().rstrip().decode('utf-8')
            if not msg: #client disconnected
                return
            addr = client_sock.getpeername()
            logging.info(f'action: receive_message | result: success | ip: {addr[0]} | msg: {msg}')

            bets = comms.parse_bet(msg)
            store_bets(bets)
            
            for bet in bets:
                if bet:
                    comms.full_write(client_sock,f"ack {bet.document} {bet.number}\n")
                else:
                    comms.full_write(client_sock,f"err {bet.document} {bet.number}\n")


        except OSError as e:
            logging.error(f"action: receive_message | result: fail | error: {e}")
        finally:
            addr = client_sock.getpeername()
            self.active_clients.pop(addr[0])
            client_sock.close()


    def __accept_new_connection(self):
        """
        Accept new connections

        Function blocks until a connection to a client is made.
        Then connection created is printed and returned
        """
        # Connection arrived
        logging.info('action: accept_connections | result: in_progress')
        if self.running:
            try:
                c, addr = self._server_socket.accept()
                logging.info(f'action: accept_connections | result: success | ip: {addr[0]}')
                self.active_clients[addr[0]] = c
                return c
            except:
                logging.error("SOCKET CERRADO")
                return None

