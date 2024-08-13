package handlers

import (
	"encoding/json"
	"log/slog"

	"github.com/lucat1/consulns/proto"
	"github.com/lucat1/consulns/store"
)

type SetDomainMetadataRequest struct {
	DomainRequest
	Kind  string   `json:"kind"`
	Value []string `json:"value"`
}

func SetDomainMetadata(req *proto.Request, res *proto.Response) {
	var r SetDomainMetadataRequest
	if err := json.Unmarshal(req.Parameters(), &r); err != nil {
		slog.Error("invalid domain metadata request", "parameters", req.Parameters(), "err", err)
		res.Fail()
		return
	}

	slog.Info("setting metadata", "domain", r.Name, "kind", r.Kind, "value", r.Value)
	_, d, err := store.Get().GetDomainByName(r.Name)
	if err != nil {
		slog.Error("cannot find domain by name", "domain", r.Name, "err", err)
		res.Fail()
		return
	}
	if err := d.SetMetadata(r.Kind, r.Value); err != nil {
		slog.Error("cannot save metadata", "domain", d.Zone(), "err", err)
		res.Fail()
		return
	}
	res.SetValue(true)
}
