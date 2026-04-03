Welcome to RA2CE's documentation!
===================================

.. raw:: html

   <div class="ra2ce-hero">
     <div class="ra2ce-hero-text">
       <div class="ra2ce-hero-tagline">Resilience Assessment and Adaptation for <span class="ra2ce-hero-accent">Critical infrastructurE</span></div>
       <p class="ra2ce-hero-sub">
         Quantify network vulnerability, prioritize interventions, and support adaptation decisions.
         For transport infrastructure exposed to natural hazards and future climate conditions.
         Built by <strong>Deltares</strong>.
       </p>
       <div class="ra2ce-hero-actions">
         <a class="ra2ce-btn ra2ce-btn-primary" href="getting_started/index.html">🚀 Get Started</a>
         <a class="ra2ce-btn ra2ce-btn-secondary" href="tutorials/index.html">📓 Browse tutorials</a>
         <a class="ra2ce-btn ra2ce-btn-outline" href="https://github.com/Deltares/ra2ce" target="_blank">⭐ GitHub</a>
       </div>
     </div>
   </div>

.. raw:: html

   <div class="ra2ce-feature-row">
     <div class="ra2ce-feature-cell">
       <div class="ra2ce-feature-icon">🌊</div>
       <div class="ra2ce-feature-title">Assess hazard exposure</div>
       <div class="ra2ce-feature-text">Overlay flood depths and other hazard maps onto networks to identify exposed segments across return periods.</div>
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

Who uses RA2CE
--------------

.. raw:: html

   <div class="ra2ce-audience-grid">
     <a class="ra2ce-aud-card" href="tutorials/index.html">
       <div class="ra2ce-aud-icon">📐</div>
       <div class="ra2ce-aud-title">Consultants</div>
       <div class="ra2ce-aud-desc">Run flood impact analyses and generate risk metrics for infrastructure projects. Plug RA2CE into your workflow without proprietary tooling or licensing costs.</div>
       <div class="ra2ce-aud-cta">Start with the tutorials →</div>
     </a>
     <a class="ra2ce-aud-card" href="api/index.html">
       <div class="ra2ce-aud-icon">🔬</div>
       <div class="ra2ce-aud-title">Researchers</div>
       <div class="ra2ce-aud-desc">Extend the methodology, integrate custom damage curves, and contribute back. Full API reference and modular architecture included alongside peer-reviewed publications.</div>
       <div class="ra2ce-aud-cta">Browse the API reference →</div>
     </a>
     <a class="ra2ce-aud-card" href="showcases/index.html">
       <div class="ra2ce-aud-icon">🏛️</div>
       <div class="ra2ce-aud-title">Decision makers</div>
       <div class="ra2ce-aud-desc">Review real case studies with interpretable outputs before asking your team to adopt the tool. Understand what RA2CE produces and what data inputs it needs.</div>
       <div class="ra2ce-aud-cta">View showcases →</div>
     </a>
   </div>

Typical analysis workflow
--------------------------

Each module builds on the previous. Network and Hazard are required foundations;
the analysis modules can be combined depending on your objectives.

.. raw:: html

   <div class="ra2ce-workflow">
     <div class="ra2ce-wf-step">
       <div class="ra2ce-wf-num">01</div>
       <div class="ra2ce-wf-icon">🗺️</div>
       <div class="ra2ce-wf-title">Network</div>
       <div class="ra2ce-wf-sub">OSM or shapefile</div>
     </div>
     <div class="ra2ce-wf-step">
       <div class="ra2ce-wf-num">02</div>
       <div class="ra2ce-wf-icon">🌊</div>
       <div class="ra2ce-wf-title">Hazard</div>
       <div class="ra2ce-wf-sub">Overlay raster data</div>
     </div>
     <div class="ra2ce-wf-step">
       <div class="ra2ce-wf-num">03</div>
       <div class="ra2ce-wf-icon">🔗</div>
       <div class="ra2ce-wf-title">Criticality</div>
       <div class="ra2ce-wf-sub">Redundancy &amp; detours</div>
     </div>
     <div class="ra2ce-wf-step">
       <div class="ra2ce-wf-num">04</div>
       <div class="ra2ce-wf-icon">💰</div>
       <div class="ra2ce-wf-title">Damages / Losses</div>
       <div class="ra2ce-wf-sub">EAD &amp; EAL metrics</div>
     </div>
     <div class="ra2ce-wf-step">
       <div class="ra2ce-wf-num">05</div>
       <div class="ra2ce-wf-icon">🛡️</div>
       <div class="ra2ce-wf-title">Adaptation</div>
       <div class="ra2ce-wf-sub">Compare strategies</div>
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

      Real-world case studies.

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
   webinars/index.rst
   tutorials/index.rst
   api/index.rst
   technical_documentation/technical_documentation.rst