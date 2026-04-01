.. _tutorials_index:

Tutorials
=========

.. raw:: html

   <style>
   .bd-sidebar-secondary { display: none !important; }
   </style>

Step-by-step worked examples for every RA2CE module. Find the question you're trying to
answer, pick the right analysis, and follow an executable notebook to results.

.. note::

   **First time here?** :doc:`../getting_started/index` covers installation and the required
   folder structure. Come back once your environment is ready.

.. raw:: html

   <!-- ── FOUNDATION ────────────────────────────────────── -->
   <div class="ra2ce-sec-head">
     <h2>Foundation</h2>
     <span class="ra2ce-sec-badge ra2ce-sec-badge-req">Required for all analyses</span>
   </div>

   <div class="ra2ce-foundation-grid">

     <!-- Network -->
     <a href="network.html" class="ra2ce-feat-card">
       <div class="ra2ce-feat-card-inner">
       <div class="ra2ce-feat-visual ra2ce-feat-visual-net">
         <svg width="220" height="120" viewBox="0 0 220 120" style="display:block">
           <circle cx="35" cy="60" r="8" fill="#1D9E75" stroke="white" stroke-width="2"/>
           <circle cx="95" cy="30" r="8" fill="#1D9E75" stroke="white" stroke-width="2"/>
           <circle cx="95" cy="90" r="8" fill="#1D9E75" stroke="white" stroke-width="2"/>
           <circle cx="165" cy="60" r="8" fill="#1D9E75" stroke="white" stroke-width="2"/>
           <circle cx="58" cy="85" r="5" fill="#5DCAA5" stroke="white" stroke-width="1.5"/>
           <circle cx="130" cy="42" r="5" fill="#5DCAA5" stroke="white" stroke-width="1.5"/>
           <line x1="35" y1="60" x2="95" y2="30" stroke="#9FE1CB" stroke-width="2.5"/>
           <line x1="35" y1="60" x2="58" y2="85" stroke="#9FE1CB" stroke-width="2"/>
           <line x1="58" y1="85" x2="95" y2="90" stroke="#9FE1CB" stroke-width="2"/>
           <line x1="95" y1="30" x2="130" y2="42" stroke="#9FE1CB" stroke-width="2"/>
           <line x1="130" y1="42" x2="165" y2="60" stroke="#9FE1CB" stroke-width="2.5"/>
           <line x1="95" y1="90" x2="165" y2="60" stroke="#9FE1CB" stroke-width="2.5"/>
           <line x1="95" y1="30" x2="95" y2="90" stroke="#9FE1CB" stroke-width="1.5" stroke-dasharray="4 2"/>
           <text x="190" y="28" font-size="9" fill="#0F6E56" font-family="system-ui,sans-serif" font-weight="600">OSM</text>
           <text x="185" y="40" font-size="8" fill="#1D9E75" font-family="system-ui,sans-serif">import</text>
           <text x="185" y="78" font-size="9" fill="#0F6E56" font-family="system-ui,sans-serif" font-weight="600">.shp</text>
           <text x="180" y="90" font-size="8" fill="#1D9E75" font-family="system-ui,sans-serif">shapefile</text>
         </svg>
       </div>
       <div class="ra2ce-feat-body">
         <div class="ra2ce-feat-cat ra2ce-feat-cat-net">
           Network <span class="ra2ce-feat-step">step 01</span>
         </div>
         <div class="ra2ce-feat-title">Build your network</div>
         <div class="ra2ce-feat-desc">Import or download a graph representation of your transport network. All subsequent analyses depend on this foundation step.</div>
         <div class="ra2ce-feat-notebooks">
           <span class="ra2ce-feat-nb">
             <span class="ra2ce-feat-nb-dot ra2ce-feat-nb-dot-net"></span>
             Network from OSM download
             <span class="ra2ce-feat-nb-arr">→</span>
           </span>
           <span class="ra2ce-feat-nb">
             <span class="ra2ce-feat-nb-dot ra2ce-feat-nb-dot-net"></span>
             Network from shapefile
             <span class="ra2ce-feat-nb-arr">→</span>
           </span>
         </div>
       </div>
       </div><!-- /feat-card-inner -->
     </a>


     <!-- Hazard -->
     <a href="hazard.html" class="ra2ce-feat-card">
       <div class="ra2ce-feat-card-inner">
       <div class="ra2ce-feat-visual ra2ce-feat-visual-haz">
         <svg width="220" height="120" viewBox="0 0 220 120" style="display:block">
           <defs>
             <linearGradient id="depthGrad" x1="0" y1="0" x2="0" y2="1">
               <stop offset="0%" stop-color="#042C53"/>
               <stop offset="100%" stop-color="#E6F1FB"/>
             </linearGradient>
           </defs>
           <rect x="20" y="20" width="30" height="30" rx="2" fill="#B5D4F4" opacity="0.5"/>
           <rect x="50" y="20" width="30" height="30" rx="2" fill="#378ADD" opacity="0.6"/>
           <rect x="80" y="20" width="30" height="30" rx="2" fill="#185FA5" opacity="0.75"/>
           <rect x="110" y="20" width="30" height="30" rx="2" fill="#0C447C" opacity="0.8"/>
           <rect x="140" y="20" width="30" height="30" rx="2" fill="#B5D4F4" opacity="0.4"/>
           <rect x="20" y="50" width="30" height="30" rx="2" fill="#E6F1FB" opacity="0.4"/>
           <rect x="50" y="50" width="30" height="30" rx="2" fill="#85B7EB" opacity="0.5"/>
           <rect x="80" y="50" width="30" height="30" rx="2" fill="#378ADD" opacity="0.65"/>
           <rect x="110" y="50" width="30" height="30" rx="2" fill="#378ADD" opacity="0.6"/>
           <rect x="140" y="50" width="30" height="30" rx="2" fill="#B5D4F4" opacity="0.45"/>
           <rect x="20" y="80" width="30" height="25" rx="2" fill="#E6F1FB" opacity="0.3"/>
           <rect x="50" y="80" width="30" height="25" rx="2" fill="#E6F1FB" opacity="0.35"/>
           <rect x="80" y="80" width="30" height="25" rx="2" fill="#85B7EB" opacity="0.45"/>
           <rect x="110" y="80" width="30" height="25" rx="2" fill="#B5D4F4" opacity="0.4"/>
           <rect x="140" y="80" width="30" height="25" rx="2" fill="#E6F1FB" opacity="0.3"/>
           <path d="M15 57 L175 57" stroke="#EF9F27" stroke-width="3" fill="none" stroke-linecap="round"/>
           <rect x="180" y="20" width="10" height="75" rx="3" fill="url(#depthGrad)"/>
           <text x="193" y="26" font-size="8" fill="#185FA5" font-family="system-ui,sans-serif">2 m</text>
           <text x="193" y="94" font-size="8" fill="#185FA5" font-family="system-ui,sans-serif">0 m</text>
           <text x="95" y="115" text-anchor="middle" font-size="9" fill="#378ADD" font-family="system-ui,sans-serif">Flood depth (m) per segment</text>
         </svg>
       </div>
       <div class="ra2ce-feat-body">
         <div class="ra2ce-feat-cat ra2ce-feat-cat-haz">
           Hazard <span class="ra2ce-feat-step">step 02</span>
         </div>
         <div class="ra2ce-feat-title">Overlay hazard data</div>
         <div class="ra2ce-feat-desc">Map flood, earthquake, or other hazard intensity onto each network link. Produces per-segment exposure attributes used in all downstream risk analyses.</div>
         <div class="ra2ce-feat-notebooks">
           <span class="ra2ce-feat-nb">
             <span class="ra2ce-feat-nb-dot ra2ce-feat-nb-dot-haz"></span>
             Hazard overlay tutorial
             <span class="ra2ce-feat-nb-arr">→</span>
           </span>
         </div>
       </div>
       </div><!-- /feat-card-inner -->
     </a>

   </div><!-- /foundation-grid -->

   <div class="ra2ce-section-divider"></div>

   <!-- ── ANALYSIS MODULES ──────────────────────────────── -->
   <div class="ra2ce-sec-head">
     <h2>Analysis modules</h2>
     <span class="ra2ce-sec-badge">Choose one or combine</span>
   </div>

   <div class="ra2ce-analysis-grid">

     <!-- Criticality -->
     <a href="criticality.html" class="ra2ce-feat-card">
       <div class="ra2ce-feat-card-inner">
       <div class="ra2ce-feat-visual ra2ce-feat-visual-crit">
         <svg width="220" height="130" viewBox="0 0 220 130" style="display:block">
           <defs>
             <marker id="arrC" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse">
               <path d="M2 1L8 5L2 9" fill="none" stroke="#1D9E75" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
             </marker>
           </defs>
           <!-- Normal route (blocked) -->
           <path d="M28 65 L90 40 L155 65" stroke="#EF9F27" stroke-width="3" fill="none" stroke-linecap="round"/>
           <!-- X mark on blocked segment -->
           <line x1="100" y1="46" x2="112" y2="58" stroke="#E24B4A" stroke-width="2.5" stroke-linecap="round"/>
           <line x1="112" y1="46" x2="100" y2="58" stroke="#E24B4A" stroke-width="2.5" stroke-linecap="round"/>
           <!-- Detour route -->
           <path d="M90 40 Q95 10 130 18 Q160 24 175 50 L175 65" stroke="#1D9E75" stroke-width="2.5" stroke-dasharray="5 3" fill="none" stroke-linecap="round" marker-end="url(#arrC)"/>
           <!-- Lower road -->
           <path d="M28 90 L75 80 L130 88 L175 80" stroke="#B4B2A9" stroke-width="2" fill="none" stroke-linecap="round"/>
           <!-- Nodes -->
           <circle cx="28"  cy="65" r="7" fill="#1D9E75" stroke="white" stroke-width="2"/>
           <circle cx="90"  cy="40" r="7" fill="#E24B4A" stroke="white" stroke-width="2"/>
           <circle cx="155" cy="65" r="7" fill="#EF9F27" stroke="white" stroke-width="2"/>
           <circle cx="175" cy="65" r="7" fill="#1D9E75" stroke="white" stroke-width="2"/>
           <circle cx="75"  cy="80" r="4" fill="#888780" stroke="white" stroke-width="1.5"/>
           <circle cx="130" cy="88" r="4" fill="#888780" stroke="white" stroke-width="1.5"/>
           <!-- Detour label -->
           <rect x="118" y="4" width="82" height="16" rx="8" fill="#FAEEDA" stroke="#FAC775" stroke-width="1"/>
           <text x="159" y="15" text-anchor="middle" font-size="8.5" fill="#BA7517" font-family="system-ui,sans-serif" font-weight="500">+22 min detour</text>
           <!-- Labels -->
           <text x="28"  y="110" font-size="8" fill="#888780" font-family="system-ui,sans-serif" text-anchor="middle">Origin</text>
           <text x="175" y="110" font-size="8" fill="#888780" font-family="system-ui,sans-serif" text-anchor="middle">Destination</text>
           <text x="90"  y="112" font-size="8" fill="#E24B4A" font-family="system-ui,sans-serif" text-anchor="middle">Closed link</text>
         </svg>
       </div>
       <div class="ra2ce-feat-body">
         <div class="ra2ce-feat-cat ra2ce-feat-cat-crit">
           Criticality <span class="ra2ce-feat-step">analysis</span>
         </div>
         <div class="ra2ce-feat-title">Network redundancy &amp; detour analysis</div>
         <div class="ra2ce-feat-desc">Identify which links, when disrupted, cause the greatest impact to network connectivity. Compute detour times and quantify the cost of losing any road segment.</div>
         <div class="ra2ce-feat-notebooks">
           <span class="ra2ce-feat-nb">
             <span class="ra2ce-feat-nb-dot ra2ce-feat-nb-dot-crit"></span>
             Single link redundancy tutorial
             <span class="ra2ce-feat-nb-arr">→</span>
           </span>
           <span class="ra2ce-feat-nb">
             <span class="ra2ce-feat-nb-dot ra2ce-feat-nb-dot-crit"></span>
             Multi link redundancy tutorial
             <span class="ra2ce-feat-nb-arr">→</span>
           </span>
         </div>
       </div>
       </div><!-- /feat-card-inner -->
     </a>

     <!-- Accessibility -->
     <a href="accessibility.html" class="ra2ce-feat-card">
       <div class="ra2ce-feat-card-inner">
       <div class="ra2ce-feat-visual ra2ce-feat-visual-acc">
         <svg width="220" height="130" viewBox="0 0 220 130" style="display:block">
           <defs>
             <marker id="arrA" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse">
               <path d="M2 1L8 5L2 9" fill="none" stroke="#1D9E75" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
             </marker>
           </defs>
           <!-- Destination: hospital -->
           <rect x="148" y="30" width="36" height="30" rx="5" fill="#F4C0D1" stroke="#D4537E" stroke-width="1.5"/>
           <text x="166" y="49" text-anchor="middle" font-size="14" font-family="system-ui,sans-serif">🏥</text>
           <!-- Origins: districts -->
           <rect x="18" y="20" width="26" height="20" rx="4" fill="#993556" opacity="0.15"/>
           <rect x="18" y="50" width="26" height="20" rx="4" fill="#993556" opacity="0.25"/>
           <rect x="18" y="80" width="26" height="20" rx="4" fill="#993556" opacity="0.12"/>
           <text x="31" y="34" text-anchor="middle" font-size="8" fill="#993556" font-family="system-ui,sans-serif" font-weight="500">A</text>
           <text x="31" y="64" text-anchor="middle" font-size="8" fill="#993556" font-family="system-ui,sans-serif" font-weight="500">B</text>
           <text x="31" y="94" text-anchor="middle" font-size="8" fill="#993556" font-family="system-ui,sans-serif" font-weight="500">C</text>
           <!-- Route A → hospital (reachable, green) -->
           <path d="M44 30 Q90 20 148 40" stroke="#1D9E75" stroke-width="2" fill="none" stroke-linecap="round" marker-end="url(#arrA)"/>
           <text x="96" y="18" text-anchor="middle" font-size="8" fill="#1D9E75" font-family="system-ui,sans-serif" font-weight="500">12 min</text>
           <!-- Route B → hospital (detour, amber) -->
           <path d="M44 60 Q90 55 148 52" stroke="#EF9F27" stroke-width="2" stroke-dasharray="4 2" fill="none" stroke-linecap="round" marker-end="url(#arrA)"/>
           <text x="96" y="50" text-anchor="middle" font-size="8" fill="#BA7517" font-family="system-ui,sans-serif" font-weight="500">34 min</text>
           <!-- Route C → hospital (isolated, red) -->
           <path d="M44 90 Q80 88 115 80" stroke="#E24B4A" stroke-width="2" fill="none" stroke-linecap="round"/>
           <line x1="118" y1="77" x2="126" y2="85" stroke="#E24B4A" stroke-width="2" stroke-linecap="round"/>
           <line x1="126" y1="77" x2="118" y2="85" stroke="#E24B4A" stroke-width="2" stroke-linecap="round"/>
           <text x="96" y="100" text-anchor="middle" font-size="8" fill="#E24B4A" font-family="system-ui,sans-serif" font-weight="500">Isolated</text>
           <!-- Legend dots -->
           <circle cx="18" cy="118" r="4" fill="#1D9E75"/>
           <text x="26" y="121" font-size="7.5" fill="#888780" font-family="system-ui,sans-serif">Reachable</text>
           <circle cx="80" cy="118" r="4" fill="#EF9F27"/>
           <text x="88" y="121" font-size="7.5" fill="#888780" font-family="system-ui,sans-serif">Detour</text>
           <circle cx="138" cy="118" r="4" fill="#E24B4A"/>
           <text x="146" y="121" font-size="7.5" fill="#888780" font-family="system-ui,sans-serif">No access</text>
         </svg>
       </div>
       <div class="ra2ce-feat-body">
         <div class="ra2ce-feat-cat ra2ce-feat-cat-acc">
           Accessibility <span class="ra2ce-feat-step">analysis</span>
         </div>
         <div class="ra2ce-feat-title">Origin–destination reachability</div>
         <div class="ra2ce-feat-desc">Measure travel times from origin zones to critical destinations — hospitals, shelters, emergency services — under normal and disrupted network conditions.</div>
         <div class="ra2ce-feat-notebooks">
           <span class="ra2ce-feat-nb">
             <span class="ra2ce-feat-nb-dot ra2ce-feat-nb-dot-acc"></span>
             Defined OD pairs tutorial
             <span class="ra2ce-feat-nb-arr">→</span>
           </span>
           <span class="ra2ce-feat-nb">
             <span class="ra2ce-feat-nb-dot ra2ce-feat-nb-dot-acc"></span>
             Origins to closest destinations
             <span class="ra2ce-feat-nb-arr">→</span>
           </span>
         </div>
       </div>
       </div><!-- /feat-card-inner -->
     </a>

     <!-- Damages -->
     <a href="damages.html" class="ra2ce-feat-card">
       <div class="ra2ce-feat-card-inner">
       <div class="ra2ce-feat-visual ra2ce-feat-visual-dmg">
         <svg width="220" height="130" viewBox="0 0 220 130" style="display:block">
           <!-- Grid lines -->
           <line x1="28" y1="20" x2="28" y2="100" stroke="#F7C1C1" stroke-width="0.8"/>
           <line x1="28" y1="100" x2="195" y2="100" stroke="#F7C1C1" stroke-width="0.8"/>
           <line x1="28" y1="70"  x2="195" y2="70"  stroke="#F7C1C1" stroke-width="0.5" stroke-dasharray="3 3"/>
           <line x1="28" y1="45"  x2="195" y2="45"  stroke="#F7C1C1" stroke-width="0.5" stroke-dasharray="3 3"/>
           <!-- Damage curve (reference) -->
           <path d="M28 100 Q55 100 70 85 Q90 65 110 45 Q135 25 160 22 L195 22" stroke="#E24B4A" stroke-width="2.5" fill="none" stroke-linecap="round"/>
           <!-- Manual curve (dashed blue) -->
           <path d="M28 100 Q60 100 80 88 Q105 72 130 52 Q155 32 185 28" stroke="#378ADD" stroke-width="2" stroke-dasharray="5 3" fill="none" stroke-linecap="round"/>
           <!-- Axis labels -->
           <text x="110" y="116" text-anchor="middle" font-size="8.5" fill="#A32D2D" font-family="system-ui,sans-serif">Water depth (m)</text>
           <text x="14" y="100" text-anchor="middle" font-size="8" fill="#A32D2D" font-family="system-ui,sans-serif">0</text>
           <text x="14" y="70"  text-anchor="middle" font-size="8" fill="#A32D2D" font-family="system-ui,sans-serif">50%</text>
           <text x="14" y="45"  text-anchor="middle" font-size="8" fill="#A32D2D" font-family="system-ui,sans-serif">75%</text>
           <text x="14" y="25"  text-anchor="middle" font-size="8" fill="#A32D2D" font-family="system-ui,sans-serif">100%</text>
           <!-- Legend -->
           <rect x="52" y="22" width="10" height="3" rx="1" fill="#E24B4A"/>
           <text x="66" y="27" font-size="7.5" fill="#888780" font-family="system-ui,sans-serif">Reference curves</text>
           <rect x="52" y="33" width="10" height="3" rx="1" fill="none" stroke="#378ADD" stroke-width="1.5" stroke-dasharray="3 2"/>
           <text x="66" y="38" font-size="7.5" fill="#888780" font-family="system-ui,sans-serif">Manual curves</text>
           <!-- EAD annotation -->
           <rect x="148" y="54" width="52" height="22" rx="5" fill="#FCEBEB" stroke="#F7C1C1" stroke-width="1"/>
           <text x="174" y="63" text-anchor="middle" font-size="7.5" fill="#A32D2D" font-family="system-ui,sans-serif" font-weight="500">EAD</text>
           <text x="174" y="72" text-anchor="middle" font-size="7" fill="#A32D2D" font-family="system-ui,sans-serif">€ 2.4 M / yr</text>
         </svg>
       </div>
       <div class="ra2ce-feat-body">
         <div class="ra2ce-feat-cat ra2ce-feat-cat-dmg">
           Damages <span class="ra2ce-feat-step">analysis</span>
         </div>
         <div class="ra2ce-feat-title">Physical damage &amp; EAD estimation</div>
         <div class="ra2ce-feat-desc">Apply depth–damage functions to exposed road segments to estimate repair costs per event, then integrate across return periods to compute Expected Annual Damage.</div>
         <div class="ra2ce-feat-notebooks">
           <span class="ra2ce-feat-nb">
             <span class="ra2ce-feat-nb-dot ra2ce-feat-nb-dot-dmg"></span>
             Reference damage curves tutorial
             <span class="ra2ce-feat-nb-arr">→</span>
           </span>
           <span class="ra2ce-feat-nb">
             <span class="ra2ce-feat-nb-dot ra2ce-feat-nb-dot-dmg"></span>
             Manual damage curves tutorial
             <span class="ra2ce-feat-nb-arr">→</span>
           </span>
           <span class="ra2ce-feat-nb">
             <span class="ra2ce-feat-nb-dot ra2ce-feat-nb-dot-dmg"></span>
             Expected Annual Damage (EAD)
             <span class="ra2ce-feat-nb-arr">→</span>
           </span>
         </div>
       </div>
       </div><!-- /feat-card-inner -->
     </a>

     <!-- Losses -->
     <a href="losses.html" class="ra2ce-feat-card">
       <div class="ra2ce-feat-card-inner">
       <div class="ra2ce-feat-visual ra2ce-feat-visual-loss">
         <svg width="220" height="130" viewBox="0 0 220 130" style="display:block">
           <!-- Return period axis -->
           <line x1="28" y1="98" x2="195" y2="98" stroke="#CECBF6" stroke-width="0.8"/>
           <line x1="28" y1="28" x2="28"  y2="98" stroke="#CECBF6" stroke-width="0.8"/>
           <!-- Horizontal guides -->
           <line x1="28" y1="70" x2="195" y2="70" stroke="#CECBF6" stroke-width="0.5" stroke-dasharray="3 3"/>
           <line x1="28" y1="45" x2="195" y2="45" stroke="#CECBF6" stroke-width="0.5" stroke-dasharray="3 3"/>
           <!-- Loss curve -->
           <path d="M32 98 Q50 97 65 92 Q85 84 105 68 Q125 50 145 36 Q165 26 190 24" stroke="#7F77DD" stroke-width="2.5" fill="none" stroke-linecap="round"/>
           <!-- Area under curve -->
           <path d="M32 98 Q50 97 65 92 Q85 84 105 68 Q125 50 145 36 Q165 26 190 24 L190 98 Z" fill="#7F77DD" opacity="0.1"/>
           <!-- EAL annotation -->
           <line x1="110" y1="68" x2="132" y2="50" stroke="#7F77DD" stroke-width="1" stroke-dasharray="2 2"/>
           <rect x="132" y="38" width="60" height="22" rx="5" fill="#EEEDFE" stroke="#CECBF6" stroke-width="1"/>
           <text x="162" y="47" text-anchor="middle" font-size="7.5" fill="#534AB7" font-family="system-ui,sans-serif" font-weight="500">EAL</text>
           <text x="162" y="56" text-anchor="middle" font-size="7" fill="#534AB7" font-family="system-ui,sans-serif">€ 890 K / yr</text>
           <!-- Axis tick labels -->
           <text x="44"  y="108" text-anchor="middle" font-size="7.5" fill="#7F77DD" font-family="system-ui,sans-serif">1:10</text>
           <text x="90"  y="108" text-anchor="middle" font-size="7.5" fill="#7F77DD" font-family="system-ui,sans-serif">1:50</text>
           <text x="145" y="108" text-anchor="middle" font-size="7.5" fill="#7F77DD" font-family="system-ui,sans-serif">1:100</text>
           <text x="190" y="108" text-anchor="middle" font-size="7.5" fill="#7F77DD" font-family="system-ui,sans-serif">1:250</text>
           <text x="110" y="120" text-anchor="middle" font-size="8" fill="#7F77DD" font-family="system-ui,sans-serif">Return period</text>
           <!-- Y label -->
           <text x="14" y="70" text-anchor="middle" font-size="7.5" fill="#888780" font-family="system-ui,sans-serif">Loss</text>
           <!-- Travel time badge -->
           <rect x="30" y="28" width="70" height="16" rx="4" fill="#EEEDFE" stroke="#CECBF6" stroke-width="1"/>
           <text x="65" y="39" text-anchor="middle" font-size="7.5" fill="#534AB7" font-family="system-ui,sans-serif">Travel time lost</text>
         </svg>
       </div>
       <div class="ra2ce-feat-body">
         <div class="ra2ce-feat-cat ra2ce-feat-cat-loss">
           Losses <span class="ra2ce-feat-step">analysis</span>
         </div>
         <div class="ra2ce-feat-title">Economic losses &amp; EAL estimation</div>
         <div class="ra2ce-feat-desc">Translate network disruption into indirect economic losses — value of lost travel time, freight delays — and integrate across return periods to derive Expected Annual Loss.</div>
         <div class="ra2ce-feat-notebooks">
           <span class="ra2ce-feat-nb">
             <span class="ra2ce-feat-nb-dot ra2ce-feat-nb-dot-loss"></span>
             Multi link redundancy losses
             <span class="ra2ce-feat-nb-arr">→</span>
           </span>
         </div>
       </div>
       </div><!-- /feat-card-inner -->
     </a>

   </div><!-- /analysis-grid -->

   <!-- output strip -->
   <div class="ra2ce-sec-head" style="margin-bottom:0.75rem">
     <h2>What you'll get</h2>
     <span class="ra2ce-sec-badge">Example outputs</span>
   </div>
   <div class="ra2ce-output-strip">
     <div class="ra2ce-out-item">
       <div class="ra2ce-out-thumb">
         <svg width="120" height="80" viewBox="0 0 120 80">
           <line x1="10" y1="65" x2="110" y2="65" stroke="#D3D1C7" stroke-width="0.5"/>
           <line x1="10" y1="45" x2="110" y2="45" stroke="#D3D1C7" stroke-width="0.5" stroke-dasharray="2 2"/>
           <line x1="10" y1="25" x2="110" y2="25" stroke="#D3D1C7" stroke-width="0.5" stroke-dasharray="2 2"/>
           <path d="M15 60 L30 50 L45 55 L60 30 L75 40 L90 25 L105 32" stroke="#E24B4A" stroke-width="2" fill="none" stroke-linecap="round"/>
           <path d="M15 65 L30 62 L45 65 L60 60 L75 64 L90 62 L105 65" stroke="#378ADD" stroke-width="1.5" stroke-dasharray="3 2" fill="none" stroke-linecap="round"/>
           <text x="60" y="78" text-anchor="middle" font-size="7" fill="#888780" font-family="system-ui,sans-serif">Water depth</text>
         </svg>
       </div>
       <div class="ra2ce-out-label">Damage curves</div>
       <div class="ra2ce-out-sub">Depth–damage functions</div>
     </div>
     <div class="ra2ce-out-item">
       <div class="ra2ce-out-thumb">
         <svg width="120" height="80" viewBox="0 0 120 80">
           <line x1="10" y1="65" x2="110" y2="65" stroke="#D3D1C7" stroke-width="0.5"/>
           <line x1="10" y1="45" x2="110" y2="45" stroke="#D3D1C7" stroke-width="0.5" stroke-dasharray="2 2"/>
           <rect x="16" y="38" width="12" height="27" rx="2" fill="#E24B4A" opacity="0.85"/>
           <rect x="33" y="48" width="12" height="17" rx="2" fill="#EF9F27" opacity="0.85"/>
           <rect x="50" y="30" width="12" height="35" rx="2" fill="#E24B4A" opacity="0.85"/>
           <rect x="67" y="44" width="12" height="21" rx="2" fill="#EF9F27" opacity="0.85"/>
           <rect x="84" y="52" width="12" height="13" rx="2" fill="#EF9F27" opacity="0.6"/>
           <rect x="101" y="58" width="12" height="7" rx="2" fill="#5DCAA5" opacity="0.8"/>
           <text x="60" y="78" text-anchor="middle" font-size="7" fill="#888780" font-family="system-ui,sans-serif">Road segment</text>
         </svg>
       </div>
       <div class="ra2ce-out-label">EAD per segment</div>
       <div class="ra2ce-out-sub">Expected annual damage</div>
     </div>
     <div class="ra2ce-out-item">
       <div class="ra2ce-out-thumb">
         <svg width="120" height="80" viewBox="0 0 120 80">
           <circle cx="30" cy="35" r="8" fill="#1D9E75" stroke="white" stroke-width="1.5"/>
           <circle cx="65" cy="22" r="8" fill="#E24B4A" stroke="white" stroke-width="1.5"/>
           <circle cx="55" cy="52" r="6" fill="#1D9E75" stroke="white" stroke-width="1.5"/>
           <circle cx="92" cy="42" r="6" fill="#1D9E75" stroke="white" stroke-width="1.5"/>
           <line x1="30" y1="35" x2="55" y2="52" stroke="#1D9E75" stroke-width="2"/>
           <line x1="55" y1="52" x2="92" y2="42" stroke="#1D9E75" stroke-width="2"/>
           <line x1="30" y1="35" x2="65" y2="22" stroke="#E24B4A" stroke-width="2.5" stroke-dasharray="4 2"/>
           <line x1="65" y1="22" x2="92" y2="42" stroke="#EF9F27" stroke-width="2"/>
           <rect x="2" y="64" width="6" height="6" rx="1" fill="#1D9E75"/>
           <text x="11" y="70" font-size="7" fill="#5F5E5A" font-family="system-ui,sans-serif">OK</text>
           <rect x="30" y="64" width="6" height="6" rx="1" fill="#E24B4A"/>
           <text x="39" y="70" font-size="7" fill="#5F5E5A" font-family="system-ui,sans-serif">Critical</text>
           <rect x="67" y="64" width="6" height="6" rx="1" fill="#EF9F27"/>
           <text x="76" y="70" font-size="7" fill="#5F5E5A" font-family="system-ui,sans-serif">Detour</text>
         </svg>
       </div>
       <div class="ra2ce-out-label">Network risk map</div>
       <div class="ra2ce-out-sub">Criticality per link</div>
     </div>
   </div>

   <div class="ra2ce-section-divider"></div>

   <!-- ── ADVANCED ───────────────────────────────────────── -->
   <div class="ra2ce-sec-head">
     <h2>Advanced modules</h2>
     <span class="ra2ce-sec-badge">Build on analysis results</span>
   </div>

   <div class="ra2ce-advanced-grid">

     <a href="adaptation.html" class="ra2ce-adv-card">
       <div class="ra2ce-adv-top">
         <div class="ra2ce-adv-icon ra2ce-adv-icon-adp">🛡️</div>
         <span class="ra2ce-adv-badge ra2ce-adv-badge-adp">Advanced</span>
       </div>
       <div class="ra2ce-adv-cat ra2ce-adv-cat-adp">Adaptation</div>
       <div class="ra2ce-adv-title">Resilience strategy evaluation</div>
       <div class="ra2ce-adv-desc">Compare infrastructure upgrades, nature-based solutions, and maintenance strategies by their impact on EAD and network connectivity under current and future hazard conditions. Identify the most cost-effective resilience measures.</div>
     </a>

     <a href="equity.html" class="ra2ce-adv-card">
       <div class="ra2ce-adv-top">
         <div class="ra2ce-adv-icon ra2ce-adv-icon-eq">⚖️</div>
         <span class="ra2ce-adv-badge ra2ce-adv-badge-eq">Advanced</span>
       </div>
       <div class="ra2ce-adv-cat ra2ce-adv-cat-eq">Equity</div>
       <div class="ra2ce-adv-title">Distributional risk analysis</div>
       <div class="ra2ce-adv-desc">Evaluate who is most exposed to infrastructure disruptions. Identify socially vulnerable populations with limited access to alternative routes or critical services, and quantify the equity implications of adaptation choices.</div>
     </a>

   </div><!-- /advanced-grid -->

