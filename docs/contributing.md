# Contributing

KLIPSLICE is a community project under the AGPL-3.0. Contributions are welcome:
code, printer profiles, translations, testing on real Klipper machines, and this
wiki. This page covers the source repository; the wiki has its own
[section at the end](#this-wiki).

## Ground rules

- **Klipper only.** A change that only matters for non-Klipper firmware, for a
  vendor cloud or for a print host other than Moonraker does not belong in
  KLIPSLICE.
- **No silent regressions.** Existing `.3mf` projects and printer profiles must
  keep loading. Format or profile changes need migration handling.
- **Cross-platform.** Every change has to build and work on Windows, macOS and
  Linux.
- **Options off means unchanged.** A feature behind an option must not change
  behaviour while the option is off.
- **Reuse before adding.** Add helpers only when existing code cannot reasonably
  be reused.

## Repository layout

| Path | Contents |
|---|---|
| `src/libslic3r/` | Slicing engine: geometry, G-code generation (`GCode/`), infill (`Fill/`), supports (`Support/`), Arachne walls, file formats (`Format/`) |
| `src/libslic3r/PrintConfig.cpp` | Every print, printer and filament setting |
| `src/libslic3r/Print.cpp` | Slicing pipeline |
| `src/slic3r/GUI/` | wxWidgets user interface |
| `src/slic3r/Utils/` | Print host and network code, including the Moonraker host (`Moonraker.cpp`) |
| `src/OrcaSlicer.cpp` | Application entry point (file name kept from upstream) |
| `resources/profiles/` | Printer, process and filament profiles: `<Vendor>.json` plus a `<Vendor>/` directory |
| `localization/i18n/` | Translation catalogs (`<lang>/OrcaSlicer_<lang>.po`, template `OrcaSlicer.pot`) |
| `tests/` | Catch2 test suites |
| `deps/` | Dependency build, done once before the slicer build |
| `scripts/` | Profile tool, test runner, packaging and helper scripts |
| `docs/` | Design documents: `HLSD/` (subsystem designs), `klipslice/` (removal plan), `design/` (brand and design tokens) |
| `.github/workflows/` | CI |

Several internal names still carry the upstream name, among them the
`OrcaSlicer` CMake target, the gettext domain and many source file names. The
CMake target stays so dependency and compiler caches remain valid; the gettext
domain stays so upstream translation catalogs can still be merged. The
user-visible identity (binaries, app bundle, data directory, installer IDs) is
KLIPSLICE.

## Code style

- C++17, selectively C++20. `PascalCase` for classes, `snake_case` for functions
  and variables, `#pragma once` in headers.
- Prefer smart pointers and RAII.
- Parallel code uses TBB; be careful with shared state.
- On top-level windows use `SetSizerAndFit(sizer)` rather than `SetSizer(sizer)`.
- Architectural changes are explained in a code comment and in the pull request.

## Commit messages

Commits use a short area prefix, a colon and an imperative summary in lower case,
followed by a body that explains *why*:

```text
profiles: drop every non-Klipper printer

KLIPSLICE targets Klipper only. Removed vendors without a single Klipper
machine and pruned Marlin/RRF/Repetier machines, their orphaned
process/filament presets and unused assets from mixed vendors.
```

Areas in use include `profiles`, `ci`, `rebrand`, `i18n`, `docs/klipslice` and
`docs/design`. One logical change per commit; a commit that removes files also
removes their CMake entries.

## Printer profiles { #printer-profiles }

Profiles live in `resources/profiles/<Vendor>.json` (the vendor index) and
`resources/profiles/<Vendor>/` (`machine/`, `process/`, `filament/`). For
KLIPSLICE, every printer profile must resolve to `gcode_flavor` = `klipper`.

All profile maintenance goes through one tool:

```bash
python3 scripts/orca_profile_tool.py check
```

`check` validates the whole tree and is what CI runs. After adding, renaming or
deleting profile files, run the tool's commands in this order:

```bash
python3 scripts/orca_profile_tool.py normalize
python3 scripts/orca_profile_tool.py update-index
python3 scripts/orca_profile_tool.py generate-id
python3 scripts/orca_profile_tool.py check
```

`--vendor <Vendor>` limits a command to one vendor and `--dry-run` shows what
would change without writing. `trim` deletes profile files that no vendor index
references; preview it with `--dry-run`, because it can delete new presets that
are not indexed yet.

When you change anything under `resources/profiles/<Vendor>/`, bump `version` in
`resources/profiles/<Vendor>.json`.

## Translations

- Catalogs are `localization/i18n/<lang>/OrcaSlicer_<lang>.po`. The gettext domain
  stays `OrcaSlicer`, independent of the app name, so upstream catalogs can still
  be merged.
- Only edit `msgstr`, never `msgid`. Keep placeholders (`%s`, `%d`, `%1%`), line
  breaks, leading and trailing spaces and HTML tags exactly as in the source
  string, and never reorder positional arguments.
- Keep product names, file formats, G-code commands and macro names untranslated.
- Check a catalog with:

  ```bash
  msgfmt --check-format -o /tmp/check.mo localization/i18n/<lang>/OrcaSlicer_<lang>.po
  ```

## Tests

Tests use Catch2 and live in `tests/`. Pick the suite by the code under test:

| Suite | Covers |
|---|---|
| `libslic3r` | Core library: geometry, meshes, file formats, config and presets |
| `fff_print` | The FFF pipeline from model and config to emitted G-code |
| `sla_print` | SLA support and pad geometry |
| `libnest2d` | 2D nesting and packing |
| `slic3rutils` | Python plugin system and its bindings |
| `filament_group` | Filament-to-extruder grouping |
| `cli` | End-to-end runs of the built binary (Linux only) |

One file per subsystem (`test_<subsystem>.cpp`), listed in the suite's
`CMakeLists.txt` in the same change. Behaviour changes in slicing, profiles,
formats or GUI defaults come with a targeted test or documented verification. How
to build and run the tests is described in
[Building from source](build.md#running-the-tests).

## CI gates

| Workflow | Runs on | Checks |
|---|---|---|
| `build_all.yml` | Push and pull request to `main` that touch source, deps, CMake, resources, localization or tests; manual dispatch | Linux x86_64 build and unit tests. Windows, macOS, Linux arm64 and Flatpak builds run only on manual dispatch. |
| `check_profiles.yml` | Pull request to `main` that touches profiles, `scripts/` or `PrintConfig.cpp` | Profile tool unit tests, `orca_profile_tool.py check`, system profile validation, slicing with expanded custom G-code, custom preset validation |
| `check_locale.yml` | Pull request to `main` that touches `localization/` | Translation catalog format |
| `shellcheck.yml` | Every pull request | ShellCheck on all `*.sh` files and `scripts/linux.d/` |

A pull request is ready when the gates that apply to it are green.

## This wiki { #this-wiki }

The wiki is a separate MkDocs repository. English pages are `<name>.md`, German
pages `<name>.de.md` next to them; both languages are kept complete.

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/mkdocs serve
```

The printer list is generated from a KLIPSLICE checkout and must not be edited by
hand:

```bash
python3 scripts/gen_printers.py --source ../KlipSlice --docs docs
python3 scripts/gen_printers.py --source ../KlipSlice --docs docs --check
```

Diagrams are hand-written SVG in `docs/assets/diagrams/` (one file per language),
using the CSS variables from `docs/stylesheets/extra.css` so they work in the dark
and the light theme. Screenshots are only taken from real builds; see
`docs/assets/screenshots/README.md` for the capture specification. Every change
must pass `mkdocs build --strict`.
