.. _tutorials_index:

Tutorials
=========

.. _tutorials_index:

Tutorials
=========

.. raw:: html

   <!-- Widen this page: hide right-hand "On this page" sidebar -->
   <style>
   .bd-sidebar-secondary { display: none !important; }
   </style>

   <p style="font-size:1.05rem;margin:0 0 8px;max-width:820px;line-height:1.7;">
     Whether you are estimating flood damage costs, checking whether roads stay connected during a
     disaster, or identifying the most cost-effective adaptation investment — start from the
     framework diagram below. Each box is clickable. The arrows show how module outputs feed into
     the next step; a dashed arrow indicates an optional dependency.
   </p>

   <!-- ============================================================
        RA2CE FRAMEWORK DIAGRAM  (corrected DAG)
        ============================================================ -->
   <svg viewBox="0 0 700 380" xmlns="http://www.w3.org/2000/svg"
        role="img" aria-label="RA2CE modelling framework diagram"
        style="max-width:100%;height:auto;display:block;margin:16px 0 32px;
               font-family:system-ui,sans-serif;">
     <style>
       .fc-node rect  { transition:filter .15s; }
       .fc-node:hover rect { filter:brightness(1.2); cursor:pointer; }
       .fc-node text  { pointer-events:none; user-select:none; }
     </style>
     <defs>
       <!-- solid arrowhead -->
       <marker id="arr-s" viewBox="0 0 10 10" refX="9" refY="5"
               markerWidth="6" markerHeight="6" orient="auto">
         <path d="M0 1.5 L9 5 L0 8.5z" fill="#9aabb8"/>
       </marker>
       <!-- dashed arrowhead (same shape, different colour) -->
       <marker id="arr-d" viewBox="0 0 10 10" refX="9" refY="5"
               markerWidth="6" markerHeight="6" orient="auto">
         <path d="M0 1.5 L9 5 L0 8.5z" fill="#b0c4ce"/>
       </marker>
     </defs>

     <!-- ── solid edges ─────────────────────────────────────────── -->
     <g stroke="#9aabb8" stroke-width="1.8" fill="none" marker-end="url(#arr-s)">
       <!-- Network → Hazard -->
       <path d="M 280 48 C 280 80, 100 78, 100 108"/>
       <!-- Network → Criticality -->
       <path d="M 350 48 C 350 78, 460 78, 460 108"/>
       <!-- Hazard → Damages -->
       <line x1="100" y1="146" x2="100" y2="208"/>
       <!-- Criticality → Losses -->
       <line x1="460" y1="146" x2="460" y2="208"/>
       <!-- Damages → Annual EAD/EAL -->
       <path d="M 135 246 C 135 285, 290 285, 295 298"/>
       <!-- Losses → Annual EAD/EAL -->
       <path d="M 425 246 C 425 285, 380 285, 365 298"/>
       <!-- Annual → Prioritisation → Adaptation -->
       <line x1="330" y1="336" x2="330" y2="358"/>
     </g>

     <!-- ── dashed edges (optional inputs) ────────────────────────── -->
     <g stroke="#b0c4ce" stroke-width="1.6" stroke-dasharray="5,3"
        fill="none" marker-end="url(#arr-d)">
       <!-- Hazard → Criticality  (optional: hazard can inform criticality) -->
       <path d="M 165 124 C 220 110, 330 110, 390 118"/>
     </g>

     <!-- ── NODES ──────────────────────────────────────────────────── -->

     <!-- 1. Network -->
     <a href="network.html">
       <g class="fc-node">
         <rect x="230" y="10" width="140" height="38" rx="7" fill="#4a6fa5"/>
         <text x="300" y="34" fill="#fff" text-anchor="middle"
               font-size="13" font-weight="600">1 · Network</text>
       </g>
     </a>

     <!-- 2. Hazard (Network Exposure) -->
     <a href="hazard.html">
       <g class="fc-node">
         <rect x="25" y="108" width="150" height="38" rx="7" fill="#0072b2"/>
         <text x="100" y="125" fill="#fff" text-anchor="middle"
               font-size="11" font-weight="600">2 · Network Exposure</text>
         <text x="100" y="139" fill="#dde" text-anchor="middle"
               font-size="10">(Hazard)</text>
       </g>
     </a>

     <!-- 4. Criticality -->
     <a href="criticality.html">
       <g class="fc-node">
         <rect x="385" y="108" width="160" height="38" rx="7" fill="#d55e00"/>
         <text x="465" y="125" fill="#fff" text-anchor="middle"
               font-size="11" font-weight="600">4 · Network Criticality</text>
         <text x="465" y="139" fill="#ffe" text-anchor="middle"
               font-size="10">(connectivity &amp; detour)</text>
       </g>
     </a>

     <!-- 3. Damages -->
     <a href="damages.html">
       <g class="fc-node">
         <rect x="25" y="208" width="150" height="38" rx="7" fill="#cc3333"/>
         <text x="100" y="225" fill="#fff" text-anchor="middle"
               font-size="11" font-weight="600">3 · Damages ($)</text>
         <text x="100" y="239" fill="#fee" text-anchor="middle"
               font-size="10">(physical repair cost)</text>
       </g>
     </a>

     <!-- 5. Losses -->
     <a href="losses.html">
       <g class="fc-node">
         <rect x="385" y="208" width="160" height="38" rx="7" fill="#8b2fc9"/>
         <text x="465" y="225" fill="#fff" text-anchor="middle"
               font-size="11" font-weight="600">5 · Losses ($ / pax)</text>
         <text x="465" y="239" fill="#ede" text-anchor="middle"
               font-size="10">(indirect economic loss)</text>
       </g>
     </a>

     <!-- 6. Annual Expected EAD + EAL -->
     <rect x="220" y="298" width="220" height="38" rx="7"
           fill="none" stroke="#9aabb8" stroke-width="1.5" stroke-dasharray="4,3"/>
     <text x="330" y="315" fill="#555" text-anchor="middle"
           font-size="11" font-weight="600">6 · Annual Expected</text>
     <text x="330" y="329" fill="#555" text-anchor="middle"
           font-size="10">Damages &amp; Losses (EAD / EAL)</text>

     <!-- 7/8. Prioritisation + Adaptation -->
     <a href="adaptation.html">
       <g class="fc-node">
         <rect x="220" y="358" width="220" height="38" rx="7" fill="#0b6b3a"/>
         <text x="330" y="375" fill="#fff" text-anchor="middle"
               font-size="11" font-weight="600">7 · Prioritisation /</text>
         <text x="330" y="389" fill="#cec" text-anchor="middle"
               font-size="10">8 · Adaptation Measures</text>
       </g>
     </a>

     <!-- Accessibility (side, linked from Criticality path) -->
     <a href="accessibility.html">
       <g class="fc-node">
         <rect x="565" y="208" width="130" height="38" rx="7" fill="#009e73"/>
         <text x="630" y="225" fill="#fff" text-anchor="middle"
               font-size="11" font-weight="600">Accessibility</text>
         <text x="630" y="239" fill="#dfd" text-anchor="middle"
               font-size="10">(services reachable?)</text>
       </g>
     </a>
     <!-- Criticality → Accessibility dashed -->
     <g stroke="#b0c4ce" stroke-width="1.4" stroke-dasharray="4,3"
        fill="none" marker-end="url(#arr-d)">
       <line x1="545" y1="127" x2="630" y2="208"/>
     </g>

     <!-- Equity -->
     <a href="equity.html">
       <g class="fc-node">
         <rect x="565" y="298" width="130" height="38" rx="7" fill="#c87000"/>
         <text x="630" y="315" fill="#fff" text-anchor="middle"
               font-size="11" font-weight="600">Equity</text>
         <text x="630" y="329" fill="#ffe" text-anchor="middle"
               font-size="10">(distributional impact)</text>
       </g>
     </a>
     <!-- Accessibility → Equity -->
     <g stroke="#9aabb8" stroke-width="1.5" fill="none" marker-end="url(#arr-s)">
       <line x1="630" y1="246" x2="630" y2="298"/>
     </g>

     <!-- Legend -->
     <g font-size="10" fill="#9aabb8">
       <line x1="230" y1="410" x2="270" y2="410" stroke="#9aabb8"
             stroke-width="1.6" marker-end="url(#arr-s)"/>
       <text x="275" y="414">required input</text>
       <line x1="370" y1="410" x2="410" y2="410" stroke="#b0c4ce"
             stroke-width="1.4" stroke-dasharray="5,3" marker-end="url(#arr-d)"/>
       <text x="415" y="414">optional input</text>
       <text x="330" y="432" text-anchor="middle">Click any module to jump to its tutorial</text>
     </g>
   </svg>



