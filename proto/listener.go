package proto

import (
	"bufio"
	"context"
	"log/slog"
	"net"
	"sync"
	"time"
)

type Listener struct {
	ctx     context.Context
	addr    string
	handler *rawHandler

	listener net.Listener
	wg       sync.WaitGroup
}

func NewListener(ctx context.Context, addr string) *Listener {
	return &Listener{
		ctx:     ctx,
		addr:    addr,
		handler: newHandler(),
	}
}

func (s *Listener) ListenAndServe() (err error) {
	s.listener, err = net.Listen("unix", s.addr)
	if err != nil {
		return
	}

	go s.serve()

	<-s.ctx.Done()
	s.listener.Close()
	s.wg.Wait()
	return
}

func (s *Listener) serve() {
	s.wg.Add(1)
	defer s.wg.Done()

	slog.Info("listening", "addr", s.listener.Addr)
	for {
		conn, err := s.listener.Accept()
		if err != nil {
			select {
			case <-s.ctx.Done():
				return
			default:
				slog.Error("could not accept client connection", "err", err)
			}
		} else {
			// +1 on the wait queue as we have to wait for another routine to finish
			go s.handle(conn)
		}
	}
}

func (s *Listener) HandleMethod(method string, handler Handler) {
	s.handler.handleMethod(method, handler)
}

func (s *Listener) handle(conn net.Conn) {
	s.wg.Add(1)
	defer s.wg.Done()

	slog.Info("handling connection", "conn", conn)

	scanner := bufio.NewScanner(conn)
	defer conn.Close()
	for {
		select {
		case <-s.ctx.Done():
			return
		default:
			if !scanner.Scan() {
				slog.Info("connection closed", "conn", conn)
				return // EOF
			}
			if err := scanner.Err(); err != nil {
				slog.Error("error while rading connection", "err", err)
				return
			}

			line := scanner.Bytes()
			slog.Debug("received", "conn", conn, "data", string(line))
			ctx, _ := context.WithTimeout(s.ctx, time.Millisecond*2000)
			s.handler.handle(ctx, line, conn)
		}
	}
}
