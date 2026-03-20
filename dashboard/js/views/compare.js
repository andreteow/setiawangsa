import { fetchJSON, formatNumber, formatPct, ETHNICITY_KEYS, AGE_BANDS, AGE_LABELS, slugify, ETHNICITY_COLORS } from "../utils.js";
import { barChart, doughnutChart, COLORS } from "../charts.js";

export async function renderCompare(container, params) {
    const overview = await fetchJSON("overview.json");
    const lokIndex = await fetchJSON("lokaliti-index.json");

    // Parse params
    const searchParams = new URLSearchParams(params);
    const mode = searchParams.get("mode") || "dm";
    const aSlug = searchParams.get("a") || "";
    const bSlug = searchParams.get("b") || "";

    container.innerHTML = `
        <div class="page-header">
            <h2>Compare Areas</h2>
            <p class="subtitle">Side-by-side comparison of two Daerah Mengundi or Lokaliti</p>
        </div>

        <div class="compare-controls">
            <div class="tab-group">
                <button class="tab-btn ${mode === "dm" ? "active" : ""}" data-mode="dm">Compare DMs</button>
                <button class="tab-btn ${mode === "lokaliti" ? "active" : ""}" data-mode="lokaliti">Compare Lokaliti</button>
            </div>
            <div class="compare-pickers">
                <select id="pick-a" class="select-input">
                    <option value="">Select Area A</option>
                </select>
                <span class="vs-badge">VS</span>
                <select id="pick-b" class="select-input">
                    <option value="">Select Area B</option>
                </select>
            </div>
        </div>

        <div id="compare-content"></div>
    `;

    // Tab switching
    container.querySelectorAll(".tab-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            window.location.hash = `#/compare?mode=${btn.dataset.mode}`;
        });
    });

    // Populate dropdowns
    const pickA = document.getElementById("pick-a");
    const pickB = document.getElementById("pick-b");

    if (mode === "dm") {
        overview.dm_summary.forEach(d => {
            pickA.add(new Option(d.name, d.slug, false, d.slug === aSlug));
            pickB.add(new Option(d.name, d.slug, false, d.slug === bSlug));
        });
    } else {
        // Group lokaliti by DM
        const byDm = {};
        lokIndex.forEach(l => {
            if (!byDm[l.dm]) byDm[l.dm] = [];
            byDm[l.dm].push(l);
        });
        Object.keys(byDm).sort().forEach(dm => {
            const grpA = document.createElement("optgroup");
            grpA.label = dm;
            const grpB = document.createElement("optgroup");
            grpB.label = dm;
            byDm[dm].forEach(l => {
                const val = `${l.dm_slug}::${encodeURIComponent(l.name)}`;
                grpA.add(new Option(`${l.name} (${l.voters})`, val, false, val === aSlug));
                grpB.add(new Option(`${l.name} (${l.voters})`, val, false, val === bSlug));
            });
            pickA.add(grpA);
            pickB.add(grpB);
        });
    }

    function onPickChange() {
        const a = pickA.value;
        const b = pickB.value;
        if (a && b) {
            window.location.hash = `#/compare?mode=${mode}&a=${a}&b=${b}`;
        }
    }
    pickA.addEventListener("change", onPickChange);
    pickB.addEventListener("change", onPickChange);

    // Render comparison if both selected
    if (aSlug && bSlug) {
        if (mode === "dm") {
            await renderDmComparison(aSlug, bSlug);
        } else {
            await renderLokComparison(aSlug, bSlug);
        }
    }
}

