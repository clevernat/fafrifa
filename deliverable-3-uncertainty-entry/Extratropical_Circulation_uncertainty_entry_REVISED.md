# Extratropical Circulation — *revised uncertainty entry*

> **Category:** Climate response
> **Scope:** Changes in extratropical circulation — the polar vortices, jet
> streams, and storm tracks — under SAI, after controlling for global-mean
> temperature.
>
> *Revision prepared for the SAI Uncertainty Database prototype (Track A,
> 2026). This draft proposes updated ratings and an expanded evidence base that
> incorporates the new multi-model GeoMIP G6-1.5K-SAI and G6-1.5K-HiLLA
> simulations, and links the entry to a reproducible quantification (Deliverables
> 1 & 2). Proposed changes from the live entry are flagged in* ***bold italic***.

| Rating | Current | **Proposed** | Rationale for change |
|---|---|---|---|
| **Uncertainty** | Medium | **Medium** | Mechanism well understood; magnitude and inter-model sign agreement still limited, but the first multi-model G6-1.5K ensembles now constrain it. |
| **Decision relevance** | Medium | ***Medium–High*** | The response is *injection-strategy-dependent* (equatorial vs subtropical vs high-latitude), so it bears directly on the choice between deployment designs — not only on whether to deploy. |
| **Resolvability scale** | Long-term sustained | ***Medium-term (research)*** | The data needed for a genuine multi-model assessment (G6-1.5K-SAI in 4 models; HiLLA in 3) now exist on the Cloud Hub; the gap is analysis, not new observing systems. |

---

## Metric

A detectable change in **Northern Hemisphere mid-latitude extreme winter
weather** attributable to the extratropical circulation response to SAI, on a
50-year timescale at ~0.5 °C residual cooling, **relative to a reference world
with the same global-mean temperature but neither elevated CO₂ nor SAI.**

To make this metric *quantifiable and reproducible* (the purpose of this
prototype), it is operationalised as the multi-model change, G6-1.5K-SAI minus
reference and G6-1.5K-HiLLA minus reference, in:

* **circulation indices** — the boreal-winter (DJF) station/EOF North Atlantic
  Oscillation index; the latitude and speed of the sub-polar/eddy-driven jet
  (zonal-mean and Atlantic-sector U at 850 hPa / 500 hPa); and the
  lower-stratospheric polar-vortex strength (zonal-mean U at 10 hPa, 60°N); and
* **surface extremes indices** — the ETCCDI cold/temperature-tail set most
  relevant to winter weather: frost days (FD), icing days (ID), coldest night
  (TNn) and day (TXn), cold nights (TN10p), the Cold Spell Duration Index
  (CSDI), and heavy-precipitation indices (Rx1day, Rx5day, R95p, CWD) over the
  Euro-Atlantic, Mediterranean, Northern-European and Eurasian sectors.

These indices are computed by the workflow in **Deliverable 1** and tabulated in
**Deliverable 2**, so any reader can reproduce or extend the assessment on the
Cloud Hub without downloading data.

> **Baseline caveat (Duffey & Irvine, 2024).** The response *attributed* to SAI
> depends on whether the reference is a transient-warming state or a
> quasi-equilibrium state at the same global-mean temperature. Because the metric
> specifies "the same global-mean temperature," the base period must be a
> **quasi-equilibrium reference at the target GMT (~1.5 K)**, not a transient SSP
> segment; otherwise part of the transient adjustment is mis-attributed to SAI.
> This choice is encoded in the workflow's data catalog and recorded in every
> output file.

---

## State of the evidence

### The physical mechanism is fairly well understood

For **equatorial** stratospheric sulfate injection (the older G6sulfur design),
the dynamical chain is well characterised and reproduced across models
(Jones et al., 2021; Bednarz et al., 2023a, b):

1. Sulfate aerosol absorbs near-IR and terrestrial longwave radiation, **heating
   the tropical lower stratosphere**.
2. Because there is no compensating polar heating in winter (polar night), this
   **strengthens the equator-to-pole lower-stratospheric temperature gradient**,
   which **strengthens the stratospheric polar vortex** (zonal-mean westerly
   anomaly of order +9 to +12 m s⁻¹ at 10 hPa, 60–70°N in the two models of
   Jones et al., 2021).
3. The strengthened vortex **couples downward** through wave–mean-flow
   interaction, increasing tropospheric westerlies north of ~50°N, especially
   over the North Atlantic.
