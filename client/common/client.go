package common

import (
	"bufio"
	"errors"
	"io"
	"net"
	"os"
	"os/signal"
	"strings"
	"syscall"
	"time"

	log "github.com/sirupsen/logrus"
)

// ClientConfig Configuration used by the client
type ClientConfig struct {
	ID            string
	ServerAddress string
	LoopLapse     time.Duration
	LoopPeriod    time.Duration
}

// Client Entity that encapsulates how
type Client struct {
	config ClientConfig
	conn   net.Conn
}

// NewClient Initializes a new client receiving the configuration
// as a parameter
func NewClient(config ClientConfig) *Client {
	client := &Client{
		config: config,
	}
	return client
}

// CreateClientSocket Initializes client socket. In case of
// failure, error is printed in stdout/stderr and exit 1
// is returned
func (c *Client) createClientSocket() error {
	conn, err := net.Dial("tcp", c.config.ServerAddress)
	if err != nil {
		log.Fatalf(
			"action: connect | result: fail | client_id: %v | error: %v",
			c.config.ID,
			err,
		)
	}
	c.conn = conn
	return nil
}

// StartClientLoop Send messages to the client until some time threshold is met
func (c *Client) StartClientLoop() {
	// autoincremental msgID to identify every message sent
	sigchan := make(chan os.Signal, 1)
	signal.Notify(sigchan, syscall.SIGTERM)

	filename := "agency-" + c.config.ID + ".csv"
	file, err := os.Open(filename)
	if err != nil {
		log.Fatalf("Failed to open file: %s", err)
	}
	defer file.Close()
	reader := bufio.NewReader(file)

	done := make(chan bool, 1)
	go func() {
		sig := <-sigchan
		log.Infof("CLIENTE RECIBIO SIGTERM: %v", sig)
		if file != nil {
			file.Close()
		}
		c.conn.Close()
		done <- true
	}()
	last_batch := false

loop:
	// Send messages if the loopLapse threshold has not been surpassed
	for !last_batch {
		// Create the connection the server in every loop iteration.
		c.createClientSocket()

		batch_size := 30
		msg_to_sv := create_message(batch_size, reader, c, &last_batch)

		// SENDING
		send_message(c, c.conn, msg_to_sv)

		//READING
		sv_answer := read_message(c, c.conn)
		answer := strings.Split(sv_answer, " ")
		if answer[0] == "err" {
			for answer[0] == "err" {
				send_message(c, c.conn, msg_to_sv)
				sv_answer := read_message(c, c.conn)
				answer = strings.Split(sv_answer, " ")
			}
		}

		if last_batch {
			file.Close()
			c.conn.Close()
			break loop
		}

		c.conn.Close()
		// Wait a time between sending one message and the next one
		time.Sleep(c.config.LoopPeriod)
	}

	c.createClientSocket()
	winners_msg := "winners|" + c.config.ID
	send_message(c, c.conn, winners_msg)
	sv_answer := read_message(c, c.conn)
	log.Infof("action: consulta ganadores | result: success | client_id: %v | cantidad: %v", c.config.ID, sv_answer)
	c.conn.Close()
}

func read_csv_line(reader *bufio.Reader, id string) string {
	line, err := reader.ReadString('\n')
	if errors.Is(err, io.EOF) {
		return ""
	}
	if err != nil {
		log.Fatalf("Failed to read line: %s", err)
	}

	fields := strings.Split(line, ",")
	fields[4] = strings.TrimSuffix(fields[4], "\n")
	fields[4] = strings.TrimSuffix(fields[4], "\r")

	msg := "|" + id
	for i := 0; i < len(fields); i++ {
		msg += "|" + fields[i]
	}
	msg += "|$"
	return msg
}
