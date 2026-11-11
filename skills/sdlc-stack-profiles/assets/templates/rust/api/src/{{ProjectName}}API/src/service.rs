//! Item services and their storage boundary. The web layer depends on
//! the traits declared here; implementations are wired in `main.rs`.

use std::collections::HashMap;
use std::sync::RwLock;
use std::sync::atomic::{AtomicI64, Ordering};

use crate::model::Item;

/// Storage boundary for items. The service depends on this trait only.
pub trait ItemRepository: Send + Sync {
    /// Stores a new item with the next sequence id.
    fn save(&self, name: &str) -> Item;
    /// Returns the item with the given id, if one exists.
    fn find_by_id(&self, id: i64) -> Option<Item>;
    /// Returns every item, ordered by id.
    fn find_all(&self) -> Vec<Item>;
}

/// In-memory [`ItemRepository`] shipped with the template's sample
/// slice.
pub struct InMemoryItemRepository {
    store: RwLock<HashMap<i64, Item>>,
    sequence: AtomicI64,
}

impl InMemoryItemRepository {
    /// Creates an empty in-memory repository.
    pub fn new() -> Self {
        Self {
            store: RwLock::new(HashMap::new()),
            sequence: AtomicI64::new(0),
        }
    }
}

impl Default for InMemoryItemRepository {
    fn default() -> Self {
        Self::new()
    }
}

impl ItemRepository for InMemoryItemRepository {
    fn save(&self, name: &str) -> Item {
        let item = Item {
            id: self.sequence.fetch_add(1, Ordering::SeqCst) + 1,
            name: name.to_owned(),
        };
        self.store
            .write()
            .expect("item store lock poisoned")
            .insert(item.id, item.clone());
        item
    }

    fn find_by_id(&self, id: i64) -> Option<Item> {
        self.store
            .read()
            .expect("item store lock poisoned")
            .get(&id)
            .cloned()
    }

    fn find_all(&self) -> Vec<Item> {
        let mut items: Vec<Item> = self
            .store
            .read()
            .expect("item store lock poisoned")
            .values()
            .cloned()
            .collect();
        items.sort_by_key(|item| item.id);
        items
    }
}

/// Item operations the web layer depends on.
pub trait ItemService: Send + Sync {
    /// Creates an item with the given name.
    fn create(&self, name: &str) -> Item;
    /// Returns the item with the given id, if one exists.
    fn get(&self, id: i64) -> Option<Item>;
    /// Returns every item, ordered by id.
    fn list(&self) -> Vec<Item>;
}

/// Default [`ItemService`] backed by an [`ItemRepository`].
pub struct DefaultItemService {
    repository: std::sync::Arc<dyn ItemRepository>,
}

impl DefaultItemService {
    /// Wires the service to its repository.
    pub fn new(repository: std::sync::Arc<dyn ItemRepository>) -> Self {
        Self { repository }
    }
}

impl ItemService for DefaultItemService {
    fn create(&self, name: &str) -> Item {
        self.repository.save(name)
    }

    fn get(&self, id: i64) -> Option<Item> {
        self.repository.find_by_id(id)
    }

    fn list(&self) -> Vec<Item> {
        self.repository.find_all()
    }
}
