package handlers

import (
	"encoding/json"
	"log/slog"

	"github.com/lucat1/consulns/proto"
	"github.com/lucat1/consulns/store"
)

type DomainKeysRequest struct {
	Name string `json:"name"`
}

type DomainKey struct {
	ID        int    `json:"id"`
	Flags     int    `json:"flags"`
	Active    bool   `json:"active"`
	Published bool   `json:"published"`
	Content   string `json:"content"`
}

func GetDomainKeys(req *proto.Request, res *proto.Response) {
	var dkr DomainKeysRequest
	if err := json.Unmarshal(req.Parameters(), &dkr); err != nil {
		slog.Error("invalid domain keys request", "parameters", req.Parameters(), "err", err)
		res.Fail()
		return
	}

	slog.Info("returning all domain keys")
	keys := []DomainKey{}
	zones := store.Get().Zones()
	for _, z := range zones {
		if z.Domain() == dkr.Name {
			for id, key := range z.Keys() {
				keys = append(keys, DomainKey{
					ID:        id,
					Flags:     key.Flags,
					Active:    key.Active,
					Published: key.Published,
					Content:   key.Content,
				})
			}
		}
	}
	res.SetValue(keys)
}
