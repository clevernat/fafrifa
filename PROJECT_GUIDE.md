# Project Guide — Read Me to Understand Everything

This is the **plain-language companion** to the repository. It explains, from
the ground up, *what* this project is, *why* it exists, *how the pieces fit
together*, and *how to run it* — with mind-maps and diagrams you can follow even
if you're new to climate modelling or Python. (The diagrams render automatically
on GitHub.)

If you only read one section, read **"The 30-second version"** and look at the
first mind-map.

---

## The 30-second version

Scientists are studying **solar geoengineering** — specifically **Stratospheric
Aerosol Injection (SAI)**, the idea of spraying tiny reflective particles high
in the atmosphere to cool the planet, like a man-made volcano. It could reduce
some climate damage, but it has side-effects we don't fully understand.

One side-effect is on **winter weather in the mid-latitudes** (Europe, the US,
Asia): SAI can nudge the jet stream and storm tracks, changing how cold, stormy,
or mild winters are. **How big that effect is, and whether different climate
models agree on it, is uncertain.**

This project builds three things to help pin that uncertainty down:

1. **A software tool** that measures "extreme weather" from climate-model data.
2. **A dataset** of those measurements across 4 models and 2 SAI strategies.
3. **A written assessment** that updates the official "uncertainty entry" with
   the new evidence.

```mermaid
mindmap
  root((Track A Project))
    The Question
      Does SAI change mid-latitude winter extremes
      Do the climate models agree
      Which injection strategy matters
    Deliverable 1 - Tool
      sai_extremes Python package
      Computes 24 extremes indices
      Reads data from cloud
      Fully tested
    Deliverable 2 - Dataset
      Indices for 4 models
      Two SAI scenarios
      Data card and schema
      Demo figures
    Deliverable 3 - Assessment
      Revised uncertainty entry
      Synthesises 6 papers
      Proposes new ratings
    Open Science
      Runs on Reflective Cloud Hub
      Anyone can reproduce
      On GitHub with automated tests
```

---

## 1. The science, in everyday terms

### What is SAI?

When a big volcano erupts (like Pinatubo in 1991), it throws sulfur high into the
**stratosphere** (the calm layer ~15–30 km up). Those particles reflect a little
sunlight back to space, and the planet cools for a year or two. **SAI** proposes
to do this deliberately and continuously to offset global warming.

### Why does it affect *winter winds*?

Here's the chain of cause and effect. The key insight: the particles don't just
reflect sunlight — they also **absorb heat and warm the stratosphere**, and that
warming reshapes the winds.

```mermaid
flowchart TD
    A["SAI particles in the<br/>tropical stratosphere"] --> B["They absorb heat →<br/>warm the tropical stratosphere"]
    B --> C["Bigger temperature difference<br/>between equator and pole<br/>(in winter)"]
    C --> D["Stronger 'polar vortex'<br/>(the ring of wind high over the Arctic)"]
    D --> E["That strengthening pushes down<br/>into the lower atmosphere"]
    E --> F["Stronger westerly winds /<br/>'positive NAO' pattern"]
    F --> G["Milder, wetter Northern Europe<br/>Drier Mediterranean<br/>Warmer Eurasian winters<br/>Fewer cold extremes"]

    style A fill:#cfe8ff,stroke:#3a7bd5
    style F fill:#ffe6cc,stroke:#e08a3c
    style G fill:#d6f5d6,stroke:#3aa655
```

Two crucial details this project tests:

- **It's the particles, not just the cooling.** If you simulate cooling by simply
  "dimming the sun" (no particles), this winter-wind effect *doesn't appear*. So
  the effect depends on the **aerosol physics** — which means **where you inject**
  matters a lot.
- **Two injection strategies are compared:**

```mermaid
flowchart LR
    subgraph SAI["G6-1.5K-SAI"]
        S1["Inject in the subtropics<br/>30°N and 30°S"]
        S2["Strong tropical<br/>stratospheric heating"]
        S3["Bigger winter-wind effect<br/>expected"]
        S1 --> S2 --> S3
    end
    subgraph HiLLA["G6-1.5K-HiLLA"]
        H1["Inject high and low<br/>60°N/S, 13–15 km, seasonal"]
        H2["Less tropical<br/>stratospheric heating"]
        H3["Weaker winter-wind effect<br/>expected"]
        H1 --> H2 --> H3
    end
    SAI -. "compare the two<br/>to isolate the mechanism" .- HiLLA
```

