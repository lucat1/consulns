package handlers

import (
	"encoding/json"
	"log/slog"

	"github.com/lucat1/consulns/proto"
	"github.com/lucat1/consulns/store"
)

type DomainKey struct {
	ID        int    `json:"id"`
	Flags     int    `json:"flags"`
	Active    bool   `json:"active"`
	Published bool   `json:"published"`
	Content   string `json:"content"`
}

func GetDomainKeys(req *proto.Request, res *proto.Response) {
	var r DomainRequest
	if err := json.Unmarshal(req.Parameters(), &r); err != nil {
		slog.Error("invalid domain keys request", "parameters", req.Parameters(), "err", err)
		res.Fail()
		return
	}

	slog.Info("returning all domain keys", "domain", r.Name)
	_, d, err := store.Get().GetDomainByName(r.Name)
	if err != nil {
		slog.Error("cannot find domain by name", "domain", r.Name, "err", err)
		res.Fail()
		return
	}

	keys := []DomainKey{}
	for id, key := range d.Keys() {
		keys = append(keys, DomainKey{
			ID:        id,
			Flags:     key.Flags,
			Active:    key.Active,
			Published: key.Published,
			Content:   key.Content,
		})
	}
	res.SetValue(keys)
}
