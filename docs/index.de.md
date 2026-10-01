# KLIPSLICE

KLIPSLICE ist ein quelloffener Slicer für 3D-Drucker, auf denen
[Klipper](https://www.klipper3d.org/) läuft. Er ist ein Fork von
[OrcaSlicer](https://github.com/OrcaSlicer/OrcaSlicer), aus dem alles entfernt
wird, was nicht zu einer Klipper-Maschine führt, und er spricht mit Druckern über
genau eine Schnittstelle: [Moonraker](https://moonraker.readthedocs.io/).

Der Quellcode ist öffentlich unter
[github.com/Extrutex/KlipSlice](https://github.com/Extrutex/KlipSlice).

!!! warning "Pre-Alpha"

    Es gibt noch keine Releases und keine Installer. Die CI baut KLIPSLICE bei
    jedem Push für Windows, macOS und Linux; diese Builds prüfen aber nur den
    Build selbst. Wer KLIPSLICE nutzen will, [baut es aus dem Quellcode](build.md).
    Einstellungen, Profile und Dateiformate können sich noch ohne Migration ändern.
    Für Drucke, auf die es ankommt, ist KLIPSLICE noch nicht geeignet.

!!! note "Keine Verbindung zu Klipper"

    KLIPSLICE ist ein unabhängiges Projekt. Es steht in keiner
    Verbindung zum Klipper-Projekt und wird von diesem weder unterstützt noch
    empfohlen.

## Was KLIPSLICE ist

Nur Klipper
:   Systemprofile gibt es nur für Drucker, die nachweislich echtes Klipper
    ausführen: ab Werk, über einen etablierten Community-Mod oder als Selbstbau.
    Der Nachweis je Modell (Firmware-Status, Mod-Projekt, Quellen) steht auf der
    [Druckerseite](printers.md), die aus Profilen und Nachweisdatei gemeinsam
    erzeugt wird. Der G-Code-Dialekt ist fest auf `klipper` gesetzt; ältere
    Projekte und Presets mit anderem Dialekt werden beim Laden umgestellt.

Eigene Drucker sind vollwertig
:   Selbstbauten und umgebaute Maschinen funktionieren ohne Systemprofil: mit
    **Generic Klipper Printer** als Ausgangspunkt oder über den Dialog
    **Create printer** (siehe
    [Eigener Klipper-Drucker](printers.md#own-printer)).

Moonraker als einziger Host
:   KLIPSLICE lädt G-Code über Moonrakers HTTP-API hoch und startet darüber den
    Druck. Eigene Druckerprotokolle bringt es nicht mit; auch Drucker von
    Herstellern mit eigener Klipper-Anbindung (Creality, Elegoo, Qidi, Snapmaker,
    Flashforge) werden über Moonraker verbunden.

Kein Bambu-Netzwerk, keine Hersteller-Cloud
:   Das Bambu-Lab-Netzwerk-Plugin und Hersteller-Clouds gehören nicht zum
    Konzept. Der von Upstream übernommene Code dafür wird noch entfernt (siehe
    Statustabelle unten).

Parallel zu OrcaSlicer
:   KLIPSLICE hat eigenen Programmnamen, eigene Programmdateien und ein eigenes
    Datenverzeichnis. Ein installiertes OrcaSlicer wird weder gelesen noch
    verändert, und Einstellungen werden zwischen beiden nicht übernommen.

    | System  | Datenverzeichnis                         |
    |---------|------------------------------------------|
    | Windows | `%APPDATA%\KLIPSLICE`                    |
    | macOS   | `~/Library/Application Support/KLIPSLICE`|
    | Linux   | `~/.config/KLIPSLICE`                    |

<figure class="ksd-figure">
--8<-- "assets/diagrams/architecture.de.svg"
<figcaption>KLIPSLICE, Moonraker und Klipper. Durchgezogene Pfeile gibt es heute; gestrichelte sind für Stufe 1 (Maschinen-Sync) geplant.</figcaption>
</figure>

[Diagramm in voller Größe öffnen](assets/diagrams/architecture.svg){ .ksd-fullsize }

## Verhältnis zu OrcaSlicer

Fast die gesamte Slicing-Engine, die Oberfläche und die Druckerprofile stammen aus
OrcaSlicer, begonnen von SoftFever und weiterentwickelt von den
OrcaSlicer-Mitwirkenden. OrcaSlicer baut seinerseits auf
[Bambu Studio](https://github.com/bambulab/BambuStudio) auf, das von
[PrusaSlicer](https://github.com/prusa3d/PrusaSlicer) abgespalten wurde, das
wiederum auf [Slic3r](https://github.com/Slic3r/Slic3r) von Alessandro Ranellucci
und der RepRap-Community zurückgeht. Ohne diese Arbeit gäbe es KLIPSLICE nicht.

KLIPSLICE steht unter der
[GNU Affero General Public License v3.0](https://www.gnu.org/licenses/agpl-3.0.html),
derselben Lizenz wie OrcaSlicer. Wer KLIPSLICE weitergibt, verändert oder
unverändert, muss den zugehörigen Quellcode unter denselben Bedingungen
zugänglich machen.

Die aktuelle Codebasis ist OrcaSlicer `2.5.0-dev`. Was KLIPSLICE hinzufügt, ist
bewusst eng gefasst: Nicht-Klipper-Pfade entfernen und Funktionen bauen, die nur
Sinn ergeben, wenn der Slicer sich darauf verlassen kann, dass am anderen Ende
Klipper und Moonraker laufen (siehe [Vision & Fahrplan](vision.md)).

## Projektstatus { #project-status }

| Bereich | Stand |
|---|---|
| Druckerprofile nur für Klipper, mit Firmware-Nachweis je Modell | Erledigt. Siehe [Unterstützte Drucker](printers.md). |
| Öffentliches Quellrepository | Erledigt: [github.com/Extrutex/KlipSlice](https://github.com/Extrutex/KlipSlice). |
| CI-Builds für Windows, macOS und Linux | Laufen bei jedem Push. |
| Eigene Identität: Programmdateien, App-Bundle, Datenverzeichnis, Installer-IDs | Erledigt. KLIPSLICE lässt sich neben OrcaSlicer installieren, ohne es zu berühren. |
| Entfernen des Bambu-Netzwerk-Plugins und der Nicht-Moonraker-Druck-Hosts | In Arbeit. Jeder gespeicherte Host-Typ wird beim Laden bereits auf Moonraker abgebildet; Teile des übernommenen Codes sind noch im Quellbaum. |
| Von Upstream übernommene OrcaSlicer-Cloud-Funktionen (Anmeldung, Preset-Sync) | Noch vorhanden. Über ihr Entfernen ist noch nicht entschieden. |
| Releases und Installer | Noch keine (Pre-Alpha). |
| Maschinen-Sync, Klipper-Druckzeit, adaptives Mesh und Purge | Geplant. Siehe [Vision & Fahrplan](vision.md). |

## Wie es weitergeht

- [Vision & Fahrplan](vision.md): was KLIPSLICE erreichen will und was es bewusst
  nicht tut.
- [Klipper-Einrichtung](klipper-setup.md): die Klipper- und Moonraker-Konfiguration,
  die KLIPSLICE erwartet, einschließlich des `PRINT_START`-Makros.
- [Aus dem Quellcode bauen](build.md): Windows, macOS und Linux.
- [Mitwirken](contributing.md): Aufbau des Repositorys, Commit-Stil und CI-Prüfungen.
