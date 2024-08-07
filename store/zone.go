package store

import (
	"fmt"
	"strings"
	"time"
)

type IPKey [16]byte

type Zone struct {
	defaults   Defaults
	domain     string
	lastUpdate time.Time
	records    map[string][]Record
}

func (z Zone) Domain() string {
	return z.domain
}

func (z Zone) LastUpdate() time.Time {
	return z.lastUpdate
}

func (z Zone) ForwardLookup(query string, rt RecordType) (records []Record) {
	rs := z.records[query]
	for _, r := range rs {
		if r.MatchesType(rt) {
			records = append(records, r)
		}
	}
	return
}

func (z *Zone) AddRecord(domain string, record Record) (err error) {
	if !strings.HasSuffix(domain, ".") {
		err = fmt.Errorf("invalid domain: %s, expected trailing .", domain)
		return
	}

	if record.TTL == 0 {
		record.TTL = z.defaults.TTL
	}

	if record.Priority == 0 {
		record.Priority = z.defaults.Priority
	}

	z.records[domain] = append(z.records[domain], record)
	// TODO: efficiently handle reverse lookup
	return
}

type Defaults struct {
	TTL      uint32
	Priority uint32
}

const (
	RecordTypeANY   RecordType = "ANY"
	RecordTypeA     RecordType = "A"
	RecordTypeAAAA  RecordType = "AAAA"
	RecordTypeMX    RecordType = "MX"
	RecordTypeNS    RecordType = "NS"
	RecordTypeCNAME RecordType = "CNAME"
	RecordTypeTXT   RecordType = "TXT"
	RecordTypeSRV   RecordType = "SRV"
)

type RecordType string

type Record struct {
	TTL      uint32
	Type     RecordType
	Priority uint32
	Consul   bool
	Value    string
}

func (r Record) MatchesType(rt RecordType) bool {
	return rt == RecordTypeANY || rt == r.Type
}
