Losses Analysis
===============

🚧 What happens when infrastructure is disrupted by hazards?
------------------------------------------------------------

The **Losses module** in RA2CE estimates the **economic (indirect) losses** caused
by service disruptions to infrastructure during hazard events.

While the :doc:`Damages module <damages>` answers *“How much does it cost to repair my infrastructure?”*,
the **Losses module** answers *“What is the economic impact when my infrastructure cannot function?”*.

This includes, for example:

- Extra travel time due to blocked or slowed road segments.
- Detour and rerouting costs.
- Productivity and accessibility losses.
- Wider socio-economic impacts of reduced service levels.



----

Types of Loss Analysis
-----------------------

RA2CE currently supports only one type of losses workflow:

- :doc:`Criticiality based losses <losses.multi_link_redundancy_losses>`
  This is the economic losses due to disruption of road segments, based on the criticality of each link in the network (see details in the :doc:`Criticality analysis <criticality>`).


----


Direct vs Indirect Impacts
---------------------------

RA2CE distinguishes between **damages** and **losses**:

+--------------------------+------------------------------------------------+
| **Damages**              | **Losses**                                     |
+==========================+================================================+
| Physical repair/rebuild  | Economic cost of disruption                    |
| costs (in €)             | (in €)                                         |
+--------------------------+------------------------------------------------+
| Based on *damage curves* | Based on *loss functions* and Value of Time    |
+--------------------------+------------------------------------------------+
| Example: *Cost to repair | Example: *Extra cost from 1h travel delay for  |
| a flooded bridge*        | 10,000 commuters*                              |
+--------------------------+------------------------------------------------+

Both are essential in **risk assessment**:
- *Damages* reflect how much money is needed to repair/replace assets.
- *Losses* reflect the broader economic cost of losing access to those assets.


Where to Start
--------------

The following tutorials guide you through different parts of the losses workflow:

.. toctree::
   :maxdepth: 1

   losses.multi_link_redundancy_losses

