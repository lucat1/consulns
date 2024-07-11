package handlers

import (
	"time"

	"github.com/lucat1/consulns/proto"
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
	NotifiedSerial int       `json:"notified_serial,omitempty"`
	Serial         int       `json:"serial"`
	LastCheck      time.Time `json:"last_check,omitempty"`
	Kind           string    `json:"kind"`
}

func GetAllDomains(req *proto.Request, res *proto.Response) {
	res.SetValue([]Domain{{
		ID:             1,
		Zone:           "teapot.ovh.",
		NotifiedSerial: 1,
		Serial:         1,
		LastCheck:      time.Now(),
		Kind:           "native",
	}})
}
