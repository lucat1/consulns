package handlers

import (
	"encoding/json"
	"log/slog"

	"github.com/lucat1/consulns/proto"
	"github.com/lucat1/consulns/store"
)

type GetDomainMetadataRequest struct {
	DomainRequest
	Kind string `json:"kind"`
}

func GetDomainMetadata(req *proto.Request, res *proto.Response) {
	var r SetDomainMetadataRequest
	if err := json.Unmarshal(req.Parameters(), &r); err != nil {
		slog.Error("invalid domain metadata request", "parameters", req.Parameters(), "err", err)
		res.Fail()
		return
	}

	slog.Info("getting metadata", "domain", r.Name, "kind", r.Kind)
	_, d, err := store.Get().GetDomainByName(r.Name)
	if err != nil {
		slog.Error("cannot find domain by name", "domain", r.Name, "err", err)
		res.Fail()
		return
	}
	res.SetValue(d.GetMetadata(r.Kind))
}
