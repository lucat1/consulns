package cli

import (
	"crypto/sha1"
	"fmt"
	"strings"
	"time"

	"github.com/lucat1/consulns/client"
	"github.com/urfave/cli/v2"
)

// Prints the zone info in a one-line format without furhter API fetching
func listZone(zone client.Zone) {
	fmt.Printf("%s\t\t\t%s\t\t%s\n", zone.Domain(), zone.Kind(), zone.LastUpdate().Format(time.RFC1123))
}

// Prints the detailed zone info
func showZone(zone client.Zone) (err error) {
	defs, err := zone.Defaults()
	if err != nil {
		return
	}
	keys, err := zone.Keys()
	if err != nil {
		return
	}
	metadata, err := zone.Metadata()
	if err != nil {
		return
	}

	fmt.Printf("Showing zone %s\n", zone.Domain())
	fmt.Printf("Kind: %s\n", zone.Kind())
	fmt.Printf("Last edit: %s\n", zone.LastUpdate())
	fmt.Printf("Defaults:\n")
	fmt.Printf("    Time To Live: %d\n", defs.TTL)
	fmt.Printf("    Priority: %d\n", defs.Priority)
	fmt.Printf("Keys:\n")
	if len(keys) == 0 {
		fmt.Printf("    (empty)\n")
	} else {
		for _, key := range keys {
			fmt.Printf("    (%d) %x\n", key.ID, sha1.Sum([]byte(key.Content)))
		}
	}
	fmt.Printf("Metadata:\n")
	if len(metadata) == 0 {
		fmt.Printf("    (empty)\n")
	} else {
		for k, vs := range metadata {
			fmt.Printf("    %s: %s\n", k, strings.Join(vs, ";"))
		}
	}
	return
}

func ListZones(ctx *cli.Context) (err error) {
	if ctx.Args().Len() > 0 {
		err = fmt.Errorf("Expected no command line arguments, got %d", ctx.Args().Len())
		return
	}

	if err = client.Initialize(); err != nil {
		return
	}

	zones, err := client.Get().Zones()
	if err != nil {
		return
	}

	for _, zone := range zones {
		listZone(zone)
	}
	return
}

func ShowZone(ctx *cli.Context) (err error) {
	if ctx.Args().Len() != 1 {
		err = fmt.Errorf("Expected exactly one argument, got %d", ctx.Args().Len())
		return
	}
	domain := ctx.Args().First()
	if err = client.Initialize(); err != nil {
		return
	}

	zone, err := client.Get().GetZone(domain)
	if err != nil {
		return
	}

	err = showZone(zone)
	return
}

func AddZone(ctx *cli.Context) (err error) {
	if ctx.Args().Len() != 1 {
		err = fmt.Errorf("Expected exactly one argument, got %d", ctx.Args().Len())
		return
	}
	domain := ctx.Args().First()

	if err = client.Initialize(); err != nil {
		return
	}

	_, err = client.Get().AddZone(domain, client.ZoneKindNative)
	return
}
