/**
 * VER Platform - Main Application
 * Leaflet map + sidebar dashboard for Village Ecological Register data
 */

// --- State ---
let map;
let villageMarkers = [];
let allVillages = [];
let currentVillageData = null;
let charts = {};

// --- Initialize ---
document.addEventListener('DOMContentLoaded', init);

async function init() {
    initMap();
    initEventListeners();
    await loadVillages();
    setLanguage('en');
}

// --- Map Setup ---
function initMap() {
    map = L.map('map', {
        center: [22.5, 78.5], // Center of India
        zoom: 5,
        minZoom: 4,
        maxZoom: 18,
    });

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a> | VER Platform',
        maxZoom: 19,
    }).addTo(map);

    // India Administrative Boundary (Survey of India / Living Atlas)
    // Using dynamicMapLayer for complete boundary rendering (server-side)
    L.esri.dynamicMapLayer({
        url: 'https://livingatlas.esri.in/server/rest/services/IAB2024/India_Administrative_Boundaries_2024/MapServer',
        opacity: 0.6,
        layers: [1],
        interactive: false,
    }).addTo(map);
}

// --- Load GeoJSON Data ---
async function loadVillages() {
    // Try multiple paths to support both local dev and GitHub Pages
    const paths = ['data/villages.geojson', '../data/villages.geojson', './data/villages.geojson'];
    for (const path of paths) {
        try {
            const response = await fetch(path);
            if (!response.ok) continue;
            const geojson = await response.json();
            allVillages = geojson.features;
            renderMarkers(allVillages);
            updateStats(allVillages);
            console.log(`Loaded ${allVillages.length} villages from ${path}`);
            return;
        } catch (err) { /* try next path */ }
    }
    console.error('Failed to load villages from any path');
}

function renderMarkers(features) {
    // Clear existing markers
    villageMarkers.forEach(m => map.removeLayer(m));
    villageMarkers = [];

    const villageIcon = L.divIcon({
        className: 'village-marker',
        html: '<div style="background:#2d6a4f;width:12px;height:12px;border-radius:50%;border:2px solid white;box-shadow:0 1px 3px rgba(0,0,0,0.4);"></div>',
        iconSize: [16, 16],
        iconAnchor: [8, 8],
    });

    features.forEach(feature => {
        const coords = feature.geometry.coordinates;
        const props = feature.properties;

        const marker = L.marker([coords[1], coords[0]], { icon: villageIcon })
            .addTo(map)
            .bindTooltip(
                `<strong>${props.village_name}</strong>${props.village_name_local ? ' (' + props.village_name_local + ')' : ''}<br/>` +
                `${props.block || ''}, ${props.state || ''}<br/>` +
                `<small>${props.total_species_recorded || 0} species | Pop: ${props.population || '?'}</small>`,
                { direction: 'top', offset: [0, -8] }
            );

        marker.on('click', () => openSidebar(props));
        villageMarkers.push(marker);
    });
}

function updateStats(features) {
    const totalSpecies = features.reduce((sum, f) => sum + (f.properties.total_species_recorded || 0), 0);
    document.getElementById('village-count').textContent = `${features.length} ${t('villages_count')}`;
    document.getElementById('species-count').textContent = `${totalSpecies} ${t('species_count')}`;
}

// --- Sidebar ---
async function openSidebar(props) {
    const sidebar = document.getElementById('sidebar');
    sidebar.classList.remove('hidden');

    // Header
    document.getElementById('village-name').textContent =
        props.village_name + (props.village_name_local ? ` (${props.village_name_local})` : '');
    document.getElementById('village-location').textContent =
        [props.gram_panchayat, props.block, props.district, props.state].filter(Boolean).join(', ');
    document.getElementById('data-status').textContent =
        props.data_status ? props.data_status.replace(/_/g, ' ') : '';

    // Overview stats
    document.getElementById('stat-population').textContent = props.population || '-';
    document.getElementById('stat-area').textContent = props.total_area_ha || '-';
    document.getElementById('stat-households').textContent = props.total_households || '-';
    document.getElementById('stat-species').textContent = props.total_species_recorded || '-';

    // Livelihoods
    const livList = document.getElementById('livelihoods-list');
    livList.innerHTML = '';
    (props.livelihoods || []).forEach(l => {
        const li = document.createElement('li');
        li.textContent = l;
        livList.appendChild(li);
    });

    // Load full village data for charts
    await loadFullVillageData(props.data_file || `data/structured/${props.village_id}.json`);

    // Switch to overview tab
    switchTab('overview');
}

