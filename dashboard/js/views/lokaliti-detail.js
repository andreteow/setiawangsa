import { fetchJSON, formatNumber, formatPct, statCard, ETHNICITY_KEYS, AGE_BANDS, AGE_LABELS } from "../utils.js";
import { ethnicityDoughnut, ageBandsBar, housingDoughnut } from "../charts.js";

export async function renderLokaliti(container, dmSlug, lokName) {
    const dmData = await fetchJSON(`dm/${dmSlug}.json`);
    const decoded = decodeURIComponent(lokName);
    const lok = dmData.lokaliti.find(l => l.name === decoded);

    if (!lok) {
        container.innerHTML = `<div class="page-header"><h2>Lokaliti not found</h2><p><a href="#/dm/${dmSlug}">Back to ${dmData.name}</a></p></div>`;
        return;
    }

    const topEth = Object.entries(lok.ethnicity).sort((a, b) => b[1] - a[1])[0];
    const topHousing = Object.entries(lok.housing).sort((a, b) => b[1] - a[1])[0];

    container.innerHTML = `
        <div class="page-header">
            <div class="breadcrumb">
                <a href="#/overview">Overview</a> <span>/</span>
                <a href="#/dm/${dmSlug}">${dmData.name}</a> <span>/</span>
                <span>${lok.name}</span>
            </div>
            <h2>${lok.name}</h2>
            <div class="header-badges">
                ${lok.priority_rank ? `<span class="badge badge-primary">Priority #${lok.priority_rank}</span>` : ""}
                <span class="badge">${formatNumber(lok.voters)} voters</span>
            </div>
        </div>

        <div class="stat-grid">
            ${statCard("Total Voters", formatNumber(lok.voters))}
            ${statCard("Male", formatNumber(lok.male), formatPct(lok.male / lok.voters * 100))}
            ${statCard("Female", formatNumber(lok.female), formatPct(lok.female / lok.voters * 100))}
            ${statCard("Top Ethnicity", topEth[0], formatPct(topEth[1] / lok.voters * 100))}
            ${statCard("Top Housing", topHousing ? topHousing[0] : "—", topHousing ? formatNumber(topHousing[1]) + " voters" : "")}
            ${statCard("Priority Score", lok.priority_score ? lok.priority_score.toFixed(4) : "—")}
        </div>

        <div class="chart-row">
            <div class="chart-card">
                <h3>Age Distribution</h3>
                <div class="chart-container"><canvas id="lok-age"></canvas></div>
            </div>
            <div class="chart-card">
                <h3>Ethnic Composition</h3>
                <div class="chart-container"><canvas id="lok-ethnicity"></canvas></div>
            </div>
        </div>

        <div class="chart-row">
            <div class="chart-card">
                <h3>Housing Type</h3>
                <div class="chart-container"><canvas id="lok-housing"></canvas></div>
            </div>
            <div class="chart-card">
                <h3>Ethnicity Breakdown</h3>
                <div class="detail-table">
                    <table class="data-table compact">
                        <thead><tr><th>Ethnicity</th><th>Voters</th><th>%</th></tr></thead>
                        <tbody>
                            ${ETHNICITY_KEYS.map(k => `
                                <tr>
                                    <td>${k}</td>
                                    <td>${formatNumber(lok.ethnicity[k] || 0)}</td>
                                    <td>${formatPct((lok.ethnicity[k] || 0) / lok.voters * 100)}</td>
                                </tr>
                            `).join("")}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    `;

    ageBandsBar("lok-age", lok.age_bands);
    ethnicityDoughnut("lok-ethnicity", lok.ethnicity);
    if (lok.housing && Object.keys(lok.housing).length) {
        housingDoughnut("lok-housing", lok.housing);
    }
}
