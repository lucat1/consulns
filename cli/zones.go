package cli

import (
	"fmt"

	"github.com/lucat1/consulns/client"
	"github.com/urfave/cli/v2"
)

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
		fmt.Printf("%s\n", zone)
	}
	return
}
