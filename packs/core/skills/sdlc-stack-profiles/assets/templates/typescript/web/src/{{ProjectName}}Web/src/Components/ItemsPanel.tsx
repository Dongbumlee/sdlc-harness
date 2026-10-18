"use client";

import { useState } from "react";

import { Button } from "@/Components/ui/Button";
import { ItemsService, type Item } from "@/Services/ItemsService";

const service = new ItemsService();

export function ItemsPanel() {
  const [items, setItems] = useState<Item[]>([]);
  const [name, setName] = useState("");
  const [error, setError] = useState<string | null>(null);

  const addItem = () => {
    try {
      service.create(name);
      setItems(service.list());
      setName("");
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to add item.");
    }
  };

  return (
    <section className="mx-auto flex w-full max-w-xl flex-col gap-4 p-6">
      <h1 className="text-2xl font-semibold">{{ProjectName}}</h1>
      <div className="flex gap-2">
        <input
          aria-label="Item name"
          className="h-9 flex-1 rounded-md border border-neutral-200 px-3 text-sm"
          value={name}
          onChange={(event) => setName(event.target.value)}
          placeholder="Item name"
        />
        <Button onClick={addItem}>Add item</Button>
      </div>
      {error ? <p className="text-sm text-red-600">{error}</p> : null}
      <ul className="flex flex-col gap-2">
        {items.map((item) => (
          <li
            key={item.id}
            className="rounded-md border border-neutral-200 px-3 py-2 text-sm"
          >
            {item.name}
          </li>
        ))}
      </ul>
    </section>
  );
}
