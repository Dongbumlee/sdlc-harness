package service

import "example.com/{{project-name}}/internal/model"

// ItemService is the item operations contract the web layer depends on.
type ItemService interface {
	Create(name string) model.Item
	Get(id int64) (model.Item, bool)
	List() []model.Item
}
