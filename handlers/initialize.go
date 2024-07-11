package handlers

import (
	"log/slog"

	"github.com/lucat1/consulns/proto"
)

func Initialize(req *proto.Request, res *proto.Response) {
	slog.Info("initialized")
}
