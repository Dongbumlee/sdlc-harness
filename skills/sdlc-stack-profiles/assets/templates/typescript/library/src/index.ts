/**
 * {{ProjectName}} public API. This module is the entire published
 * surface: the package `exports` map exposes only this entry point,
 * and the API report in `etc/` is generated from it. If it is not
 * exported here, it is not public.
 */
export { slugify, truncate } from "./text-transforms.js";
