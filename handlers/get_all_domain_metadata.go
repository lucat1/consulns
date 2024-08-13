package handlers

import (
	"encoding/json"
	"log/slog"

	"github.com/lucat1/consulns/proto"
)

type MetadataRequest struct {
	Name string `json:"name"`
}

func GetAllDomainMetadata(req *proto.Request, res *proto.Response) {
	var mr MetadataRequest
	if err := json.Unmarshal(req.Parameters(), &mr); err != nil {
		slog.Error("invalid domain metadata request", "parameters", req.Parameters(), "err", err)
		res.Fail()
		return
	}

	slog.Info("getting all domain metadata", "request", mr)
	// TODO: figure out what we nee to implement here
	res.SetValue(map[string]interface{}{})
}
