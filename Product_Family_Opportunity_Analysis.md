# Making Sense of the 12,298 Product-Family Opportunities

*Prepared for the Product Data team · Analysis date: 2026-06-02*
*Source: `Product_Family_Gap.csv` — 12,298 opportunities, all of type "Product Family Gap"*

---

## 0. TL;DR

- **Two things were built from the raw opportunity descriptions:** (A) a **3-level
  product outline** of all 12,298 opportunities organized from scratch (not the
  McMaster outline), and (B) a **5-tier estimate of how big each family would get
  in the real world** if every size/material/style were carried.
- **The database is overwhelmingly a long tail of genuinely-new but *small* families.**
  ~91% of opportunities, if pursued, would top out at well under ~100 items in the
  whole world (think *jointers*, not *o-rings*).
- **The big combinatorial commodities you'd worry about — fasteners, o-rings,
  fittings, bearings, raw stock — are almost entirely *absent* as gaps,** because
  McMaster already carries them comprehensively. The deep families left in the gap
  list are a **small set of curated gems (27 opportunities)**, listed in full below.
- **A few real gems exist:** engine valves, orthopedic/bone screws, automotive
  gaskets (each >5,000 worldwide), plus pipe seals, tower packing/Raschig rings,
  aircraft hose fittings, fiber-optic connectors, cylinder sleeves, and trailer
  leaf springs (each ~500–5,000).

| Tier | What it means | Opportunities | Share |
|---|---|--:|--:|
| **1** | Accessories / replacement parts | **950** | 7.7% |
| **2** | Genuinely new, small world inventory (≲100) | **11,194** | 91.0% |
| **3** | Niche component, real size×material depth (~100–500) | **127** | 1.0% |
| **4** | Deep family / system (~500–5,000) | **20** | 0.2% |
| **5** | Massive / universal commodity (>5,000) | **7** | 0.1% |

---

## 1. What we mean by a "family" (and why it matters here)

From the *Organizing broad product families* write-up and the *Seven Disciplines*
slide, a **product family** at McMaster is:

> A group of products organized around **purpose, name, and shared
> characteristics** — narrow enough that a customer reaches it with one search term
> and every item needs similar product information.

Key principles that shaped this analysis:

- **Narrow purpose beats broad purpose.** Electrical Cable was split because "sends
  an electrical signal" was too broad; Electrical Connectors split into 31 families
  by *type of connection*, and daily transactions rose 44%.
- **Breadth alone is not a reason to split.** Hinges have hundreds of products but
  share one purpose and one search behavior — they stay together.
- **An *opportunity* is a family-shaped gap** — a feature/benefit we don't sell yet.
  Today an opportunity is usually 1–8 items (suffixes); the question this analysis
  answers is *"if we fully built it out, how big could that family get in the world?"*

Where an opportunity's description didn't name a clean family, the family was
inferred from the description (and the head noun of its name), consistent with the
definition above.

---

## 2. How this was produced (method & honest caveats)

This is a **hybrid** analysis: Claude-authored world-knowledge rules did the bulk
classification of all 12,298 rows, and the high-value tiers (3–5) were **read and
hand-curated**.

- **Outline (Deliverable A)** and **Tiers 1–2** are produced algorithmically from a
  rule set encoding product-domain knowledge (head-noun + keyword routing).
  Coverage is 92.9%; the residual 7.1% is a genuine miscellaneous tail, kept honest
  as an "Other / Specialty" bucket rather than force-fit.
- **Tiers 3–5 (the gems)** are **curated by reading the candidate pool**. A pure
  keyword pass massively over-counts them (it flags *"Cable Tie Installation Tools"*
  as a fastener and *"Bone Screws"* the same as *"Wood Screws"*). The world-size of a
  family depends on the specific product, so these were judged item by item.
- **No supplier websites were used.** This container has no outbound access to
  `mcmaster.com` or supplier domains (network policy returns 403), so the supplier
  URLs in the data were not scraped. Estimates rely on Claude's world knowledge of
  each product category, exactly as requested.
