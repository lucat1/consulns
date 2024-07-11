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
)

func main() {
	flag.Parse()
	slog.SetLogLoggerLevel(slog.LevelDebug)
	args := flag.Args()
	if len(args) != 1 {
		slog.Error("invalid program usage, missing socket path", "args", args)
		os.Exit(1)
	}

	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer stop()

	s := proto.NewListener(ctx, args[0])
	s.HandleMethod("initialize", handlers.Initialize)
	s.HandleMethod("getAllDomains", handlers.GetAllDomains)
	if err := s.ListenAndServe(); err != nil {
		slog.Error("could not open unix listener", "path", args[0], "err", err)
		os.Exit(1)
	}
}
