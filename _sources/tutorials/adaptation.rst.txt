Adaptation Analysis
===================

💡 Which road interventions are worth the investment?
------------------------------------------------------

When a road network is repeatedly exposed to flood events, it is not enough to
know *how much damage* occurs. Decision-makers also need to know *whether an
intervention is cost-effective*. The **Adaptation module** in RA2CE answers this
question by comparing one or more adaptation options against a business-as-usual
reference using a **Cost-Benefit Analysis (CBA)**.

----

What is a Cost-Benefit Analysis?
---------------------------------

A CBA compares the total expected costs of an intervention against the total
expected benefits, both expressed in present-day monetary value.

In the context of road network adaptation:

- **Costs** — discounted construction and maintenance expenditures, expressed per
  metre of road.
- **Benefits** — discounted avoided damages: the reduction in flood damage compared
  to the reference (no-adaptation) scenario, accumulated over the analysis time
  horizon.

The key output metric is the **Benefit-Cost Ratio (BCR)**:

.. math::

   \text{BCR} = \frac{\text{Total discounted benefits}}{\text{Total discounted costs}}

- **BCR > 1** — the intervention pays off: avoided damages exceed its costs.
- **BCR < 1** — the intervention costs more than it saves.
- **BCR = 1** — break-even point.

Future costs and benefits are discounted back to present value using a
user-supplied discount rate, and the increasing likelihood of events under
climate change is captured via an annual climate factor.

----

How RA2CE Runs an Adaptation Analysis
--------------------------------------

The analysis follows four steps:

1. **Build the network** and overlay it with a single-event hazard raster (e.g. a
   flood depth map). The hazard file must *not* use a return-period prefix (``RP``),
   as that triggers the separate risk-based damages workflow.
2. **Configure damages** — choose a manual damage curve (``DamageCurveEnum.MAN``)
   that maps flood depth to road damage fraction.  This curve is defined
   independently for each adaptation option, allowing the reduced vulnerability
   of the adapted surface to be captured directly.
3. **Define adaptation options** — each option gets its own folder of input files
   under ``input/<option_id>/``.  The first option (``AO0``) is always the
   reference case; subsequent options represent the interventions being evaluated.
4. **Inspect results** — the output GeoPackage contains one row per road segment
   with benefit, cost, and BCR columns for every non-reference adaptation option.

👉 Follow the complete step-by-step example in the :doc:`adaptation tutorial notebook <../_examples/adaptation>`.

.. note::

   The adaptation module currently requires an **event-based** setup (single
   hazard map).  Risk-based adaptation across multiple return periods is not yet
   supported.

----

.. toctree::
   :maxdepth: 1

   ../_examples/adaptation
