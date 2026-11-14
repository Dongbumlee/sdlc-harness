// Command {{project-name}} is the composition root: it wires the
// implementations and starts the HTTP server. Wiring only — no
// business logic lives here.
package main

import (
	"log"
	"net/http"
	"os"

	"example.com/{{project-name}}/internal/config"
	"example.com/{{project-name}}/internal/items"
	"example.com/{{project-name}}/internal/web"
)

func main() {
	server := web.NewServer(items.NewSeededStore(), config.LoadPublic(), config.LoadServer())

	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}
	log.Printf("listening on :%s", port)
	log.Fatal(http.ListenAndServe(":"+port, server.Mux()))
}