Comparing these two is like a controlled experiment: if the winter-wind effect is
much weaker under HiLLA, that confirms it's driven by tropical stratospheric
heating.

### Glossary (the jargon, decoded)

| Term | Plain meaning |
|------|---------------|
| **SAI** | Stratospheric Aerosol Injection — the cooling-particles idea |
| **GeoMIP** | A coordinated project where many modelling groups run the *same* SAI experiment so results can be compared |
| **G6-1.5K-SAI / G6-1.5K-HiLLA** | The two specific SAI experiments compared here |
| **Earth system model** (CESM, MIROC, UKESM, E3SM) | Big physics simulators of the whole climate; each lab has its own |
| **Mid-latitudes** | The temperate zone — roughly 30°–60° N/S (Europe, US, China) |
| **Jet stream** | A fast river of wind high in the atmosphere that steers storms |
| **NAO** (North Atlantic Oscillation) | A see-saw in air pressure between Iceland and the Azores that controls European winters |
| **Polar vortex** | A ring of strong winds circling the Arctic in winter |
| **Blocking** | When that flow gets "stuck," causing prolonged cold/calm spells |
| **ETCCDI indices** | A standard set of ~27 agreed recipes for measuring climate extremes (e.g. "number of frost days") |
| **Extremes index** | A single number summarising extreme weather, e.g. *frost days = how many days below 0 °C this year* |
| **Baseline / reference** | The "world without SAI" you compare against to isolate SAI's effect |

---

## 2. What's in this repository

Three deliverables, each in its own folder.

```mermaid
flowchart TD
    ROOT["Track-A-Deliverables/"] --> D1["deliverable-1-workflow/<br/><b>The software tool</b>"]
    ROOT --> D2["deliverable-2-dataset/<br/><b>The measurements</b>"]
    ROOT --> D3["deliverable-3-uncertainty-entry/<br/><b>The written assessment</b>"]
    ROOT --> EXTRA["README, guides,<br/>CI, license, bundle"]

    D1 --> D1a["sai_extremes Python package<br/>(the engine)"]
    D1 --> D1b["tests (proof it's correct)"]
    D1 --> D1c["demo notebook (a guided tour)"]

    D2 --> D2a["indices dataset files"]
    D2 --> D2b["DATA_CARD.md (the dataset's manual)"]
    D2 --> D2c["figures"]

    D3 --> D3a["Revised 'Extratropical<br/>Circulation' entry"]

    style D1 fill:#cfe8ff,stroke:#3a7bd5
    style D2 fill:#ffe6cc,stroke:#e08a3c
    style D3 fill:#d6f5d6,stroke:#3aa655
```

### How the three connect (the story arc)

```mermaid
flowchart LR
    DATA["Climate model data<br/>(daily temperature<br/>& rainfall)"] -->|"Deliverable 1<br/>processes it"| IDX["Extremes measurements<br/>(Deliverable 2)"]
    IDX -->|"feeds the evidence"| ENTRY["Updated uncertainty<br/>assessment (Deliverable 3)"]
    DIAG["Circulation diagnostics<br/>jet / NAO / blocking"] -->|"explains WHY"| ENTRY
    DATA -->|"Deliverable 1<br/>also computes"| DIAG
```

- **Deliverable 1 answers "what tools do we need?"** — it's the reusable engine.
- **Deliverable 2 answers "WHAT happens?"** — the numbers: how extremes change.
- The **circulation diagnostics** answer "**WHY** does it happen?" — jet/NAO/blocking.
- **Deliverable 3** ties it together into a decision-useful assessment.

---

## 3. Deliverable 1 — the software tool (`sai_extremes`)

### What it does

You give it daily climate-model data (max temperature, min temperature, rainfall)
for a model and an SAI scenario. It gives you back **24 "extremes indices"** — one
number per year, per location — like *frost days*, *heaviest 5-day rainfall*, or
*warm-spell length*. Then it can also compute **circulation diagnostics** (jet
position, NAO, blocking) that explain the weather patterns behind those extremes.

### The 24 indices, grouped

```mermaid
mindmap
  root((24 Extremes Indices))
    Temperature counts
      SU summer days
      ID icing days
      FD frost days
      TR tropical nights
    Hottest and coldest
      TXx TXn warmest coldest day
      TNx TNn warmest coldest night
    Rainfall amounts
      Rx1day wettest day
      Rx5day wettest 5 days
      PRCPTOT yearly total
      SDII average wet day
    Rainfall counts and spells
      R10mm R20mm heavy days
      CDD dry spell length
      CWD wet spell length
    Percentile based
      TX90p TX10p warm cool days
      TN90p TN10p warm cold nights
      WSDI CSDI warm cold spells
      R95p R99p very wet days
```