- **The size tiers are estimates meant for triage, not procurement.** They answer
  "roughly how deep is this family in the world," and should be validated by the
  team before acting — especially the Tier 4–5 gems.

> **Why so few deep families?** It's a structural feature of a *gap* database. The
> reason fasteners, o-rings, and fittings are deep is exactly why McMaster already
> carries them in full — so they rarely show up as gaps. What's left to discover is
> the niche long tail, which is mostly shallow.

---

## 3. Deliverable A — The 3-Level Product Outline

Built bottom-up from the opportunity descriptions, **not** the McMaster outline.
**Level 1** = broad domain, **Level 2** = sub-domain, **Level 3** = leaf category
(with the opportunity count). 18 domains; counts are opportunities, not SKUs.

### Domain summary (Level 1)

| # | Domain | Opportunities |
|--:|---|--:|
| 1 | Fasteners & Hardware | 1,971 |
| 2 | Electrical & Electronic | 1,846 |
| 3 | Plumbing, Pipe & Fluid Handling | 1,510 |
| 4 | Cutting, Machining & Metalworking | 1,150 |
| 5 | Test, Measurement & Inspection | 989 |
| — | *Other / Specialty (unclassified tail)* | 872 |
| 6 | Power Transmission & Motion | 760 |
| 7 | Automation, Robotics & Controls | 476 |
| 8 | Material Handling & Storage | 467 |
| 9 | Cleaning, Chemicals & Lubrication | 416 |
| 10 | Abrasives & Surface Finishing | 408 |
| 11 | Raw Materials & Stock | 380 |
| 12 | Industrial & Specialty Equipment | 257 |
| 13 | Safety, PPE & Facility | 188 |
| 14 | Welding, Soldering & Joining | 171 |
| 15 | Hand & Power Tools | 168 |
| 16 | Lab, Optics & Scientific | 158 |
| 17 | HVAC, Thermal & Process | 111 |

### Full outline (Level 1 → Level 2 → Level 3 : count)

**Fasteners & Hardware (1,971)**
- Hardware (965)
  - Knobs, Handles & Pulls: 337 · Hooks, Brackets & Mounts: 248 · Magnets: 164 · Latches, Locks & Catches: 130 · Springs: 68 · Hinges: 18
- Threaded Fasteners (489)
  - Screws: 195 · Bolts & Studs: 185 · Nuts: 58 · Washers: 51
- Non-Threaded Fasteners (330)
  - Pins, Clips & Retaining Rings: 259 · Anchors & Inserts: 51 · Rivets & Riveting: 16 · Rings: 4
- Mounts, Stands & Holders (84)
  - Holders: 24 · Mounts: 24 · Stands: 16 · Supports: 9 · Bases: 8 · Hangers: 3
- Caps, Plugs & Covers (44) — Covers: 23 · Caps: 11 · Protectors: 10
- Adapters, Extensions & Couplers (33) — Adapters: 24 · Extenders: 6 · Extensions: 3
- Spacers & Standoffs (14) — Spacers: 13 · Standoffs: 1
- Frames & Structural (6) · Clamps, Bands & Straps (6)

**Electrical & Electronic (1,846)**
- Wire, Cable & Conduit (470) — Wire & Cable: 443 · Conduit & Cable Management: 27
- Lighting (325) — Lights, Bulbs & Lighting: 325
- Components & Boards (302) — Electronic Components/Boards/Modules: 284 · Displays: 9 · Cards: 9
- Enclosures & Panels (276) — Enclosures, Boxes & Panels: 276
- Connectors & Terminals (216) — Electrical Connectors: 149 · Feedthroughs & Isolators: 46 · Terminals & Terminal Blocks: 21
- Power & Circuit Protection (129) — Power Supplies & Converters: 79 · Fuses/Breakers/Protection: 38 · Generators: 9 · Cells & Batteries: 3
- Switches & Relays (128) — Switches: 96 · Relays & Contactors: 32