async function loadFullVillageData(dataFile) {
    try {
        // Try multiple path resolutions for local dev and GitHub Pages
        let data;
        for (const prefix of ['', '../', 'data/structured/']) {
            try {
                const path = prefix + dataFile;
                const resp = await fetch(path);
                if (resp.ok) {
                    data = await resp.json();
                    break;
                }
            } catch(e) { /* try next */ }
        }
        if (!data) return;

        currentVillageData = data;
        renderLandUseChart(data);
        renderBiodiversityChart(data);
        renderLivestockChart(data);
        renderWaterChart(data);
        renderDocumentTab(data);
    } catch (err) {
        console.error('Failed to load village data:', err);
    }
}

// --- Charts ---
function destroyChart(id) {
    if (charts[id]) {
        charts[id].destroy();
        delete charts[id];
    }
}

function renderLandUseChart(data) {
    destroyChart('landuse');
    const land = data.section_2_general_info?.land_details || {};
    const values = [
        land.forest_land_ha || 0,
        land.grazing_land_ha || 0,
        land.agricultural_land_ha || 0,
        land.revenue_wasteland_ha || 0,
        land.other_ha || 0,
    ];

    if (values.every(v => v === 0)) return;

    const ctx = document.getElementById('chart-landuse').getContext('2d');
    charts.landuse = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: [t('forest'), t('grazing'), t('agriculture'), t('wasteland'), t('other')],
            datasets: [{
                data: values,
                backgroundColor: ['#2d6a4f', '#95d5b2', '#d4a373', '#bc6c25', '#adb5bd'],
            }]
        },
        options: {
            responsive: true,
            plugins: { legend: { position: 'bottom', labels: { font: { size: 11 } } } }
        }
    });
}

function renderBiodiversityChart(data) {
    destroyChart('biodiversity');
    const flora = data.section_20_flora_fauna || {};
    const groups = {
        trees: flora.trees?.length || 0,
        shrubs: flora.shrubs?.length || 0,
        herbs_grasses: flora.herbs_and_grasses?.length || 0,
        mammals: flora.mammals?.length || 0,
        birds: flora.birds?.length || 0,
        reptiles: flora.reptiles_amphibians?.length || 0,
        butterflies: flora.butterflies?.length || 0,
        dragonflies: flora.dragonflies?.length || 0,
        fish_insects: flora.fish_insects_others?.length || 0,
        soil_macrofauna: flora.soil_macrofauna?.length || 0,
    };

    const labels = Object.keys(groups).map(k => t(k));
    const values = Object.values(groups);

    if (values.every(v => v === 0)) {
        document.getElementById('chart-biodiversity').parentElement.innerHTML =
            `<h3>${t('biodiversity_summary')}</h3><p>${t('no_data')}</p>`;
        return;
    }

    const ctx = document.getElementById('chart-biodiversity').getContext('2d');
    charts.biodiversity = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: t('species_recorded'),
                data: values,
                backgroundColor: '#40916c',
            }]
        },
        options: {
            responsive: true,
            indexAxis: 'y',
            plugins: { legend: { display: false } },
            scales: { x: { beginAtZero: true, ticks: { stepSize: 1 } } }
        }
    });

    // Species tags
    const listsEl = document.getElementById('species-lists');
    listsEl.innerHTML = '';
    const groupKeys = ['trees', 'shrubs', 'herbs_and_grasses', 'mammals', 'birds',
                       'reptiles_amphibians', 'butterflies', 'dragonflies'];
    groupKeys.forEach(key => {
        const items = flora[key] || [];
        if (items.length === 0) return;
        const div = document.createElement('div');
        div.className = 'species-group';
        const tKey = key.replace('_and_', '_').replace('_amphibians', '');
        div.innerHTML = `<h4>${t(tKey) || key} (${items.length})</h4>`;
        items.forEach(sp => {
            const tag = document.createElement('span');
            tag.className = 'species-tag';
            tag.textContent = sp.local_name || sp.local_name_script || sp.guide_name || '?';
            div.appendChild(tag);
        });
        listsEl.appendChild(div);
    });
}

