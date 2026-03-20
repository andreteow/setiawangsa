import { fetchJSON, formatNumber, formatPct, statCard, COLORS } from "../utils.js";
import { horizontalBarChart, barChart, scatterChart } from "../charts.js";

export async function renderPriority(container) {
    const data = await fetchJSON("priority.json");
    const { dm_rankings, lokaliti_rankings, institutional_zones } = data;

    // Constituency totals from institutional
    const constTotal = institutional_zones.find(z => z.group === "Constituency Total");
    const civTotal = institutional_zones.find(z => z.group === "Civilian Total");
    const instTotal = institutional_zones.find(z => z.group === "Institutional Total");

    container.innerHTML = `
        <div class="page-header">
            <h2>Priority & Canvassing</h2>
            <p class="subtitle">Strategic targeting for MUDA's ground game. Priority score weights: Youth 35%, Diversity 25%, B40 25%, Household Density 15%.</p>
        </div>

        <div class="stat-grid">
            ${statCard("Civilian Voters", formatNumber(civTotal?.total || 0), formatPct(civTotal?.pct_of_total || 0))}
            ${statCard("Institutional", formatNumber(instTotal?.total || 0), "MINDEF + PULAPOL")}
            ${statCard("#1 Priority DM", dm_rankings[0]?.name || "—", "Score: " + (dm_rankings[0]?.priority_score?.toFixed(4) || "—"))}
            ${statCard("#1 Priority Lokaliti", lokaliti_rankings[0]?.name || "—", "Score: " + (lokaliti_rankings[0]?.priority_score?.toFixed(4) || "—"))}
        </div>

        <div class="chart-row">
            <div class="chart-card">
                <h3>DM Priority Ranking</h3>
                <div class="chart-container chart-tall"><canvas id="pri-dm-bar"></canvas></div>
            </div>
            <div class="chart-card">
                <h3>Priority Score vs Voter Count</h3>
                <div class="chart-container chart-tall"><canvas id="pri-scatter"></canvas></div>
            </div>
        </div>

        <div class="chart-card full-width">
            <h3>Youth Concentration by DM</h3>
            <div class="chart-container chart-wide"><canvas id="pri-youth"></canvas></div>
        </div>

        <div class="table-card">
            <h3>DM Priority Ranking (Detail)</h3>
            <div class="table-scroll">
                <table class="data-table compact" id="pri-dm-table">
                    <thead>
                        <tr>
                            <th>Rank</th><th>Daerah Mengundi</th><th>Voters</th><th>Score</th>
                            <th>Youth %</th><th>Diversity</th><th>B40 %</th><th>HH Size</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${dm_rankings.map(d => `
                            <tr>
                                <td><strong>#${d.rank}</strong></td>
                                <td class="name-col"><a href="#/dm/${d.slug}" class="table-link">${d.name}</a></td>
                                <td>${formatNumber(d.total_voters)}</td>
                                <td><strong>${d.priority_score.toFixed(4)}</strong></td>
                                <td>${formatPct(d.youth_pct)}</td>
                                <td>${d.diversity_index.toFixed(3)}</td>
                                <td>${formatPct(d.b40_pct)}</td>
                                <td>${d.avg_hh_size.toFixed(2)}</td>
                            </tr>
                        `).join("")}
                    </tbody>
                </table>
            </div>
        </div>

        <div class="table-card">
            <h3>Top 50 Lokaliti by Priority Score</h3>
            <div class="table-scroll">
                <table class="data-table compact">
                    <thead>
                        <tr><th>Rank</th><th>Lokaliti</th><th>Voters</th><th>Score</th><th>Youth %</th><th>B40 %</th></tr>
                    </thead>
                    <tbody>
                        ${lokaliti_rankings.map(l => `
                            <tr>
                                <td><strong>#${l.rank}</strong></td>
                                <td class="name-col">${l.name}</td>
                                <td>${formatNumber(l.total_voters)}</td>
                                <td><strong>${l.priority_score.toFixed(4)}</strong></td>
                                <td>${formatPct(l.youth_pct)}</td>
                                <td>${formatPct(l.b40_pct)}</td>
                            </tr>
                        `).join("")}
                    </tbody>
                </table>
            </div>
        </div>

        <div class="chart-row">
            <div class="chart-card">
                <h3>MINDEF Profile</h3>
                <div class="inst-card">
                    ${renderInstCard(institutional_zones.find(z => z.group === "MINDEF"))}
                </div>
            </div>
            <div class="chart-card">
                <h3>PULAPOL Profile</h3>
                <div class="inst-card">
                    ${renderInstCard(institutional_zones.find(z => z.group === "PULAPOL"))}
                </div>
            </div>
        </div>
    `;

    // DM priority bar chart
    const sorted = [...dm_rankings].sort((a, b) => a.rank - b.rank);
    horizontalBarChart(
        "pri-dm-bar",
        sorted.map(d => d.name),
        sorted.map(d => d.priority_score),
        sorted.map(d => d.rank <= 5 ? "#6366f1" : "#3f3f46"),
        { scales: { x: { max: 1 } } },
    );

    // Scatter: score vs voters
    scatterChart("pri-scatter", dm_rankings.map(d => ({
        x: d.total_voters,
        y: d.priority_score,
        label: d.name,
    })), {
        scales: {
            x: { title: { display: true, text: "Voters", color: COLORS.textMuted } },
            y: { title: { display: true, text: "Priority Score", color: COLORS.textMuted }, max: 1 },
        },
    });

    // Youth concentration bar
    const youthSorted = [...dm_rankings].sort((a, b) => b.youth_pct - a.youth_pct);
    barChart("pri-youth", youthSorted.map(d => d.name), [{
        data: youthSorted.map(d => d.youth_pct),
        backgroundColor: youthSorted.map(d => d.youth_pct > 45 ? "#6366f1" : d.youth_pct > 35 ? "#818cf8" : "#3f3f46"),
        borderRadius: 4,
    }], {
        plugins: { legend: { display: false } },
        scales: {
            x: { ticks: { font: { size: 10 }, maxRotation: 45, minRotation: 45, color: COLORS.textMuted } },
        },
    });
}

function renderInstCard(zone) {
    if (!zone) return "<p>No data</p>";
    return `
        <div class="inst-stats">
            <div><strong>${formatNumber(zone.total)}</strong> voters (${formatPct(zone.pct_of_total)})</div>
            <div>Male: ${formatPct(zone.male_pct)}</div>
            <div class="inst-breakdown">
                <span>Malay ${formatPct(zone.ethnicity.Malay)}</span>
                <span>Chinese ${formatPct(zone.ethnicity.Chinese)}</span>
                <span>Indian ${formatPct(zone.ethnicity.Indian)}</span>
            </div>
        </div>
    `;
}
