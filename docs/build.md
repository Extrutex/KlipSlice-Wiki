# Building from source

There are no KLIPSLICE release builds yet, so building from source is currently the
only way to run it. The build scripts are the ones inherited from OrcaSlicer, adapted
for the KLIPSLICE binary names. Every command on this page is taken from those
scripts; run a script with `-h` to see all of its options.

```bash
git clone https://github.com/Extrutex/KlipSlice.git
cd KlipSlice
```

The build happens in two steps on every platform: first the **dependencies**
(`deps/`, built once and reused), then the **slicer** itself. The dependency build
takes a long time and needs several gigabytes of disk space.

## What the build produces

| | Windows | macOS | Linux |
|---|---|---|---|
| Executable | `klipslice.exe` | `KLIPSLICE.app` | `klipslice` |
| Data directory | `%APPDATA%\KLIPSLICE` | `~/Library/Application Support/KLIPSLICE` | `~/.config/KLIPSLICE` |

The data directory is separate from OrcaSlicer's, so a KLIPSLICE build runs next
to an installed OrcaSlicer without reading or changing its settings.

## Build

=== "Windows"

    **Requirements:** Windows with WinGet, Visual Studio 2019, 2022 or 2026 (the
    script detects the installed release), CMake, Perl and Git.

    Install or update CMake, Perl and Git with WinGet, and optionally the Visual
    Studio Build Tools:

    ```bat
    build_win.bat -u
    build_win.bat -u --install-vs buildtools
    ```

    Build the dependencies, then the slicer:

    ```bat
    build_win.bat -d
    build_win.bat -s
    ```

    `-ds` does both in one run. The executable ends up in
    `build\src\Release\klipslice.exe`. With `-i` the build is also installed into
    the build tree, as `build\OrcaSlicer\klipslice.exe`.

    Useful options:

    | Option | Effect |
    |---|---|
    | `--config debug` | Debug build (`release`, `debug`, `relwithdebinfo`, `minsizerel`) |
    | `--arch arm64` | Target architecture `x64` or `arm64` (default: the host) |
    | `-l -x` | clang-cl with the Ninja Multi-Config generator, as CI builds it |
    | `-j N` | Limit the build to N parallel jobs |
    | `--run-tests` | Build the unit tests and run them |
    | `-D` | Dry run: print the commands instead of running them |

=== "macOS"

    **Requirements:** Xcode (the default CMake generator is Xcode), CMake and
    gettext (the build checks the translations with `msgfmt`). The minimum macOS
    version of the build is 12.0 unless set with `-t`. Before building the
    dependencies, the macOS CI job installs automake, texinfo, libtool, pkgconf,
    yasm and nasm with Homebrew (`.github/workflows/build_deps.yml`).

    Build dependencies and slicer for Apple silicon:

    ```bash
    ./build_release_macos.sh -d -a arm64
    ./build_release_macos.sh -s -a arm64
    ```

    Without `-d` or `-s` the script builds both. `-a x86_64` builds for Intel.
    The app bundle ends up in `build/arm64/OrcaSlicer/KLIPSLICE.app`
    (`build/x86_64/…` for Intel); the executable inside it is
    `Contents/MacOS/KLIPSLICE`.

    Useful options:

    | Option | Effect |
    |---|---|
    | `-x` | Ninja Multi-Config generator instead of Xcode, as CI builds it |
    | `-c Debug` | CMake build configuration (default `Release`) |
    | `-b` | Build without reconfiguring CMake |
    | `-j N` | Number of parallel build jobs |
    | `-T` | Build and run the tests |
    | `-u` | Combine existing arm64 and x86_64 builds into a universal app (`-a universal`) |

    After a first full build, an incremental rebuild of an already configured tree
    works directly with CMake:

    ```bash
    cmake --build build/arm64 --config RelWithDebInfo --target all --
    ```

=== "Linux"

    **Requirements:** more than 10 GiB of available memory and more than 10 GiB
    of free disk space (the script checks both; `-r` skips the check for
    low-memory builds).
    The system-dependency step supports the distributions that have a file in
    `scripts/linux.d/` (Arch, CachyOS, Clear Linux, Debian and Debian-like
    distributions such as Ubuntu, Fedora, Gentoo, openSUSE).

    Install the system dependencies (asks for the sudo password), then build the
    dependencies, the slicer and the AppImage:

    ```bash
    ./build_linux.sh -u
    ./build_linux.sh -dsi
    ```

    The executable ends up in `build/package/bin/klipslice`; the AppImage is
    written to `build/KLIPSLICE_Linux_V<version>.AppImage`.

    To build inside a Docker or Podman container based on Ubuntu 24.04, close to
    the GitHub Actions Linux runner:

    ```bash
    ./build_linux.sh -g -istrlL
    ```

    Useful options:

    | Option | Effect |
    |---|---|
    | `-b` / `-e` | Debug / RelWithDebInfo build (default: Release) |
    | `-c` | Force a clean build |
    | `-t` | Build the tests (together with `-s`) |
    | `-l` | Clang instead of GCC |
    | `-L` | Link with ld.lld |
    | `-j N` | Limit the build to N cores |
    | `-D` | Dry run |

## Running the tests

The unit tests use Catch2 and are off by default.

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

All build scripts use multi-configuration generators, so `ctest` always needs `-C`
with the build configuration. Without it, tests lose their labels and report
"Not Run". Single suites can be run on their own, for example
`ctest --test-dir build/tests/libslic3r -C Release`.
