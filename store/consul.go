package store

import (
	"encoding/json"
	"log/slog"
	"slices"
	"strings"

	// "log/slog"
	"fmt"
	"time"

	capi "github.com/hashicorp/consul/api"
)

func getDomainFromConsul(path string) (Domain, error) {
	var d Domain

	pair, _, err := KVApi.Get(path+"keys", nil)
	if err != nil {
		return d, err
	}
	var keys []Key
	err = json.Unmarshal(pair.Value, &keys)
	if err != nil {
		return d, err
	}
	d.keys = keys

	pair, _, err = KVApi.Get(path+"options/defaults", nil)
	if err != nil {
		return d, err
	}
	var def Defaults
	err = json.Unmarshal(pair.Value, &def)
	if err != nil {
		return d, err
	}
	d.defaults = def

	pair, _, err = KVApi.Get(path+"options/kind", nil)
	if err != nil {
		return d, err
	}
	var kind string
	err = json.Unmarshal(pair.Value, &kind)
	if err != nil {
		return d, err
	}
	d.kind = kind

	pair, _, err = KVApi.Get(path+"options/last_update", nil)
	if err != nil {
		return d, err
	}
	var last_update time.Time
	err = json.Unmarshal(pair.Value, &last_update)
	if err != nil {
		return d, err
	}
	d.lastUpdate = last_update

	records, _, err := KVApi.Keys(path+CONSUL_RECORDS+"/", "/", nil)
	if err != nil {
		return d, err
	}

	if d.records == nil {
		d.records = make(map[string][]Record, 0)
	}

	for i := range records {
		pair, _, err = KVApi.Get(records[i], nil)
		if err != nil {
			return d, err
		}

		var r []Record
		err := json.Unmarshal(pair.Value, &r)
		if err != nil {
			slog.With("value", pair.Value).Error("")
			return d, err
		}

		if strings.HasSuffix(records[i], "@") {
			domain := strings.Split(records[i], "/")[1]
			d.records[domain] = r
		}
	}

	if d.metadata == nil {
		d.metadata = make(map[string][]string, 0)
	}

	metadatas, _, err := KVApi.Keys(path+CONSUL_METADATA+"/", "/", nil)
	if err != nil {
		return d, err
	}

	for i := range metadatas {
		pair, _, err = KVApi.Get(metadatas[i], nil)
		if err != nil {
			return d, err
		}

		var r []string
		err := json.Unmarshal(pair.Value, &r)
		if err != nil {
			slog.With("value", pair.Value).Error("")
			return d, err
		}

		if strings.HasSuffix(records[i], "@") {
			domain := strings.Split(records[i], "/")[1]
			d.metadata[domain] = r
		}
	}

	return d, nil
}

// tmp
func fillConsul() {
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
	store.AddZone(z1)

	var err error
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

	// slog.Debug("store initialized", "store", store)
}

func consulAddRecord(zone, domain string, record *Record) {
	path := CONSUL_DNS_BASE + "/" + zone + "/" + CONSUL_RECORDS + "/"

	domain = strings.TrimSuffix(domain, zone)
	if len(domain) == 0 {
		domain = "@"
	}
	path = path + domain
	pair, _, err := KVApi.Get(path, nil)
	if err != nil {
		panic(err)
	}

	var records []Record

	if pair != nil {
		err = json.Unmarshal(pair.Value, &records)
		if err != nil {
			panic(err)
		}
	}

	records = append(records, *record)

	m, err := json.Marshal(records)
	if err != nil {
		panic(err)
	}
	putIfNotExists(path, m)
}
