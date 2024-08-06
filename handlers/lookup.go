package handlers

import (
	"encoding/json"
	"log/slog"
	"strings"

	"github.com/lucat1/consulns/proto"
	"github.com/lucat1/consulns/store"
)

type LookupRequest struct {
	Local      string           `json:"local"`
	QName      string           `json:"qname"`
	QType      store.RecordType `json:"qtype"`
	RealRemote string           `json:"real-remote"`
	Remote     string           `json:"remote"`
	ZoneID     int              `json:"zone-id"`
}

type Record struct {
	QType   string `json:"qtype"`
	QName   string `json:"qname"`
	Content string `json:"content"`
	TTL     uint32 `json:"ttl"`
}

func cutDots(qname string) string {
	s1, _ := strings.CutSuffix(qname, ".")
	s2, _ := strings.CutSuffix(s1, ".")
	return s2
}

func Lookup(req *proto.Request, res *proto.Response) {
	var lookup LookupRequest
	if err := json.Unmarshal(req.Parameters(), &lookup); err != nil {
		slog.Error("invalid lookup request", "parameters", req.Parameters(), "err", err)
		res.Fail()
		return
	}

	slog.Debug("performing lookup", "lookup", lookup)
	s := store.Get()
	z, err := s.GetZone(lookup.ZoneID)
	if err != nil {
		slog.Error("invalid lookup zone", "id", lookup.ZoneID, "err", err)
		res.Fail()
		return
	}
	records := z.ForwardLookup(lookup.QName, lookup.QType)

	// TODO: expand records with consul data
	results := []Record{}
	// convert our internal structure to PDNS's
	for _, rr := range records {
		record := Record{
			QType:   string(rr.Type),
			QName:   cutDots(lookup.QName),
			Content: rr.Value,
			TTL:     rr.TTL,
		}
		results = append(results, record)
	}

	res.SetValue(results)
}
