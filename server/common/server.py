import socket
import logging
import signal
import multiprocessing as mp
from .utils import Bet, store_bets, load_bets, has_won
from .comms import Comms, split_message
from .Abstract_client import Abstract_client

CANTIDAD_CLIENTES = 5

class Server:
    def __init__(self, port, listen_backlog):
        # Initialize server socket
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(('', port))
        self._server_socket.listen(listen_backlog)
        self.active_clients = {}
        self.client_handlers = {}
        self.running = True
        self.ready = {}
        self.file = None
        
    def handle_sigterm(self, signum, frame):
        logging.info("HANDLING SIGTERM")
        #self.running = False
        if self.file:
            self.file.close()
        for client in self.active_clients.values():
            client.close()

        for client_handler in self.client_handlers.values():
            client_handler.process.join()
            client_handler.parent_conn.close()
            client_handler.child_conn.close()

        self._server_socket.close()

    def run(self):
        """
        Dummy Server loop

        Server that accept a new connections and establishes a
        communication with a client. After client with communucation
        finishes, servers starts to accept new connections again
        """
        signal.signal(signal.SIGTERM, self.handle_sigterm)

        self.file = open("bets.csv", "w")
        lock = mp.Lock()

        amount_of_connections = 0
        while amount_of_connections < CANTIDAD_CLIENTES:
            client_sock = self.__accept_new_connection()
            if client_sock:
                client_handler = Abstract_client(client_sock, self.file, lock)
                client_handler.process.start()
                self.client_handlers[client_sock] = client_handler
                amount_of_connections += 1

        while amount_of_connections > 0:
            amount_of_connections = self.read_from_clients(amount_of_connections)

        self._server_socket.close()


    def read_from_clients(self, amount):
        handlers = list(self.client_handlers.values())
        for handler in handlers:
            conn = handler.parent_conn
            if conn.poll():
                recv = conn.recv()
                if recv.startswith("winners"):
                    self.handle_winners_request(conn, recv)
                elif recv.startswith("exit"):
                    handler.process.join()
                    self.client_handlers.pop(handler.sock)
        return len(self.client_handlers)


    def __accept_new_connection(self):
        """
        Accept new connections

        Function blocks until a connection to a client is made.
        Then connection created is printed and returned
        """
        # Connection arrived
        logging.info('action: accept_connections | result: in_progress')
        #if self.running:
        try:
            c, addr = self._server_socket.accept()
            logging.info(f'action: accept_connections | result: success | ip: {addr[0]}')
            self.active_clients[addr[0]] = c
            return c
        except:
            logging.error("SOCKET CERRADO")
            return None



    def handle_winners_request(self,parent_conn, msg):
        header, payload = split_message(msg)
        self.ready[payload] = parent_conn
        if len(self.ready) < CANTIDAD_CLIENTES:
            return
        
        amount_of_winners = self.get_winners()

        for client in self.ready.keys():
            client_sock = self.ready[client]
            message = "winners: " 

            if client in amount_of_winners.keys():
                client_winners = amount_of_winners[client]
                message += f" {len(client_winners)} "
                for i in client_winners:
                    message += " " + i
            message += "\n"
            client_sock.send(message)

        #self.running = False  # Stop the server loop
        logging.info("action: sorteo | result: success")

    def get_winners(self):
        bets = load_bets()
        winners = filter(has_won, bets)
        amount_of_winners = {}
        for winner in winners: 
            if str(winner.agency) not in amount_of_winners:
                amount_of_winners[str(winner.agency)] = []
            amount_of_winners[str(winner.agency)].append(winner.document)
        return amount_of_winners