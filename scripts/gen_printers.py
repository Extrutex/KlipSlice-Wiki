#!/usr/bin/env python3
"""Generate the "Supported printers" pages from a KLIPSLICE source checkout.

Reads resources/profiles/<Vendor>.json and the machine presets they index,
resolves every instantiable printer preset through its `inherits` chain and
writes one Markdown page per wiki language (docs/printers.md and
docs/printers.de.md).

Every instantiable preset must resolve to gcode_flavor = klipper. Anything
else is a data error in the source tree and aborts the run: the page must
never list a printer KLIPSLICE does not target.

Usage:
    python3 scripts/gen_printers.py --source /path/to/KLIPSLICE --docs docs
    python3 scripts/gen_printers.py --source /path/to/KLIPSLICE --docs docs --check

--check writes nothing and exits 1 if the committed pages differ from what the
source tree generates.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

# Vendor bundles that are libraries or control files, not printer vendors.
NON_VENDOR_BUNDLES = frozenset({"OrcaFilamentLibrary", "blacklist"})

# Maximum inheritance depth before a chain is treated as a cycle.
MAX_INHERIT_DEPTH = 32

TEXT = {
    "en": {
        "title": "Supported printers",
        "intro": (
            "This list is generated from the printer profiles in the KLIPSLICE "
            "source tree (`resources/profiles/`) by `scripts/gen_printers.py`. "
            "Do not edit it by hand; regenerate it instead."
        ),
        "klipper_only": (
            "Every printer listed here runs Klipper. The generator resolves each "
            "printer preset through its inheritance chain and refuses to write the "
            "page if any preset ends up with a G-code flavor other than `klipper`."
        ),
        "moonraker_title": "Connection",
        "moonraker": (
            "KLIPSLICE uses Moonraker as its only print host. This includes the "
            "Klipper-based models from Creality, Elegoo, Qidi, Snapmaker and "
            "Flashforge: they connect through Moonraker, not through a vendor "
            "cloud or vendor-specific protocol. Some profile files inherited from "
            "OrcaSlicer still name their upstream host type; KLIPSLICE maps every "
            "host type to Moonraker when it loads a profile or project."
        ),
        "missing_title": "Printer not listed?",
        "missing": (
            "Any Klipper printer works with the generic profile "
            "(**Generic Klipper Printer**, vendor *Custom Printer*). See "
            "[Contributing](contributing.md#printer-profiles) for adding a profile."
        ),
        "summary_title": "Summary",
        "vendors": "Vendors",
        "models": "Printer models",
        "presets": "Printer presets (model × nozzle)",
        "vendor_col": "Vendor",
        "model_col": "Model",
        "nozzle_col": "Nozzle sizes (mm)",
        "count_col": "Models",
        "generated_from": "Generated from source commit",
    },
    "de": {
        "title": "Unterstützte Drucker",
        "intro": (
            "Diese Liste wird von `scripts/gen_printers.py` aus den Druckerprofilen "
            "im KLIPSLICE-Quellbaum (`resources/profiles/`) erzeugt. Nicht von Hand "
            "bearbeiten, sondern neu generieren."
        ),
        "klipper_only": (
            "Jeder hier aufgeführte Drucker läuft mit Klipper. Der Generator löst "
            "jedes Druckerprofil über seine Vererbungskette auf und bricht ab, "
            "sobald ein Profil bei einem anderen G-Code-Dialekt als `klipper` landet."
        ),
        "moonraker_title": "Verbindung",
        "moonraker": (
            "KLIPSLICE nutzt Moonraker als einzigen Druck-Host. Das gilt auch für "
            "die Klipper-Modelle von Creality, Elegoo, Qidi, Snapmaker und "
            "Flashforge: Sie werden über Moonraker angebunden, nicht über eine "
            "Hersteller-Cloud oder ein herstellereigenes Protokoll. Einige aus "
            "OrcaSlicer übernommene Profildateien nennen noch ihren ursprünglichen "
            "Host-Typ; KLIPSLICE bildet beim Laden eines Profils oder Projekts "
            "jeden Host-Typ auf Moonraker ab."
        ),
        "missing_title": "Drucker fehlt?",
        "missing": (
            "Jeder Klipper-Drucker funktioniert mit dem generischen Profil "
            "(**Generic Klipper Printer**, Hersteller *Custom Printer*). Wie man ein Profil ergänzt, "
            "steht unter [Mitwirken](contributing.md#printer-profiles)."
        ),
        "summary_title": "Übersicht",
        "vendors": "Hersteller",
        "models": "Druckermodelle",
        "presets": "Druckerprofile (Modell × Düse)",
        "vendor_col": "Hersteller",
        "model_col": "Modell",
        "nozzle_col": "Düsengrößen (mm)",
        "count_col": "Modelle",
        "generated_from": "Erzeugt aus Quell-Commit",
    },
}

OUTPUT_NAMES = {"en": "printers.md", "de": "printers.de.md"}


class ProfileError(Exception):
    """Raised when the profile tree is inconsistent."""


@dataclass
class Model:
    name: str
    nozzles: set[str] = field(default_factory=set)
    presets: int = 0


@dataclass
class Vendor:
    name: str
    models: list[Model]


def load_json(path: Path) -> dict:
    try:
        with path.open(encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise ProfileError(f"cannot read {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ProfileError(f"{path}: top level is not a JSON object")
    return data


def resolve(name: str, presets: dict[str, dict], key: str, vendor: str):
    """Return `key` for preset `name`, following `inherits` until it is set."""
    current = name
    for _ in range(MAX_INHERIT_DEPTH):
        preset = presets.get(current)
        if preset is None:
            raise ProfileError(f"{vendor}: preset '{current}' (reached from '{name}') is not indexed")
        if key in preset:
            return preset[key]
        parent = preset.get("inherits", "")
        if not parent:
            return None
        current = parent
    raise ProfileError(f"{vendor}: inheritance of '{name}' exceeds {MAX_INHERIT_DEPTH} levels (cycle?)")


def nozzle_values(raw) -> list[str]:
    if raw is None:
        return []
    items = raw if isinstance(raw, list) else str(raw).split(";")
    return [str(item).strip() for item in items if str(item).strip()]


def nozzle_sort_key(value: str) -> float:
    try:
        return float(value)
    except ValueError as exc:
        raise ProfileError(f"nozzle diameter '{value}' is not a number") from exc


def read_vendor(bundle: Path) -> Vendor | None:
    index = load_json(bundle)
    model_entries = index.get("machine_model_list") or []
    if not model_entries:
        return None
    vendor_name = str(index.get("name") or bundle.stem)
    vendor_dir = bundle.parent / bundle.stem

    presets: dict[str, dict] = {}
    for entry in index.get("machine_list") or []:
        sub_path = entry.get("sub_path")
        if not sub_path:
            raise ProfileError(f"{vendor_name}: machine_list entry without sub_path: {entry}")
        data = load_json(vendor_dir / sub_path)
        preset_name = data.get("name")
        if not preset_name:
            raise ProfileError(f"{vendor_name}: {sub_path} has no 'name'")
        presets[preset_name] = data

    models = {str(entry["name"]): Model(str(entry["name"])) for entry in model_entries if entry.get("name")}

    for preset_name, data in presets.items():
        if str(data.get("instantiation", "")).lower() != "true":
            continue
        flavor = resolve(preset_name, presets, "gcode_flavor", vendor_name)
        if flavor != "klipper":
            raise ProfileError(
                f"{vendor_name}: printer preset '{preset_name}' resolves to gcode_flavor={flavor!r}, not 'klipper'"
            )
        model_name = resolve(preset_name, presets, "printer_model", vendor_name)
        if not model_name:
            raise ProfileError(f"{vendor_name}: printer preset '{preset_name}' has no printer_model")
        model = models.get(str(model_name))
        if model is None:
            raise ProfileError(
                f"{vendor_name}: printer preset '{preset_name}' names model '{model_name}', "
                "which is not in machine_model_list"
            )
        model.presets += 1
        model.nozzles.update(nozzle_values(resolve(preset_name, presets, "nozzle_diameter", vendor_name)))

    listed = [model for model in models.values() if model.presets > 0]
    if not listed:
        return None
    listed.sort(key=lambda m: m.name.casefold())
    return Vendor(vendor_name, listed)


def collect(source: Path) -> list[Vendor]:
    profiles = source / "resources" / "profiles"
    if not profiles.is_dir():
        raise ProfileError(f"{profiles} does not exist; --source must point at a KLIPSLICE checkout")
    vendors = []
    for bundle in sorted(profiles.glob("*.json"), key=lambda p: p.stem.casefold()):
        if bundle.stem in NON_VENDOR_BUNDLES:
            continue
        vendor = read_vendor(bundle)
        if vendor is not None:
            vendors.append(vendor)
    if not vendors:
        raise ProfileError(f"no printer vendors found under {profiles}")
    return vendors


def anchor(name: str) -> str:
    slug = "".join(ch if ch.isalnum() else "-" for ch in name.casefold())
    while "--" in slug:
        slug = slug.replace("--", "-")
    return "vendor-" + slug.strip("-")


def cell(text: str) -> str:
    return text.replace("|", "\\|")


def render(vendors: list[Vendor], lang: str, commit: str) -> str:
    t = TEXT[lang]
    model_total = sum(len(v.models) for v in vendors)
    preset_total = sum(m.presets for v in vendors for m in v.models)
    lines = [
        "<!-- Generated by scripts/gen_printers.py. Do not edit by hand. -->",
        "",
        f"# {t['title']}",
        "",
        t["intro"],
        "",
        f"!!! info \"{t['moonraker_title']}\"",
        "",
        f"    {t['moonraker']}",
        "",
        t["klipper_only"],
        "",
        f"## {t['summary_title']}",
        "",
        f"| {t['vendors']} | {t['models']} | {t['presets']} |",
        "|---:|---:|---:|",
        f"| {len(vendors)} | {model_total} | {preset_total} |",
        "",
        f"| {t['vendor_col']} | {t['count_col']} |",
        "|---|---:|",
    ]
    for vendor in vendors:
        lines.append(f"| [{cell(vendor.name)}](#{anchor(vendor.name)}) | {len(vendor.models)} |")
    lines.append("")
    for vendor in vendors:
        lines += [
            f"## {vendor.name} {{ #{anchor(vendor.name)} }}",
            "",
            f"| {t['model_col']} | {t['nozzle_col']} |",
            "|---|---|",
        ]
        for model in vendor.models:
            nozzles = ", ".join(sorted(model.nozzles, key=nozzle_sort_key))
            lines.append(f"| {cell(model.name)} | {nozzles} |")
        lines.append("")
    lines += [
        f"!!! question \"{t['missing_title']}\"",
        "",
        f"    {t['missing']}",
        "",
        f"<small>{t['generated_from']} `{commit}`.</small>",
        "",
    ]
    return "\n".join(lines)


def source_commit(source: Path) -> str:
    head = source / ".git"
    # Resolve HEAD without invoking git so the script has no external tool dependency.
    if head.is_file():
        gitdir_line = head.read_text(encoding="utf-8").strip()
        if not gitdir_line.startswith("gitdir:"):
            raise ProfileError(f"{head}: unexpected .git file format")
        head = (source / gitdir_line.split(":", 1)[1].strip()).resolve()
    head_file = head / "HEAD"
    if not head_file.is_file():
        raise ProfileError(f"{source} is not a git checkout (no {head_file})")
    ref = head_file.read_text(encoding="utf-8").strip()
    if not ref.startswith("ref:"):
        return ref[:10]
    ref_name = ref.split(":", 1)[1].strip()
    ref_path = head / ref_name
    if ref_path.is_file():
        return ref_path.read_text(encoding="utf-8").strip()[:10]
    packed = head / "packed-refs"
    if packed.is_file():
        for line in packed.read_text(encoding="utf-8").splitlines():
            parts = line.split()
            if len(parts) == 2 and parts[1] == ref_name:
                return parts[0][:10]
    raise ProfileError(f"cannot resolve {ref_name} in {head}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--source", required=True, type=Path, help="path to a KLIPSLICE source checkout")
    parser.add_argument("--docs", required=True, type=Path, help="wiki docs directory to write into")
    parser.add_argument("--check", action="store_true", help="compare only, write nothing; exit 1 on difference")
    args = parser.parse_args()

    if not args.docs.is_dir():
        print(f"error: {args.docs} is not a directory", file=sys.stderr)
        return 2
    try:
        vendors = collect(args.source)
        commit = source_commit(args.source)
    except ProfileError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    stale = []
    for lang, filename in OUTPUT_NAMES.items():
        target = args.docs / filename
        content = render(vendors, lang, commit)
        if args.check:
            current = target.read_text(encoding="utf-8") if target.is_file() else None
            if current != content:
                stale.append(str(target))
        else:
            target.write_text(content, encoding="utf-8")
            print(f"wrote {target}")
    if stale:
        print("out of date: " + ", ".join(stale), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
