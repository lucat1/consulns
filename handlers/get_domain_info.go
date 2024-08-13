package handlers

import (
	"encoding/json"
	"log/slog"

	"github.com/lucat1/consulns/proto"
	"github.com/lucat1/consulns/store"
)

func GetDomainInfo(req *proto.Request, res *proto.Response) {
	var dr DomainRequest
	if err := json.Unmarshal(req.Parameters(), &dr); err != nil {
		slog.Error("invalid domain info request", "parameters", req.Parameters(), "err", err)
		res.Fail()
		return
	}

	slog.Info("getting all domain info", "request", dr)
	id, d, err := store.Get().GetDomainByName(dr.Name)
	if err != nil {
		slog.Error("cannot find domain by name", "name", dr.Name, "err", err)
		res.Fail()
		return
	}
	res.SetValue(Domain{
		ID:     id,
		Zone:   d.Zone(),
		Serial: d.Serial(),
		Kind:   d.Kind(),
	})
}
