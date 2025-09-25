Damages Analysis
================

💥 What happens to infrastructure when a hazard strikes?
--------------------------------------------------------

The **Damages module** in RA2CE estimates the physical (direct) damage to infrastructure
caused by natural hazards such as floods, cyclones, or earthquakes.
This provides a critical step in risk assessment: quantifying how exposed assets
will be affected when hazard intensities exceed certain thresholds.

Two main types of questions can be addressed:

- *Event-based damages* – *What is the expected physical damage to my infrastructure for a specific hazard event?*
- *Risk-based damages* – *What is the **Expected Annual Damage (EAD)** to my infrastructure, based on hazard probability distributions?*

RA2CE supports both workflows through a combination of **damage curves** and
**hazard layers**.

----

How RA2CE Calculates Damage
----------------------------

The basic workflow for calculating physical damage is:

1. **Hazard input** – A spatial layer (e.g., flood depth, wind speed, PGA) is provided
   for a specific event or set of events.
2. **Asset data** – Infrastructure elements (e.g., roads, buildings, facilities) are
   represented as network components or spatial layers.
3. **Damage curves** – Functions that map hazard intensity to expected damage
   (from 0% = no damage to 100% = full destruction).
4. **Overlay and calculation** – For each asset, RA2CE looks up the hazard intensity,
   applies the appropriate damage curve, and computes the damage fraction and cost.
5. **Aggregation** – Results can be summarized per asset, per category, or across
   the entire network. Risk-based analyses additionally integrate across probability
   distributions to compute **EAD**.

----

Types of Damage Curves
-----------------------

RA2CE offers several ways to represent the hazard–damage relationship:

- :doc:`Reference damage curves <damages.reference_damage_curves>`
  Built-in functions from literature or past studies.
  *Examples: Huizinga global flood curves (HZ), OSdaMage European functions (OSD).*

- :doc:`Manual damage curves <damages.manual_damage_curves>`
  User-defined curves tailored to site-specific infrastructure, historical data,
  or alternative vulnerability scenarios.

Which option to choose?

- **Reference curves** – Fast and consistent for large-scale or exploratory analysis.
- **Manual curves** – Essential when local calibration or specific engineering detail is available.

----

Expected Annual Damage (EAD)
-----------------------------

While single-event damages are valuable, decision-making often requires a **risk perspective**.
RA2CE therefore supports the computation of
:doc:`Expected Annual Damage (EAD) <damages.EAD>`:

- Hazard scenarios are combined with their **annual exceedance probabilities (AEP)**.
- Damages across events are aggregated to obtain the long-term average expected damage.
- EAD provides a measure of *risk* that can be compared across assets, regions,
  or investment strategies.

This is especially useful for cost–benefit analyses, adaptation planning,
and prioritizing investments in resilience.

----

Where to Start
--------------

The following tutorials guide you through different parts of the damages workflow:

.. toctree::
   :maxdepth: 1

   damages.reference_damage_curves
   damages.manual_damage_curves
   damages.EAD
