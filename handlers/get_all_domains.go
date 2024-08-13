package handlers

import (
	"log/slog"

	"github.com/lucat1/consulns/proto"
	"github.com/lucat1/consulns/store"
)

type Domain struct {
	ID   int    `json:"id"`
	Zone string `json:"zone"`
	// NotifiedSerial int64     `json:"notified_serial,omitempty"`
	Serial uint32 `json:"serial"`
	// LastCheck      time.Time `json:"last_check,omitempty"`
	Kind string `json:"kind"`
}

func GetAllDomains(req *proto.Request, res *proto.Response) {
	slog.Info("returning all domains")
	domains := []Domain{}
	for id, z := range store.Get().Domains() {
		domain := Domain{
			ID:   id,
			Zone: z.Zone(),
			// NotifiedSerial: 0, // TODO
			Serial: z.Serial(),
			// LastCheck:      z.LastUpdate(),
			Kind: z.Kind(),
		}
		domains = append(domains, domain)
	}
	res.SetValue(domains)
}
