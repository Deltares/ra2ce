Criticality Analysis
====================

🚦 What happens when roads get blocked?
---------------------------------------

If a key road in your network is suddenly closed because of flooding or road maintenance, can traffic still flow? Which routes are most important for keeping the network connected?

This is what criticality analysis in RA2CE is all about. It helps you:

- Find out if detours exist when a road is blocked
- Compare how much longer the detour takes (distance or time)
- Spot the roads that have no backup routes at all


.. note::

   Criticality analysis is about **resilience**. By simulating disruptions,
   you can identify weak spots in the network and prepare for emergencies.

You can explore this in two ways:

1. **One road blocked at a time** (single-road analysis)
2. **Multiple roads blocked together** (multi-road analysis, e.g. a flood scenario)

Case 1: What if one road is blocked?
------------------------------------

The **single link redundancy** analysis provides insight into the criticality of each individual link in the network.
For each link, the analysis identifies the best existing alternative route in case that link is disrupted.
If no alternative exists, the analysis highlights the lack of redundancy for that link.

This process is performed sequentially for each network link, and the results indicate the degree of redundancy
and potential impact if a specific segment becomes unavailable.


You can learn more and follow the step-by-step instructions in the :doc:`single link redundancy tutorial <../_examples/criticality_single_link_redundancy>`.


Case 1: One Road Blocked
------------------------

When a single road (or *link*) is disrupted, RA2CE checks whether
there is a **backup route** available.

For each road, the analysis:

- Identifies the best detour
- Calculates the extra distance or time compared to the original route
- Highlights roads without alternatives

.. note::

   This is called a *single-link redundancy analysis*,
   but you can think of it simply as:
   *"What if this one road is blocked, can I still get through?"*

👉 Learn how to do this step by step in the
:doc:`single link redundancy tutorial <../_examples/criticality_single_link_redundancy>`.

----





Case 2: Several Roads Blocked
-----------------------------

Sometimes multiple roads are affected at the same time such as during a flood
or when a hazard map highlights consecutive vulnerable segments.

In this case, RA2CE performs a **multi-road analysis**:

- For each blocked road, it looks for the best detour
- It calculates how much longer the trip becomes
- It flags areas that are completely cut off

.. note::

   This is called a *multi-link redundancy analysis*,
   but you can think of it simply as:
   *"What if this a whole area is blocked, can I still get through?"*

.. tip::

   You can define a **disruption threshold**.
   For example: in a flood map, you may choose to ignore water depths
   below 0.5 m, and only consider roads with higher depths as blocked.

👉 Try this yourself in the
:doc:`multi link redundancy tutorial <../_examples/criticality_multi_link_redundancy>`.
:doc:`asdfghj <../_examples/network_from_shapefile>`.


----

Why It Matters
--------------

Understanding criticality helps you:

- Plan for disasters (floods, landslides, accidents)
- Design more resilient transport networks
- Prioritize maintenance for the most vulnerable roads


.. toctree::
   :maxdepth: 1

   ../_examples/criticality_single_link_redundancy
   ../_examples/criticality_multi_link_redundancy