The **"percentile-based"** group is the clever part the project added: instead of
fixed thresholds (like 0 °C), they ask "how often is it more extreme than the
*local* historical 90th-or-10th percentile?" — which adapts to each place.

### How the code is built (and why it's trustworthy)

The single most important design idea: **the maths is separated from the data
plumbing.** The actual formulas live in tiny, simple functions called **kernels**
that use only NumPy (basic Python maths). These are checked against hand-computed
answers in the tests. A second layer wraps them to run efficiently over huge
climate datasets.

```mermaid
flowchart TD
    subgraph CORE["The maths (verified)"]
        K["kernels.py<br/>simple formulas, pure NumPy<br/>✔ unit-tested by hand"]
    end
    subgraph WRAP["The plumbing (runs at scale)"]
        I["indices.py / percentiles.py<br/>run the kernels over<br/>big data cubes (xarray)"]
        DI["diagnostics.py<br/>jet, NAO, blocking"]
    end
    subgraph IO["Getting the data"]
        IOL["io.py — pluggable readers<br/>local files · cloud S3 · Zarr"]
        CAT["catalog.yaml<br/>where each dataset lives"]
    end
    CAT --> IOL --> WRAP
    K --> I
    K --> DI
    WRAP --> OUT["pipeline.py<br/>produces the dataset"]

    style CORE fill:#d6f5d6,stroke:#3aa655
    style WRAP fill:#cfe8ff,stroke:#3a7bd5
    style IO fill:#ffe6cc,stroke:#e08a3c
```

Why this matters for the application: it means the index definitions are
**provably correct** (19 tests pass), the same code can read data from anywhere
(your laptop or the cloud) by editing one config file, and adding a new index is
a one-line change. That's exactly the "open, reproducible science" the internship
is about.

### The files in the package

| File | What it's for |
|------|---------------|
| `kernels.py` | The actual extremes formulas (simple, tested) |
| `indices.py` | Runs the temperature/rainfall indices over big datasets |
| `percentiles.py` | The percentile indices + a statistical correction (Zhang 2005) |
| `diagnostics.py` | Jet stream, NAO, storm-track, blocking calculations |
| `io.py` | Reads data from local files, cloud S3, or Zarr — interchangeably |
| `catalog.yaml` | A directory of which model/scenario data lives where |
| `regions.py` | Defines map regions (Mediterranean, Eurasia, etc.) and winter season |
| `pipeline.py` | The "run everything" driver that produces the dataset |
| `synthetic.py` | Makes fake-but-realistic data so the demo runs without the cloud |

---

## 4. Deliverable 2 — the dataset

This is the **output**: the 24 indices computed for every available
model × scenario combination, saved in the standard scientific file format
(**CF-NetCDF**), plus a tidy table of regional averages and example figures.

```mermaid
flowchart LR
    M["4 models<br/>CESM · MIROC<br/>UKESM · E3SM"] --> RUN
    S["2 scenarios<br/>SAI · HiLLA"] --> RUN
    RUN["pipeline runs<br/>all combinations"] --> FILES["One file per<br/>model × scenario"]
    FILES --> CSV["Tidy table:<br/>region averages<br/>per index per year"]
    FILES --> FIG["Figures:<br/>model spread,<br/>maps"]
    RUN -.->|"skips"| SKIP["MIROC has no HiLLA run<br/>→ automatically skipped"]
```

A key honesty note baked into the dataset's manual (`DATA_CARD.md`): the demo
files here were generated on **synthetic (fake) data**, because the real cloud
data wasn't reachable while building this. They have the exact right *structure*
and use the *same tested maths*, but they're for demonstration — point the tool at
the real Cloud Hub and it produces the real dataset unchanged.

The **example figure** already shows the expected story: under SAI, Eurasian
winters have **fewer frost days** than under HiLLA — the milder-winter signal the
science predicts.

---

## 5. Deliverable 3 — the uncertainty assessment

The Reflective "SAI Uncertainty Database" has a public entry called
**Extratropical Circulation**. This deliverable is a **revised version** of that
entry, bringing in the brand-new multi-model evidence and proposing updated
ratings.

