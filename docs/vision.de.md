# Vision & Fahrplan

Ein Allzweck-Slicer darf über den Drucker am anderen Ende kaum etwas annehmen.
KLIPSLICE darf viel annehmen: Auf dem Drucker läuft Klipper, Moonraker ist
erreichbar, und Klipper legt seine eigene Konfiguration offen. Darum geht es im
Fahrplan.

Die Leitregel: **Der Slicer soll die echten Grenzen der Maschine kennen und nie
zulassen, dass ein Wert sie unbemerkt überschreitet.** Bei Klipper ist das
besonders wichtig, weil Klipper Bewegungsbefehle nicht auf die Werte aus der
`printer.cfg` begrenzt. Seit der
[Änderung vom 30.04.2021](https://www.klipper3d.org/Config_Changes.html) dürfen
`SET_VELOCITY_LIMIT` und `M204` Geschwindigkeit, Beschleunigung und Square Corner
Velocity *über* die konfigurierten Werte setzen, und Klipper führt sie aus. Was
der Slicer schreibt, macht die Maschine.

<figure class="ksd-figure">
--8<-- "assets/diagrams/roadmap.de.svg"
<figcaption>Stufen des Fahrplans. Stufe 0 ist in Arbeit, Stufen 1–3 sind geplant, Stufe 4 ist eine Vision ohne Entwurf.</figcaption>
</figure>

[Diagramm in voller Größe öffnen](assets/diagrams/roadmap.svg){ .ksd-fullsize }

## Stufe 0: Fundament (in Arbeit)

Vor jeder neuen Funktion muss der Fork zu einem sauberen Slicer nur für Klipper
werden: Druckerprofile nur für Klipper, eine eigene Identität neben OrcaSlicer und
das Entfernen von Druck-Hosts und Netzwerkcode, die nicht zu Moonraker führen. Die
[Startseite](index.md#project-status) zeigt, was erledigt ist und was noch fehlt.

## Stufe 1: Maschinen-Sync

Heute plant KLIPSLICE gegen Bewegungsgrenzen, die im Druckerprofil eingetragen
sind. Sie stammen aus einem Datenblatt oder sind geschätzt, und sie weichen von der
echten Maschine ab, sobald jemand die `printer.cfg` ändert. Stufe 1 liest die
Grenzen stattdessen vom Drucker.

**Woher die Daten kommen.** Klippers Statusobjekt `configfile` stellt
`settings.<section>.<option>` bereit: jeden Konfigurationswert einschließlich der
Standardwerte, Stand des letzten Starts oder Neustarts von Klipper
([Status Reference: configfile](https://www.klipper3d.org/Status_Reference.html#configfile)).
Moonraker macht Klipper-Statusobjekte über
[`printer.objects.query`](https://moonraker.readthedocs.io/en/latest/external_api/printer/#query-printer-object-status)
zugänglich (`GET /printer/objects/query?configfile=settings`). Das ist eine reine
Leseanfrage.

**Was gelesen wird.**

| Klipper-Abschnitt | Option | Verwendung |
|---|---|---|
| [`[printer]`](https://www.klipper3d.org/Config_Reference.html#printer) | `max_velocity` | Obergrenze für jede Feature-Geschwindigkeit |
| `[printer]` | `max_accel` | Obergrenze für jede Feature-Beschleunigung |
| `[printer]` | `square_corner_velocity` | Kurvengeschwindigkeit; Klippers Ersatz für Jerk (siehe [unten](#no-jerk-settings)) |
| `[printer]` | `minimum_cruise_ratio` | Geschwindigkeitsbegrenzung kurzer Zickzack-Bewegungen ([Kinematics](https://www.klipper3d.org/Kinematics.html#minimum-cruise-ratio)) |
| [`[input_shaper]`](https://www.klipper3d.org/Config_Reference.html#input_shaper) | `shaper_type` oder `shaper_type_x` / `shaper_type_y` | Wird neben den Beschleunigungsgrenzen angezeigt |
| `[input_shaper]` | `shaper_freq_x`, `shaper_freq_y` | Wird neben den Beschleunigungsgrenzen angezeigt |

**Warum `configfile` und nicht `toolhead`.** Auch das Objekt `toolhead` meldet
`max_velocity`, `max_accel`, `minimum_cruise_ratio` und `square_corner_velocity`,
aber als die *gerade wirksamen* Grenzen, die ein `SET_VELOCITY_LIMIT` oder `M204`
aus einem vorherigen Druck verändert haben kann
([Status Reference: toolhead](https://www.klipper3d.org/Status_Reference.html#toolhead)).
Die konfigurierten Werte sind die stabile Referenz. Werte, die `SAVE_CONFIG` in
die `printer.cfg` geschrieben hat (etwa nach `SHAPER_CALIBRATE`), gehören zur
Konfigurationsdatei und erscheinen nach dem nächsten Neustart wie jede andere
Einstellung.

**Warum der Input Shaper hier zählt.** Die Klipper-Dokumentation verknüpft die
nutzbare Beschleunigung mit dem gewählten Shaper: Stärkere Shaper glätten mehr,
und `max_accel` soll so gewählt werden, dass die Glättung vertretbar bleibt
([Resonance Compensation: Selecting max_accel](https://www.klipper3d.org/Resonance_Compensation.html#selecting-max_accel),
[Measuring Resonances: Selecting max_accel](https://www.klipper3d.org/Measuring_Resonances.html#selecting-max_accel)).
Shaper-Typ und -Frequenz neben den Beschleunigungsgrenzen zu zeigen, macht diesen
Zusammenhang bei der Wahl der Beschleunigungen pro Feature sichtbar.

**Planung.** KLIPSLICE setzt die Beschleunigung schon heute pro Feature
(Außenwand, Innenwand, Füllung, Leerfahrt usw.) mit `SET_VELOCITY_LIMIT ACCEL=…`.
Mit synchronisierten Grenzen wird jeder dieser Werte vor dem Schreiben des G-Codes
gegen das echte `max_accel` und `max_velocity` der Maschine geprüft, und ein Wert
über der Grenze wird gemeldet statt durchgereicht.

<figure class="ksd-figure">
--8<-- "assets/diagrams/machine-sync.de.svg"
<figcaption>Maschinen-Sync: von der printer.cfg zu den Grenzen, die die Planung pro Feature begrenzen.</figcaption>
</figure>

[Diagramm in voller Größe öffnen](assets/diagrams/machine-sync.svg){ .ksd-fullsize }

**Übernommenes Verhalten, das Stufe 1 ersetzt.** Ist die Profiloption
*accel_to_decel* aktiv (Standard), hängt der von OrcaSlicer übernommene Code an
jedes geschriebene `SET_VELOCITY_LIMIT ACCEL=…` ein `ACCEL_TO_DECEL=` an. Klipper
hat diesen Parameter am 13.03.2024 zugunsten von `minimum_cruise_ratio` als
veraltet markiert und am 11.08.2025 entfernt
([Config Changes](https://www.klipper3d.org/Config_Changes.html)). Das aktuelle
[`SET_VELOCITY_LIMIT`](https://www.klipper3d.org/G-Codes.html#set_velocity_limit)
kennt nur noch `VELOCITY`, `ACCEL`, `MINIMUM_CRUISE_RATIO` und
`SQUARE_CORNER_VELOCITY`; der zusätzliche Parameter bleibt also wirkungslos.
Stufe 1 verwendet stattdessen das `minimum_cruise_ratio` der Maschine.

## Stufe 2: Klipper-genaue Druckzeit

Eine Druckzeitschätzung ist nur so gut wie das Bewegungsmodell und die Grenzen
dahinter. Klippers Bewegungsmodell ist dokumentiert: konstante Beschleunigung, ein
Trapezgenerator pro Bewegung, Look-ahead mit Übergangsgeschwindigkeiten, die aus
der `square_corner_velocity` abgeleitet werden, und die Begrenzung kurzer
Bewegungen durch `minimum_cruise_ratio`
([Kinematics](https://www.klipper3d.org/Kinematics.html)).

Der von OrcaSlicer übernommene Schätzer leitet Klippers Übergangsgeschwindigkeit
bereits aus der Square Corner Velocity ab. `minimum_cruise_ratio` bildet er nicht
ab, und er rechnet mit den im Profil eingetragenen Grenzen. Stufe 2 baut auf
Stufe 1 auf: Der Schätzer nutzt die synchronisierten Grenzen und ergänzt die
fehlenden Teile von Klippers Bewegungsmodell, damit die Schätzung dem entspricht,
was Klipper mit der Datei tatsächlich tut.

## Stufe 3: Natives adaptives Mesh und Purge

Klipper kann nur den Bereich abtasten, den ein Druck belegt:
[`BED_MESH_CALIBRATE ADAPTIVE=1`](https://www.klipper3d.org/G-Codes.html#bed_mesh_calibrate)
beschränkt das Mesh auf die in der G-Code-Datei definierten Objekte plus einen
optionalen `adaptive_margin` und verringert die Zahl der Messpunkte entsprechend
([Bed Mesh: Adaptive Meshes](https://www.klipper3d.org/Bed_Mesh.html#adaptive-meshes)).
Die Objekte kommen aus
[`[exclude_object]`](https://www.klipper3d.org/Exclude_Object.html): Klipper liest
die `POLYGON`-Umrisse aus `EXCLUDE_OBJECT_DEFINE`. Ohne Abschnitt
`[exclude_object]` meldet Klipper „Exclude objects not enabled. Using full
mesh...“ und tastet das ganze Bett ab.

KLIPSLICE schreibt `EXCLUDE_OBJECT_DEFINE` mit `CENTER` und `POLYGON` (der
konvexen Hülle jeder Objektinstanz) bereits heute, wenn die Option *Objekte
ausschließen* aktiv ist, und zwar *vor* dem Maschinen-Start-G-Code. Genau diese
Reihenfolge sorgt dafür, dass `ADAPTIVE=1` in einem `PRINT_START`-Makro
funktioniert (siehe [Klipper-Einrichtung](klipper-setup.md)).

Stufe 3 macht daraus eine native Funktion statt eines Makro-Rezepts:

- Druckerprofile, deren Startsequenz `BED_MESH_CALIBRATE ADAPTIVE=1` aufruft,
  wobei die Voraussetzungen (`[exclude_object]`, *Objekte ausschließen* aktiv)
  vor dem Slicen geprüft statt erst beim Druck entdeckt werden,
- eine Purge-Linie direkt neben dem Druckbereich der ersten Schicht statt an einer
  festen Bettposition, auf Basis der Grenzen der ersten Schicht, die KLIPSLICE
  beim Schreiben der Datei ohnehin kennt.

Die Klipper-Dokumentation weist darauf hin, dass adaptive Meshes für Maschinen
gedacht sind, deren volles Mesh um nicht mehr als etwa eine Schichthöhe schwankt,
und dass adaptive Meshes nicht zur Wiederverwendung gespeichert werden sollen
([Bed Mesh: Adaptive Meshes](https://www.klipper3d.org/Bed_Mesh.html#adaptive-meshes)).
Stufe 3 ist auf beide Punkte ausgelegt: ein frisches Mesh für jeden Druck, nie als
wiederverwendbares Profil gespeichert.

## Stufe 4: Regelkreis (Vision)

Die Stufen 1 bis 3 bringen Daten einmal pro Slice-Vorgang von der Maschine in den
Slicer. Die langfristige Idee ist ein Kreislauf: Gemessene Maschinendaten fließen
zurück und verändern, wie das nächste Teil gesliced wird. Dafür gibt es noch
keinen Entwurf; die Stufe steht hier, damit die früheren Stufen die Tür offen
halten, nicht als Zusage.

## Was wir bewusst nicht tun

### Keine Jerk-Einstellungen { #no-jerk-settings }

Klipper kennt kein Jerk. Es ändert die Geschwindigkeit mit konstanter
Beschleunigung und berechnet die Geschwindigkeit am Übergang zwischen zwei
Bewegungen mit einem angenäherten Zentripetalmodell, das über einen einzigen Wert
eingestellt wird, die `square_corner_velocity`: die zulässige Geschwindigkeit durch
eine 90°-Ecke. Die Übergangsgeschwindigkeiten für andere Winkel werden daraus
abgeleitet
([Kinematics: Look-ahead](https://www.klipper3d.org/Kinematics.html#look-ahead)).

Die von OrcaSlicer übernommenen Jerk-Felder werden für Klipper deshalb als
`SET_VELOCITY_LIMIT SQUARE_CORNER_VELOCITY=…` geschrieben, nie als `M205`.
KLIPSLICE wird kein Jerk-artiges Tuning einführen, das Klipper nicht ausführen
würde.

### Kein Arc Fitting für Klipper { #no-arc-fitting-for-klipper }

Klipper akzeptiert `G2`/`G3` nur mit einem Abschnitt
[`[gcode_arcs]`](https://www.klipper3d.org/Config_Reference.html#gcode_arcs) und
zerlegt jeden Bogen vor der Bewegungsplanung in gerade Segmente von `resolution`
mm (Standard 1 mm). Die Bewegungsplanung sieht in jedem Fall Liniensegmente; Bögen
geben Klipper also nichts, was lineare Bewegungen nicht auch liefern. Die von
OrcaSlicer übernommene Option *Als Bogen drucken* (Arc Fitting) sagt das selbst im
Tooltip und empfiehlt, sie bei Klipper auszuschalten: Der Slicer macht aus
Segmenten Bögen, und Klipper macht daraus wieder Segmente. KLIPSLICE braucht
`[gcode_arcs]` deshalb nicht.

### Keine „Vektor-API“ in Klipper

Bewegungen erreichen Klipper als G-Code, entweder aus einer Datei, die über
[`[virtual_sdcard]`](https://www.klipper3d.org/Config_Reference.html#virtual_sdcard)
gedruckt wird, oder als Befehle über den Endpunkt
[`gcode/script`](https://www.klipper3d.org/API_Server.html#gcodescript) des
API-Servers. Die [Endpunkte](https://www.klipper3d.org/API_Server.html#available-endpoints)
des API-Servers bieten keinen Weg, Werkzeugbahnen oder Trajektorien direkt zu
übergeben; über die `motion_report`-Endpunkte können Clients Bewegungsdaten nur
zur Diagnose *abonnieren*. KLIPSLICE schreibt G-Code und verlässt sich auf Klippers
dokumentierte Bewegungsplanung, statt sie zu umgehen.