----

.. dropdown:: How does RA2CE work? — Modelling framework
   :icon: info

   The diagram below shows how all modules connect.
   Each box is clickable. Solid arrows are required inputs; dashed arrows are optional.

   .. raw:: html

      <svg viewBox="0 0 700 440" xmlns="http://www.w3.org/2000/svg"
           role="img" aria-label="RA2CE modelling framework diagram"
           style="max-width:100%;height:auto;display:block;margin:16px 0 32px;
                  font-family:system-ui,sans-serif;">
        <style>
          .fc-node rect  { transition:filter .15s; }
          .fc-node:hover rect { filter:brightness(1.2); cursor:pointer; }
          .fc-node text  { pointer-events:none; user-select:none; }
        </style>
        <defs>
          <marker id="arr-s" viewBox="0 0 10 10" refX="9" refY="5"
                  markerWidth="6" markerHeight="6" orient="auto">
            <path d="M0 1.5 L9 5 L0 8.5z" fill="#9aabb8"/>
          </marker>
          <marker id="arr-d" viewBox="0 0 10 10" refX="9" refY="5"
                  markerWidth="6" markerHeight="6" orient="auto">
            <path d="M0 1.5 L9 5 L0 8.5z" fill="#b0c4ce"/>
          </marker>
        </defs>

        <g stroke="#9aabb8" stroke-width="1.8" fill="none" marker-end="url(#arr-s)">
          <path d="M 280 48 C 280 80, 100 78, 100 108"/>
          <path d="M 350 48 C 350 78, 460 78, 460 108"/>
          <line x1="100" y1="146" x2="100" y2="208"/>
          <line x1="460" y1="146" x2="460" y2="208"/>
          <path d="M 135 246 C 135 285, 290 285, 295 298"/>
          <path d="M 425 246 C 425 285, 380 285, 365 298"/>
          <line x1="330" y1="336" x2="330" y2="358"/>
        </g>

        <g stroke="#b0c4ce" stroke-width="1.6" stroke-dasharray="5,3"
           fill="none" marker-end="url(#arr-d)">
          <path d="M 165 124 C 220 110, 330 110, 390 118"/>
        </g>

        <a href="network.html">
          <g class="fc-node">
            <rect x="230" y="10" width="140" height="38" rx="7" fill="#4a6fa5"/>
            <text x="300" y="34" fill="#fff" text-anchor="middle"
                  font-size="13" font-weight="600">1 · Network</text>
          </g>
        </a>
        <a href="hazard.html">
          <g class="fc-node">
            <rect x="25" y="108" width="150" height="38" rx="7" fill="#0072b2"/>
            <text x="100" y="125" fill="#fff" text-anchor="middle"
                  font-size="11" font-weight="600">2 · Network Exposure</text>
            <text x="100" y="139" fill="#dde" text-anchor="middle"
                  font-size="10">(Hazard)</text>
          </g>
        </a>
        <a href="criticality.html">
          <g class="fc-node">
            <rect x="385" y="108" width="160" height="38" rx="7" fill="#d55e00"/>
            <text x="465" y="125" fill="#fff" text-anchor="middle"
                  font-size="11" font-weight="600">4 · Network Criticality</text>
            <text x="465" y="139" fill="#ffe" text-anchor="middle"
                  font-size="10">(connectivity &amp; detour)</text>
          </g>
        </a>
        <a href="damages.html">
          <g class="fc-node">
            <rect x="25" y="208" width="150" height="38" rx="7" fill="#cc3333"/>
            <text x="100" y="225" fill="#fff" text-anchor="middle"
                  font-size="11" font-weight="600">3 · Damages ($)</text>
            <text x="100" y="239" fill="#fee" text-anchor="middle"
                  font-size="10">(physical repair cost)</text>
          </g>
        </a>
        <a href="losses.html">
          <g class="fc-node">
            <rect x="385" y="208" width="160" height="38" rx="7" fill="#8b2fc9"/>
            <text x="465" y="225" fill="#fff" text-anchor="middle"
                  font-size="11" font-weight="600">5 · Losses ($ / pax)</text>
            <text x="465" y="239" fill="#ede" text-anchor="middle"
                  font-size="10">(indirect economic loss)</text>
          </g>
        </a>
        <rect x="220" y="298" width="220" height="38" rx="7"
              fill="none" stroke="#9aabb8" stroke-width="1.5" stroke-dasharray="4,3"/>
        <text x="330" y="315" fill="#555" text-anchor="middle"
              font-size="11" font-weight="600">6 · Annual Expected</text>
        <text x="330" y="329" fill="#555" text-anchor="middle"
              font-size="10">Damages &amp; Losses (EAD / EAL)</text>
        <a href="adaptation.html">
          <g class="fc-node">
            <rect x="220" y="358" width="220" height="38" rx="7" fill="#0b6b3a"/>
            <text x="330" y="375" fill="#fff" text-anchor="middle"
                  font-size="11" font-weight="600">7 · Prioritisation /</text>
            <text x="330" y="389" fill="#cec" text-anchor="middle"
                  font-size="10">8 · Adaptation Measures</text>
          </g>
        </a>
        <a href="accessibility.html">
          <g class="fc-node">
            <rect x="565" y="208" width="130" height="38" rx="7" fill="#009e73"/>
            <text x="630" y="225" fill="#fff" text-anchor="middle"
                  font-size="11" font-weight="600">Accessibility</text>
            <text x="630" y="239" fill="#dfd" text-anchor="middle"
                  font-size="10">(services reachable?)</text>
          </g>
        </a>
        <g stroke="#b0c4ce" stroke-width="1.4" stroke-dasharray="4,3"
           fill="none" marker-end="url(#arr-d)">
          <line x1="545" y1="127" x2="630" y2="208"/>
        </g>
        <a href="equity.html">
          <g class="fc-node">
            <rect x="565" y="298" width="130" height="38" rx="7" fill="#c87000"/>
            <text x="630" y="315" fill="#fff" text-anchor="middle"
                  font-size="11" font-weight="600">Equity</text>
            <text x="630" y="329" fill="#ffe" text-anchor="middle"
                  font-size="10">(distributional impact)</text>
          </g>
        </a>
        <g stroke="#9aabb8" stroke-width="1.5" fill="none" marker-end="url(#arr-s)">
          <line x1="630" y1="246" x2="630" y2="298"/>
        </g>
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

   :icon: map

   .. grid:: 2
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

