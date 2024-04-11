package common

import (
	"bufio"
	"errors"
	"fmt"
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
	// total_sent := 0
	// ack := 0

loop:
	// Send messages if the loopLapse threshold has not been surpassed
	for timeout := time.After(c.config.LoopLapse); ; {
		select {
		case <-timeout:
			log.Infof("action: timeout_detected | result: success | client_id: %v",
				c.config.ID,
			)
			break loop

		case <-sigchan:
			log.Infof("CLIENTE RECIBIO SIGTERM")
			c.conn.Close()
			return

		default:
		}

		// Create the connection the server in every loop iteration. Send an

		c.createClientSocket()

		batch_size := 30
		msg_to_sv := ""
		last_batch := false
		for i := 0; i < batch_size; i++ {
			line := read_csv_line(reader, c.config.ID)
			if line == "" {
				last_batch = true
				break
			}
			header := fmt.Sprintf("%v", len(line))
			msg_to_sv += header + line
		}
		header := ""
		if last_batch {
			header = fmt.Sprintf("%v %v %v|", batch_size, len(msg_to_sv), 1)
		} else {
			header = fmt.Sprintf("%v %v %v|", batch_size, len(msg_to_sv), 0)
		}

		msg_to_sv = header + msg_to_sv
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
			break loop
		}

		c.conn.Close()
		// Wait a time between sending one message and the next one
		time.Sleep(c.config.LoopPeriod)
	}

	c.conn.Close()
	log.Infof("action: loop_finished | result: success | client_id: %v", c.config.ID)
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
