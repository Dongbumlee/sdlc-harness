// Package config is the application configuration, split the way
// the web type requires.
//
// The split is structural, not a naming habit. Values a browser
// may see live in Public and are the only ones templates ever
// receive. Server-only values live in Server, are read from the
// environment at startup, and must never be rendered, logged, or
// sent to a client — leaking one into a page is this type's
// signature security defect, and the test suite pins a sentinel
// secret out of every response.
package config

import (
	"os"
	"strings"
)

var prefix = strings.ReplaceAll(strings.ToUpper("{{project-name}}"), "-", "_") + "_"

// Public holds browser-safe values: fine to render into any page.
type Public struct {
	AppName string
}

// Server holds server-only values: never rendered, never sent to
// a client.
type Server struct {
	APIKey string
}

func LoadPublic() Public {
	appName := os.Getenv(prefix + "PUBLIC_APP_NAME")
	if appName == "" {
		appName = "{{ProjectName}}"
	}
	return Public{AppName: appName}
}

func LoadServer() Server {
	return Server{APIKey: os.Getenv(prefix + "SERVER_API_KEY")}
}
