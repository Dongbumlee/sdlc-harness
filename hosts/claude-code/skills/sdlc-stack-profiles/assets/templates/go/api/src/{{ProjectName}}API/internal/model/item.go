// Package model holds the data types shared by every layer. It depends
// on nothing else in this module.
package model

// Item is an item in the sample vertical slice.
type Item struct {
	ID   int64  `json:"id"`
	Name string `json:"name"`
}

// ItemCreate is the request body for creating an item.
type ItemCreate struct {
	Name string `json:"name"`
}