function renderLivestockChart(data) {
    destroyChart('livestock');
    const livestock = data.section_5_livestock?.livestock_numbers || [];
    if (livestock.length === 0) return;

    const labels = livestock.map(l => l.type || l.type_local || '?');
    const currentData = livestock.map(l => l.current_count || 0);
    const trend10 = livestock.map(l => typeof l.trend_10yr === 'number' ? l.trend_10yr : 0);
    const trend25 = livestock.map(l => typeof l.trend_25yr === 'number' ? l.trend_25yr : 0);
    const trend50 = livestock.map(l => typeof l.trend_50yr === 'number' ? l.trend_50yr : 0);

    const ctx = document.getElementById('chart-livestock').getContext('2d');
    charts.livestock = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                { label: t('current'), data: currentData, backgroundColor: '#2d6a4f' },
                { label: t('years_ago_10'), data: trend10, backgroundColor: '#40916c' },
                { label: t('years_ago_25'), data: trend25, backgroundColor: '#95d5b2' },
                { label: t('years_ago_50'), data: trend50, backgroundColor: '#d8f3dc' },
            ]
        },
        options: {
            responsive: true,
            plugins: { legend: { position: 'bottom', labels: { font: { size: 11 } } } },
            scales: { y: { beginAtZero: true } }
        }
    });

    // Table
    const tableContainer = document.getElementById('livestock-table-container');
    let html = '<table class="data-table"><thead><tr>';
    html += `<th>Type</th><th>${t('current')}</th><th>${t('years_ago_10')}</th><th>${t('years_ago_25')}</th><th>${t('years_ago_50')}</th><th>Reason</th>`;
    html += '</tr></thead><tbody>';
    livestock.forEach(l => {
        html += `<tr><td>${l.type || l.type_local}</td>`;
        html += `<td><strong>${l.current_count || 0}</strong></td>`;
        html += `<td>${formatTrend(l.trend_10yr)}</td>`;
        html += `<td>${formatTrend(l.trend_25yr)}</td>`;
        html += `<td>${formatTrend(l.trend_50yr)}</td>`;
        html += `<td>${l.reason_for_change || ''}</td></tr>`;
    });
    html += '</tbody></table>';
    tableContainer.innerHTML = html;
}

function renderWaterChart(data) {
    destroyChart('water');
    const drinking = data.section_6_waterscape?.drinking_water || [];
    if (drinking.length === 0) return;

    const labels = drinking.map(w => t(w.source_type) || w.source_type);
    const values = drinking.map(w => w.total_count || 0);

    const ctx = document.getElementById('chart-water').getContext('2d');
    charts.water = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: t('drinking_domestic'),
                data: values,
                backgroundColor: '#0077b6',
            }]
        },
        options: {
            responsive: true,
            plugins: { legend: { display: false } },
            scales: { y: { beginAtZero: true } }
        }
    });

    // Water details
    const detailsEl = document.getElementById('water-details');
    let html = `<h3>${t('livestock_use')}</h3>`;
    const livestockWater = data.section_6_waterscape?.livestock_water || [];
    if (livestockWater.length > 0) {
        html += '<ul>';
        livestockWater.forEach(w => {
            html += `<li>${t(w.source_type) || w.source_type}: ${w.total_count || 0} (${w.availability_months?.replace(/_/g, ' ') || ''})</li>`;
        });
        html += '</ul>';
    }

    const irrigation = data.section_6_waterscape?.irrigation_sources;
    if (irrigation) {
        html += `<h3>Irrigation</h3><p>${irrigation}</p>`;
    }
    detailsEl.innerHTML = html;
}

