package client

import (
	"encoding/json"
	"fmt"
	"time"
)

const lastUpdateTimeFormat = time.RFC3339

type Kind string

const (
	ZoneKindNative  = "native"
	ZoneKindDynamic = "dynamic"
)

func ParseKind(b []byte) (z Kind, err error) {
	z = Kind(b)
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
	kind       Kind
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

func (z Zone) Kind() Kind {
	return z.kind
}

func (z Zone) LastUpdate() time.Time {
	return z.lastUpdate
}

type Defaults struct {
	TTL      uint32 `json:"ttl"`
	Priority uint32 `json:"priority"`
}

func (z Zone) Defaults() (defaults Defaults, err error) {
	defaultsKV, _, err := z.client.kv.Get(z.paths.defaults, nil)
	if err != nil || defaultsKV == nil {
		err = fmt.Errorf("Cannot read defaults for zone %s", z.domain)
		return
	}

	if err = json.Unmarshal(defaultsKV.Value, &defaults); err != nil {
		err = fmt.Errorf("Could not parse defaults: %v", err)
	}
	return
}

type Key struct {
	ID        int    `json:"id"`
	Flags     int    `json:"flags"`
	Active    bool   `json:"active"`
	Published bool   `json:"published"`
	Content   string `json:"content"`
}

func (z Zone) Keys() (keys []Key, err error) {
	keysKV, _, err := z.client.kv.Get(z.paths.keys, nil)
	if err != nil || keysKV == nil {
		err = fmt.Errorf("Cannot read keys for zone %s", z.domain)
		return
	}

	var rawKeys []Key
	if err = json.Unmarshal(keysKV.Value, &rawKeys); err != nil {
		err = fmt.Errorf("Could not parse keys: %v", err)
	}

	// Preserve the order across load-store cycles
	keys = make([]Key, len(rawKeys))
	for _, rawKey := range rawKeys {
		keys[rawKey.ID] = rawKey
	}
	return
}

type Metadata map[string][]string

func (z Zone) Metadata() (metadata Metadata, err error) {
	metadataKV, _, err := z.client.kv.Get(z.paths.metadata, nil)
	if err != nil || metadataKV == nil {
		err = fmt.Errorf("Cannot read metadata for zone %s", z.domain)
		return
	}

	if err = json.Unmarshal(metadataKV.Value, &metadata); err != nil {
		err = fmt.Errorf("Could not parse metadata: %v", err)
	}
	return
}