**Plumbing, Pipe & Fluid Handling (1,510)**
- Pumps & Compressors (303) — Pumps: 239 · Compressors & Vacuum: 64
- Valves (276)
- Filtration (214) — Filters & Strainers: 214
- Sealing (181) — O-Rings, Seals & Gaskets: 181
- Hose, Tubing & Ducting (173) — Hose & Tubing: 158 · Hose Reels/Clamps/Fittings: 14 · Reels: 1
- Tanks & Reservoirs (159)
- Pipe & Tube Fittings (145) — Pipe Fittings: 68 · Flanges: 41 · Tube & Hose Fittings: 36
- Nozzles & Spray (59)

**Cutting, Machining & Metalworking (1,150)**
- Cutting Tools (488) — Taps/Dies/Threading: 131 · Saw Blades & Saws: 129 · Inserts & Tool Bits: 110 · Drills & Drill Bits: 42 · End Mills & Milling Cutters: 33 · Reamers/Countersinks/Counterbores: 32 · Other: 9 · Tips: 2
- Machine Tooling & Workholding (382) — Tool Holders & Chucks: 167 · Vises/Fixtures/Clamping: 156 · Spindles, Liners & Accessories: 46 · Heads: 9 · Indexing & Rotary Tables: 4
- Machine Tools (233) — Lathes/Mills/Machining Centers: 130 · Presses & Forming: 45 · Grinders & Sharpeners: 41 · Other: 17
- Metalworking Supplies (47) — Cutting & Coolant Fluids: 42 · Lapping & Polishing Compounds: 5

**Test, Measurement & Inspection (989)**
- Dimensional Metrology (254) — Gauges/Calipers/Micrometers: 129 · Scales & Balances: 112 · CMMs & 3D Measurement: 13
- Sensors & Transducers (217)
- Analyzers & Spectrometers (183) · Meters & Monitors (183)
- Testers & Test Equipment (116)
- Inspection & NDT (36)

**Power Transmission & Motion (760)**
- Shafts & Linear Motion (270) — Shafts/Rails/Slides/Rollers: 265 · Collars: 5
- Motors & Actuators (241) — Motors: 108 · Actuators & Cylinders: 93 · Drives & Speed Controls: 40
- Belts, Chains & Pulleys (133)
- Bearings & Bushings (73) — Bearings: 64 · Sleeves: 9
- Gears & Drives (43)

**Automation, Robotics & Controls (476)**
- Machine Vision & ID (150) — Vision, Cameras & Scanners: 150
- Robots & Vehicles (107) — Industrial & Collaborative Robots: 88 · Drones & UAVs: 15 · AGVs/AMRs/Mobile Robots: 4
- Controllers & PLCs (104) · Conveying & Feeding (61) · 3D Printing & Additive (54)

**Material Handling & Storage (467)**
- Containers (170) — Boxes/Cases/Bags/Containers: 170
- Shelving & Storage (128) — Racks/Shelving/Cabinets: 121 · Baskets: 4 · Trays: 3
- Lifting & Rigging (115) — Hoists/Cranes/Lifts: 79 · Slings/Straps/Rigging: 36
- Carts & Trucks (54)

**Cleaning, Chemicals & Lubrication (416)**
- Industrial Chemicals (251) — Chemicals/Acids/Additives: 248 · Wraps & Tapes: 3
- Cleaning Equipment (70) · Lubrication (57) · Dispensing (28) · Cleaning Supplies (10)

**Abrasives & Surface Finishing (408)**
- Coatings & Platings (290) · Brushes (49) · Polishing & Buffing (43) · Bonded & Coated Abrasives (19) · Blasting & Tumbling (7)

**Raw Materials & Stock (380)**
- Metal Stock (315) — Bar/Rod/Shapes: 113 · Tube & Pipe Stock: 95 · Sheet/Plate/Foil: 53 · Wire & Mesh Stock: 48 · Blocks: 6
- Plastic & Rubber Stock (44) · Composite & Other Stock (11) · Framing & Extrusion (T-Slot): 10

**Industrial & Specialty Equipment (257)**
- Kits & Sets (52) · Systems & Assemblies (51) · Specialty Machines (40) · Replacement Parts (22) · Medical & Healthcare (22) · Mixing & Processing (20) · Food & Agriculture (19) · Accessories (18) · Packaging Equipment (12) · Printing & Marking (1)

