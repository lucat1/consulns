package proto

import (
	"context"
	"encoding/json"
	"log/slog"
	"net"
)

type Command struct {
	Method     string          `json:"method"`
	Parameters json.RawMessage `json:"parameters"`
}

type Request struct {
	ctx context.Context
	cmd Command
}

func NewRequest(ctx context.Context, cmd Command) Request {
	return Request{
		ctx: ctx,
		cmd: cmd,
	}
}

func (r *Request) Context() context.Context {
	return r.ctx
}

func (r *Request) Method() string {
	return r.cmd.Method
}

func (r *Request) Parameters() json.RawMessage {
	return r.cmd.Parameters
}

type Response struct {
	Result interface{} `json:"result"`
}

func NewResponse() Response {
	return Response{Result: true}
}

func (r *Response) Fail() {
	r.Result = false
}

func (r *Response) SetValue(v interface{}) {
	r.Result = v
}

func (r *Response) serialize() (res []byte) {
	res, err := json.Marshal(r)
	if err != nil {
		slog.Error("could not serialize response", "response", *r)
	}
	return
}

type Handler func(req *Request, res *Response)

type rawHandler struct {
	handlers map[string]Handler
}

func newHandler() *rawHandler {
	return &rawHandler{
		handlers: map[string]Handler{},
	}
}

func (h *rawHandler) handleMethod(method string, handler Handler) {
	if h.handlers[method] != nil {
		slog.Warn("re-registered handler", "method", method, "handler", handler)
	}
	slog.Debug("registered handler", "method", method, "handler", handler)
	h.handlers[method] = handler
}

func (h *rawHandler) send(conn net.Conn, response *Response) {
	data := response.serialize()
	slog.Debug("writing", "conn", conn, "data", string(data))
	if _, err := conn.Write(data); err != nil {
		slog.Error("could not serialize error in response to invalid command", "err", err)
	}
}

func (h *rawHandler) handle(ctx context.Context, rawCommand []byte, conn net.Conn) {
	response := NewResponse()

	var cmd Command
	if err := json.Unmarshal(rawCommand, &cmd); err != nil {
		slog.Error("could not parse command", "raw", string(rawCommand))
		response.Fail()
		h.send(conn, &response)
	}

	request := NewRequest(ctx, cmd)
	if h.handlers[cmd.Method] != nil {
		h.handlers[cmd.Method](&request, &response)
		h.send(conn, &response)
	} else {
		slog.Error("no handler defined", "method", cmd.Method)
		response.Fail()
		h.send(conn, &response)
	}
}