Prerequisite: build your network
---------------------------------

Before any analysis, you need a network. RA2CE can create one from OpenStreetMap
or import a shapefile you already have.

.. grid:: 1
   :gutter: 3

   .. grid-item-card::
      :link: network
      :link-type: doc
      :class-card: ra2ce-card-network

      🗺 **Network** — *"Do I have a usable road network?"*
      ^^^
      .. raw:: html

         <ul class="ra2ce-q-list">
           <li>How do I create a road network from OpenStreetMap?</li>
           <li>How do I import a pre-defined shapefile network?</li>
           <li>How do I clean and prepare my network for analysis?</li>
         </ul>

What is exposed, and how does the network perform?
---------------------------------------------------

Once you have a network, overlay hazard data and evaluate how the network responds
to disruption — both in terms of connectivity and in terms of people's ability to
reach key services.

.. grid:: 2
   :gutter: 3

   .. grid-item-card::
      :link: hazard
      :link-type: doc
      :class-card: ra2ce-card-hazard

      🌊 **Hazard** — *"Where is my network exposed?"*
      ^^^
      .. raw:: html

         <ul class="ra2ce-q-list">
           <li>What flood depth is expected at each road segment?</li>
           <li>How do I overlay a hazard map onto my network?</li>
           <li>Which links are inundated during a 1-in-100-year event?</li>
         </ul>

   .. grid-item-card::
      :link: criticality
      :link-type: doc
      :class-card: ra2ce-card-criticality

      🔗 **Criticality** — *"Does my network stay connected?"*
      ^^^
      .. raw:: html

         <ul class="ra2ce-q-list">
           <li>Are there alternative routes when a road fails?</li>
           <li>What is the detour distance or time during a disaster?</li>
           <li>Which road segments are critical with no redundancy?</li>
         </ul>

      .. note::
         Hazard data is an optional input to criticality analysis — you can assess
         structural redundancy with or without a hazard scenario.

   .. grid-item-card::
      :link: accessibility
      :link-type: doc
      :class-card: ra2ce-card-accessibility

      🧭 **Accessibility** — *"Can people still reach what they need?"*
      ^^^
      .. raw:: html

         <ul class="ra2ce-q-list">
           <li>What is the shortest evacuation route in emergency conditions?</li>
           <li>Are hospitals, shelters, and schools still reachable during a disaster?</li>
           <li>Which communities become isolated when roads are flooded?</li>
         </ul>