**Safety, PPE & Facility (188)**
- Machine & Area Safety (65) · Facility & Grounds (46) · Signage & Identification (41) · PPE (23) · Emergency & Environmental (13)

**Welding, Soldering & Joining (171)**
- Welding (65) · Adhesive Bonding (48) · Tape & Sealants (38) · Soldering & Brazing (20)

**Hand & Power Tools (168)**
- Wrenches & Drivers (58) · Clamping & Holding (39) · Striking & Gripping (33) · Specialty & Other Tools (32) · Power Tools (6)

**Lab, Optics & Scientific (158)**
- Optics & Photonics (54) · Lab Equipment (35) · Lasers (32) · Vacuum & Chambers (22) · Sample Handling (15)

**HVAC, Thermal & Process (111)**
- Heating (62) · Air Movement (33) · Drying & Dehumidification (9) · Cooling & Refrigeration (7)

**Other / Specialty (872)** — genuine miscellaneous tail not cleanly routable
(e.g., *Sharpening Strops, IV Poles, Smoking Shelters, Dry Ice Blasters, Tourniquets,
Planters, Zircon Sand*). Worth a manual pass if a clean home is wanted.

---

## 4. Deliverable B — How big would each family get in the real world?

Five tiers, by estimated **worldwide** item count if the family were fully built
out (every size × material × style). Tiers 1–2 are algorithmic; 3–5 are curated.

### Tier 1 — Accessories & Replacement Parts — **950 opportunities (7.7%)**

Families that exist to support a product we (or someone) already sells: replacement
parts, attachments, consumables, repair kits. Real-world size varies, but they're
*accessory-shaped* — defined by the parent product, not by independent demand.

**10 examples:**
1. **Tumbler Replacement Parts** — replacement bowls and lids for vibrating tumblers (wear out fastest).
2. **Torque Multipliers Replacement Parts** — kits and replacement parts for Enerpac torque multipliers.
3. **Replacement Bulbs for Ultraviolet Disinfectant Lamps** — our copy says to replace bulbs, but we don't sell them.
4. **Abrasive Blasting Nozzle Liners** — protect blasting nozzles; cheaper than replacing the nozzle.
5. **Impact Wrench Replacement Parts** — e.g., muffler kits for impact wrenches.
6. **Bolt Tensioner Accessories** — couplers and hydraulic hoses used with bolt tensioners.
7. **Polishing Kits** — buffer/polisher bundled with the consumables we sell separately.
8. **Torque Multiplier Extensions** — extensions that increase applied torque.
9. **Ring Buffs** — consumables for reciprocating polishers we already carry.
10. **Torque Wrench Shock Absorber Accessories** — shock-absorbing tools for reaction arms.

### Tier 2 — Genuinely New, Small World Inventory (≲100) — **11,194 (91.0%)**

The heart of the database. These are *real* new families, but even adding every
brand in the world yields a modest count — the *jointer* case from the brief. This
tier is dominated by modern instruments, machines, and niche components (consistent
with 82% of opportunities originating from "Offering Comparison" supplier/competitor
catalog scans).

**10 examples:**
1. **Lapping Machines** — automate the lapping process across various shapes.
2. **Electrochemical Cutting Machines** — EDM-style spark-erosion material removal.
3. **Combination 3D Printer / CNC Machine** — prints then machines a design.
4. **Dispensing Machines** — extrude/dispense fluids like a 3D printer.
5. **Soldering Machines** — wave/dip soldering for PCB components.
6. **Gas Detector Tubes** — glass tube + reagent that reacts to a specific gas.
7. **Robot Welding Sensors** — track a weld seam in real time.
8. **Vending Machines** — locked, individually-accessed dispensing cabinets.
9. **Coolant Cycling System** — automotive coolant service tool.
10. **Building Management System Interface Modules** — bridge incompatible controller signals.

*Strategic read:* the opportunity pipeline is mostly **breadth of new niches**, not
**depth within commodities**. Each is a small win on its own; value comes from volume
and from picking niches adjacent to strong existing families.

