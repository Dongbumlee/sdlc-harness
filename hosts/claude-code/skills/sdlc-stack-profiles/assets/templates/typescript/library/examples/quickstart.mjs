// Runnable quickstart — this is the README example, and CI executes
// it against the BUILT package (imported by its own name through
// the `exports` map), so the documented usage can never drift from
// what the package actually ships.
import { slugify, truncate } from "{{project-name}}";

console.log(slugify("Hello, World!"));
console.log(truncate("hello world", 8));
