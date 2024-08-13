package handlers

import (
	"encoding/json"
	"log/slog"

	"github.com/lucat1/consulns/proto"
	"github.com/lucat1/consulns/store"
)

type ListRequest struct {
	Zonename string `json:"zonename"`
	DomainID int    `json:"domain_id"`
}

func List(req *proto.Request, res *proto.Response) {
	var list ListRequest
	if err := json.Unmarshal(req.Parameters(), &list); err != nil {
		slog.Error("invalid list request", "parameters", req.Parameters(), "err", err)
		res.Fail()
		return
	}

	slog.Info("performing list", "list", list)
	s := store.Get()
	var (
		d   *store.Domain
		err error
	)
	if s.HasZone(list.DomainID) {
		d, err = s.GetZone(list.DomainID)
	} else {
		_, d, err = s.GetDomainByName(list.Zonename)
	}
	if err != nil {
		slog.Error("invalid list domain", "id", list.DomainID, "domain", list.Zonename, "err", err)
		res.Fail()
		return
	}

	// TODO: expand records with consul data
	results := []Record{}
	// convert our internal structure to PDNS's
	for domain, records := range d.Records() {
		for _, rr := range records {
			record := Record{
				QType:   string(rr.Type),
				QName:   domain,
				Content: rr.Value,
				TTL:     rr.TTL,
			}
			results = append(results, record)
		}
	}

	res.SetValue(results)
}
