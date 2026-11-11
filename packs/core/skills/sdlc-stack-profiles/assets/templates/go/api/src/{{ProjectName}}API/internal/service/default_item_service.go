package service

import "example.com/{{project-name}}/internal/model"

// DefaultItemService is the default ItemService backed by an
// ItemRepository.
type DefaultItemService struct {
	repository ItemRepository
}

// NewDefaultItemService wires the service to its repository.
func NewDefaultItemService(repository ItemRepository) *DefaultItemService {
	return &DefaultItemService{repository: repository}
}

// Create stores a new item.
func (s *DefaultItemService) Create(name string) model.Item {
	return s.repository.Save(name)
}

// Get returns the item with the given id, if one exists.
func (s *DefaultItemService) Get(id int64) (model.Item, bool) {
	return s.repository.FindByID(id)
}

// List returns every item, ordered by id.
func (s *DefaultItemService) List() []model.Item {
	return s.repository.FindAll()
}