### Tier 3 — Niche Components with Real Size×Material Depth (~100–500) — **127 (1.0%)**

This is the *Bleed Rings* tier from the brief: a single niche component that still
fans out across sizes and materials into a few hundred items. Organized as a
3-level hierarchy below.

**3-level hierarchy of Tier-3 findings:**

- **Sealing & Gasketing components**
  - *Application-specific seals (18)* — Axle Seals, Fork Seals, Kingpin Seals, Pinion Seals, Valve Stem Seals, Engine Shaft Seals, Track Pin Seals, Universal Joint Seals, Shock Absorber Seals, Water Pump Bearing Seals, Tube Seals, Transmission Seals…
  - *Tube / heat-exchanger / fiber ferrules (4)* — Boiler Tube Ferrules, Heat Exchanger Ferrules, Grounding Strap Ferrules, Ferrules
- **Specialty fasteners (sized × thread)**
  - *Bolts (8)* — Banjo Bolts, Clevis Bolts, Cam Bolts, Connecting Rod Bolts, Breakaway Bolts, Double-Arming Bolts, Turbine Rotor Bolts
  - *Nuts (8)* — Barrel Nuts, Captive Nuts, Cam Nuts, Wedge Nuts, Eccentric Nuts, Hook Nuts, Hydraulic Nuts, Corner Nuts
  - *Locknuts (4)* — Cord Grip Locknuts, Cord Grip Grounding Locknuts, Panel Locknuts, Weld Locknuts
  - *Niche washers (4)* — Clamping, Spacing, Terminal, Tamper-Resistant Washers
- **Pipe / tube / well plumbing components**
  - *Niche fitting systems (9)* — Drop Pipe Fittings, Casing Fittings, Riser Tube Fittings, Glass Joint Fittings, Aerator Fittings, Drop Nipples, Stubout Fittings
  - *Sized sleeves (7)* — Rebar Sleeves, Conduit Compression Sleeves, Riser Tube Sleeves, Cylinder/Crush/Compression Sleeves, Thermometer Sleeves
  - *Sized spacers (6)* — Conduit Spacers, Casing Pipe Spacers, Concrete Spacers, Carburetor Spacers
  - *Couplings (5)* — Rebar Couplings, Fluid Couplings, Gear Box Couplings, Belt Couplings, Supplied-Air Couplings
- **Springs, rings & motion components**
  - *Specialty springs (8)* — Valve Springs, Gas Die Springs, Overhead Door Springs, Cantilever Springs, Lateral Springs, Counter-Balance Springs, Box Springs
  - *Small mechanical/jewelry rings (5)* — Jump Rings, Lock Rings, Press Die Lock Rings, Retaining Springs
  - *Mold / die / injection bushings (8)* — Sprue Bushings, Die and Mold Bushings, Injection Molding Bushings, Spring Plunger Locating Bushings
  - *Engine / valve-seat & thread inserts (6)* — Valve Seat Inserts, Counterbore Inserts, Thread Mill Inserts, Reaming/Broaching Inserts, Electrical Connector Thread Inserts
- **Electrical grounding & anchoring**
  - *Grounding hardware family (10)* — Grounding Studs, Grounding Washers, Grounding Terminals, Grounding Plates, Grounding Mesh, Grounding Elbows, Shaft Grounding Rings
  - *Structural / refractory / marine anchors (8)* — Refractory Anchors, Wire Rope Anchors, Marine Anchors, Rail Anchors, Fence Post Anchors, Winch Anchors, Insulation Lacing Anchors
- **Packaging / industrial tubes (sized) (7)** — Squeeze Tubes, Toothpaste Tubes, Condenser Tubes, Dip Tubes, Gas Collection/Dispersion Tubes

**10 quick examples:** Axle Seals · Banjo Bolts · Barrel Nuts · Drop Pipe Fittings ·
Rebar Couplings · Valve Springs · Sprue Bushings · Grounding Studs · Refractory
Anchors · Valve Seat Inserts.

