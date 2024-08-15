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

const (
	CONSUL_DNS_BASE = "dns"
	CONSUL_RECORDS  = "records"
	CONSUL_METADATA = "metadata"
)

func initConsul() (*capi.KV, error) {
	// TODO: Actual login in a cluster
	client, err := capi.NewClient(capi.DefaultConfig())
	if err != nil {
		return nil, err
	}

	return client.KV(), nil
}

// Get all values from consul and fill the store
func getFromConsul() {
	path := CONSUL_DNS_BASE + "/"

	keys, _, err := KVApi.Keys(path, "/", nil)
	if err != nil {
		panic(err)
	}

	var domains []Domain
	for i := range keys {
		domains = append(domains, getDomainFromConsul(keys[i]))
	}
	store.domains = domains
}

func getDomainFromConsul(path string) (d Domain) {
	pair, _, err := KVApi.Get(path+"keys", nil)
	if err != nil {
		panic(err)
	}
	var keys []Key
	err = json.Unmarshal(pair.Value, &keys)
	if err != nil {
		panic(err)
	}
	d.keys = keys

	pair, _, err = KVApi.Get(path+"options/defaults", nil)
	if err != nil {
		panic(err)
	}
	var def Defaults
	err = json.Unmarshal(pair.Value, &def)
	if err != nil {
		panic(err)
	}
	d.defaults = def

	pair, _, err = KVApi.Get(path+"options/kind", nil)
	if err != nil {
		panic(err)
	}
	var kind string
	err = json.Unmarshal(pair.Value, &kind)
	if err != nil {
		panic(err)
	}
	d.kind = kind

	pair, _, err = KVApi.Get(path+"options/last_update", nil)
	if err != nil {
		panic(err)
	}
	var last_update time.Time
	err = json.Unmarshal(pair.Value, &last_update)
	if err != nil {
		panic(err)
	}
	d.lastUpdate = last_update

	records, _, err := KVApi.Keys(path+CONSUL_RECORDS+"/", "/", nil)
	if err != nil {
		panic(err)
	}

	if d.records == nil {
		d.records = make(map[string][]Record, 0)
	}

	for i := range records {
		pair, _, err = KVApi.Get(records[i], nil)
		if err != nil {
			panic(err)
		}

		var r []Record
		err := json.Unmarshal(pair.Value, &r)
		if err != nil {
			slog.With("value", pair.Value).Error("")
			panic(err)
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
		panic(err)
	}

	for i := range metadatas {
		pair, _, err = KVApi.Get(metadatas[i], nil)
		if err != nil {
			panic(err)
		}

		var r []string
		err := json.Unmarshal(pair.Value, &r)
		if err != nil {
			slog.With("value", pair.Value).Error("")
			panic(err)
		}

		if strings.HasSuffix(records[i], "@") {
			domain := strings.Split(records[i], "/")[1]
			d.metadata[domain] = r
		}
	}

	return
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

func putIfNotExists(key string, value []byte) {
	pair, _, err := KVApi.Get(key, nil)
	if err != nil {
		panic(err)
	}
	if pair != nil && slices.Equal(pair.Value, value) {
		return
	}

	_, err = KVApi.Put(&capi.KVPair{Key: key, Value: value}, nil)
	if err != nil {
		panic(err)
	}
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

func consulAddZone(zone *Domain) {
	path := CONSUL_DNS_BASE + "/" + zone.zone

	m, err := json.Marshal(zone.defaults)
	if err != nil {
		panic(err)
	}
	putIfNotExists(path+"/options/defaults", m)

	putIfNotExists(path+"/options/kind", []byte(zone.kind))

	m, err = json.Marshal(zone.lastUpdate)
	if err != nil {
		panic(err)
	}
	putIfNotExists(path+"/options/last_update", m)

	m, err = json.Marshal(zone.keys)
	if err != nil {
		panic(err)
	}
	putIfNotExists(path+"/keys", m)

	for d, i := range zone.records {
		m, err := json.Marshal(i)
		if err != nil {
			panic(err)
		}

		putIfNotExists(path+"/"+CONSUL_RECORDS+"/"+d, m)
	}

	for d, i := range zone.metadata {
		m, err := json.Marshal(i)
		if err != nil {
			panic(err)
		}

		putIfNotExists(path+"/"+CONSUL_METADATA+"/"+d, m)
	}
}
