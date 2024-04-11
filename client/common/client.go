package common

import (
	"fmt"
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

func getEnvs() []string {
	envs := []string{
		os.Getenv("NOMBRE"),
		os.Getenv("APELLIDO"),
		os.Getenv("DOCUMENTO"),
		os.Getenv("NACIMIENTO"),
		os.Getenv("NUMERO"),
	}
	return envs
}

// StartClientLoop Send messages to the client until some time threshold is met
func (c *Client) StartClientLoop() {
	// autoincremental msgID to identify every message sent
	sigchan := make(chan os.Signal, 1)
	signal.Notify(sigchan, syscall.SIGTERM)

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

		bytes_sent := 0
		data := getEnvs()

		nombre := data[0]
		apellido := data[1]
		dni := data[2]
		nacimiento := data[3]
		numero := data[4]
		msg_to_sv := fmt.Sprintf("|%v|%v|%v|%v|%v|%v", c.config.ID, nombre, apellido, dni, nacimiento, numero) //PONER CONSTANTES
		header := fmt.Sprintf("%v ", len(msg_to_sv))
		msg_to_sv = header + msg_to_sv

		// SENDING
		send_message(c, c.conn, msg_to_sv[bytes_sent:])

		//READING
		sv_answer := read_message(c, c.conn)
		answer := strings.Split(sv_answer, " ")
		if answer[0] == "err" {
			log.Errorf("action: receive_message | result: fail | client_id: %v | error: could not store bet",
				c.config.ID,
			)
			c.conn.Close()
			break loop
		}
		c.conn.Close()
		// Wait a time between sending one message and the next one
		time.Sleep(c.config.LoopPeriod)
	}
	c.conn.Close()

	log.Infof("action: loop_finished | result: success | client_id: %v", c.config.ID)
}
