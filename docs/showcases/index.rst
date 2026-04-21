Showcases
=========

Real-world applications of RA2CE demonstrating how hazard exposure, network criticality, accessibility, and damage assessments can be integrated to inform climate-resilient infrastructure planning and adaptation strategies (non-exhaustive).  

.. raw:: html

    <!-- Load Leaflet with AMD detection disabled so window.L is always set globally.
         nbsphinx injects require.js which makes Leaflet register as an AMD module
         instead of setting window.L when loaded via a plain <script> tag. -->
    <script>
    (function () {
      var d = window.define;
      if (typeof d === 'function' && d.amd) { d._amd_bak = d.amd; d.amd = false; }
    }());
    </script>
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script>
    (function () {
      var d = window.define;
      if (typeof d === 'function' && d._amd_bak) { d.amd = d._amd_bak; delete d._amd_bak; }
    }());
    </script>

    <style>
      /* ── MAP + PANEL LAYOUT ── */
      .showcase-body {
        display: grid;
        grid-template-columns: 1fr 380px;
        gap: 20px;
        align-items: start;
        margin-top: 1.5rem;
      }

      /* ── MAP ── */
      .map-wrap {
        border: 1px solid rgba(28,28,26,0.1);
        border-radius: 14px;
        overflow: hidden;
        position: sticky;
        top: 72px;
      }
      #ra2ce-map { height: 540px; }

      /* Leaflet popup overrides */
      .leaflet-popup-content-wrapper {
        border-radius: 10px !important;
        box-shadow: 0 4px 24px rgba(0,0,0,0.10) !important;
        border: 1px solid rgba(28,28,26,0.16) !important;
        padding: 0 !important;
        font-size: 13px !important;
      }
      .leaflet-popup-content { margin: 0 !important; width: auto !important; }
      .leaflet-popup-tip-container { display: none; }
      .leaflet-popup-close-button {
        top: 8px !important; right: 10px !important;
        font-size: 16px !important; color: #888780 !important;
      }

      /* ── FILTER ROW ── */
      .ra2ce-filter-row {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 1.25rem;
        flex-wrap: wrap;
      }
      .ra2ce-chip {
        font-size: 12px; padding: 5px 13px; border-radius: 20px;
        border: 1px solid rgba(28,28,26,0.16); color: #4a4945;
        background: none; cursor: pointer; transition: all .15s;
        font-family: inherit;
      }
      .ra2ce-chip:hover { border-color: #5DCAA5; }
      .ra2ce-chip.on {
        background: #E1F5EE; color: #085041;
        border-color: #5DCAA5; font-weight: 500;
      }
      .ra2ce-filter-sep { flex: 1; }
      .ra2ce-proj-count { font-size: 12px; color: #888780; }

      /* ── FULL-WIDTH PAGE LAYOUT (hide right sidebar, main takes full width) ── */
      .bd-sidebar-secondary { display: none !important; }
      .bd-article-container { max-width: 100% !important; }
      .bd-content { max-width: 100% !important; }

      /* ── SLIDER ── */
      .ra2ce-slider { position: relative; }
      .ra2ce-slider-track-wrap {
        overflow: hidden;
        transition: height 0.3s cubic-bezier(.4,0,.2,1);
      }
      .ra2ce-project-list {
        display: flex; flex-direction: column; gap: 10px;
        position: relative;
        transition: transform 0.35s cubic-bezier(.4,0,.2,1);
      }
      .ra2ce-slider-nav {
        display: flex; align-items: center;
        justify-content: space-between; margin-top: 12px; gap: 8px;
      }
      .ra2ce-slider-btn {
        width: 32px; height: 32px; border-radius: 50%;
        border: 1px solid rgba(28,28,26,0.16); background: #fff;
        cursor: pointer; font-size: 14px; color: #4a4945;
        display: flex; align-items: center; justify-content: center;
        transition: all .15s; padding: 0; line-height: 1;
      }
      .ra2ce-slider-btn:hover:not(:disabled) { border-color: #5DCAA5; color: #0F6E56; }
      .ra2ce-slider-btn:disabled { opacity: 0.3; cursor: default; }
      .ra2ce-slider-dots {
        display: flex; gap: 6px; align-items: center;
        flex: 1; justify-content: center;
      }
      .ra2ce-slider-dot {
        width: 7px; height: 7px; border-radius: 50%;
        background: rgba(28,28,26,0.15);
        transition: background .2s, transform .2s; cursor: pointer;
      }
      .ra2ce-slider-dot.on { background: #1D9E75; transform: scale(1.35); }

      /* ── PROJECT CARD ── */
      .ra2ce-proj-card {
        border: 1px solid rgba(28,28,26,0.1); border-radius: 14px;
        background: #fff; cursor: pointer;
        transition: border-color .2s, box-shadow .2s;
        overflow: hidden; text-decoration: none; color: inherit; display: block;
        flex-shrink: 0;
      }
      .ra2ce-proj-card:hover { border-color: #5DCAA5; }
      .ra2ce-proj-card.active {
        border-color: #1D9E75;
        box-shadow: 0 0 0 3px rgba(29,158,117,0.12);
      }
      .ra2ce-proj-inner { display: flex; }
      .ra2ce-proj-accent { width: 4px; flex-shrink: 0; }
      .ra2ce-proj-body { padding: 1rem 1rem 1rem 0.875rem; flex: 1; }
      .ra2ce-proj-top {
        display: flex; align-items: flex-start;
        justify-content: space-between; gap: 8px; margin-bottom: 5px;
      }
      .ra2ce-proj-title { font-size: 13.5px; font-weight: 500; line-height: 1.35; color: #1a1917; }
      .ra2ce-proj-flag { font-size: 16px; flex-shrink: 0; }
      .ra2ce-proj-location { font-size: 11.5px; color: #888780; display: block; margin-bottom: 6px; }
      .ra2ce-proj-tags { display: flex; gap: 4px; flex-wrap: wrap; }
      .ra2ce-proj-tag { font-size: 10px; padding: 2px 7px; border-radius: 10px; font-weight: 500; }
      .ra2ce-proj-desc { font-size: 12.5px; color: #4a4945; line-height: 1.5; margin-top: 6px; }
      .ra2ce-proj-link {
        display: inline-flex; align-items: center; gap: 4px;
        margin-top: 8px; font-size: 12px; color: #0F6E56; font-weight: 500;
      }

      /* ── POPUP CARD ── */
      .ra2ce-popup-card { padding: 1rem 1.125rem; min-width: 230px; max-width: 280px; }
      .ra2ce-popup-flag { font-size: 20px; margin-bottom: 6px; }
      .ra2ce-popup-title { font-size: 13px; font-weight: 500; margin-bottom: 3px; line-height: 1.35; color: #1a1917; }
      .ra2ce-popup-loc { font-size: 11px; color: #888780; margin-bottom: 8px; }
      .ra2ce-popup-tags { display: flex; gap: 4px; flex-wrap: wrap; margin-bottom: 8px; }
      .ra2ce-popup-tag { font-size: 10px; padding: 2px 7px; border-radius: 10px; font-weight: 500; }
      .ra2ce-popup-desc { font-size: 12px; color: #4a4945; line-height: 1.5; margin-bottom: 10px; }
      .ra2ce-popup-btn {
        display: inline-block; font-size: 12px; font-weight: 500; color: #fff;
        background: #0F6E56; border-radius: 6px; padding: 5px 12px;
        text-decoration: none;
      }
      .ra2ce-popup-btn:hover { background: #085041; }

      @keyframes ra2ce-pulse {
        0%   { transform: scale(1);   opacity: 0.25; }
        100% { transform: scale(2.8); opacity: 0; }
      }

      @media (max-width: 800px) {
        .showcase-body { grid-template-columns: 1fr; }
        .map-wrap { position: static; }
        #ra2ce-map { height: 360px; }
      }
    </style>

    <!-- FILTER ROW -->
    <div class="ra2ce-filter-row">
      <button class="ra2ce-chip on" onclick="ra2ceFilterBy('all',this)">All projects</button>
      <button class="ra2ce-chip" onclick="ra2ceFilterBy('flood',this)">Flood</button>
      <button class="ra2ce-chip" onclick="ra2ceFilterBy('criticality',this)">Criticality</button>
      <button class="ra2ce-chip" onclick="ra2ceFilterBy('damages',this)">Damages</button>
      <button class="ra2ce-chip" onclick="ra2ceFilterBy('accessibility',this)">Accessibility</button>
      <button class="ra2ce-chip" onclick="ra2ceFilterBy('adaptation',this)">Adaptation</button>
      <span class="ra2ce-filter-sep"></span>
      <span class="ra2ce-proj-count" id="ra2ce-proj-count">7 projects &middot; 6 countries</span>
    </div>

    <!-- MAP + PROJECT LIST -->
    <div class="showcase-body">
      <div class="map-wrap">
        <div id="ra2ce-map"></div>
      </div>
      <div class="ra2ce-slider">
        <div class="ra2ce-slider-track-wrap" id="ra2ce-track-wrap">
          <div class="ra2ce-project-list" id="ra2ce-project-list"></div>
        </div>
        <div class="ra2ce-slider-nav">
          <button class="ra2ce-slider-btn" id="ra2ce-prev" disabled>&#8593;</button>
          <div class="ra2ce-slider-dots" id="ra2ce-dots"></div>
          <button class="ra2ce-slider-btn" id="ra2ce-next">&#8595;</button>
        </div>
      </div>
    </div>

    <script>
    (function () {
      'use strict';

      var projects = [
        {
          id: 'myanmar',
          title: 'NRT Flood Impact Analysis on Road Networks',
          location: 'Mandalay region, Myanmar',
          flag: '🇲🇲',
          lat: 21.97, lng: 96.08,
          tags: ['flood', 'criticality', 'damages'],
          tagLabels: ['Flood', 'Criticality', 'Damages'],
          accent: '#378ADD', tagBg: '#E6F1FB', tagColor: '#185FA5',
          desc: 'Near-real-time analysis of flood impacts on the road network, identifying isolated communities and estimating direct road damage costs.',
          link: 'https://arcg.is/1uGm5W0',
          linkLabel: 'Open ArcGIS story map \u2197',
          year: '2023'
        },
        {
          id: 'cascading',
          title: 'Cascading Impacts of Flooded Infrastructure',
          location: 'Broward County, Florida, USA',
          flag: '\uD83C\uDDFA\uD83C\uDDF8',
          lat: 26.1, lng: -80.2,
          tags: ['flood', 'damages', 'adaptation'],
          tagLabels: ['Flood', 'Damages', 'Adaptation'],
          accent: '#1D9E75', tagBg: '#E1F5EE', tagColor: '#0F6E56',
          desc: 'Quantification of direct and indirect economic losses from cascading infrastructure disruptions, with evaluation of adaptation measures and cost-benefit ratios.',
          link: 'https://arcg.is/1iC1rX',
          linkLabel: 'Open ArcGIS story map \u2197',
          year: '2023'
        },
        {
          id: 'europe',
          title: 'Flood Risk of European Road Networks',
          location: 'Europe-wide (Alps highlighted)',
          flag: '🇪🇺',
          lat: 47.2, lng: 11.5,
          tags: ['flood', 'criticality', 'damages'],
          tagLabels: ['Flood', 'Criticality', 'Damages'],
          accent: '#7F77DD', tagBg: '#EEEDFE', tagColor: '#534AB7',
          desc: 'Pan-European analysis identifying high-risk road clusters. Alpine roads found most vulnerable to river flooding. Published 2021 with VU Amsterdam.',
          link: 'https://www.deltares.nl/en/expertise/projects/exposing-vulnerabilities-in-the-road-network',
          linkLabel: 'Read the project page \u2197',
          year: '2021'
        },
        {
          id: 'netherlands',
          title: 'National Road Network Resilience \u2014 Rijkswaterstaat',
          location: 'Netherlands',
          flag: '🇳🇱',
          lat: 52.2, lng: 5.3,
          tags: ['flood', 'criticality', 'accessibility'],
          tagLabels: ['Flood', 'Criticality', 'Accessibility'],
          accent: '#EF9F27', tagBg: '#FAEEDA', tagColor: '#BA7517',
          desc: 'Thousands of flood scenarios computed for national roads to identify vulnerable links and evacuation constraints for Rijkswaterstaat.',
          link: 'https://www.deltares.nl/en/expertise/projects/exposing-vulnerabilities-in-the-road-network',
          linkLabel: 'Read more \u2197',
          year: '2022'
        },
        {
          id: 'dominican',
          title: 'Multi-hazard Infrastructure Risk Assessment',
          location: 'Dominican Republic',
          flag: '🇩🇴',
          lat: 18.7, lng: -70.2,
          tags: ['flood', 'damages', 'adaptation'],
          tagLabels: ['Flood', 'Damages', 'Adaptation'],
          accent: '#D85A30', tagBg: '#FAECE7', tagColor: '#993C1D',
          desc: 'Risk assessment covering floods and hurricanes with damage and loss estimation for the national road network, informing adaptation planning.',
          link: 'https://www.deltares.nl/en/expertise/areas-of-expertise/future-proof-infrastructure/climate-resilient-roads/critical-infrastructure-resilience',
          linkLabel: 'Read more \u2197',
          year: '2023'
        },
        {
          id: 'nepal',
          title: 'Timely Logistics Information for Emergency Response',
          location: 'Nepal',
          flag: '\uD83C\uDDF3\uD83C\uDDF5',
          lat: 28.0, lng: 84.0,
          tags: ['flood', 'accessibility', 'criticality'],
          tagLabels: ['Flood', 'Accessibility', 'Criticality'],
          accent: '#1D9E75', tagBg: '#E1F5EE', tagColor: '#0F6E56',
          desc: 'RA2CE deployed by WFP and DPNet Nepal to identify isolated settlements during flood events and support timely humanitarian logistics and disaster response planning.',
          link: 'https://www.dpnet.org.np/news/detail/shaping-disaster-response-with-technological-innovation',
          linkLabel: 'Read the DPNet article \u2197',
          year: '2023'
        }
      ];

      function initMap(L) {

        var map = L.map('ra2ce-map', {
          center: [25, 30], zoom: 2,
          zoomControl: true, attributionControl: true,
          maxBounds: [[-90, -180], [90, 180]],
          maxBoundsViscosity: 1.0
        });

        L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
          attribution: '\u00a9 <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> \u00a9 <a href="https://carto.com/attributions">CARTO</a>',
          maxZoom: 19,
          noWrap: true
        }).addTo(map);

        function makeIcon(color) {
          return L.divIcon({
            className: '',
            html: '<div style="width:14px;height:14px;border-radius:50%;background:' + color + ';border:2.5px solid white;box-shadow:0 1px 6px rgba(0,0,0,0.25);cursor:pointer;"></div>',
            iconSize: [14, 14], iconAnchor: [7, 7], popupAnchor: [0, -10]
          });
        }

        function makePulseIcon(color) {
          return L.divIcon({
            className: '',
            html: '<div style="position:relative;width:20px;height:20px;">' +
              '<div style="position:absolute;inset:0;border-radius:50%;background:' + color + ';opacity:0.25;animation:ra2ce-pulse 1.5s ease-out infinite;"></div>' +
              '<div style="position:absolute;top:3px;left:3px;width:14px;height:14px;border-radius:50%;background:' + color + ';border:2.5px solid white;box-shadow:0 1px 6px rgba(0,0,0,0.25);"></div>' +
              '</div>',
            iconSize: [20, 20], iconAnchor: [10, 10], popupAnchor: [0, -12]
          });
        }

        var markers = {};
        var activeId = null;
        var currentSlideIdx = 0;

        projects.forEach(function (p) {
          var marker = L.marker([p.lat, p.lng], { icon: makeIcon(p.accent) }).addTo(map);

          var tagsHtml = p.tagLabels.map(function (t) {
            return '<span class="ra2ce-popup-tag" style="background:' + p.tagBg + ';color:' + p.tagColor + '">' + t + '</span>';
          }).join('');

          var popupHtml =
            '<div class="ra2ce-popup-card">' +
            '<div class="ra2ce-popup-flag">' + p.flag + '</div>' +
            '<div class="ra2ce-popup-title">' + p.title + '</div>' +
            '<div class="ra2ce-popup-loc">' + p.location + ' \u00b7 ' + p.year + '</div>' +
            '<div class="ra2ce-popup-tags">' + tagsHtml + '</div>' +
            '<div class="ra2ce-popup-desc">' + p.desc + '</div>' +
            '<a href="' + p.link + '" target="_blank" rel="noopener" class="ra2ce-popup-btn">' + p.linkLabel + '</a>' +
            '</div>';

          marker.bindPopup(popupHtml, { maxWidth: 300, autoPanPadding: [30, 30] });
          marker.on('click', function () { setActive(p.id); marker.openPopup(); });
          markers[p.id] = marker;
        });

        function goToSlide(idx) {
          var track = document.getElementById('ra2ce-project-list');
          var wrap = document.getElementById('ra2ce-track-wrap');
          var cards = track ? track.querySelectorAll('.ra2ce-proj-card') : [];
          if (!cards.length) return;
          currentSlideIdx = Math.max(0, Math.min(idx, cards.length - 1));
          track.style.transform = 'translateY(-' + cards[currentSlideIdx].offsetTop + 'px)';
          wrap.style.height = cards[currentSlideIdx].offsetHeight + 'px';
          document.querySelectorAll('.ra2ce-slider-dot').forEach(function (d, i) {
            d.classList.toggle('on', i === currentSlideIdx);
          });
          var prevBtn = document.getElementById('ra2ce-prev');
          var nextBtn = document.getElementById('ra2ce-next');
          if (prevBtn) prevBtn.disabled = (currentSlideIdx === 0);
          if (nextBtn) nextBtn.disabled = (currentSlideIdx === cards.length - 1);
        }

        function setActive(id) {
          if (activeId && markers[activeId]) {
            var prev = null;
            for (var i = 0; i < projects.length; i++) {
              if (projects[i].id === activeId) { prev = projects[i]; break; }
            }
            if (prev) markers[activeId].setIcon(makeIcon(prev.accent));
          }
          activeId = id;
          var proj = null;
          for (var j = 0; j < projects.length; j++) {
            if (projects[j].id === id) { proj = projects[j]; break; }
          }
          if (proj && markers[id]) markers[id].setIcon(makePulseIcon(proj.accent));
          document.querySelectorAll('.ra2ce-proj-card').forEach(function (c) { c.classList.remove('active'); });
          var card = document.getElementById('ra2ce-card-' + id);
          if (card) {
            card.classList.add('active');
            var allCards = document.querySelectorAll('.ra2ce-proj-card');
            var idx = Array.prototype.indexOf.call(allCards, card);
            if (idx !== -1) { goToSlide(idx); }
          }
        }

        function renderCards(list) {
          var container = document.getElementById('ra2ce-project-list');
          container.innerHTML = '';
          list.forEach(function (p) {
            var card = document.createElement('a');
            card.href = p.link;
            card.target = '_blank';
            card.rel = 'noopener';
            card.id = 'ra2ce-card-' + p.id;
            card.className = 'ra2ce-proj-card';

            var tagsHtml = p.tagLabels.map(function (t) {
              return '<span class="ra2ce-proj-tag" style="background:' + p.tagBg + ';color:' + p.tagColor + '">' + t + '</span>';
            }).join('');

            card.innerHTML =
              '<div class="ra2ce-proj-inner">' +
              '<div class="ra2ce-proj-accent" style="background:' + p.accent + '"></div>' +
              '<div class="ra2ce-proj-body">' +
              '<div class="ra2ce-proj-top">' +
              '<div class="ra2ce-proj-title">' + p.title + '</div>' +
              '<div class="ra2ce-proj-flag">' + p.flag + '</div>' +
              '</div>' +
              '<span class="ra2ce-proj-location">\ud83d\udccd ' + p.location + ' \u00b7 ' + p.year + '</span>' +
              '<div class="ra2ce-proj-tags">' + tagsHtml + '</div>' +
              '<div class="ra2ce-proj-desc">' + p.desc + '</div>' +
              '<div class="ra2ce-proj-link">' + p.linkLabel + '</div>' +
              '</div>' +
              '</div>';

            card.addEventListener('click', function (e) {
              e.preventDefault();
              setActive(p.id);
              map.flyTo([p.lat, p.lng], Math.max(map.getZoom(), 5), { duration: 0.8 });
              setTimeout(function () { markers[p.id].openPopup(); }, 850);
            });

            container.appendChild(card);
          });

          var countrySet = {};
          list.forEach(function (p) { countrySet[p.flag] = true; });
          var nCountries = Object.keys(countrySet).length;
          document.getElementById('ra2ce-proj-count').textContent =
            list.length + ' project' + (list.length !== 1 ? 's' : '') +
            ' \u00b7 ' + nCountries + ' countr' + (nCountries !== 1 ? 'ies' : 'y');
          var dotsEl = document.getElementById('ra2ce-dots');
          if (dotsEl) {
            dotsEl.innerHTML = '';
            list.forEach(function (_, i) {
              var dot = document.createElement('span');
              dot.className = 'ra2ce-slider-dot' + (i === 0 ? ' on' : '');
              (function (capturedIdx) {
                dot.addEventListener('click', function () { goToSlide(capturedIdx); });
              }(i));
              dotsEl.appendChild(dot);
            });
          }
          setTimeout(function () { goToSlide(0); }, 0);
        }

        window.ra2ceFilterBy = function (tag, btn) {
          document.querySelectorAll('.ra2ce-chip').forEach(function (c) { c.classList.remove('on'); });
          btn.classList.add('on');
          var filtered = tag === 'all'
            ? projects
            : projects.filter(function (p) { return p.tags.indexOf(tag) !== -1; });
          renderCards(filtered);
          projects.forEach(function (p) {
            var visible = filtered.some(function (f) { return f.id === p.id; });
            if (visible) { if (!map.hasLayer(markers[p.id])) markers[p.id].addTo(map); }
            else         { if (map.hasLayer(markers[p.id])) map.removeLayer(markers[p.id]); }
          });
          if (filtered.length > 0) {
            var bounds = L.latLngBounds(filtered.map(function (p) { return [p.lat, p.lng]; }));
            map.flyToBounds(bounds, { padding: [60, 60], duration: 0.8, maxZoom: 6 });
          }
        };

        document.getElementById('ra2ce-prev').addEventListener('click', function () {
          if (currentSlideIdx > 0) { goToSlide(currentSlideIdx - 1); }
        });
        document.getElementById('ra2ce-next').addEventListener('click', function () {
          var cards = document.querySelectorAll('.ra2ce-proj-card');
          if (currentSlideIdx < cards.length - 1) { goToSlide(currentSlideIdx + 1); }
        });

        renderCards(projects);
        var allBounds = L.latLngBounds(projects.map(function (p) { return [p.lat, p.lng]; }));
        map.fitBounds(allBounds, { padding: [50, 50], maxZoom: 5 });

      } // end initMap

      initMap(window.L);

    }());
    </script>

