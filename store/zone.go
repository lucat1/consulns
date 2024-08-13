package store

import (
	"fmt"
	"log/slog"
	"strconv"
	"strings"
	"time"
)

type IPKey [16]byte

type Defaults struct {
	TTL      uint32
	Priority uint32
}

type Zone struct {
	defaults   Defaults
	domain     string
	lastUpdate time.Time
	records    map[string][]Record
	keys       map[int]Key
}

func (z Zone) Domain() string {
	return z.domain
}

func (z Zone) LastUpdate() time.Time {
	return z.lastUpdate
}

func (z Zone) Serial() uint32 {
	// TODO: serial should be more granular, but we're limited to an uint32 in terms of size
	serial := fmt.Sprintf("%04d%02d%02d", z.lastUpdate.Year(), z.lastUpdate.Month(), z.lastUpdate.Day())
	slog.Debug("generated serial", "serial", serial, "last_update", z.lastUpdate)
	seriali, err := strconv.ParseInt(serial, 10, 32)
	if err != nil {
		panic(err)
	}
	return uint32(seriali)
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
