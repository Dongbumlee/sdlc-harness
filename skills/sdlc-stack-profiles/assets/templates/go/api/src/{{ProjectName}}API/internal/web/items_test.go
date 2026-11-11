package web_test

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"strconv"
	"strings"
	"testing"

	"example.com/{{project-name}}/internal/model"
	"example.com/{{project-name}}/internal/service"
	"example.com/{{project-name}}/internal/web"
)

func newServer(t *testing.T) http.Handler {
	t.Helper()
	repository := service.NewInMemoryItemRepository()
	return web.NewMux(service.NewDefaultItemService(repository))
}

func do(t *testing.T, handler http.Handler, method, path, body string) *httptest.ResponseRecorder {
	t.Helper()
	var reader *strings.Reader
	if body == "" {
		reader = strings.NewReader("")
	} else {
		reader = strings.NewReader(body)
	}
	request := httptest.NewRequest(method, path, reader)
	recorder := httptest.NewRecorder()
	handler.ServeHTTP(recorder, request)
	return recorder
}

func decodeItem(t *testing.T, recorder *httptest.ResponseRecorder) model.Item {
	t.Helper()
	var item model.Item
	if err := json.NewDecoder(recorder.Body).Decode(&item); err != nil {
		t.Fatalf("decode item: %v", err)
	}
	return item
}

func TestHealthEndpoints(t *testing.T) {
	handler := newServer(t)

	recorder := do(t, handler, http.MethodGet, "/health", "")
	if recorder.Code != http.StatusOK {
		t.Fatalf("GET /health: got status %d, want %d", recorder.Code, http.StatusOK)
	}
	var health map[string]string
	if err := json.NewDecoder(recorder.Body).Decode(&health); err != nil {
		t.Fatalf("decode health: %v", err)
	}
	if health["status"] != "healthy" {
		t.Fatalf("GET /health: got status value %q, want %q", health["status"], "healthy")
	}

	recorder = do(t, handler, http.MethodGet, "/health/ready", "")
	if recorder.Code != http.StatusOK {
		t.Fatalf("GET /health/ready: got status %d, want %d", recorder.Code, http.StatusOK)
	}
	var ready map[string]string
	if err := json.NewDecoder(recorder.Body).Decode(&ready); err != nil {
		t.Fatalf("decode ready: %v", err)
	}
	if ready["status"] != "ready" {
		t.Fatalf("GET /health/ready: got status value %q, want %q", ready["status"], "ready")
	}
}

func TestCreateAndGetItem(t *testing.T) {
	handler := newServer(t)

	recorder := do(t, handler, http.MethodPost, "/items", `{"name":"first"}`)
	if recorder.Code != http.StatusCreated {
		t.Fatalf("POST /items: got status %d, want %d", recorder.Code, http.StatusCreated)
	}
	created := decodeItem(t, recorder)
	if created.Name != "first" {
		t.Fatalf("POST /items: got name %q, want %q", created.Name, "first")
	}

	recorder = do(t, handler, http.MethodGet, "/items/"+strconv.FormatInt(created.ID, 10), "")
	if recorder.Code != http.StatusOK {
		t.Fatalf("GET /items/{id}: got status %d, want %d", recorder.Code, http.StatusOK)
	}
	fetched := decodeItem(t, recorder)
	if fetched != created {
		t.Fatalf("GET /items/{id}: got %+v, want %+v", fetched, created)
	}
}

func TestGetMissingItem(t *testing.T) {
	handler := newServer(t)
	recorder := do(t, handler, http.MethodGet, "/items/999", "")
	if recorder.Code != http.StatusNotFound {
		t.Fatalf("GET /items/999: got status %d, want %d", recorder.Code, http.StatusNotFound)
	}
}

func TestCreateBlankNameRejected(t *testing.T) {
	handler := newServer(t)
	recorder := do(t, handler, http.MethodPost, "/items", `{"name":"  "}`)
	if recorder.Code != http.StatusBadRequest {
		t.Fatalf("POST /items blank name: got status %d, want %d", recorder.Code, http.StatusBadRequest)
	}
}

func TestListItems(t *testing.T) {
	handler := newServer(t)
	do(t, handler, http.MethodPost, "/items", `{"name":"one"}`)
	do(t, handler, http.MethodPost, "/items", `{"name":"two"}`)

	recorder := do(t, handler, http.MethodGet, "/items", "")
	if recorder.Code != http.StatusOK {
		t.Fatalf("GET /items: got status %d, want %d", recorder.Code, http.StatusOK)
	}
	var items []model.Item
	if err := json.NewDecoder(recorder.Body).Decode(&items); err != nil {
		t.Fatalf("decode items: %v", err)
	}
	if len(items) != 2 || items[0].Name != "one" || items[1].Name != "two" {
		t.Fatalf("GET /items: got %+v, want [one two] in id order", items)
	}
}
