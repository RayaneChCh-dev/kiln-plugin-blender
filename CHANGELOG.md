# Changelog

## 0.19.1 (2026-11-04)

### Fixed

- Generated files no longer overwrite each other. Two generations that finished in the
  same second with the same prompt opening got the same file name, and the second
  download replaced the first (a paid video was lost, and both tasks pointed at the
  surviving file). Names are now `YYYYMMDD-HHMMSS-mmm-<slug>-<6 hex>.<ext>`
  (milliseconds and a random suffix; date, time and slug still come first, so sorting
  by name still sorts by time), and a download never writes over an existing file: it
  takes `<name>-2`, `-3`… instead, claimed atomically.
- Task ids no longer collide. Two tasks started in the same millisecond shared an id, so
  the MCP `task_status(id)` returned both. Ids are now the millisecond clock plus a
  session counter (e.g. `1a1a3f2742f-7`).
