package client

import (
	"encoding/json"
	"fmt"
	"time"
)

const lastUpdateTimeFormat = time.RFC3339

type ZoneKind string

const (
	ZoneKindNative  = "native"
	ZoneKindDynamic = "dynamic"
)

func ParseKind(b []byte) (z ZoneKind, err error) {
	z = ZoneKind(b)
	switch z {
	case ZoneKindNative:
	case ZoneKindDynamic:
		return
	default:
		err = fmt.Errorf("Invalid zone kind: %s", string(b))
		return
	}
	return
}

type Zone struct {
	client *Client

	domain     string
	kind       ZoneKind
	lastUpdate time.Time

	paths paths
}

type paths struct {
	root string

	options    string
	defaults   string
	kind       string
	lastUpdate string

	keys     string
	metadata string
	records  string
}

func zonePaths(domain string) (paths paths, err error) {
	if paths.root, err = join(DNS_PREFIX, domain); err != nil {
		return
	}

	if paths.options, err = join(paths.root, OPTIONS); err != nil {
		return
	}
	if paths.defaults, err = join(paths.options, DEFAULTS); err != nil {
		return
	}
	if paths.kind, err = join(paths.options, KIND); err != nil {
		return
	}
	if paths.lastUpdate, err = join(paths.options, LAST_UPDATE); err != nil {
		return
	}

	if paths.keys, err = join(paths.root, KEYS); err != nil {
		return
	}
	if paths.metadata, err = join(paths.root, METADATA); err != nil {
		return
	}
	if paths.records, err = join(paths.root, RECORDS); err != nil {
		return
	}
	return
}

func (z Zone) Domain() string {
	return z.domain
}

type Defaults struct {
	TTL      uint32 `json:"ttl"`
	Priority uint32 `json:"priority"`
}

func (z Zone) Defaults() (defaults Defaults, err error) {
	defaultsKV, _, err := z.client.kv.Get(z.paths.kind, nil)
	if err != nil || defaultsKV == nil {
		err = fmt.Errorf("Cannot read defaults for zone %s", z.domain)
		return
	}

	if err = json.Unmarshal(defaultsKV.Value, &defaults); err != nil {
		err = fmt.Errorf("Could not parse defaults: %v", err)
	}
	return
}
