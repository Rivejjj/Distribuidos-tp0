package common

import (
	"bufio"
	"fmt"
	"net"
	"strconv"

	log "github.com/sirupsen/logrus"
)

func read_message(c *Client, conn net.Conn) string {
	bytes_read := 0
	reader := bufio.NewReader(conn)
	recv, err := reader.ReadString('\n')
	verify_recv_error(c, err)
	bytes_read += len(recv)
	for !verify_message(c, recv) {
		read, err := reader.ReadString('\n')
		verify_recv_error(c, err)
		bytes_read += len(read)
		recv += read
	}

	header := get_header(recv)
	header_len := len(header)
	payload_len, err := strconv.Atoi(recv[:header_len-1])
	verify_recv_error(c, err)

	for bytes_read < payload_len+header_len {
		read, err := reader.ReadString('\n')
		verify_recv_error(c, err)
		bytes_read += len(read)
	}
	// Return the message without the header
	return recv[header_len:]
}

func verify_message(c *Client, msg string) bool {
	header := get_header(msg)

	payload_len, err := strconv.Atoi(msg[:len(header)-1])
	if err != nil {
		log.Errorf("action: receive_message | result: fail | client_id: %v | error: %v",
			c.config.ID,
			err,
		)
	}
	if header[len(header)-1] != '|' {
		return false
	}
	return len(msg) == payload_len+len(header)
}

func get_header(msg string) string {
	header := ""
	for i := 0; i < len(msg); i++ {
		header += string(msg[i])
		if msg[i] == '|' {
			break
		}
	}
	return header
}

func verify_recv_error(c *Client, err error) {
	if err != nil {
		log.Errorf("action: receive_message | result: fail | client_id: %v | error: %v",
			c.config.ID,
			err,
		)
		return
	}
}

func send_message(c *Client, conn net.Conn, msg string) {
	bytes_sent := 0
	for bytes_sent < len(msg) {
		bytes, err := fmt.Fprintf(
			conn,
			msg[bytes_sent:],
		)
		if err != nil {
			log.Errorf("action: send_message | result: fail | client_id: %v | error: %v",
				c.config.ID,
				err,
			)
			conn.Close()
			return
		}
		bytes_sent += bytes
	}
}

func create_message(batch_size int, reader *bufio.Reader, c *Client, last_batch *bool) string {
	msg_to_sv := ""
	for i := 0; i < batch_size; i++ {
		line := read_csv_line(reader, c.config.ID)
		if line == "" {
			*last_batch = true
			break
		}
		header := fmt.Sprintf("%v", len(line))
		msg_to_sv += header + line
	}
	header := ""
	if *last_batch {
		//header: batch_size, payload_len, (0 = not last batch, 1 = last batch)
		header = fmt.Sprintf("%v %v %v|", batch_size, len(msg_to_sv), 1)
	} else {
		header = fmt.Sprintf("%v %v %v|", batch_size, len(msg_to_sv), 0)
	}
	msg_to_sv = header + msg_to_sv
	return msg_to_sv
}
