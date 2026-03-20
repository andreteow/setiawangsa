import { fetchJSON, formatNumber, formatPct, statCard, ETHNICITY_KEYS, AGE_BANDS, AGE_LABELS, ETHNICITY_COLORS, HOUSING_COLORS } from "../utils.js";
import { ethnicityDoughnut, ageBandsBar, housingDoughnut, horizontalBarChart, barChart, COLORS } from "../charts.js";

export async function renderDmDetail(container, slug) {
    const data = await fetchJSON(`dm/${slug}.json`);
    const { name, voters, age_bands, ethnicity, gender, housing, migration, youth_pct, priority, lokaliti } = data;

    const topEth = Object.entries(ethnicity).sort((a, b) => b[1] - a[1])[0];

    container.innerHTML = `
        <div class="page-header">
            <div class="breadcrumb">
                <a href="#/overview">Overview</a> <span>/</span> <span>${name}</span>
            </div>
            <h2>${name}</h2>
            <div class="header-badges">
                ${priority.rank ? `<span class="badge badge-primary">Priority #${priority.rank}</span>` : ""}
                <span class="badge">${formatNumber(voters.total)} voters</span>
            </div>
        </div>

        <div class="stat-grid">
            ${statCard("Total Voters", formatNumber(voters.total))}
            ${statCard("Male", formatNumber(voters.male), formatPct(gender.male_pct))}
            ${statCard("Female", formatNumber(voters.female), formatPct(gender.female_pct))}
            ${statCard("Youth (22-39)", formatPct(youth_pct))}
            ${statCard("B40 Proxy", formatPct(housing.b40_pct || 0), formatNumber(housing.b40_proxy || 0) + " voters")}
            ${statCard("Priority Score", priority.score ? priority.score.toFixed(4) : "—")}
        </div>

        <div class="chart-row">
            <div class="chart-card">
                <h3>Age Distribution</h3>
                <div class="chart-container"><canvas id="dm-age"></canvas></div>
            </div>
            <div class="chart-card">
                <h3>Ethnic Composition</h3>
                <div class="chart-container"><canvas id="dm-ethnicity"></canvas></div>
            </div>
        </div>

        <div class="chart-row">
            <div class="chart-card">
                <h3>Housing / Income Proxy</h3>
                <div class="chart-container"><canvas id="dm-housing"></canvas></div>
            </div>
            <div class="chart-card">
                <h3>Migration Origins (Top 5)</h3>
                <div class="chart-container"><canvas id="dm-migration"></canvas></div>
            </div>
        </div>

        <div class="table-card">
            <h3>Lokaliti in ${name}</h3>
            <p class="table-hint">Click a lokaliti name to view details. Click column headers to sort.</p>
            <table id="lokaliti-table" class="data-table"></table>
        </div>
    `;

    // Charts
    ageBandsBar("dm-age", age_bands);
    ethnicityDoughnut("dm-ethnicity", ethnicity);

    // Housing doughnut
    if (housing.b40_proxy != null) {
        const housingData = {
            "B40 (PPR/Flat)": housing.b40_proxy,
            "Middle-class": housing.middle_class,
            "Institutional": housing.institutional,
        };
        // Filter out zeros
        const filtered = Object.fromEntries(Object.entries(housingData).filter(([, v]) => v > 0));
        const labels = Object.keys(filtered);
        const values = Object.values(filtered);
        const colors = ["#ef4444", "#10b981", "#71717a"];
        import("../charts.js").then(m => m.doughnutChart("dm-housing", labels, values, colors.slice(0, labels.length)));
    }

    // Migration
    if (migration.top_origins.length) {
        const origins = migration.top_origins.sort((a, b) => b.voters - a.voters);
        horizontalBarChart(
            "dm-migration",
            origins.map(o => o.state),
            origins.map(o => o.voters),
            origins.map(() => COLORS.primaryLight),
        );
    }

    // Lokaliti table
    const headers = ["Lokaliti", "Voters", "Top Ethnicity", "Priority"];
    let sortCol = 1, sortDir = "desc";

    const lokData = lokaliti.map(l => {
        const topE = Object.entries(l.ethnicity).sort((a, b) => b[1] - a[1])[0];
        return {
            name: l.name,
            voters: l.voters,
            topEth: topE ? topE[0] : "—",
            topEthPct: topE ? Math.round(topE[1] / l.voters * 100) : 0,
            priRank: l.priority_rank,
        };
    });

    function renderLokTable() {
        const sorted = [...lokData];
        sorted.sort((a, b) => {
            const keys = ["name", "voters", "topEth", "priRank"];
            let va = sorted.indexOf(a), vb = sorted.indexOf(b);
            if (sortCol === 0) { va = a.name; vb = b.name; }
            else if (sortCol === 1) { va = a.voters; vb = b.voters; }
            else if (sortCol === 2) { va = a.topEth; vb = b.topEth; }
            else if (sortCol === 3) { va = a.priRank ?? 999; vb = b.priRank ?? 999; }
            if (typeof va === "string") return sortDir === "asc" ? va.localeCompare(vb) : vb.localeCompare(va);
            return sortDir === "asc" ? va - vb : vb - va;
        });

        const table = document.getElementById("lokaliti-table");
        table.innerHTML = `
            <thead><tr>${headers.map((h, i) => `<th data-col="${i}" class="${i === sortCol ? "sorted " + sortDir : ""}">${h}</th>`).join("")}</tr></thead>
            <tbody>${sorted.map(l => `
                <tr class="lokaliti-row" data-name="${encodeURIComponent(l.name)}" data-dm="${slug}">
                    <td class="name-col"><a href="#/dm/${slug}/lokaliti/${encodeURIComponent(l.name)}" class="table-link">${l.name}</a></td>
                    <td>${formatNumber(l.voters)}</td>
                    <td>${l.topEth} (${l.topEthPct}%)</td>
                    <td>${l.priRank ? "#" + l.priRank : "—"}</td>
                </tr>
            `).join("")}</tbody>
        `;

        table.querySelectorAll("th").forEach(th => {
            th.addEventListener("click", () => {
                const col = parseInt(th.dataset.col);
                if (col === sortCol) sortDir = sortDir === "asc" ? "desc" : "asc";
                else { sortCol = col; sortDir = col === 0 ? "asc" : "desc"; }
                renderLokTable();
            });
        });
    }
    renderLokTable();
}
