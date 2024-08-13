package handlers

import (
	"encoding/json"
	"fmt"
	"log/slog"

	"github.com/lucat1/consulns/proto"
	"github.com/lucat1/consulns/store"
)

type UpdateDomainKeyRequest struct {
	DomainRequest
	ID int `json:"id"`
}

func update(method string) (upd store.KeyUpdate, err error) {
	t := true
	f := false

	switch method {
	case "activateDomainKey":
		upd = store.KeyUpdate{Active: &t}
	case "deactivateDomainKey":
		upd = store.KeyUpdate{Active: &f}
	case "publishDomainKey":
		upd = store.KeyUpdate{Published: &t}
	case "unpublishDomainKey":
		upd = store.KeyUpdate{Published: &f}
	default:
		err = fmt.Errorf("Unrecognized method name for domain key update: %s", method)
	}
	return
}

func UpdateDomainKey(req *proto.Request, res *proto.Response) {
	var r UpdateDomainKeyRequest
	if err := json.Unmarshal(req.Parameters(), &r); err != nil {
		slog.Error("invalid update domain key request", "parameters", req.Parameters(), "err", err)
		res.Fail()
		return
	}

	upd, err := update(req.Method())
	if err != nil {
		slog.Error("invalid update domain key method", "method", req.Method(), "err", err)
		res.Fail()
		return
	}

	slog.Info("updating domain key", "domain", r.Name, "update", upd, "id", r.ID)
	_, d, err := store.Get().GetDomainByName(r.Name)
	if err != nil {
		slog.Error("cannot find domain by name", "domain", r.Name, "err", err)
		res.Fail()
		return
	}

	if err := d.UpdateKey(r.ID, upd); err != nil {
		slog.Error("cannot update key for domain", "domain", r.Name, "id", r.ID, "err", err)
		res.Fail()
		return
	}

	res.SetValue(true)
}
