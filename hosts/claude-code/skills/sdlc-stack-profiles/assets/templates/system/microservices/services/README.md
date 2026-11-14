# services/

One directory per service in `system.json`. Each is a complete
service project, instantiated from **that stack's api template**
(this system is stack-agnostic — services may mix stacks; what
they share is the contract machinery, not a runtime):

- `items-api/` — from `assets/templates/<stack>/api`
- `catalog-api/` — from `assets/templates/<stack>/api`

Rules that keep this a system of services rather than a
distributed monolith:

- **Independent deployability.** Each service builds, tests, and
  releases on its own. Its CI calls the system's one reusable
  workflow (`.github/workflows/service-ci.yml` at the system root)
  at a pinned ref — no copied pipeline YAML.
- **Own datastore.** A service's data lives behind its own API;
  the compose file gives each service its own environment, and no
  service connects to another's tables.
- **Uniform entry points.** Each service keeps the entry points
  its template declares (`ci.sh` running install → build → test,
  and `contract.sh` for its consumer/provider contract stage), so
  the shared workflow can drive every stack the same way.
- **Polyrepo is the same shape.** If a service outgrows this
  repository, it moves to its own repo unchanged: it keeps calling
  the same reusable workflow, and this directory keeps a pointer
  in `system.json` (add a `repo` field to its entry).