### Tier 4 — Deep Family / System (~500–5,000) — **20 opportunities (≈6 family-types)**

The genuine mid-depth gems. A handful of opportunity records collapse into ~6
distinct deep families. **Full list, grouped:**

| Family (deep) | Why it's deep (~500–5,000) | Opportunity records |
|---|---|--:|
| **Fiber-optic connectors / ferrules / sleeves** | Connector ecosystem: LC/SC/ST/MPO × singlemode/multimode × ferrule bore × material | 8 |
| **Pipe seals** (link-seal type) | Every carrier-pipe × casing-bore combination × material/durometer | 6 |
| **Aircraft hydraulic & plumbing hose fittings** | AN/MS spec system: AN sizes × fitting types × materials | 2 |
| **Tower packing / Raschig rings** | Size × material (ceramic/metal/plastic) × style (Pall, Raschig, saddles) | 2 |
| **Engine cylinder sleeves / liners** | Per engine bore across all combustion engines | 1 |
| **Trailer leaf springs** | Capacity × length × leaf count across trailer classes | 1 |

> Note: a few specialty *bearing* types initially flagged here (tilt-pad journal,
> combination needle/thrust-roller) were **demoted to Tier 2** — they're engineered,
> low-inventory types, not deep catalogs.

### Tier 5 — Massive / Universal Commodity (>5,000) — **7 opportunities (3 family-types)**

True deep wells. **In a gap database these are nearly nonexistent** — McMaster
already owns the universal commodities (fasteners, o-rings, fittings, bearings, raw
stock), so they don't appear as gaps. The three that *do* are all **aftermarket /
regulated specialty domains** McMaster may or may not choose to enter:

| Family | Worldwide depth driver | Records | Caveat |
|---|---|--:|---|
| **Engine valves** (intake/exhaust) | Every engine make/model/displacement × intake/exhaust × material | 2 | Automotive/industrial aftermarket |
| **Orthopedic / bone / medical screws** | Cortical/cancellous/locking/cannulated × dia × length × Ti/SS/PEEK | 4 | Medical-grade, regulated |
| **Automotive gaskets** | Every vehicle make/model × engine/exhaust/system | 1 | Vehicle-specific aftermarket |

**Honest finding:** there are **no clean, unregulated >5,000-item commodity gaps** in
this database. If the goal is "find the next o-rings/fasteners," the realistic answer
is that those wells are already drilled — the upside in this list is in **Tier 4 and
the deepest Tier 3 families**, not Tier 5.

---

## 5. Cross-cutting observations & suggested next steps

1. **Pipeline shape = breadth, not depth.** 91% Tier-2 means the team is surfacing
   *many shallow new niches*. That's healthy for assortment breadth, but no single
   one is a "gusher." Prioritize Tier-2 niches that sit **adjacent to strong existing
   families** (e.g., consumables/variants near high-transaction families).
2. **The gems are concrete and few.** The 27 Tier-4/5 opportunities are the ones
   worth a deep build-out study. Start with **fiber-optic connectors, pipe seals,
   tower packing, and aircraft hose fittings** — deep, unregulated, and squarely
   industrial.
3. **Two-thirds of the catalog skew toward instruments/equipment** (Test &
   Measurement, Automation, Electrical) because 82% of opportunities come from
   competitor/supplier *Offering Comparison* scans. These are mostly Tier 2.
4. **Process state:** 95% of opportunities are still unassigned (`R2ASSIGN`) with no
   `intended_approach` — this analysis can serve as a first triage layer over that
   backlog.
5. **To refine:** (a) clean up the 872-item "Other / Specialty" tail; (b) validate
   the Tier-3 size estimates against real supplier catalogs (the URLs are in the
   data); (c) if useful, re-run the classifier on the live `productopportunities`
   database to keep counts current.

---

*Counts are reproducible from the source CSV. Tiers 1–2 and the outline are rule-based
across all 12,298 rows; Tiers 3–5 are Claude-curated from the candidate pool using
world knowledge of each product category. Size tiers are triage estimates — validate
the Tier 4–5 gems before acting.*
