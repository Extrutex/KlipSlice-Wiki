# KLIPSLICE

KLIPSLICE is an open-source 3D printing slicer for printers that run
[Klipper](https://www.klipper3d.org/). It is a fork of
[OrcaSlicer](https://github.com/OrcaSlicer/OrcaSlicer) with every path that does
not lead to a Klipper machine removed, and it talks to printers through one
interface only: [Moonraker](https://moonraker.readthedocs.io/).

The source code is public at
[github.com/Extrutex/KlipSlice](https://github.com/Extrutex/KlipSlice).

!!! warning "Pre-alpha"

    There are no releases and no installers yet. CI builds KLIPSLICE for
    Windows, macOS and Linux on every push, but these builds are for testing the
    build itself; to run KLIPSLICE, [build it from source](build.md). Settings,
    profiles and file formats can still change without migration. Do not rely on
    it for prints that matter.

!!! note "Not affiliated with Klipper"

    KLIPSLICE is an independent project and is not affiliated with or
    endorsed by the Klipper project.

## What KLIPSLICE is

Klipper only
:   System printer profiles ship only for printers that verifiably run real
    Klipper: from the factory, through an established community mod, or as a
    self-built machine. The evidence for each model (firmware status, mod
    project, sources) is listed on the [printer page](printers.md), which is
    generated from the profiles and the evidence file together. The G-code
    flavor is locked to `klipper`; older projects and presets with another
    flavor are converted when they load.

Your own printer is first-class
:   Self-built and converted machines work without a system profile: start
    from **Generic Klipper Printer** or use the **Create printer** dialog (see
    [Your own Klipper printer](printers.md#own-printer)).

Moonraker as the only host
:   KLIPSLICE uploads G-code and starts prints through Moonraker's HTTP API. It
    does not ship its own printer protocols, and printers from vendors with their
    own Klipper integration (Creality, Elegoo, Qidi, Snapmaker, Flashforge) are
    connected through Moonraker as well.

No Bambu network, no vendor cloud
:   The Bambu Lab network plugin and vendor cloud services are not part of the
    design. Removing the code inherited from upstream is ongoing work (see the
    status table below).

Side by side with OrcaSlicer
:   KLIPSLICE uses its own application name, binaries and data directory. An
    installed OrcaSlicer is never read from or written to, and settings are not
    migrated between the two.

    | System  | Data directory                           |
    |---------|------------------------------------------|
    | Windows | `%APPDATA%\KLIPSLICE`                    |
    | macOS   | `~/Library/Application Support/KLIPSLICE`|
    | Linux   | `~/.config/KLIPSLICE`                    |

<figure class="ksd-figure">
--8<-- "assets/diagrams/architecture.svg"
<figcaption>KLIPSLICE, Moonraker and Klipper. Solid arrows exist today; dashed arrows are planned for stage 1 (machine sync).</figcaption>
</figure>

[Open the diagram at full size](assets/diagrams/architecture.svg){ .ksd-fullsize }

## Relation to OrcaSlicer

Almost all of the slicing engine, the user interface and the printer profiles come
from OrcaSlicer, created by SoftFever and developed by the OrcaSlicer
contributors. OrcaSlicer itself builds on
[Bambu Studio](https://github.com/bambulab/BambuStudio), which was forked from
[PrusaSlicer](https://github.com/prusa3d/PrusaSlicer), which in turn comes from
[Slic3r](https://github.com/Slic3r/Slic3r) by Alessandro Ranellucci and the RepRap
community. KLIPSLICE would not exist without that work.

KLIPSLICE is licensed under the
[GNU Affero General Public License v3.0](https://www.gnu.org/licenses/agpl-3.0.html),
the same license as OrcaSlicer. Anyone who distributes KLIPSLICE, modified or
not, has to make the corresponding source code available under the same terms.

The current code base is OrcaSlicer `2.5.0-dev`. What KLIPSLICE adds on top is
narrow and deliberate: removing non-Klipper paths, and building features that
only make sense when the slicer can rely on Klipper and Moonraker being on the
other end (see [Vision & roadmap](vision.md)).

## Project status

| Area | State |
|---|---|
| Klipper-only printer profile set, with per-model firmware evidence | Done. See [Supported printers](printers.md). |
| Public source repository | Done: [github.com/Extrutex/KlipSlice](https://github.com/Extrutex/KlipSlice). |
| CI builds for Windows, macOS and Linux | Running on every push. |
| Own identity: binaries, app bundle, data directory, installer IDs | Done. KLIPSLICE installs next to OrcaSlicer without touching it. |
| Removal of the Bambu network plugin and of non-Moonraker print hosts | In progress. Every stored host type is already mapped to Moonraker on load; parts of the inherited code are still in the tree. |
| OrcaSlicer cloud features (login, preset sync) inherited from upstream | Still present. No decision to remove them yet. |
| Releases and installers | None yet (pre-alpha). |
| Machine sync, Klipper print time, adaptive mesh and purge | Planned. See [Vision & roadmap](vision.md). |

## Where to go next

- [Vision & roadmap](vision.md): what KLIPSLICE is trying to do, and what it
  deliberately does not do.
- [Klipper setup](klipper-setup.md): the Klipper and Moonraker configuration
  KLIPSLICE expects, including the `PRINT_START` macro.
- [Building from source](build.md): Windows, macOS and Linux.
- [Contributing](contributing.md): repository layout, commit style and CI gates.