async function renderDmComparison(slugA, slugB) {
    const [a, b] = await Promise.all([
        fetchJSON(`dm/${slugA}.json`),
        fetchJSON(`dm/${slugB}.json`),
    ]);

    const content = document.getElementById("compare-content");
    content.innerHTML = `
        <div class="compare-grid">
            <div class="compare-header">
                <div class="compare-title area-a">${a.name}</div>
                <div class="compare-title metric">Metric</div>
                <div class="compare-title area-b">${b.name}</div>
            </div>
            ${compareRow("Total Voters", formatNumber(a.voters.total), formatNumber(b.voters.total), a.voters.total, b.voters.total)}
            ${compareRow("Male %", formatPct(a.gender.male_pct), formatPct(b.gender.male_pct))}
            ${compareRow("Youth (22-39)", formatPct(a.youth_pct), formatPct(b.youth_pct), a.youth_pct, b.youth_pct, true)}
            ${compareRow("B40 %", formatPct(a.housing.b40_pct || 0), formatPct(b.housing.b40_pct || 0), a.housing.b40_pct || 0, b.housing.b40_pct || 0, true)}
            ${compareRow("Priority Rank", a.priority.rank ? "#" + a.priority.rank : "—", b.priority.rank ? "#" + b.priority.rank : "—", a.priority.rank || 999, b.priority.rank || 999, false, true)}
            ${compareRow("Priority Score", a.priority.score?.toFixed(4) || "—", b.priority.score?.toFixed(4) || "—", a.priority.score || 0, b.priority.score || 0, true)}
        </div>

        <div class="chart-row">
            <div class="chart-card">
                <h3>Age Distribution</h3>
                <div class="chart-container"><canvas id="cmp-age"></canvas></div>
            </div>
            <div class="chart-card">
                <h3>Ethnicity</h3>
                <div class="chart-container"><canvas id="cmp-eth"></canvas></div>
            </div>
        </div>
    `;

    // Age comparison
    barChart("cmp-age", AGE_LABELS, [
        { label: a.name, data: AGE_BANDS.map(band => a.age_bands[band] || 0), backgroundColor: "#6366f1", borderRadius: 4 },
        { label: b.name, data: AGE_BANDS.map(band => b.age_bands[band] || 0), backgroundColor: "#f59e0b", borderRadius: 4 },
    ]);

    // Ethnicity comparison
    barChart("cmp-eth", ETHNICITY_KEYS, [
        { label: a.name, data: ETHNICITY_KEYS.map(k => a.ethnicity[k] || 0), backgroundColor: "#6366f1", borderRadius: 4 },
        { label: b.name, data: ETHNICITY_KEYS.map(k => b.ethnicity[k] || 0), backgroundColor: "#f59e0b", borderRadius: 4 },
    ]);
}

async function renderLokComparison(valA, valB) {
    const [dmSlugA, lokNameA] = valA.split("::");
    const [dmSlugB, lokNameB] = valB.split("::");

    const [dmA, dmB] = await Promise.all([
        fetchJSON(`dm/${dmSlugA}.json`),
        fetchJSON(`dm/${dmSlugB}.json`),
    ]);

    const a = dmA.lokaliti.find(l => encodeURIComponent(l.name) === lokNameA);
    const b = dmB.lokaliti.find(l => encodeURIComponent(l.name) === lokNameB);

    if (!a || !b) {
        document.getElementById("compare-content").innerHTML = `<p class="error-text">Could not find one or both lokaliti.</p>`;
        return;
    }

    const content = document.getElementById("compare-content");
    content.innerHTML = `
        <div class="compare-grid">
            <div class="compare-header">
                <div class="compare-title area-a">${a.name}<br><small>${dmA.name}</small></div>
                <div class="compare-title metric">Metric</div>
                <div class="compare-title area-b">${b.name}<br><small>${dmB.name}</small></div>
            </div>
            ${compareRow("Total Voters", formatNumber(a.voters), formatNumber(b.voters), a.voters, b.voters)}
            ${compareRow("Priority Rank", a.priority_rank ? "#" + a.priority_rank : "—", b.priority_rank ? "#" + b.priority_rank : "—", a.priority_rank || 999, b.priority_rank || 999, false, true)}
        </div>

        <div class="chart-row">
            <div class="chart-card">
                <h3>Age Distribution</h3>
                <div class="chart-container"><canvas id="cmp-age"></canvas></div>
            </div>
            <div class="chart-card">
                <h3>Ethnicity</h3>
                <div class="chart-container"><canvas id="cmp-eth"></canvas></div>
            </div>
        </div>
    `;

    barChart("cmp-age", AGE_LABELS, [
        { label: a.name, data: AGE_BANDS.map(band => a.age_bands[band] || 0), backgroundColor: "#6366f1", borderRadius: 4 },
        { label: b.name, data: AGE_BANDS.map(band => b.age_bands[band] || 0), backgroundColor: "#f59e0b", borderRadius: 4 },
    ]);

    barChart("cmp-eth", ETHNICITY_KEYS, [
        { label: a.name, data: ETHNICITY_KEYS.map(k => a.ethnicity[k] || 0), backgroundColor: "#6366f1", borderRadius: 4 },
        { label: b.name, data: ETHNICITY_KEYS.map(k => b.ethnicity[k] || 0), backgroundColor: "#f59e0b", borderRadius: 4 },
    ]);
}

function compareRow(metric, valA, valB, numA, numB, higherBetter = true, lowerBetter = false) {
    let classA = "", classB = "";
    if (numA != null && numB != null) {
        if (lowerBetter) {
            if (numA < numB) classA = "highlight-better";
            else if (numB < numA) classB = "highlight-better";
        } else if (higherBetter) {
            if (numA > numB) classA = "highlight-better";
            else if (numB > numA) classB = "highlight-better";
        }
    }
    return `
        <div class="compare-row">
            <div class="compare-val ${classA}">${valA}</div>
            <div class="compare-metric">${metric}</div>
            <div class="compare-val ${classB}">${valB}</div>
        </div>
    `;
}
