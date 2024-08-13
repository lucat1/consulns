package store

import (
	"fmt"
	"log/slog"
	"time"
)

type Store struct {
	zones []Zone
}

func (s Store) Zones() []Zone {
	return s.zones
}

func (s Store) HasZone(id int) bool {
	return id >= 0 && id < len(s.zones)
}

func (s Store) GetZone(id int) (zone Zone, err error) {
	if id < 0 || id >= len(s.zones) {
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

func (s Store) ForwardLookup(query string, rt RecordType) (records []Record) {
	for _, z := range s.zones {
		records = append(records, z.ForwardLookup(query, rt)...)
	}
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
		lastUpdate: time.Now(),
		records:    map[string][]Record{},
	}
	store = &Store{}
	store.AddZone(z1)

	if err = z1.AddRecord("teapot.ovh.", Record{
		Type:  RecordTypeSOA,
		Value: fmt.Sprintf("ns1.teapot.ovh. root.teapot.ovh. %d 7200 3600 1209600 3600", z1.Serial()),
	}); err != nil {
		return
	}
	if err = z1.AddRecord("teapot.ovh.", Record{
		Type:  RecordTypeNS,
		Value: "ns1.teapot.ovh",
	}); err != nil {
		return
	}
	if err = z1.AddRecord("ns1.teapot.ovh.", Record{
		Type:  RecordTypeA,
		Value: "1.2.3.4",
	}); err != nil {
		return
	}
	if err = z1.AddRecord("teapot.ovh.", Record{
		Type:  RecordTypeA,
		Value: "1.2.3.4",
	}); err != nil {
		return
	}
	slog.Debug("store initialized", "store", store)
	return
}
