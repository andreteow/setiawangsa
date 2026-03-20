import { fetchJSON, formatNumber, formatPct, statCard, sortableTable, ETHNICITY_KEYS, AGE_BANDS, AGE_LABELS } from "../utils.js";
import { ethnicityDoughnut, ageBandsBar, barChart, COLORS } from "../charts.js";

export async function renderOverview(container) {
    const data = await fetchJSON("overview.json");
    const { total_voters, gender, age_bands, ethnicity, youth_pct, b40_pct, dm_summary } = data;

    // Find dominant ethnicity
    const topEth = Object.entries(ethnicity).sort((a, b) => b[1] - a[1])[0];

    container.innerHTML = `
        <div class="page-header">
            <h2>P.118 Setiawangsa Overview</h2>
            <p class="subtitle">Constituency-wide voter demographics across 17 Daerah Mengundi</p>
        </div>

        <div class="stat-grid">
            ${statCard("Total Voters", formatNumber(total_voters))}
            ${statCard("Male", formatNumber(gender.male), formatPct(gender.male / total_voters * 100))}
            ${statCard("Female", formatNumber(gender.female), formatPct(gender.female / total_voters * 100))}
            ${statCard("Youth (22-39)", formatPct(youth_pct), formatNumber(age_bands["22-27 (Youth)"] + age_bands["28-39 (Young Adult)"]) + " voters")}
            ${statCard("B40 Proxy", formatPct(b40_pct), "PPR + Flat residents")}
            ${statCard("Largest Group", topEth[0], formatPct(topEth[1] / total_voters * 100))}
        </div>

        <div class="chart-row">
            <div class="chart-card">
                <h3>Age Distribution</h3>
                <div class="chart-container"><canvas id="overview-age"></canvas></div>
            </div>
            <div class="chart-card">
                <h3>Ethnic Composition</h3>
                <div class="chart-container"><canvas id="overview-ethnicity"></canvas></div>
            </div>
        </div>

        <div class="chart-card full-width">
            <h3>Gender Split by DM</h3>
            <div class="chart-container chart-wide"><canvas id="overview-gender"></canvas></div>
        </div>

        <div class="table-card">
            <h3>Daerah Mengundi Summary</h3>
            <p class="table-hint">Click column headers to sort. Click a DM name to view details.</p>
            <table id="dm-table" class="data-table"></table>
        </div>
    `;

    // Charts
    ageBandsBar("overview-age", age_bands);
    ethnicityDoughnut("overview-ethnicity", ethnicity);

    // Gender chart
    const dmNames = dm_summary.map(d => d.name);
    const maleData = dm_summary.map(d => d.male);
    const femaleData = dm_summary.map(d => d.female);
    barChart("overview-gender", dmNames, [
        { label: "Male", data: maleData, backgroundColor: "#6366f1", borderRadius: 4 },
        { label: "Female", data: femaleData, backgroundColor: "#f59e0b", borderRadius: 4 },
    ], {
        scales: {
            x: { ticks: { color: COLORS.textMuted, font: { size: 10 }, maxRotation: 45, minRotation: 45 } },
        },
    });

    // DM table
    const rows = dm_summary.map(d => [
        `<a href="#/dm/${d.slug}" class="table-link">${d.name}</a>`,
        formatNumber(d.voters),
        formatPct(d.youth_pct),
        formatPct(d.b40_pct),
        d.priority_rank != null ? `#${d.priority_rank}` : "—",
    ]);

    // Sort raw values for sorting
    const rawRows = dm_summary.map(d => [
        d.name,
        d.voters,
        d.youth_pct,
        d.b40_pct,
        d.priority_rank ?? 999,
    ]);

    // Manual table since we need links in first column
    const table = document.getElementById("dm-table");
    const headers = ["Daerah Mengundi", "Voters", "Youth %", "B40 %", "Priority"];
    let sortCol = 1, sortDir = "desc";

    function renderTable() {
        const indices = rawRows.map((_, i) => i);
        indices.sort((a, b) => {
            let va = rawRows[a][sortCol], vb = rawRows[b][sortCol];
            if (typeof va === "string") return sortDir === "asc" ? va.localeCompare(vb) : vb.localeCompare(va);
            return sortDir === "asc" ? va - vb : vb - va;
        });

        table.innerHTML = `
            <thead><tr>${headers.map((h, i) => `<th data-col="${i}" class="${i === sortCol ? "sorted " + sortDir : ""}">${h}</th>`).join("")}</tr></thead>
            <tbody>${indices.map(i => `<tr>${rows[i].map((c, j) => `<td${j === 0 ? ' class="name-col"' : ""}>${c}</td>`).join("")}</tr>`).join("")}</tbody>
        `;

        table.querySelectorAll("th").forEach(th => {
            th.addEventListener("click", () => {
                const col = parseInt(th.dataset.col);
                if (col === sortCol) sortDir = sortDir === "asc" ? "desc" : "asc";
                else { sortCol = col; sortDir = col === 0 ? "asc" : "desc"; }
                renderTable();
            });
        });
    }
    renderTable();
}