4. This projects onto a **persistent positive North Atlantic Oscillation (NAO)**
   (deeper Icelandic low, stronger Azores high; NAO index shift of order +1 in
   both models), with the associated surface footprint: **wintertime warming over
   northern Eurasia, wetter Northern Europe, and a drier Mediterranean.**

Crucially, **idealised solar dimming (G6solar) does not reproduce this signal**:
the NAO/jet response appears only when the aerosol radiative physics — and the
lower-stratospheric heating in particular — are represented. This is the single
most important and robust qualitative result for this uncertainty: the
extratropical circulation response is a property of the *aerosol forcing*, not of
cooling per se, so it is **not captured by solar-constant or surrogate-forcing
experiments** and is **sensitive to the latitude and altitude of injection**.

### What the new G6-1.5K simulations add

The live entry predates the current GeoMIP ensemble. Two developments change the
evidence base:

* ***G6-1.5K-SAI uses hemispherically symmetric subtropical injection (30°N and
  30°S), not equatorial injection*** (Lee et al., 2026). Subtropical injection
  produces a different aerosol distribution and a less concentrated tropical
  lower-stratospheric heating than equatorial G6sulfur, so the *strength* of the
  vortex/NAO forcing in step 2 above is expected to differ — and is now testable
  in four models (CESM2-WACCM, MIROC-ES2H, UKESM1, E3SMv3). Lee et al. (2026)
  show the models already disagree on AOD per unit injection and on residual
  Arctic amplification, foreshadowing spread in the circulation response.
* ***G6-1.5K-HiLLA provides a designed contrast*** (Duffey et al., 2026):
  high-latitude (60°N/S), low-altitude (13–15 km), *seasonal* injection
  deliberately **reduces tropical stratospheric heating**. Mechanistically, HiLLA
  should therefore drive a **weaker tropically-forced vortex/NAO response** than
  tropical or subtropical injection, while introducing its own high-latitude and
  seasonal forcing. The SAI-vs-HiLLA contrast is thus a near-clean test of how
  much of the extratropical circulation response is mediated by tropical
  lower-stratospheric heating. HiLLA is available in three models (UKESM1,
  CESM2-WACCM, E3SMv3), enabling a first multi-model assessment.

Together these let us move the entry from "*mechanism known, magnitude
uncertain, single/two-model evidence*" toward a **quantified, multi-model,
strategy-resolved** statement.

### Sources of uncertainty and inter-model spread

* **Injection strategy is a first-order control.** Bednarz et al. (2022, 2023b)
  show the latitude of injection governs both hemispheres' annular-mode
  responses; the equatorial→subtropical→high-latitude progression spans a wide
  range of vortex forcing. This is the dominant *structural* uncertainty.
* **Inter-model differences in regional response** remain substantial,
  particularly over the continental USA and Africa (Jones et al., 2021), and in
  AOD-per-injection and residual amplification (Lee et al., 2026). Robust
  continental-scale conclusions require the full multi-model set — exactly what
  Deliverable 2 assembles.
* **Confounding ocean-driven circulation change.** SAI limits but does not
  eliminate AMOC weakening. Joshi & Zhang (2026) show that AMOC weakening alone
  drives a boreal-winter upper-troposphere/lower-stratosphere warming over the
  extratropical North Pacific via a tropical-Pacific-forced stationary wave. Such
  ocean-forced signals can **modulate or mask** the aerosol-forced jet/storm-track
  response and likely contribute to inter-model spread, since models differ in
  AMOC sensitivity. Attribution of the extratropical response to SAI should
  therefore account for differing baseline AMOC trajectories.
* **Internal variability.** NAO/jet indices have large interannual variance;
  gridpoint percentile-extreme indices are noisy in single realisations.
  Regional, area-weighted aggregation and multi-decadal means (the level at which
  Deliverable 2 reports) are the appropriate comparison scale.

---

## Decision relevance

Consequences include changes to **Northern Hemisphere mid-latitude winter surface
climate** — temperature and precipitation extremes over Europe and Eurasia
(Bednarz et al., 2023a) — and, via the Southern Annular Mode, **circulation-induced
effects on Antarctic ice shelves and grounded ice** (Bednarz et al., 2022;
Goddard et al., 2023; McCusker et al., 2015).

The decision-relevant point is that this response is **design-dependent**: because
equatorial, subtropical and high-latitude strategies force the extratropical
circulation differently, this uncertainty informs not just *whether* to deploy
SAI but *how* — i.e. the choice of injection latitude/altitude trades global
cooling efficiency (highest for tropical, high-altitude injection) against
regional circulation side-effects (potentially larger for the same strategies).
That coupling is why the proposed decision-relevance rating is raised toward
**Medium–High**.