function renderDocumentTab(data) {
    // Village history
    const hist = data.section_3_village_history?.village_history;
    const histText = document.getElementById('village-history-text');
    if (hist) {
        histText.textContent = hist.narrative_local || hist.narrative || t('no_data');
    } else {
        histText.textContent = t('no_data');
    }

    // Photos with geotagging
    const gallery = document.getElementById('photo-gallery');
    gallery.innerHTML = '';
    const photos = data.photos || [];

    // Destroy previous photo map
    if (charts.photoMap) {
        charts.photoMap.remove();
        charts.photoMap = null;
    }

    if (photos.length > 0) {
        // Build photo mini-map for geotagged photos
        const geoPhotos = photos.filter(p => p.coordinates?.latitude && p.coordinates?.longitude);
        if (geoPhotos.length > 0) {
            const photoMap = L.map('photo-map', { scrollWheelZoom: false, zoomControl: true });
            L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                attribution: '&copy; OSM', maxZoom: 19,
            }).addTo(photoMap);

            const bounds = [];
            const cameraIcon = L.divIcon({
                className: 'photo-marker',
                html: '<div style="background:#e63946;width:14px;height:14px;border-radius:50%;border:2px solid white;box-shadow:0 1px 3px rgba(0,0,0,0.5);cursor:pointer;"></div>',
                iconSize: [18, 18], iconAnchor: [9, 9],
            });

            geoPhotos.forEach(p => {
                const ll = [p.coordinates.latitude, p.coordinates.longitude];
                bounds.push(ll);
                L.marker(ll, { icon: cameraIcon })
                    .addTo(photoMap)
                    .bindPopup(
                        `<div style="max-width:200px;"><img src="${p.image_path}" style="width:100%;border-radius:4px;"/><br/>` +
                        `<small><strong>${p.caption || ''}</strong></small>` +
                        (p.elevation_m ? `<br/><small>Elev: ${p.elevation_m}m</small>` : '') +
                        (p.timestamp ? `<br/><small>${p.timestamp}</small>` : '') +
                        `</div>`, { maxWidth: 220 }
                    );
            });

            photoMap.fitBounds(bounds, { padding: [30, 30], maxZoom: 16 });
            charts.photoMap = photoMap;
        } else {
            document.getElementById('photo-map').style.display = 'none';
        }

        // Photo gallery cards
        photos.forEach(p => {
            if (!p.image_path) return;
            const card = document.createElement('div');
            card.className = 'photo-card';
            const hasGeo = p.coordinates?.latitude && p.coordinates?.longitude;
            card.innerHTML =
                `<img src="${p.image_path}" alt="${p.caption || ''}" loading="lazy"/>` +
                `<div class="photo-info">` +
                `<p class="photo-caption">${p.caption_local || p.caption || ''}</p>` +
                (hasGeo ? `<p class="photo-coords"><small>${p.coordinates.latitude.toFixed(4)}°N, ${p.coordinates.longitude.toFixed(4)}°E` +
                    (p.elevation_m ? ` | ${p.elevation_m}m` : '') + `</small></p>` : '') +
                (p.category ? `<span class="photo-category">${p.category.replace(/_/g, ' ')}</span>` : '') +
                `</div>`;
            gallery.appendChild(card);
        });
    } else {
        document.getElementById('photo-map').style.display = 'none';
        gallery.innerHTML = `<p>${t('no_data')}</p>`;
    }

    // Download link
    const vid = data.metadata?.village_id || 'village';
    document.getElementById('download-json').href = `data/structured/${vid}.json`;
}

// --- Helpers ---
function formatTrend(value) {
    if (typeof value === 'number') return value.toString();
    if (value === 'increase') return '<span class="trend-up">&#9650;</span>';
    if (value === 'decrease') return '<span class="trend-down">&#9660;</span>';
    if (value === 'stable') return '<span class="trend-stable">&#9654;</span>';
    return '-';
}

