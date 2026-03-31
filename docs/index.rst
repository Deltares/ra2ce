Welcome to RA2CE's documentation!
===================================

.. raw:: html

   <div class="ra2ce-hero">
     <div class="ra2ce-hero-text">
       <div class="ra2ce-hero-tagline">Quantify resilience. <span class="ra2ce-hero-accent">Prioritise action.</span></div>
       <p class="ra2ce-hero-sub">
         RA2CE (<em>just say race!</em>) is a Python toolkit by <strong>Deltares</strong> for assessing the resilience
         of critical infrastructure networks — from hazard exposure to economic risk and adaptation planning.
       </p>
       <div class="ra2ce-hero-actions">
         <a class="ra2ce-btn ra2ce-btn-primary" href="getting_started/index.html">🚀 Get Started</a>
         <a class="ra2ce-btn ra2ce-btn-secondary" href="tutorials/index.html">📓 Tutorials</a>
         <a class="ra2ce-btn ra2ce-btn-outline" href="https://github.com/Deltares/ra2ce" target="_blank">⭐ GitHub</a>
       </div>
     </div>
   </div>

This is the documentation of ``ra2ce`` — the **Resilience Assessment and Adaptation for Critical
infrastructurE** Toolkit, developed by `Deltares <https://www.deltares.nl/en/>`_.
RA2CE helps to quantify resilience of critical infrastructure networks, prioritize
interventions and adaptation measures, and select the most appropriate action perspective
to increase resilience considering future conditions.

.. raw:: html

   <div class="ra2ce-feature-row">
     <div class="ra2ce-feature-cell">
       <div class="ra2ce-feature-icon">🌊</div>
       <div class="ra2ce-feature-title">Assess hazard exposure</div>
       <div class="ra2ce-feature-text">Overlay flood depths and other hazard maps onto road networks to identify exposed segments across return periods.</div>
     </div>
     <div class="ra2ce-feature-cell">
       <div class="ra2ce-feature-icon">🔗</div>
       <div class="ra2ce-feature-title">Quantify criticality</div>
       <div class="ra2ce-feature-text">Identify critical links, measure redundancy, and compute detour costs under single- or multi-link failure scenarios.</div>
     </div>
     <div class="ra2ce-feature-cell">
       <div class="ra2ce-feature-icon">💰</div>
       <div class="ra2ce-feature-title">Estimate economic risk</div>
       <div class="ra2ce-feature-text">Compute direct damages (EAD) and indirect economic losses (EAL), and compare adaptation strategies side-by-side.</div>
     </div>
   </div>

.. admonition:: 💡 New to RA2CE?

   Start with the :doc:`getting_started/index` guide, then work through the :doc:`tutorials/index`
   to run your first analysis step-by-step using Jupyter Notebooks.

Navigate directly to a section
--------------------------------

.. grid:: 4
   :gutter: 2

   .. grid-item-card:: Getting Started
      :link: getting_started/index
      :link-type: doc
      :text-align: center

      :octicon:`rocket;2.5em`

      Installation, environment setup, and your first run.

   .. grid-item-card:: Showcases
      :link: showcases/index
      :link-type: doc
      :text-align: center

      :octicon:`globe;2.5em`

      Real-world case studies from Myanmar and beyond.

   .. grid-item-card:: Tutorials
      :link: tutorials/index
      :link-type: doc
      :text-align: center

      :octicon:`book;2.5em`

      Step-by-step notebooks for every analysis module.

   .. grid-item-card:: API Reference
      :link: api/index
      :link-type: doc
      :text-align: center

      :octicon:`list-unordered;2.5em`

      Full docstrings for all classes and functions.

   .. grid-item-card:: Technical Docs
      :link: technical_documentation/technical_documentation
      :link-type: doc
      :text-align: center

      :octicon:`tools;2.5em`

      Architecture, data models, and implementation details.

   .. grid-item-card:: Publications
      :link: publications
      :link-type: ref
      :text-align: center

      :octicon:`mortar-board;2.5em`

      Peer-reviewed papers using or describing RA2CE.

   .. grid-item-card:: FAQ
      :link: faq
      :link-type: ref
      :text-align: center

      :octicon:`question;2.5em`

      Frequently asked questions and troubleshooting tips.

Lost? Try the :ref:`search`.

.. toctree::
   :caption: Table of Contents
   :maxdepth: 1
   :titlesonly:
   :hidden:

   getting_started/index.rst
   showcases/index.rst
   tutorials/index.rst
   api/index.rst
   technical_documentation/technical_documentation.rst