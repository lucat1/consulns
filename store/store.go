package store

import (
	"fmt"
	"log/slog"

	capi "github.com/hashicorp/consul/api"
)

type Store struct {
	domains []Domain
}

var store *Store

// Api for kv store inside consul
var KVApi *capi.KV

func Get() *Store {
	return store
}

func Init() (err error) {

	KVApi, err = initConsul()
	if err != nil {
		return err
	}

	store = &Store{}

	// fillConsul()
	getFromConsul()

	slog.With("store", store).Debug("")

	return
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
	consulAddZone(&zone)
	s.domains = append(s.domains, zone)
	return
}

func (s *Store) ForwardLookup(query string, rt RecordType) (records []Record) {
	for _, z := range s.domains {
		records = append(records, z.ForwardLookup(query, rt)...)
	}
	return
}
