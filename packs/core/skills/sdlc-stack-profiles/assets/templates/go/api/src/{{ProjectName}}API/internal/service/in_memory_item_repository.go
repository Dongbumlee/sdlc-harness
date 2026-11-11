package service

import (
	"sort"
	"sync"
	"sync/atomic"

	"example.com/{{project-name}}/internal/model"
)

// InMemoryItemRepository is the in-memory ItemRepository shipped with
// the template's sample slice.
type InMemoryItemRepository struct {
	mu       sync.RWMutex
	store    map[int64]model.Item
	sequence atomic.Int64
}

// NewInMemoryItemRepository creates an empty in-memory repository.
func NewInMemoryItemRepository() *InMemoryItemRepository {
	return &InMemoryItemRepository{store: make(map[int64]model.Item)}
}

// Save stores a new item with the next sequence id.
func (r *InMemoryItemRepository) Save(name string) model.Item {
	item := model.Item{ID: r.sequence.Add(1), Name: name}
	r.mu.Lock()
	defer r.mu.Unlock()
	r.store[item.ID] = item
	return item
}

// FindByID returns the item with the given id, if one exists.
func (r *InMemoryItemRepository) FindByID(id int64) (model.Item, bool) {
	r.mu.RLock()
	defer r.mu.RUnlock()
	item, ok := r.store[id]
	return item, ok
}

// FindAll returns every item, ordered by id.
func (r *InMemoryItemRepository) FindAll() []model.Item {
	r.mu.RLock()
	defer r.mu.RUnlock()
	items := make([]model.Item, 0, len(r.store))
	for _, item := range r.store {
		items = append(items, item)
	}
	sort.Slice(items, func(i, j int) bool { return items[i].ID < items[j].ID })
	return items
}