function switchTab(tabName) {
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.tab === tabName);
    });
    document.querySelectorAll('.tab-content').forEach(tc => {
        tc.classList.toggle('active', tc.id === `tab-${tabName}`);
    });
}

// --- Event Listeners ---
function initEventListeners() {
    // Sidebar close
    document.getElementById('sidebar-close').addEventListener('click', () => {
        document.getElementById('sidebar').classList.add('hidden');
    });

    // Tab switching
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => switchTab(btn.dataset.tab));
    });

    // Language toggle
    document.querySelectorAll('.lang-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            setLanguage(btn.dataset.lang);
            if (allVillages.length > 0) updateStats(allVillages);
        });
    });

    // Search with dropdown suggestions
    const searchInput = document.getElementById('search-input');
    const searchDropdown = document.getElementById('search-dropdown');

    searchInput.addEventListener('input', (e) => {
        const query = e.target.value.toLowerCase();
        if (!query) {
            searchDropdown.classList.add('hidden');
            renderMarkers(allVillages);
            updateStats(allVillages);
            return;
        }
        const filtered = allVillages.filter(f => {
            const p = f.properties;
            return (p.village_name || '').toLowerCase().includes(query) ||
                   (p.village_name_local || '').includes(query) ||
                   (p.state || '').toLowerCase().includes(query) ||
                   (p.block || '').toLowerCase().includes(query);
        });
        renderMarkers(filtered);
        updateStats(filtered);
        showSearchDropdown(filtered);
    });

    searchInput.addEventListener('focus', () => {
        if (searchInput.value) {
            const filtered = allVillages.filter(f => {
                const p = f.properties;
                const q = searchInput.value.toLowerCase();
                return (p.village_name || '').toLowerCase().includes(q) ||
                       (p.village_name_local || '').includes(q);
            });
            showSearchDropdown(filtered);
        } else {
            showSearchDropdown(allVillages);
        }
    });

    document.addEventListener('click', (e) => {
        if (!searchInput.contains(e.target) && !searchDropdown.contains(e.target)) {
            searchDropdown.classList.add('hidden');
        }
    });

    // State filter with village list
    document.getElementById('state-filter').addEventListener('change', (e) => {
        const state = e.target.value;
        if (state === 'all') {
            renderMarkers(allVillages);
            updateStats(allVillages);
            showSearchDropdown(allVillages);
        } else {
            const filtered = allVillages.filter(f =>
                (f.properties.state || '').toLowerCase().replace(/\s+/g, '_') === state
            );
            renderMarkers(filtered);
            updateStats(filtered);
            showSearchDropdown(filtered);
            if (filtered.length > 0) {
                const coords = filtered[0].geometry.coordinates;
                map.setView([coords[1], coords[0]], 8);
            }
        }
    });
}

// --- Search Dropdown ---
function showSearchDropdown(villages) {
    const dropdown = document.getElementById('search-dropdown');
    dropdown.innerHTML = '';

    if (villages.length === 0) {
        dropdown.innerHTML = '<div class="search-item no-results">No villages found</div>';
        dropdown.classList.remove('hidden');
        return;
    }

    villages.forEach(f => {
        const p = f.properties;
        const item = document.createElement('div');
        item.className = 'search-item';
        item.innerHTML = `<strong>${p.village_name}</strong>${p.village_name_local ? ' (' + p.village_name_local + ')' : ''}` +
            `<br/><small>${[p.block, p.district, p.state].filter(Boolean).join(', ')} | ${p.total_species_recorded || 0} species</small>`;
        item.addEventListener('click', () => {
            dropdown.classList.add('hidden');
            document.getElementById('search-input').value = p.village_name;
            const coords = f.geometry.coordinates;
            map.setView([coords[1], coords[0]], 12);
            openSidebar(p);
        });
        dropdown.appendChild(item);
    });

    dropdown.classList.remove('hidden');
}
