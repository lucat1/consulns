package store

import (
	"fmt"
	"log/slog"
	"time"
)

type Store struct {
	domains []Domain
}

func (s *Store) Domains() []Domain {
	return s.domains
}

func (s *Store) HasZone(id int) bool {
	return id >= 0 && id < len(s.domains)
}

func (s *Store) GetZone(id int) (zone *Domain, err error) {
	if id < 0 || id >= len(s.domains) {
		err = fmt.Errorf("zone with %d does not exist", id)
		return
	}
	zone = &s.domains[id]
	return
}

func (s *Store) GetDomainByName(name string) (id int, dom *Domain, err error) {
	for i, d := range s.domains {
		if d.Zone() == name {
			id = i
			dom = &s.domains[i]
			return
		}
	}
	err = fmt.Errorf("Domain with zone name %s not found", name)
	return
}

func (s *Store) AddZone(zone Domain) (err error) {
	for _, z := range s.domains {
		if z.zone == zone.zone {
			err = fmt.Errorf("zone for domain %s already exists", zone.zone)
			return
		}
	}
	s.domains = append(s.domains, zone)
	return
}

func (s *Store) ForwardLookup(query string, rt RecordType) (records []Record) {
	for _, z := range s.domains {
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
	z1 := Domain{
		zone: "teapot.ovh.",
		defaults: Defaults{
			TTL:      3600,
			Priority: 10,
		},
		lastUpdate: time.Now(),
		records:    map[string][]Record{},
		metadata:   map[string][]string{},
	}
	store = &Store{}

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
	store.AddZone(z1)
	slog.Debug("store initialized", "store", store)
	return
}
