import { fetchJSON, formatNumber, formatPct, statCard, ETHNICITY_KEYS, AGE_BANDS, AGE_LABELS, ETHNICITY_COLORS, HOUSING_COLORS } from "../utils.js";
import { doughnutChart, stackedBarChart, barChart, horizontalBarChart, COLORS } from "../charts.js";

export async function renderHousing(container) {
    const data = await fetchJSON("housing.json");
    const { type_summary, by_ethnicity, by_age, income_proxy_by_dm, household_size } = data;

    const totalVoters = type_summary.reduce((s, t) => s + t.voters, 0);
    const pprFlat = type_summary.filter(t => t.type === "PPR" || t.type === "Flat").reduce((s, t) => s + t.voters, 0);
    const tamanCondo = type_summary.filter(t => t.type === "Taman" || t.type === "Condo/Apartment").reduce((s, t) => s + t.voters, 0);

    container.innerHTML = `
        <div class="page-header">
            <h2>Housing & Socioeconomic</h2>
            <p class="subtitle">Voter distribution by housing type as a proxy for socioeconomic status</p>
        </div>

        <div class="stat-grid">
            ${statCard("B40 Proxy (PPR+Flat)", formatNumber(pprFlat), formatPct(pprFlat / totalVoters * 100))}
            ${statCard("Middle Class (Taman+Condo)", formatNumber(tamanCondo), formatPct(tamanCondo / totalVoters * 100))}
            ${statCard("Institutional", formatNumber(type_summary.find(t => t.type === "Institutional")?.voters || 0), "MINDEF + PULAPOL")}
            ${statCard("PPR Voters", formatNumber(type_summary.find(t => t.type === "PPR")?.voters || 0), "Lowest income tier")}
        </div>

        <div class="chart-row">
            <div class="chart-card">
                <h3>Housing Type Distribution</h3>
                <div class="chart-container"><canvas id="hs-type"></canvas></div>
            </div>
            <div class="chart-card">
                <h3>Housing Type Summary</h3>
                <div class="detail-table">
                    <table class="data-table compact">
                        <thead><tr><th>Type</th><th>Voters</th><th>%</th></tr></thead>
                        <tbody>
                            ${type_summary.map(t => `
                                <tr>
                                    <td>${t.type}</td>
                                    <td>${formatNumber(t.voters)}</td>
                                    <td>${formatPct(t.pct)}</td>
                                </tr>
                            `).join("")}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <div class="chart-row">
            <div class="chart-card">
                <h3>Ethnicity by Housing Type</h3>
                <div class="chart-container"><canvas id="hs-eth"></canvas></div>
            </div>
            <div class="chart-card">
                <h3>Age by Housing Type</h3>
                <div class="chart-container"><canvas id="hs-age"></canvas></div>
            </div>
        </div>

        <div class="chart-card full-width">
            <h3>B40 vs Middle-Class by DM</h3>
            <div class="chart-container chart-wide"><canvas id="hs-income"></canvas></div>
        </div>

        <div class="chart-row">
            <div class="chart-card">
                <h3>Household Size Distribution</h3>
                <div class="chart-container"><canvas id="hs-hh"></canvas></div>
            </div>
            <div class="chart-card">
                <h3>Household Summary</h3>
                <div class="detail-table">
                    <table class="data-table compact">
                        <thead><tr><th>Size</th><th>Households</th><th>Voters</th><th>Avg Size</th></tr></thead>
                        <tbody>
                            ${household_size.map(h => `
                                <tr>
                                    <td>${h.category}</td>
                                    <td>${formatNumber(h.households)}</td>
                                    <td>${formatNumber(h.voters)}</td>
                                    <td>${h.avg_size.toFixed(2)}</td>
                                </tr>
                            `).join("")}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    `;

    // Housing type doughnut
    const htLabels = type_summary.map(t => t.type);
    const htValues = type_summary.map(t => t.voters);
    const htColors = htLabels.map(l => HOUSING_COLORS[l] || COLORS.muted);
    doughnutChart("hs-type", htLabels, htValues, htColors);

    // Ethnicity by housing (stacked bar)
    const ethLabels = by_ethnicity.map(e => e.type);
    stackedBarChart("hs-eth", ethLabels, ETHNICITY_KEYS.map(k => ({
        label: k,
        data: by_ethnicity.map(e => e[k]),
        backgroundColor: ETHNICITY_COLORS[k],
    })));

    // Age by housing (stacked bar)
    const ageLabels = by_age.map(a => a.type);
    const ageColors = ["#818cf8", "#6366f1", "#4f46e5", "#3730a3"];
    stackedBarChart("hs-age", ageLabels, AGE_BANDS.map((band, i) => ({
        label: AGE_LABELS[i],
        data: by_age.map(a => a[band]),
        backgroundColor: ageColors[i],
    })));

    // Income proxy by DM
    const incSorted = [...income_proxy_by_dm].sort((a, b) => b.b40_pct - a.b40_pct);
    barChart("hs-income", incSorted.map(d => d.dm), [
        { label: "B40 Proxy", data: incSorted.map(d => d.b40_proxy), backgroundColor: "#ef4444", borderRadius: 4 },
        { label: "Middle-class", data: incSorted.map(d => d.middle_class), backgroundColor: "#10b981", borderRadius: 4 },
    ], {
        scales: {
            x: { stacked: true, ticks: { font: { size: 10 }, maxRotation: 45, minRotation: 45, color: COLORS.textMuted } },
            y: { stacked: true },
        },
    });

    // Household size bar
    barChart("hs-hh", household_size.map(h => h.category), [{
        data: household_size.map(h => h.households),
        backgroundColor: "#6366f1",
        borderRadius: 4,
    }], { plugins: { legend: { display: false } } });
}
