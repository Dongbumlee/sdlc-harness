package web

import (
	"encoding/json"
	"net/http"
	"strconv"
	"strings"

	"example.com/{{project-name}}/internal/model"
	"example.com/{{project-name}}/internal/service"
)

// NewMux builds the HTTP routing for the API. It is the only place
// routes are registered, so tests exercise exactly what main serves.
func NewMux(items service.ItemService) *http.ServeMux {
	mux := http.NewServeMux()
	mux.HandleFunc("GET /health", HealthHandler)
	mux.HandleFunc("GET /health/ready", ReadyHandler)
	mux.HandleFunc("POST /items", createItem(items))
	mux.HandleFunc("GET /items", listItems(items))
	mux.HandleFunc("GET /items/{id}", getItem(items))
	return mux
}

func createItem(items service.ItemService) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		var request model.ItemCreate
		if err := json.NewDecoder(r.Body).Decode(&request); err != nil {
			writeError(w, http.StatusBadRequest, "request body must be valid JSON")
			return
		}
		if strings.TrimSpace(request.Name) == "" {
			writeError(w, http.StatusBadRequest, "name must not be blank")
			return
		}
		writeJSON(w, http.StatusCreated, items.Create(request.Name))
	}
}

func listItems(items service.ItemService) http.HandlerFunc {
	return func(w http.ResponseWriter, _ *http.Request) {
		writeJSON(w, http.StatusOK, items.List())
	}
}

func getItem(items service.ItemService) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		id, err := strconv.ParseInt(r.PathValue("id"), 10, 64)
		if err != nil {
			writeError(w, http.StatusNotFound, "item not found")
			return
		}
		item, ok := items.Get(id)
		if !ok {
			writeError(w, http.StatusNotFound, "item not found")
			return
		}
		writeJSON(w, http.StatusOK, item)
	}
}
