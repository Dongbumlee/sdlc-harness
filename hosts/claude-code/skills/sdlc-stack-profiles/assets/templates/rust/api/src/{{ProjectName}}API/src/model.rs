//! Data types shared by every layer. This module depends on nothing
//! else in the crate.

use serde::{Deserialize, Serialize};

/// An item in the sample vertical slice.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct Item {
    /// Server-assigned identifier.
    pub id: i64,
    /// Display name of the item.
    pub name: String,
}

/// Request body for creating an item.
#[derive(Debug, Clone, PartialEq, Eq, Deserialize)]
pub struct ItemCreate {
    /// Display name for the new item; must not be blank.
    pub name: String,
}
