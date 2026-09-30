# Mitwirken

KLIPSLICE ist ein Community-Projekt unter der AGPL-3.0. Beiträge sind willkommen:
Code, Druckerprofile, Übersetzungen, Tests an echten Klipper-Maschinen und dieses
Wiki. Diese Seite behandelt das Quell-Repository; zum Wiki selbst gibt es einen
[Abschnitt am Ende](#this-wiki).

## Grundregeln

- **Nur Klipper.** Eine Änderung, die nur für Nicht-Klipper-Firmware, eine
  Hersteller-Cloud oder einen anderen Druck-Host als Moonraker zählt, gehört nicht
  in KLIPSLICE.
- **Keine stillen Regressionen.** Bestehende `.3mf`-Projekte und Druckerprofile
  müssen weiter laden. Format- oder Profiländerungen brauchen eine Migration.
- **Plattformübergreifend.** Jede Änderung muss unter Windows, macOS und Linux
  bauen und funktionieren.
- **Option aus heißt unverändert.** Eine Funktion hinter einer Option darf das
  Verhalten nicht ändern, solange die Option aus ist.
- **Erst wiederverwenden, dann ergänzen.** Neue Hilfsfunktionen nur, wenn sich
  vorhandener Code nicht sinnvoll nutzen lässt.

## Aufbau des Repositorys

| Pfad | Inhalt |
|---|---|
| `src/libslic3r/` | Slicing-Engine: Geometrie, G-Code-Erzeugung (`GCode/`), Füllung (`Fill/`), Stützen (`Support/`), Arachne-Wände, Dateiformate (`Format/`) |
| `src/libslic3r/PrintConfig.cpp` | Alle Druck-, Drucker- und Filamenteinstellungen |
| `src/libslic3r/Print.cpp` | Slicing-Pipeline |
| `src/slic3r/GUI/` | Oberfläche (wxWidgets) |
| `src/slic3r/Utils/` | Druck-Host- und Netzwerkcode, darunter der Moonraker-Host (`Moonraker.cpp`) |
| `src/OrcaSlicer.cpp` | Programmeinstieg (Dateiname von Upstream übernommen) |
| `resources/profiles/` | Drucker-, Prozess- und Filamentprofile: `<Vendor>.json` plus Verzeichnis `<Vendor>/` |
| `localization/i18n/` | Übersetzungskataloge (`<lang>/OrcaSlicer_<lang>.po`, Vorlage `OrcaSlicer.pot`) |
| `tests/` | Catch2-Test-Suites |
| `deps/` | Abhängigkeits-Build, einmal vor dem Slicer-Build |
| `scripts/` | Profil-Werkzeug, Test-Runner, Paketierung und Hilfsskripte |
| `docs/` | Entwurfsdokumente: `HLSD/` (Subsystem-Entwürfe), `klipslice/` (Entfernungsplan), `design/` (Marke und Design-Tokens) |
| `.github/workflows/` | CI |

Einige interne Namen tragen weiterhin den Upstream-Namen, darunter das
CMake-Target `OrcaSlicer`, die gettext-Domäne und viele Quelldateinamen. Das
CMake-Target bleibt, damit Abhängigkeits- und Compiler-Caches gültig bleiben; die
gettext-Domäne bleibt, damit sich Übersetzungskataloge von Upstream weiter
übernehmen lassen. Die sichtbare Identität (Programmdateien, App-Bundle,
Datenverzeichnis, Installer-IDs) ist KLIPSLICE.

## Code-Stil

- C++17, punktuell C++20. `PascalCase` für Klassen, `snake_case` für Funktionen
  und Variablen, `#pragma once` in Headern.
- Smart Pointer und RAII bevorzugen.
- Paralleler Code nutzt TBB; Vorsicht bei gemeinsam genutztem Zustand.
- Auf Top-Level-Fenstern `SetSizerAndFit(sizer)` statt `SetSizer(sizer)` verwenden.
- Architekturänderungen werden im Code-Kommentar und im Pull Request begründet.

## Commit-Nachrichten

Commits (auf Englisch) beginnen mit einem kurzen Bereichspräfix, einem Doppelpunkt
und einer Zusammenfassung im Imperativ in Kleinschreibung; der Text darunter
erklärt das *Warum*:

```text
profiles: drop every non-Klipper printer

KLIPSLICE targets Klipper only. Removed vendors without a single Klipper
machine and pruned Marlin/RRF/Repetier machines, their orphaned
process/filament presets and unused assets from mixed vendors.
```

Verwendete Bereiche sind unter anderem `profiles`, `ci`, `rebrand`, `i18n`,
`docs/klipslice` und `docs/design`. Eine logische Änderung pro Commit; ein Commit,
der Dateien entfernt, entfernt auch ihre CMake-Einträge.

## Druckerprofile { #printer-profiles }

Profile liegen in `resources/profiles/<Vendor>.json` (dem Hersteller-Index) und
`resources/profiles/<Vendor>/` (`machine/`, `process/`, `filament/`). Für KLIPSLICE
muss jedes Druckerprofil bei `gcode_flavor` = `klipper` landen.

Die gesamte Profilpflege läuft über ein Werkzeug:

```bash
python3 scripts/orca_profile_tool.py check
```

`check` prüft den ganzen Baum und ist das, was die CI ausführt. Nach dem Anlegen,
Umbenennen oder Löschen von Profildateien die Befehle in dieser Reihenfolge
ausführen:

```bash
python3 scripts/orca_profile_tool.py normalize
python3 scripts/orca_profile_tool.py update-index
python3 scripts/orca_profile_tool.py generate-id
python3 scripts/orca_profile_tool.py check
```

`--vendor <Vendor>` beschränkt einen Befehl auf einen Hersteller, `--dry-run` zeigt
Änderungen, ohne zu schreiben. `trim` löscht Profildateien, auf die kein
Hersteller-Index verweist; vorher mit `--dry-run` prüfen, weil es neue, noch nicht
indizierte Profile löschen kann.

Wer etwas unter `resources/profiles/<Vendor>/` ändert, erhöht `version` in
`resources/profiles/<Vendor>.json`.

## Übersetzungen

- Die Kataloge sind `localization/i18n/<lang>/OrcaSlicer_<lang>.po`. Die
  gettext-Domäne bleibt `OrcaSlicer`, unabhängig vom Programmnamen, damit sich
  Kataloge von Upstream weiter übernehmen lassen.
- Nur `msgstr` bearbeiten, nie `msgid`. Platzhalter (`%s`, `%d`, `%1%`),
  Zeilenumbrüche, führende und abschließende Leerzeichen und HTML-Tags exakt wie im
  Ausgangstext übernehmen und Positionsargumente nie umstellen.
- Produktnamen, Dateiformate, G-Code-Befehle und Makronamen nicht übersetzen.
- Einen Katalog prüfen mit:

  ```bash
  msgfmt --check-format -o /tmp/check.mo localization/i18n/<lang>/OrcaSlicer_<lang>.po
  ```

## Tests

Die Tests verwenden Catch2 und liegen in `tests/`. Die Suite richtet sich nach dem
getesteten Code:

| Suite | Deckt ab |
|---|---|
| `libslic3r` | Kernbibliothek: Geometrie, Meshes, Dateiformate, Konfiguration und Presets |
| `fff_print` | Die FFF-Pipeline vom Modell und der Konfiguration bis zum erzeugten G-Code |
| `sla_print` | SLA-Stützen- und Sockelgeometrie |
| `libnest2d` | 2D-Anordnung und Packen |
| `slic3rutils` | Python-Plugin-System und seine Bindings |
| `filament_group` | Zuordnung von Filamenten zu Extrudern |
| `cli` | Ende-zu-Ende-Läufe des gebauten Programms (nur Linux) |

Eine Datei pro Subsystem (`test_<subsystem>.cpp`), in derselben Änderung in der
`CMakeLists.txt` der Suite eingetragen. Verhaltensänderungen beim Slicen, an
Profilen, Formaten oder GUI-Standardwerten kommen mit einem gezielten Test oder
einer dokumentierten Prüfung. Wie man die Tests baut und ausführt, steht unter
[Aus dem Quellcode bauen](build.md#running-the-tests).

## CI-Prüfungen

| Workflow | Läuft bei | Prüft |
|---|---|---|
| `build_all.yml` | Push und Pull Request auf `main`, die Quellcode, Abhängigkeiten, CMake, Ressourcen, Übersetzungen oder Tests berühren; manueller Start | Linux-x86_64-Build und Unit-Tests. Builds für Windows, macOS, Linux arm64 und Flatpak laufen nur bei manuellem Start. |
| `check_profiles.yml` | Pull Request auf `main`, der Profile, `scripts/` oder `PrintConfig.cpp` berührt | Unit-Tests des Profil-Werkzeugs, `orca_profile_tool.py check`, Prüfung der Systemprofile, Slicen mit expandiertem Custom-G-Code, Prüfung benutzerdefinierter Presets |
| `check_locale.yml` | Pull Request auf `main`, der `localization/` berührt | Format der Übersetzungskataloge |
| `shellcheck.yml` | Jeder Pull Request | ShellCheck auf alle `*.sh`-Dateien und `scripts/linux.d/` |

Ein Pull Request ist fertig, wenn die für ihn zutreffenden Prüfungen grün sind.

## Dieses Wiki { #this-wiki }

Das Wiki ist ein eigenes MkDocs-Repository. Englische Seiten heißen `<name>.md`,
deutsche `<name>.de.md` daneben; beide Sprachen werden vollständig gepflegt.

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/mkdocs serve
```

Die Druckerliste wird aus einem KLIPSLICE-Checkout erzeugt und darf nicht von Hand
bearbeitet werden:

```bash
python3 scripts/gen_printers.py --source ../KlipSlice --docs docs
python3 scripts/gen_printers.py --source ../KlipSlice --docs docs --check
```

Diagramme sind handgeschriebene SVG-Dateien in `docs/assets/diagrams/` (eine Datei
pro Sprache). Sie nutzen die CSS-Variablen aus `docs/stylesheets/extra.css` und
funktionieren so im dunklen wie im hellen Theme. Screenshots stammen nur aus
echten Builds; die Aufnahmevorgaben stehen in `docs/assets/screenshots/README.md`.
Jede Änderung muss `mkdocs build --strict` bestehen.
