package handlers

import (
	"encoding/json"
	"log/slog"

	"github.com/lucat1/consulns/proto"
	"github.com/lucat1/consulns/store"
)

type RemoveDomainKeyRequest struct {
	DomainRequest
	ID int `json:"id"`
}

func RemoveDomainKey(req *proto.Request, res *proto.Response) {
	var r RemoveDomainKeyRequest
	if err := json.Unmarshal(req.Parameters(), &r); err != nil {
		slog.Error("invalid remove domain key request", "parameters", req.Parameters(), "err", err)
		res.Fail()
		return
	}

	slog.Info("removing domain key", "domain", r.Name, "id", r.ID)
	_, d, err := store.Get().GetDomainByName(r.Name)
	if err != nil {
		slog.Error("cannot find domain by name", "domain", r.Name, "err", err)
		res.Fail()
		return
	}

	if err := d.RemoveKey(r.ID); err != nil {
		slog.Error("cannot remove key from domain", "domain", r.Name, "id", r.ID, "err", err)
		res.Fail()
		return
	}

	res.SetValue(true)
}
