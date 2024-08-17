package client

import (
	"fmt"

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
	CONSUL_DNS_BASE = "dns"
	CONSUL_RECORDS  = "records"
	CONSUL_METADATA = "metadata"
)

func (client Client) Zones() (zones []string, err error) {
	path := CONSUL_DNS_BASE + "/"
	zones, _, err = client.kv.Keys(path, "/", nil)
	if err != nil {
		err = fmt.Errorf("Error while fetching zones from consul: %v", err)
		return
	}

	return

	// for i := range keys {
	// 	d, err := getDomainFromConsul(keys[i])
	// 	if err != nil {
	// 		return err
	// 	}
	// 	domains = append(domains, d)
	// }
	// store.domains = domains

	// return nil
}
