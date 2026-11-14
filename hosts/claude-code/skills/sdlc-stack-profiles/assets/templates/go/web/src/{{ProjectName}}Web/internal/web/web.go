// Package web is the HTTP boundary: server-rendered pages over
// the sample items slice.
//
// Routes: GET / renders the items page, POST /items handles the
// add form (post/redirect/get, so a refresh never resubmits),
// GET /health answers the probe, /static/ serves assets. Only
// config.Public is ever passed to a template — see the config
// package for the split. Templates are html/template, so rendered
// values are context-escaped by construction.
package web

import (
	"embed"
	"encoding/json"
	"html/template"
	"log"
	"net/http"
	"strings"

	"example.com/{{project-name}}/internal/config"
	"example.com/{{project-name}}/internal/items"
)

//go:embed templates/*.html
var templatesFS embed.FS

//go:embed static/*
var staticFS embed.FS

type pageData struct {
	Public config.Public
	Items  []items.Item
}

// Server is the web app.
type Server struct {
	store     *items.Store
	public    config.Public
	server    config.Server
	templates *template.Template
}

// NewServer builds the app. The server config is accepted to make
// the boundary explicit — it is held for server-side calls and
// never reaches a template.
func NewServer(store *items.Store, public config.Public, server config.Server) *Server {
	tmpl := template.Must(template.ParseFS(templatesFS, "templates/*.html"))
	return &Server{store: store, public: public, server: server, templates: tmpl}
}

// Mux returns the route table.
func (s *Server) Mux() *http.ServeMux {
	mux := http.NewServeMux()
	mux.HandleFunc("GET /", s.index)
	mux.HandleFunc("POST /items", s.addItem)
	mux.HandleFunc("GET /health", s.health)
	mux.Handle("GET /static/", http.FileServerFS(staticFS))
	return mux
}

func (s *Server) index(w http.ResponseWriter, r *http.Request) {
	if r.URL.Path != "/" {
		http.NotFound(w, r)
		return
	}
	w.Header().Set("Content-Type", "text/html; charset=utf-8")
	data := pageData{Public: s.public, Items: s.store.List()}
	if err := s.templates.ExecuteTemplate(w, "base.html", data); err != nil {
		log.Printf("render index: %v", err)
	}
}

func (s *Server) addItem(w http.ResponseWriter, r *http.Request) {
	if err := r.ParseForm(); err != nil {
		http.Error(w, "invalid form", http.StatusBadRequest)
		return
	}
	name := strings.TrimSpace(r.FormValue("name"))
	if name == "" {
		http.Error(w, "name is required", http.StatusBadRequest)
		return
	}
	s.store.Add(name)
	http.Redirect(w, r, "/", http.StatusSeeOther)
}

func (s *Server) health(w http.ResponseWriter, _ *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	_ = json.NewEncoder(w).Encode(map[string]string{"status": "ok"})
}
