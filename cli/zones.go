package cli

import (
	"fmt"

	"github.com/lucat1/consulns/client"
	"github.com/urfave/cli/v2"
)

// Prints the zone info in a one-line format without furhter API fetching
func listZone(zone client.Zone) {
	fmt.Printf("%s\n", zone.Domain())
}

// Prints the detailed zone info
func showZone(zone client.Zone) {
	fmt.Printf("TODO %s\n", zone.Domain())
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
	fmt.Println("show info about zone", ctx.Args().First())
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

	zone, err := client.Get().AddZone(domain, client.ZoneKindNative)
	if err != nil {
		return
	}

	listZone(zone)
	return
}
