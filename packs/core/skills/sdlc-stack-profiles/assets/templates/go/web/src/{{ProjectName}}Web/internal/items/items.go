// Package items is the sample vertical slice: a tiny in-memory
// items store. Replace with the real data layer; the page, form,
// and tests around it are the template. Items are the same sample
// resource the API templates use, here rendered server-side
// instead of serialized.
package items

import "sync"

// Item is one row of the sample slice.
type Item struct {
	ID   int
	Name string
}

// Store is a concurrency-safe in-memory store: ids from 1,
// insertion order kept.
type Store struct {
	mu     sync.Mutex
	items  []Item
	nextID int
}

// NewSeededStore returns a store with the two sample items.
func NewSeededStore() *Store {
	s := &Store{nextID: 1}
	s.Add("First item")
	s.Add("Second item")
	return s
}

// List returns a copy of the items in insertion order.
func (s *Store) List() []Item {
	s.mu.Lock()
	defer s.mu.Unlock()
	out := make([]Item, len(s.items))
	copy(out, s.items)
	return out
}

// Add appends an item and returns its id.
func (s *Store) Add(name string) int {
	s.mu.Lock()
	defer s.mu.Unlock()
	id := s.nextID
	s.nextID++
	s.items = append(s.items, Item{ID: id, Name: name})
	return id
}
