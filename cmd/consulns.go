package main

import (
	"context"
	"flag"
	"log/slog"
	"os"
	"os/signal"
	"syscall"

	"github.com/lucat1/consulns/handlers"
	"github.com/lucat1/consulns/proto"
	"github.com/lucat1/consulns/store"
)

func main() {
	flag.Parse()
	slog.SetLogLoggerLevel(slog.LevelDebug)
	args := flag.Args()
	if len(args) != 1 {
		slog.Error("invalid program usage, missing socket path", "args", args)
		os.Exit(1)
	}

	if err := store.Initialize(); err != nil {
		slog.Error("could not initialize store", "err", err)
		os.Exit(2)
	}

	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer stop()

	s := proto.NewListener(ctx, args[0])
	s.HandleMethod("initialize", handlers.Initialize)
	s.HandleMethod("lookup", handlers.Lookup)
	s.HandleMethod("list", handlers.List)

	s.HandleMethod("getAllDomains", handlers.GetAllDomains)
	s.HandleMethod("getDomainInfo", handlers.GetDomainInfo)

	s.HandleMethod("getAllDomainMetadata", handlers.GetAllDomainMetadata)
	s.HandleMethod("getDomainMetadata", handlers.GetDomainMetadata)
	s.HandleMethod("setDomainMetadata", handlers.SetDomainMetadata)

	s.HandleMethod("getDomainKeys", handlers.GetDomainKeys)
	s.HandleMethod("addDomainKey", handlers.AddDomainKey)
	s.HandleMethod("removeDomainKey", handlers.AddDomainKey)
	s.HandleMethod("activateDomainKey", handlers.UpdateDomainKey)
	s.HandleMethod("deactivateDomainKey", handlers.UpdateDomainKey)
	s.HandleMethod("publishDomainKey", handlers.UpdateDomainKey)
	s.HandleMethod("unpublishDomainKey", handlers.UpdateDomainKey)

	if err := s.ListenAndServe(); err != nil {
		slog.Error("could not open unix listener", "path", args[0], "err", err)
		os.Exit(3)
	}
}
