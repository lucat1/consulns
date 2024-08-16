package main

import (
	"fmt"
	"os"

	"github.com/urfave/cli/v2"
)

func main() {
	var (
		ttl      int
		priority int
		consul   bool
	)

	app := &cli.App{
		EnableBashCompletion: true,
		Commands: []*cli.Command{
			{
				Name:    "zones",
				Aliases: []string{"z"},
				Usage:   "actions on zones",
				Subcommands: []*cli.Command{
					{
						Name:    "list",
						Aliases: []string{"ls"},
						Usage:   "list all available zones",
						Args:    false,
						Action: func(cCtx *cli.Context) error {
							fmt.Println("list all zones")
							return nil
						},
					},
					{
						Name:  "show",
						Usage: "show information about a zone",
						Args:  true,
						Action: func(cCtx *cli.Context) error {
							fmt.Println("show info about zone", cCtx.Args().First())
							return nil
						},
					},
					{
						Name:  "add",
						Usage: "add a new zone",
						Args:  true,
						Action: func(cCtx *cli.Context) error {
							fmt.Println("add new zone", cCtx.Args().First())
							return nil
						},
					},
					{
						Name:  "remove",
						Usage: "remove a zone",
						Args:  true,
						Action: func(cCtx *cli.Context) error {
							fmt.Println("remove zone", cCtx.Args().First())
							return nil
						},
					},
				},
			},
			{
				Name:    "records",
				Aliases: []string{"r"},
				Usage:   "actions on records",
				Subcommands: []*cli.Command{
					{
						Name:  "list",
						Usage: "list all records for a given zone",
						Args:  false,
						Action: func(cCtx *cli.Context) error {
							fmt.Println("list records for zone", cCtx.Args().First())
							return nil
						},
					},
					{
						Name:  "add",
						Usage: "add a new record",
						Args:  true,
						Flags: []cli.Flag{
							&cli.IntFlag{
								Name:        "ttl",
								Usage:       "the record's ttl",
								Destination: &ttl,
							},
							&cli.IntFlag{
								Name:        "priority",
								Usage:       "the record's priority",
								Destination: &priority,
							},
							&cli.BoolFlag{
								Name:        "consul",
								Usage:       "whether this record's shall have a value from dynamic",
								Destination: &consul,
							},
						},
						Action: func(cCtx *cli.Context) error {
							zone := cCtx.Args().First()
							fmt.Println("adding new record to ", zone)
							domain := cCtx.Args().Get(1)
							kind := cCtx.Args().Get(2)
							if ttl == 0 {
								ttl = 60 // whatever, default
							}
							value := cCtx.Args().Get(3)
							fmt.Printf("record is %s.%s IN %s %d %d %t %s", domain, zone, kind, ttl, priority, consul, value)
							return nil
						},
					},
					{
						Name:  "remove",
						Usage: "remove an existing record",
						Args:  true,
						Action: func(cCtx *cli.Context) error {
							id := cCtx.Args().Get(1)
							fmt.Println("removing record", cCtx.Args().First(), id)
							return nil
						},
					},
				},
			},
		},
	}

	if err := app.Run(os.Args); err != nil {
		fmt.Fprintf(os.Stderr, "%v", err)
	}
}
