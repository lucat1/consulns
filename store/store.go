package store

import (
	"fmt"
	"log/slog"
)

type Store struct {
	zones []Zone
}

func (s Store) Zones() []Zone {
	return s.zones
}

func (s Store) GetZone(id int) (zone Zone, err error) {
	if id >= len(s.zones) || id < 0 {
		err = fmt.Errorf("zone with id %d does not exist (0 <= id <= %d)", id, len(s.zones)-1)
		return
	}
	zone = s.zones[id]
	return
}

func (s *Store) AddZone(zone Zone) (err error) {
	for _, z := range s.zones {
		if z.domain == zone.domain {
			err = fmt.Errorf("zone for domain %s already exists", zone.domain)
			return
		}
	}
	s.zones = append(s.zones, zone)
	return
}

var store *Store

func Get() *Store {
	return store
}

func Init() (err error) {
	// TODO: actually connect to consul and fetch the data from the KV store
	z1 := Zone{
		domain: "teapot.ovh",
		defaults: Defaults{
			TTL:      3600,
			Priority: 10,
		},
		records: map[string][]Record{},
	}
	store = &Store{}
	store.AddZone(z1)

	if err = z1.AddRecord("teapot.ovh.", Record{
		Type:  RecordTypeA,
		Value: "127.0.0.1",
	}); err != nil {
		return
	}
	slog.Debug("store initialized", "store", store)
	return
}