What are the economic consequences?
-------------------------------------

Translate physical exposure and connectivity loss into monetary terms — at the
event scale or as annualised risk.

.. grid:: 2
   :gutter: 3

   .. grid-item-card::
      :link: damages
      :link-type: doc
      :class-card: ra2ce-card-damages

      💥 **Damages** — *"What will it cost to repair?"*
      ^^^
      .. raw:: html

         <ul class="ra2ce-q-list">
           <li>What is the expected <strong>physical repair cost</strong> for a flood event?</li>
           <li>What is the <strong>Expected Annual Damage (EAD)</strong>?</li>
           <li>How do I apply damage curves (Huizinga / OSDaMage / custom)?</li>
         </ul>

   .. grid-item-card::
      :link: losses
      :link-type: doc
      :class-card: ra2ce-card-losses

      📉 **Losses** — *"What do disruptions cost users and the economy?"*
      ^^^
      .. raw:: html

         <ul class="ra2ce-q-list">
           <li>What are the <strong>indirect economic losses</strong> from network disruption?</li>
           <li>What is the <strong>Expected Annual Loss (EAL)</strong>?</li>
           <li>What are the detour and time costs for affected users?</li>
         </ul>

What should be done — and for whom?
--------------------------------------

Use risk results to compare adaptation options and understand how the burden of
disruption is distributed across different groups.

.. grid:: 2
   :gutter: 3

   .. grid-item-card::
      :link: adaptation
      :link-type: doc
      :class-card: ra2ce-card-adaptation

      🛡 **Adaptation** — *"Where should I invest to reduce risk?"*
      ^^^
      .. raw:: html

         <ul class="ra2ce-q-list">
           <li>Which adaptation measures reduce EAD and EAL the most?</li>
           <li>How do I compare cost-effectiveness of different interventions?</li>
           <li>How does risk change under future climate or growth scenarios?</li>
         </ul>

   .. grid-item-card::
      :link: equity
      :link-type: doc
      :class-card: ra2ce-card-equity

      ⚖️ **Equity** — *"Who bears the greatest burden?"*
      ^^^
      .. raw:: html

         <ul class="ra2ce-q-list">
           <li>Are vulnerable or low-income populations disproportionately affected?</li>
           <li>Which communities lose access to services during a disaster?</li>
           <li>How can adaptation investments address distributional impacts?</li>
         </ul>

.. toctree::
   :hidden:
   :maxdepth: 1

   network
   hazard
   criticality
   accessibility
   damages
   losses
   adaptation
   equity

