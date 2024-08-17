package client

import (
	"encoding/json"
	"fmt"
	"net/url"
	"slices"
	"strings"
	"time"

	capi "github.com/hashicorp/consul/api"
)

type Client struct {
	kv *capi.KV
}

var client *Client

func Initialize() (err error) {
	// TODO: Actual login in a cluster
	cclient, err := capi.NewClient(capi.DefaultConfig())
	if err != nil {
		err = fmt.Errorf("Could not connect to consul: %v", err)
		return
	}

	client = &Client{kv: cclient.KV()}
	return
}

func Get() *Client {
	return client
}

const (
	DNS_PREFIX = "dns"

	OPTIONS     = "options"
	DEFAULTS    = "defaults"
	KIND        = "kind"
	LAST_UPDATE = "last_update"

	KEYS     = "keys"
	METADATA = "metadata"
	RECORDS  = "records"
)

const slash = "/"

func (c Client) Zones() (zones []Zone, err error) {
	path := DNS_PREFIX + slash
	domains, _, err := c.kv.Keys(path, slash, nil)
	if err != nil {
		err = fmt.Errorf("Error while fetching zones from consul: %v", err)
		return
	}

	for _, rawDomain := range domains {
		var zone Zone

		rawDomain, _ := strings.CutPrefix(rawDomain, path)
		domain, _ := strings.CutSuffix(rawDomain, slash)
		zone, err = c.GetZone(domain)
		if err != nil {
			return
		}
		zones = append(zones, zone)
	}

	return
}

func join(base string, elems ...string) (s string, err error) {
	s, err = url.JoinPath(base, elems...)
	if err != nil {
		err = fmt.Errorf("Cannot compute concatenate path %s + %v: %v", base, elems, err)
	}
	return
}

func (client Client) update(key string, value []byte) (err error) {
	pair, _, err := client.kv.Get(key, nil)
	if err != nil {
		return
	}
	if pair != nil && slices.Equal(pair.Value, value) {
		return
	}

	_, err = client.kv.Put(&capi.KVPair{Key: key, Value: value}, nil)
	return
}

var DefaultDefaults = Defaults{
	TTL:      60,
	Priority: 0,
}

func (c *Client) GetZone(domain string) (zone Zone, err error) {
	paths, err := zonePaths(domain)
	if err != nil {
		return
	}

	kindKV, _, err := c.kv.Get(paths.kind, nil)
	if err != nil || kindKV == nil {
		err = fmt.Errorf("Cannot read kind for zone %s", domain)
		return
	}
	kind, err := ParseKind(kindKV.Value)
	if err != nil {
		return
	}

	lastUpdateKV, _, err := c.kv.Get(paths.lastUpdate, nil)
	if err != nil || lastUpdateKV == nil {
		err = fmt.Errorf("Cannot read last update for zone %s", domain)
		return
	}
	lastUpdate, err := time.Parse(lastUpdateTimeFormat, string(lastUpdateKV.Value))
	if err != nil {
		err = fmt.Errorf("Could not parse last update time: %v", err)
		return
	}

	zone = Zone{
		client: c,

		domain:     domain,
		kind:       kind,
		lastUpdate: lastUpdate,

		paths: paths,
	}
	return
}

func (c *Client) AddZone(domain string, kind ZoneKind) (zone Zone, err error) {
	_, err = c.GetZone(domain)
	if err == nil {
		err = fmt.Errorf("Zone %s already exists, refusing to overwrite", domain)
		return
	}
	err = nil

	paths, err := zonePaths(domain)
	if err != nil {
		return
	}

	m, err := json.Marshal(DefaultDefaults)
	if err != nil {
		err = fmt.Errorf("Cannot serialize zone default defaults: %v", err)
		return
	}

	if err = c.update(paths.defaults, m); err != nil {
		return
	}

	if err = c.update(paths.kind, []byte(kind)); err != nil {
		return
	}

	lastUpdate := time.Now()
	if err = c.update(paths.lastUpdate, []byte(lastUpdate.Format(lastUpdateTimeFormat))); err != nil {
		return
	}

	if err = c.update(paths.keys, []byte("[]")); err != nil {
		return
	}

	zone = Zone{
		client: c,

		domain:     domain,
		kind:       kind,
		lastUpdate: lastUpdate,

		paths: paths,
	}
	return
}
