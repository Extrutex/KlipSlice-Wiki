# Vision & roadmap

A general-purpose slicer has to assume very little about the printer on the other
end. KLIPSLICE can assume a lot: the printer runs Klipper, Moonraker is reachable,
and Klipper publishes its own configuration. The roadmap is about using that.

The guiding rule: **the slicer should know the machine's real limits and never let
a value exceed them silently.** This matters on Klipper in particular, because
Klipper does not cap motion commands at the values in `printer.cfg`. Since the
[2021-04-30 change](https://www.klipper3d.org/Config_Changes.html),
`SET_VELOCITY_LIMIT` and `M204` may set velocity, acceleration and square corner
velocity *above* the configured values, and Klipper executes them. Whatever the
slicer writes is what the machine does.

<figure class="ksd-figure">
--8<-- "assets/diagrams/roadmap.svg"
<figcaption>Roadmap stages. Stage 0 is in progress, stages 1–3 are planned, stage 4 is a vision without a design.</figcaption>
</figure>

[Open the diagram at full size](assets/diagrams/roadmap.svg){ .ksd-fullsize }

## Stage 0: Foundation (in progress)

Before any new feature, the fork has to become a clean Klipper-only slicer:
Klipper-only printer profiles, its own identity next to OrcaSlicer, and removal
of print hosts and network code that do not lead to Moonraker. The
[home page](index.md#project-status) lists what is done and what is still open.

## Stage 1: Machine sync

Today the motion limits KLIPSLICE plans against are values typed into the printer
profile. They are copied from a spec sheet or guessed, and they drift away from the
real machine the first time someone edits `printer.cfg`. Stage 1 reads the limits
from the printer instead.

**Where the data comes from.** Klipper's `configfile` status object exposes
`settings.<section>.<option>`: every config value, including defaults, as of the
last Klipper start or restart
([Status reference: configfile](https://www.klipper3d.org/Status_Reference.html#configfile)).
Moonraker makes Klipper status objects available through
[`printer.objects.query`](https://moonraker.readthedocs.io/en/latest/external_api/printer/#query-printer-object-status)
(`GET /printer/objects/query?configfile=settings`). This is a read-only request.

**What is read.**

| Klipper section | Option | Used for |
|---|---|---|
| [`[printer]`](https://www.klipper3d.org/Config_Reference.html#printer) | `max_velocity` | Upper bound for every feature speed |
| `[printer]` | `max_accel` | Upper bound for every feature acceleration |
| `[printer]` | `square_corner_velocity` | Cornering speed; Klipper's replacement for jerk (see [below](#no-jerk-settings)) |
| `[printer]` | `minimum_cruise_ratio` | Speed reduction of short zigzag moves ([Kinematics](https://www.klipper3d.org/Kinematics.html#minimum-cruise-ratio)) |
| [`[input_shaper]`](https://www.klipper3d.org/Config_Reference.html#input_shaper) | `shaper_type` or `shaper_type_x` / `shaper_type_y` | Shown next to the acceleration limits |
| `[input_shaper]` | `shaper_freq_x`, `shaper_freq_y` | Shown next to the acceleration limits |

**Why `configfile` and not `toolhead`.** The `toolhead` object also reports
`max_velocity`, `max_accel`, `minimum_cruise_ratio` and `square_corner_velocity`,
but as the limits *currently in effect*, which a previous print's
`SET_VELOCITY_LIMIT` or `M204` may have changed
([Status reference: toolhead](https://www.klipper3d.org/Status_Reference.html#toolhead)).
The configured values are the stable reference. Values that `SAVE_CONFIG` wrote
into `printer.cfg` (for example after `SHAPER_CALIBRATE`) are part of the config
file and show up after the next restart like any other setting.

**Why the input shaper matters here.** The Klipper documentation ties the usable
acceleration to the chosen shaper: stronger shapers smooth more, and
`max_accel` should be chosen so that the smoothing stays acceptable
([Resonance compensation: selecting max_accel](https://www.klipper3d.org/Resonance_Compensation.html#selecting-max_accel),
[Measuring resonances: selecting max_accel](https://www.klipper3d.org/Measuring_Resonances.html#selecting-max_accel)).
Showing shaper type and frequency next to the acceleration limits makes that
relationship visible when choosing per-feature accelerations.

**Planning.** KLIPSLICE already sets acceleration per feature (outer wall, inner
wall, infill, travel and so on) with `SET_VELOCITY_LIMIT ACCEL=…`. With synced
limits, every one of those values is checked against the machine's real
`max_accel` and `max_velocity` before the G-code is written, and a value above the
limit is reported instead of passed through.

<figure class="ksd-figure">
--8<-- "assets/diagrams/machine-sync.svg"
<figcaption>Machine sync: from printer.cfg to the limits that constrain per-feature planning.</figcaption>
</figure>

[Open the diagram at full size](assets/diagrams/machine-sync.svg){ .ksd-fullsize }

**Inherited behaviour that stage 1 replaces.** When the profile option
*accel_to_decel* is enabled (it is by default), the code inherited from OrcaSlicer
appends `ACCEL_TO_DECEL=` to every `SET_VELOCITY_LIMIT ACCEL=…` it writes. Klipper deprecated that
parameter on 2024-03-13 in favour of `minimum_cruise_ratio` and removed it on
2025-08-11 ([Config changes](https://www.klipper3d.org/Config_Changes.html)).
Current Klipper
[`SET_VELOCITY_LIMIT`](https://www.klipper3d.org/G-Codes.html#set_velocity_limit)
only accepts `VELOCITY`, `ACCEL`, `MINIMUM_CRUISE_RATIO` and
`SQUARE_CORNER_VELOCITY`, so the extra parameter has no effect. Stage 1 uses the
machine's `minimum_cruise_ratio` instead.

## Stage 2: Klipper-accurate print time

A print time estimate is only as good as the motion model and the limits behind
it. Klipper's motion model is documented: constant acceleration, a trapezoid
generator per move, look-ahead with junction speeds derived from
`square_corner_velocity`, and the `minimum_cruise_ratio` limit on short moves
([Kinematics](https://www.klipper3d.org/Kinematics.html)).

The estimator inherited from OrcaSlicer already derives Klipper's junction speed
from the square corner velocity. It does not model `minimum_cruise_ratio`, and it
works with the limits typed into the profile. Stage 2 builds on stage 1: the
estimator uses the synced limits and adds the missing parts of Klipper's motion
model, so the estimate matches what Klipper will actually do with the file.

## Stage 3: Native adaptive mesh and purge

Klipper can probe only the area a print uses:
[`BED_MESH_CALIBRATE ADAPTIVE=1`](https://www.klipper3d.org/G-Codes.html#bed_mesh_calibrate)
limits the mesh to the objects defined in the G-code file, plus an optional
`adaptive_margin`, and scales the probe count down accordingly
([Bed mesh: adaptive meshes](https://www.klipper3d.org/Bed_Mesh.html#adaptive-meshes)).
The objects come from
[`[exclude_object]`](https://www.klipper3d.org/Exclude_Object.html): Klipper reads
the `POLYGON` outlines given by `EXCLUDE_OBJECT_DEFINE`. Without an
`[exclude_object]` section, Klipper reports "Exclude objects not enabled. Using
full mesh..." and probes the full bed.

KLIPSLICE already writes `EXCLUDE_OBJECT_DEFINE` with a `CENTER` and a `POLYGON`
(the convex hull of each object instance) when the *Exclude objects* option is on,
and it writes these definitions *before* the machine start G-code. That order is
what makes `ADAPTIVE=1` inside a `PRINT_START` macro work (see
[Klipper setup](klipper-setup.md)).

Stage 3 turns this into a native feature instead of a macro recipe:

- printer profiles whose start sequence calls `BED_MESH_CALIBRATE ADAPTIVE=1`,
  with the requirements (`[exclude_object]`, *Exclude objects* enabled) checked
  before slicing instead of discovered at print time,
- a purge line placed next to the first layer's print area instead of at a fixed
  bed position, using the first-layer bounds KLIPSLICE already knows when it
  writes the file.

The Klipper documentation notes that adaptive meshes are meant for machines whose
full mesh varies by no more than about one layer height, and that adaptive meshes
should not be saved for reuse
([Bed mesh: adaptive meshes](https://www.klipper3d.org/Bed_Mesh.html#adaptive-meshes)).
Stage 3 is designed around both points: a fresh mesh for every print, never
saved as a reusable profile.

## Stage 4: Closed-loop feedback (vision)

Stages 1 to 3 move data from the machine into the slicer once per slice. The long
term idea is a loop: measured machine data flows back and changes how the next
part is sliced. There is no design for this yet, and it is listed here so the
earlier stages keep the door open, not as a commitment.

## What we deliberately don't do

### No jerk settings { #no-jerk-settings }

Klipper does not use jerk. It changes velocity with constant acceleration and
computes the speed at the junction between two moves with an approximated
centripetal model that is configured by a single value, the
`square_corner_velocity`: the speed allowed through a 90° corner. Junction speeds
for other angles are derived from it
([Kinematics: look-ahead](https://www.klipper3d.org/Kinematics.html#look-ahead)).

The jerk fields inherited from OrcaSlicer are therefore written as
`SET_VELOCITY_LIMIT SQUARE_CORNER_VELOCITY=…` for Klipper, never as `M205`.
KLIPSLICE will not add jerk-style tuning that Klipper would not execute.

### No arc fitting for Klipper

Klipper accepts `G2`/`G3` only with a
[`[gcode_arcs]`](https://www.klipper3d.org/Config_Reference.html#gcode_arcs)
section, and it splits every arc into straight segments of `resolution` mm
(default 1 mm) before motion planning. The motion planner sees line segments
either way, so arcs give Klipper nothing that linear moves do not. The *Arc
fitting* option inherited from OrcaSlicer says so in its own tooltip and
recommends leaving it off on Klipper: the slicer turns segments into arcs, and
Klipper turns them back into segments. KLIPSLICE therefore does not need
`[gcode_arcs]`.

### No "vector API" into Klipper

Motion reaches Klipper as G-code, either from a file printed through
[`[virtual_sdcard]`](https://www.klipper3d.org/Config_Reference.html#virtual_sdcard)
or as commands sent through the API server's
[`gcode/script`](https://www.klipper3d.org/API_Server.html#gcodescript) endpoint.
The API server's
[endpoints](https://www.klipper3d.org/API_Server.html#available-endpoints) offer
no way to submit toolpaths or trajectories directly; the `motion_report` endpoints
only let clients *subscribe* to motion data for diagnostics. KLIPSLICE writes
G-code and relies on Klipper's documented planner, rather than trying to bypass
it.
