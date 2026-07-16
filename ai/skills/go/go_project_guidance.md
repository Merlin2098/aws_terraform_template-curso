# Go Project Guidance

Use idiomatic Go project layout with explicit package boundaries and small,
testable functions. Keep dependencies declared in `go.mod`/`go.sum` and avoid
introducing a framework where the standard library is enough.

For this repository:

- Declare the module with `go mod init <module-path>`; keep `go.mod`/`go.sum`
  committed and up to date (`go mod tidy` after adding or removing imports).
- Prefer the standard layout: `cmd/<binary>/main.go` for entrypoints,
  `internal/` for code that must not be imported by other modules, `pkg/`
  only for code explicitly meant to be reused externally.
- Keep each package in its own directory — Go treats a directory as the unit
  of a package, not a file.
- Write tests as `<file>_test.go` next to the code they cover; use table-driven
  tests for multiple input/output cases.
- Prefer returning explicit `error` values over panics; only panic for
  programmer errors that should never happen at runtime.
- Keep configuration explicit (flags, environment variables, or a config
  struct loaded at startup) rather than global mutable state.

## Common commands

```bash
go mod tidy
go build ./...
go test ./...
go vet ./...
```