```mermaid
mindmap
  root((Revised Uncertainty Entry))
    Proposed rating changes
      Uncertainty stays Medium
      Decision relevance up to Medium-High
      Now resolvable on research timescale
    The mechanism
      Tropical heating to vortex to NAO
      Solar dimming does not reproduce it
      So injection strategy matters
    Sources of disagreement
      Injection latitude is key
      Models differ over US and Africa
      Ocean AMOC changes confound it
      Internal variability
    What would reduce it
      Multi-model G6-1.5K analysis
      Separate the mechanisms
      Quantify model spread
    Built on 6 papers
      Jones 2021 NAO
      Lee 2026 subtropical injection
      Duffey 2026 HiLLA
      Duffey and Irvine 2024 baseline
      Joshi 2026 AMOC
      Bednarz injection strategy
```

In short, it argues: the *mechanism* is well understood, but *how strongly* it
shows up — and whether models agree — is the open question, and we can now make
progress because the data finally exist. It even flags a subtle but important
methodological point (the "baseline" you compare against changes the answer, from
Duffey & Irvine 2024).

---

## 6. How to actually run it

```mermaid
flowchart TD
    A["Clone the repo"] --> B{"What do you want?"}
    B -->|"Just see it work"| C["Run the demo notebook<br/>or generate_demo_dataset.py<br/>→ no data download needed"]
    B -->|"Check the maths"| D["python tests/test_kernels.py<br/>→ 19 tests pass"]
    B -->|"Real science"| E["Edit catalog.yaml to point<br/>at the Cloud Hub, then<br/>run the production pipeline"]
```

Concretely, on a computer with Python:

```bash
# 1. get the code
git clone https://github.com/clevernat/fafrifa.git
cd fafrifa/deliverable-1-workflow/sai-extremes

# 2. install it (light version is enough to see it work)
pip install -e ".[all]"

# 3. prove the maths is right (no data needed)
python tests/test_kernels.py        # 9 tests
python tests/test_percentiles.py    # 3 tests
python tests/test_diagnostics.py    # 7 tests

# 4. make the demo dataset + figures (no data needed)
python ../../deliverable-2-dataset/scripts/generate_demo_dataset.py

# 5. open the guided tour
jupyter lab notebooks/01_extremes_workflow_demo.ipynb
```

Everything in steps 3–4 runs on **synthetic data**, so it works on any laptop with
no special access. Step 5's notebook walks through the whole story with charts.

---

## 7. Automated testing (CI)

Every time code is pushed to GitHub, a robot (**GitHub Actions**) automatically
re-runs all the tests on several Python versions, and even regenerates the demo
dataset, to make sure nothing is broken. You can watch it under the **Actions**
tab of the repo. A green check = everything works.

```mermaid
flowchart LR
    PUSH["You push code<br/>to GitHub"] --> CI["GitHub Actions runs"]
    CI --> T1["Maths tests<br/>Python 3.9–3.12"]
    CI --> T2["Full test suite<br/>with xarray"]
    CI --> T3["Demo dataset<br/>smoke test"]
    T1 --> OK["✔ green check"]
    T2 --> OK
    T3 --> OK
```

---

## 8. Where to look for what

| If you want to… | Open this |
|-----------------|-----------|
| Understand the whole project in plain English | **this file** |
| See a one-paragraph professional summary | `README.md` (repo root) |
| Read the technical package docs | `deliverable-1-workflow/sai-extremes/README.md` |
| Understand the dataset's contents | `deliverable-2-dataset/DATA_CARD.md` |
| Read the science write-up | `deliverable-3-uncertainty-entry/…REVISED.md` |
| See the code that does the maths | `…/sai_extremes/kernels.py` |
| Take the guided tour with charts | `…/notebooks/01_extremes_workflow_demo.ipynb` |

---

## 9. One-paragraph summary you can reuse

> This project is an open-science prototype for the Reflective SAI Uncertainty
> Database (Track A). It delivers (1) `sai_extremes`, a tested Python workflow that
> computes 24 ETCCDI climate-extremes indices and jet/NAO/blocking diagnostics for
> the GeoMIP G6-1.5K-SAI and G6-1.5K-HiLLA experiments across four Earth system
> models, with a pluggable cloud I/O layer; (2) a multi-model indices dataset with
> a documented schema and data card; and (3) a revised "Extratropical Circulation"
> uncertainty assessment synthesising the latest literature. Together they quantify
> how — and how consistently across models — stratospheric aerosol injection
> reshapes Northern-Hemisphere mid-latitude winter extremes, and demonstrate a
> reproducible, cloud-based workflow for communicating that uncertainty.
```
