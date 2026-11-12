//! The sample vertical slice: a tiny in-memory items store.
//! Replace with the real data layer; the page, form, and tests
//! around it are the template. Items are the same sample resource
//! the API templates use, here rendered server-side instead of
//! serialized.

use serde::Serialize;

/// One row of the sample slice.
#[derive(Debug, Clone, Serialize)]
pub struct Item {
    pub id: u64,
    pub name: String,
}

/// A concurrency-safe in-memory store: ids from 1, insertion
/// order kept. (The web layer wraps it in a Mutex.)
#[derive(Debug)]
pub struct ItemStore {
    items: Vec<Item>,
    next_id: u64,
}

impl ItemStore {
    /// A store seeded with the two sample items.
    pub fn seeded() -> Self {
        let mut store = ItemStore {
            items: Vec::new(),
            next_id: 1,
        };
        store.add("First item");
        store.add("Second item");
        store
    }

    pub fn list(&self) -> Vec<Item> {
        self.items.clone()
    }

    pub fn add(&mut self, name: &str) -> u64 {
        let id = self.next_id;
        self.next_id += 1;
        self.items.push(Item {
            id,
            name: name.to_string(),
        });
        id
    }
}