---

## Resolvability — what would reduce this uncertainty

1. **A genuine multi-model assessment of G6-1.5K-SAI and -HiLLA** for the
   circulation and extremes metrics above — the core gap flagged by Jones et al.
   (2021) ("detailed modelling is needed") and now tractable because the data
   exist. *(This is the Track A project; Deliverables 1–2 build the reproducible
   pipeline and dataset; the circulation diagnostics follow.)*
2. **Mechanistic attribution** separating (a) tropical-stratospheric-heating-driven
   vortex/NAO forcing from (b) ocean-circulation (AMOC)-driven and (c) seasonal
   high-latitude forcing — using the SAI-vs-HiLLA contrast as the lever.
3. **Quantified inter-model spread** with consistent indices and baselines, so the
   *degree* of agreement (not just the ensemble mean) is reported.
4. **Sensitivity to injection latitude/altitude/seasonality** mapped across the
   available strategies, to make the design trade-off explicit.

None of these require new observing systems or decades of new simulation; they
require consistent, open, multi-model analysis of existing runs. Hence the
proposed shift of the resolvability scale toward **medium-term / research**.

---

## Quantification (this prototype)

This entry is linked to a reproducible analysis that runs on the Reflective Cloud
Hub:

* **Deliverable 1 — workflow** (`sai_extremes`): a tested, open-source package
  that computes the ETCCDI fixed and percentile-based extremes indices for
  G6-1.5K-SAI and G6-1.5K-HiLLA across the four models, via a pluggable I/O layer.
* **Deliverable 2 — dataset**: the multi-model indices dataset (CF-NetCDF) plus
  an analysis-ready table of regional, cos(lat)-weighted means, with a data card
  documenting methods, baseline choice, and provenance.

A future revision of this entry will replace the qualitative magnitude statements
above with the quantified multi-model signal and its spread, with the supporting
notebook embedded so any reader can verify or extend it.

---

## References

* Bednarz, E. M., Visioni, D., Kravitz, B., et al. (2022). *Impact of the Latitude
  of Stratospheric Aerosol Injection on the Southern Annular Mode.* GRL.
* Bednarz, E. M., et al. (2023a). *Climate response to off-equatorial stratospheric
  sulfur injections in three Earth system models — Part 2: Stratospheric and
  free-tropospheric response.* ACP.
* Bednarz, E. M., et al. (2023b). *Injection strategy — a driver of atmospheric
  circulation and ozone response to stratospheric aerosol geoengineering.* ACP.
* Duffey, A., & Irvine, P. J. (2024). *Accounting for transience in the baseline
  climate state changes the surface climate response attributed to stratospheric
  aerosol injection.* Environ. Res.: Climate 3, 041008.
* Duffey, A., Lee, W., Wheeler, L., et al. (2026). *The global climate response to
  High-Latitude Low-Altitude Stratospheric Aerosol Injection (HiLLA-SAI).* Earth
  Syst. Dynam. 17, 353–385. *(First multi-model HiLLA simulations: UKESM1,
  CESM2-WACCM, E3SMv3.)*
* Goddard, P. B., et al. (2023). *Stratospheric Aerosol Injection Can Reduce Risks
  to Antarctic Ice Loss Depending on Injection Location and Amount.*
* Jones, A., Haywood, J. M., et al. (2021). *North Atlantic Oscillation response in
  GeoMIP experiments G6solar and G6sulfur: why detailed modelling is needed for
  understanding regional implications of solar radiation management.* (UKESM1 &
  CESM2-WACCM.)
* Joshi, R., & Zhang, R. (2026). *Impact of the AMOC Weakening on Upper
  Troposphere/Lower Stratosphere Warming Over the Extratropical North Pacific.*
  GRL 53, e2026GL122116.
* Lee, W. R., Visioni, D., Wagman, B. M., et al. (2026). *G6-1.5K-SAI and G6sulfur:
  changes in impacts and uncertainty depending on stratospheric aerosol injection
  strategy in the Geoengineering Model Intercomparison Project.* ACP 26,
  7463–7483. *(Subtropical 30°N/30°S injection; four-model ensemble.)*
* McCusker, K. E., et al. (2015). *Inability of stratospheric sulfate aerosol
  injections to preserve the West Antarctic Ice Sheet.*

---

*Prepared as Deliverable 3, Track A (Mid-latitude extreme winter weather response
to SAI). Ratings and magnitude statements are provisional pending the
multi-model quantification in Deliverables 1–2 and the Weeks 7–8 circulation
diagnostics.*
