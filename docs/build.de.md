# Aus dem Quellcode bauen

Es gibt noch keine Release-Builds von KLIPSLICE; selbst bauen ist derzeit der
einzige Weg, es zu nutzen. Die Build-Skripte stammen aus OrcaSlicer und sind an
die KLIPSLICE-Programmnamen angepasst. Jeder Befehl auf dieser Seite stammt aus
diesen Skripten; mit `-h` zeigt jedes Skript alle Optionen an.

```bash
git clone https://github.com/Extrutex/KlipSlice.git
cd KlipSlice
```

Auf allen Plattformen läuft der Build in zwei Schritten: zuerst die
**Abhängigkeiten** (`deps/`, einmal gebaut und wiederverwendet), dann der
**Slicer** selbst. Der Abhängigkeits-Build dauert lange und braucht mehrere
Gigabyte Speicherplatz.

## Was der Build erzeugt

| | Windows | macOS | Linux |
|---|---|---|---|
| Programm | `klipslice.exe` | `KLIPSLICE.app` | `klipslice` |
| Datenverzeichnis | `%APPDATA%\KLIPSLICE` | `~/Library/Application Support/KLIPSLICE` | `~/.config/KLIPSLICE` |

Das Datenverzeichnis ist von dem von OrcaSlicer getrennt; ein KLIPSLICE-Build läuft
also neben einem installierten OrcaSlicer, ohne dessen Einstellungen zu lesen oder
zu ändern.

## Bauen

=== "Windows"

    **Voraussetzungen:** Windows mit WinGet, Visual Studio 2019, 2022 oder 2026
    (das Skript erkennt die installierte Version), CMake, Perl und Git.

    CMake, Perl und Git mit WinGet installieren oder aktualisieren, optional
    zusätzlich die Visual Studio Build Tools:

    ```bat
    build_win.bat -u
    build_win.bat -u --install-vs buildtools
    ```

    Erst die Abhängigkeiten, dann den Slicer bauen:

    ```bat
    build_win.bat -d
    build_win.bat -s
    ```

    `-ds` erledigt beides in einem Lauf. Das Programm liegt danach unter
    `build\src\Release\klipslice.exe`. Mit `-i` wird der Build zusätzlich in den
    Build-Baum installiert, als `build\OrcaSlicer\klipslice.exe`.

    Nützliche Optionen:

    | Option | Wirkung |
    |---|---|
    | `--config debug` | Debug-Build (`release`, `debug`, `relwithdebinfo`, `minsizerel`) |
    | `--arch arm64` | Zielarchitektur `x64` oder `arm64` (Standard: die des Rechners) |
    | `-l -x` | clang-cl mit dem Generator Ninja Multi-Config, wie in der CI |
    | `-j N` | Build auf N parallele Jobs begrenzen |
    | `--run-tests` | Unit-Tests bauen und ausführen |
    | `-D` | Probelauf: Befehle anzeigen statt ausführen |

=== "macOS"

    **Voraussetzungen:** Xcode (der Standard-Generator für CMake ist Xcode), CMake
    und gettext (der Build prüft die Übersetzungen mit `msgfmt`). Die minimale
    macOS-Version des Builds ist 12.0, sofern nicht mit `-t` anders gesetzt. Vor dem
    Abhängigkeits-Build installiert der macOS-CI-Job automake, texinfo, libtool,
    pkgconf, yasm und nasm per Homebrew (`.github/workflows/build_deps.yml`).

    Abhängigkeiten und Slicer für Apple Silicon bauen:

    ```bash
    ./build_release_macos.sh -d -a arm64
    ./build_release_macos.sh -s -a arm64
    ```

    Ohne `-d` oder `-s` baut das Skript beides. `-a x86_64` baut für Intel. Das
    App-Bundle liegt danach unter `build/arm64/OrcaSlicer/KLIPSLICE.app`
    (`build/x86_64/…` für Intel); das Programm darin ist
    `Contents/MacOS/KLIPSLICE`.

    Nützliche Optionen:

    | Option | Wirkung |
    |---|---|
    | `-x` | Generator Ninja Multi-Config statt Xcode, wie in der CI |
    | `-c Debug` | CMake-Build-Konfiguration (Standard `Release`) |
    | `-b` | Bauen, ohne CMake neu zu konfigurieren |
    | `-j N` | Anzahl paralleler Build-Jobs |
    | `-T` | Tests bauen und ausführen |
    | `-u` | Vorhandene arm64- und x86_64-Builds zu einer Universal-App zusammenführen (`-a universal`) |

    Nach einem ersten vollständigen Build geht ein inkrementeller Neubau eines
    bereits konfigurierten Baums direkt mit CMake:

    ```bash
    cmake --build build/arm64 --config RelWithDebInfo --target all --
    ```

=== "Linux"

    **Voraussetzungen:** mehr als 10 GiB verfügbarer Arbeitsspeicher und mehr als
    10 GiB freier Speicherplatz (das Skript prüft beides; `-r` überspringt die
    Prüfung für Builds mit wenig Arbeitsspeicher). Der Schritt für die
    Systemabhängigkeiten unterstützt die Distributionen mit einer Datei in
    `scripts/linux.d/` (Arch, CachyOS, Clear Linux, Debian und Debian-artige
    Distributionen wie Ubuntu, Fedora, Gentoo, openSUSE).

    Systemabhängigkeiten installieren (fragt nach dem sudo-Passwort), dann
    Abhängigkeiten, Slicer und AppImage bauen:

    ```bash
    ./build_linux.sh -u
    ./build_linux.sh -dsi
    ```

    Das Programm liegt danach unter `build/package/bin/klipslice`; das AppImage
    wird als `build/KLIPSLICE_Linux_V<version>.AppImage` geschrieben.

    Bauen in einem Docker- oder Podman-Container auf Basis von Ubuntu 24.04, nah am
    Linux-Runner von GitHub Actions:

    ```bash
    ./build_linux.sh -g -istrlL
    ```

    Nützliche Optionen:

    | Option | Wirkung |
    |---|---|
    | `-b` / `-e` | Debug- / RelWithDebInfo-Build (Standard: Release) |
    | `-c` | Sauberen Neubau erzwingen |
    | `-t` | Tests bauen (zusammen mit `-s`) |
    | `-l` | Clang statt GCC |
    | `-L` | Mit ld.lld linken |
    | `-j N` | Build auf N Kerne begrenzen |
    | `-D` | Probelauf |

## Tests ausführen { #running-the-tests }

Die Unit-Tests verwenden Catch2 und sind standardmäßig abgeschaltet.

=== "Windows"

    ```bat
    build_win.bat -ds --run-tests
    ```

=== "macOS"

    ```bash
    ./build_release_macos.sh -s -a arm64 -T
    ```

=== "Linux"

    ```bash
    ./build_linux.sh -st
    ctest --test-dir build/tests -C Release
    ```

Alle Build-Skripte nutzen Generatoren mit mehreren Konfigurationen, deshalb braucht
`ctest` immer `-C` mit der Build-Konfiguration. Ohne verlieren Tests ihre Labels
und melden „Not Run“. Einzelne Suites lassen sich separat ausführen, zum Beispiel
`ctest --test-dir build/tests/libslic3r -C Release`.
