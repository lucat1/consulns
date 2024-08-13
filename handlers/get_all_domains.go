package handlers

import (
	"log/slog"
	"time"

	"github.com/lucat1/consulns/proto"
	"github.com/lucat1/consulns/store"
)

// {
// "id":1,
// "zone":"unit.test.",
// "masters":["10.0.0.1"],
// "notified_serial":2,
// "serial":2,
// "last_check":1464693331,
// "kind":"native"
// }

type Domain struct {
	ID             int       `json:"id"`
	Zone           string    `json:"zone"`
	Masters        []string  `json:"masters,omitempty"`
	NotifiedSerial int64     `json:"notified_serial,omitempty"`
	Serial         uint32    `json:"serial"`
	LastCheck      time.Time `json:"last_check,omitempty"`
	Kind           string    `json:"kind"`
}

func GetAllDomains(req *proto.Request, res *proto.Response) {
	slog.Info("returning all domains")
	domains := []Domain{}
	zones := store.Get().Zones()
	for id, z := range zones {
		domain := Domain{
			ID:             id,
			Zone:           z.Domain(),
			NotifiedSerial: 0, // TODO
			Serial:         z.Serial(),
			LastCheck:      z.LastUpdate(),
			Kind:           "native",
		}
		domains = append(domains, domain)
	}
	res.SetValue(domains)
}
