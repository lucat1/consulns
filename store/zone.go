package store

import (
	"fmt"
	"log/slog"
	"strconv"
	"strings"
	"time"
)

type RecordType string

const (
	RecordTypeANY   RecordType = "ANY"
	RecordTypeSOA   RecordType = "SOA"
	RecordTypeNS    RecordType = "NS"
	RecordTypeA     RecordType = "A"
	RecordTypeAAAA  RecordType = "AAAA"
	RecordTypeMX    RecordType = "MX"
	RecordTypeCNAME RecordType = "CNAME"
	RecordTypeTXT   RecordType = "TXT"
	RecordTypeSRV   RecordType = "SRV"
)

type Record struct {
	TTL      uint32     `json:"ttl"`
	Type     RecordType `json:"type"`
	Priority uint32     `json:"priority"`
	Consul   bool       `json:"consul"`
	Value    string     `json:"value"`
}

type Defaults struct {
	TTL      uint32 `json:"ttl"`
	Priority uint32 `json:"priority"`
}

type KeyUpdate struct {
	Active    *bool
	Published *bool
}

type Key struct {
	Flags     int
	Active    bool
	Published bool
	Content   string
}

type Domain struct {
	defaults   Defaults
	zone       string
	kind       string
	lastUpdate time.Time
	records    map[string][]Record
	keys       []Key
	metadata   map[string][]string
}

func (d Domain) Zone() string {
	return d.zone
}

func (d Domain) Kind() string {
	return d.kind
}

func (d Domain) LastUpdate() time.Time {
	return d.lastUpdate
}

func (d Domain) Records() map[string][]Record {
	return d.records
}

func (d Domain) Serial() uint32 {
	// TODO: serial should be more granular, but we're limited to an uint32 in terms of size
	serial := fmt.Sprintf("%04d%02d%02d", d.lastUpdate.Year(), d.lastUpdate.Month(), d.lastUpdate.Day())
	slog.Debug("generated serial", "serial", serial, "last_update", d.lastUpdate)
	seriali, err := strconv.ParseInt(serial, 10, 32)
	if err != nil {
		panic(err)
	}
	return uint32(seriali)
}

func (d Domain) Keys() []Key {
	return d.keys
}

func (d Domain) Metadata() map[string][]string {
	return d.metadata
}

func (d Domain) GetMetadata(kind string) (value []string) {
	value, found := d.metadata[kind]
	if !found {
		value = []string{}
	}
	return
}

func (d Domain) ForwardLookup(query string, rt RecordType) (records []Record) {
	rs := d.records[query]
	for _, r := range rs {
		if r.MatchesType(rt) {
			records = append(records, r)
		}
	}
	return
}

func (r Record) MatchesType(rt RecordType) bool {
	return rt == RecordTypeANY || rt == r.Type
}

func (d *Domain) AddRecord(domain string, record Record) (err error) {
	if !strings.HasSuffix(domain, ".") {
		err = fmt.Errorf("invalid domain: %s, expected trailing .", domain)
		return
	}

	if record.TTL == 0 {
		record.TTL = d.defaults.TTL
	}

	if record.Priority == 0 {
		record.Priority = d.defaults.Priority
	}

	d.records[domain] = append(d.records[domain], record)

	consulAddRecord(d.zone, domain, &record)

	// TODO: efficiently handle reverse lookup
	return
}

func (d *Domain) AddKey(ak Key) (err error) {
	d.keys = append(d.keys, Key{
		Flags:     ak.Flags,
		Active:    ak.Active,
		Published: ak.Published,
		Content:   ak.Content,
	})
	// TODO: this should be also saved on consul
	return
}

func (d *Domain) UpdateKey(id int, upd KeyUpdate) (err error) {
	if id < 0 || id >= len(d.keys) {
		err = fmt.Errorf("Zone %s has no key with id %d", d.zone, id)
		return
	}

	key := d.keys[id]
	if upd.Active != nil {
		key.Active = *upd.Active
	}
	if upd.Published != nil {
		key.Published = *upd.Published
	}
	// TODO: check that the following line is actually necessary
	d.keys[id] = key
	// TODO: this should be also saved on consul
	return
}

func (d *Domain) RemoveKey(id int) (err error) {
	if id < 0 || id >= len(d.keys) {
		err = fmt.Errorf("Zone %s has no key with id %d", d.zone, id)
		return
	}

	d.keys = append(d.keys[:id], d.keys[id+1:]...)
	// TODO: this should be also saved on consul
	return
}

func (d *Domain) SetMetadata(kind string, value []string) (err error) {
	if prev, found := d.metadata[kind]; found {
		slog.Debug("overwriting metadata", "kind", kind, "prev", strings.Join(prev, ","), "new", strings.Join(value, ","))
	}
	d.metadata[kind] = value
	// TODO: save in consul
	return
}
