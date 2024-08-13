package handlers

import (
	"encoding/json"
	"log/slog"

	"github.com/lucat1/consulns/proto"
	"github.com/lucat1/consulns/store"
)

type AddDomainKeyRequest struct {
	DomainRequest
	Key AddDomainKeyRequestKey `json:"key"`
}

type AddDomainKeyRequestKey struct {
	Flags     int    `json:"flags"`
	Active    bool   `json:"active"`
	Published bool   `json:"published"`
	Content   string `json:"content"`
}

func AddDomainKey(req *proto.Request, res *proto.Response) {
	var r AddDomainKeyRequest
	if err := json.Unmarshal(req.Parameters(), &r); err != nil {
		slog.Error("invalid add domain key request", "parameters", req.Parameters(), "err", err)
		res.Fail()
		return
	}

	slog.Info("adding domain key", "domain", r.Name, "key", r.Key)
	_, d, err := store.Get().GetDomainByName(r.Name)
	if err != nil {
		slog.Error("cannot find domain by name", "domain", r.Name, "err", err)
		res.Fail()
		return
	}

	key := store.Key{
		Flags:     r.Key.Flags,
		Active:    r.Key.Active,
		Published: r.Key.Published,
		Content:   r.Key.Content,
	}
	if err := d.AddKey(key); err != nil {
		slog.Error("cannot add key to domain", "domain", r.Name, "key", key, "err", err)
		res.Fail()
		return
	}

	res.SetValue(true)
}
