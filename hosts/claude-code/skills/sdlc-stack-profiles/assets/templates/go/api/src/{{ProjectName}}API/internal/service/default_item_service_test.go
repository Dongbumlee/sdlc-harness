package service_test

import (
	"testing"

	"example.com/{{project-name}}/internal/service"
)

func TestCreateGetList(t *testing.T) {
	items := service.NewDefaultItemService(service.NewInMemoryItemRepository())

	first := items.Create("one")
	second := items.Create("two")
	if first.ID == 0 || second.ID == first.ID {
		t.Fatalf("ids must be assigned and distinct, got %d and %d", first.ID, second.ID)
	}

	fetched, ok := items.Get(first.ID)
	if !ok || fetched != first {
		t.Fatalf("Get(%d): got %+v, %v; want %+v, true", first.ID, fetched, ok, first)
	}

	if _, ok := items.Get(999); ok {
		t.Fatal("Get(999): got ok=true, want false for a missing item")
	}

	list := items.List()
	if len(list) != 2 || list[0] != first || list[1] != second {
		t.Fatalf("List: got %+v, want [%+v %+v] in id order", list, first, second)
	}
}
