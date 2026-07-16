# Rust Project Guidance

Use idiomatic Cargo project layout with explicit module boundaries. Prefer
the type system and `Result`/`Option` over runtime checks, and keep
`Cargo.toml` as the single source of truth for dependencies.

For this repository:

- Use the standard Cargo layout: `src/main.rs` for a binary crate, `src/lib.rs`
  for a library crate, `src/bin/` for multiple binaries in one package.
- Split modules into files or directories with a `mod.rs` (or the
  `<name>.rs` + `<name>/` sibling-directory style on Rust 2018+); declare
  each with `mod <name>;` in the parent module.
- Prefer `Result<T, E>` with a project-specific error enum over `unwrap()`/
  `expect()` outside of tests and prototypes.
- Keep `Cargo.lock` committed for binaries (reproducible builds); it is
  optional for libraries meant to be consumed by other crates.
- Run `cargo clippy` as part of the normal review loop, not only in CI —
  it catches idiom violations `cargo build` does not.
- Keep async runtimes (e.g. `tokio`) as an explicit dependency choice, not a
  default — plenty of Rust code in this project doesn't need one.

## Common commands

```bash
cargo build
cargo test
cargo clippy
cargo fmt
```
