package service

import "example.com/{{project-name}}/internal/model"

// ItemRepository is the storage boundary for items. The service depends
// on this interface only.
type ItemRepository interface {
	Save(name string) model.Item
	FindByID(id int64) (model.Item, bool)
	FindAll() []model.Item
}
