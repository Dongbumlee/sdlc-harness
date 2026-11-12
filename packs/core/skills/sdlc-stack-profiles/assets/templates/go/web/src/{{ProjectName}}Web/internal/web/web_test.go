package web_test

// Page tests for the web template. These pin the web type's
// contract through HTTP, the way the API templates pin theirs:
// the page renders the sample slice, the markup floor holds
// (landmarks, skip link, labelled control), the add-item journey
// works end to end, and a server-only secret never appears in any
// response.

import (
	"io"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"

	"example.com/{{project-name}}/internal/config"
	"example.com/{{project-name}}/internal/items"
	"example.com/{{project-name}}/internal/web"
)

func newTestServer(t *testing.T) *httptest.Server {
	t.Helper()
	app := web.NewServer(items.NewSeededStore(), config.LoadPublic(), config.LoadServer())
	srv := httptest.NewServer(app.Mux())
	t.Cleanup(srv.Close)
	return srv
}

func get(t *testing.T, url string) (int, string) {
	t.Helper()
	resp, err := http.Get(url)
	if err != nil {
		t.Fatal(err)
	}
	defer resp.Body.Close()
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		t.Fatal(err)
	}
	return resp.StatusCode, string(body)
}

func TestIndexRendersItems(t *testing.T) {
	srv := newTestServer(t)
	status, body := get(t, srv.URL+"/")
	if status != http.StatusOK {
		t.Fatalf("GET / = %d, want 200", status)
	}
	for _, want := range []string{"First item", "Second item"} {
		if !strings.Contains(body, want) {
			t.Fatalf("GET / missing %q", want)
		}
	}
}

func TestMarkupFloor(t *testing.T) {
	srv := newTestServer(t)
	_, body := get(t, srv.URL+"/")
	for _, want := range []string{
		`<html lang="en">`, `<main id="main">`, "Skip to main content",
		`<label for="item-name">`, `id="item-name"`,
	} {
		if !strings.Contains(body, want) {
			t.Fatalf("GET / missing markup floor element %q", want)
		}
	}
}

func TestAddItemJourney(t *testing.T) {
	srv := newTestServer(t)
	resp, err := http.PostForm(srv.URL+"/items", map[string][]string{"name": {"Third item"}})
	if err != nil {
		t.Fatal(err)
	}
	defer resp.Body.Close()
	body, _ := io.ReadAll(resp.Body)
	if resp.StatusCode != http.StatusOK || !strings.Contains(string(body), "Third item") {
		t.Fatalf("POST /items journey = %d, body missing new item", resp.StatusCode)
	}
}

func TestHealth(t *testing.T) {
	srv := newTestServer(t)
	status, body := get(t, srv.URL+"/health")
	if status != http.StatusOK || !strings.Contains(body, `"status":"ok"`) {
		t.Fatalf("GET /health = %d %q", status, body)
	}
}

func TestStaticAssetsServed(t *testing.T) {
	srv := newTestServer(t)
	status, body := get(t, srv.URL+"/static/site.css")
	if status != http.StatusOK || !strings.Contains(body, "skip-link") {
		t.Fatalf("GET /static/site.css = %d", status)
	}
}

func TestPublicConfigRenderedAndSecretNeverLeaks(t *testing.T) {
	t.Setenv("SAMPLE_PUBLIC_APP_NAME", "Public Name")
	t.Setenv("SAMPLE_SERVER_API_KEY", "sentinel-secret-12345")
	srv := newTestServer(t)
	_, body := get(t, srv.URL+"/")
	if !strings.Contains(body, "Public Name") {
		t.Fatal("public app name not rendered")
	}
	for _, path := range []string{"/", "/health", "/static/site.css"} {
		_, content := get(t, srv.URL+path)
		if strings.Contains(content, "sentinel-secret-12345") {
			t.Fatalf("server secret leaked in %s", path)
		}
	}
}
