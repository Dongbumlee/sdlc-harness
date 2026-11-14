export interface Item {
  id: number;
  name: string;
  description?: string;
}

/**
 * Sample service slice: an in-memory items store with the same contract
 * shape as the API templates' items endpoints, so the web project can be
 * wired to a real backend by replacing these functions with fetch calls.
 */
export class ItemsService {
  private items: Item[] = [];
  private nextId = 1;

  create(name: string, description?: string): Item {
    if (!name.trim()) {
      throw new Error("Name is required.");
    }
    const item: Item = { id: this.nextId++, name, description };
    this.items.push(item);
    return item;
  }

  get(id: number): Item | undefined {
    return this.items.find((item) => item.id === id);
  }

  list(): Item[] {
    return [...this.items];
  }
}
