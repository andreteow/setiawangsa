// Chart.js wrapper functions for consistent styling
import { COLORS, ETHNICITY_COLORS, AGE_COLORS, HOUSING_COLORS, AGE_LABELS, AGE_BANDS, ETHNICITY_KEYS } from "./utils.js";
export { COLORS };

// Track chart instances for cleanup
const chartInstances = new Map();

function destroyChart(canvasId) {
    if (chartInstances.has(canvasId)) {
        chartInstances.get(canvasId).destroy();
        chartInstances.delete(canvasId);
    }
}

function createChart(canvasId, config) {
    destroyChart(canvasId);
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;
    const chart = new Chart(ctx, config);
    chartInstances.set(canvasId, chart);
    return chart;
}

// Default chart options
const defaults = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
        legend: {
            labels: { color: COLORS.textMuted, font: { size: 12 } },
        },
        tooltip: {
            backgroundColor: COLORS.card,
            titleColor: COLORS.text,
            bodyColor: COLORS.textMuted,
            borderColor: COLORS.border,
            borderWidth: 1,
        },
    },
    scales: {
        x: {
            ticks: { color: COLORS.textMuted, font: { size: 11 } },
            grid: { color: COLORS.border + "40" },
        },
        y: {
            ticks: { color: COLORS.textMuted, font: { size: 11 } },
            grid: { color: COLORS.border + "40" },
        },
    },
};

export function barChart(canvasId, labels, datasets, options = {}) {
    return createChart(canvasId, {
        type: "bar",
        data: { labels, datasets },
        options: {
            ...defaults,
            ...options,
            scales: { ...defaults.scales, ...options.scales },
            plugins: { ...defaults.plugins, ...options.plugins },
        },
    });
}

export function horizontalBarChart(canvasId, labels, data, colors, options = {}) {
    return createChart(canvasId, {
        type: "bar",
        data: {
            labels,
            datasets: [{
                data,
                backgroundColor: colors,
                borderRadius: 4,
            }],
        },
        options: {
            ...defaults,
            indexAxis: "y",
            plugins: { ...defaults.plugins, legend: { display: false }, ...options.plugins },
            scales: {
                x: { ...defaults.scales.x, ...options.scales?.x },
                y: { ...defaults.scales.y, ticks: { ...defaults.scales.y.ticks, font: { size: 11 } }, ...options.scales?.y },
            },
            ...options,
        },
    });
}

export function doughnutChart(canvasId, labels, data, colors, options = {}) {
    return createChart(canvasId, {
        type: "doughnut",
        data: {
            labels,
            datasets: [{
                data,
                backgroundColor: colors,
                borderColor: COLORS.bg,
                borderWidth: 2,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: "60%",
            plugins: {
                ...defaults.plugins,
                legend: {
                    position: "right",
                    labels: { color: COLORS.textMuted, font: { size: 12 }, padding: 12, usePointStyle: true },
                },
                ...options.plugins,
            },
            ...options,
        },
    });
}

export function stackedBarChart(canvasId, labels, datasets, options = {}) {
    return createChart(canvasId, {
        type: "bar",
        data: { labels, datasets },
        options: {
            ...defaults,
            plugins: {
                ...defaults.plugins,
                tooltip: {
                    ...defaults.plugins.tooltip,
                    callbacks: {
                        label: (ctx) => {
                            const total = ctx.dataset.data.reduce((a, b) => a + b, 0);
                            const val = ctx.raw;
                            return `${ctx.dataset.label}: ${val.toLocaleString()}`;
                        },
                    },
                },
                ...options.plugins,
            },
            scales: {
                x: { ...defaults.scales.x, stacked: true },
                y: { ...defaults.scales.y, stacked: true },
                ...options.scales,
            },
            ...options,
        },
    });
}

export function scatterChart(canvasId, dataPoints, options = {}) {
    return createChart(canvasId, {
        type: "scatter",
        data: {
            datasets: [{
                data: dataPoints,
                backgroundColor: COLORS.primary,
                pointRadius: 6,
                pointHoverRadius: 8,
            }],
        },
        options: {
            ...defaults,
            plugins: {
                ...defaults.plugins,
                legend: { display: false },
                tooltip: {
                    ...defaults.plugins.tooltip,
                    callbacks: {
                        label: (ctx) => {
                            const pt = ctx.raw;
                            return `${pt.label}: Score ${pt.y.toFixed(3)}, ${pt.x.toLocaleString()} voters`;
                        },
                    },
                },
                ...options.plugins,
            },
            ...options,
        },
    });
}

// Convenience: ethnicity doughnut
export function ethnicityDoughnut(canvasId, data) {
    const labels = ETHNICITY_KEYS;
    const values = labels.map(k => data[k] || 0);
    const colors = labels.map(k => ETHNICITY_COLORS[k]);
    return doughnutChart(canvasId, labels, values, colors);
}

// Convenience: age bands bar chart
export function ageBandsBar(canvasId, data) {
    const values = AGE_BANDS.map(b => data[b] || 0);
    return barChart(canvasId, AGE_LABELS, [{
        data: values,
        backgroundColor: AGE_COLORS,
        borderRadius: 4,
    }], {
        plugins: { legend: { display: false } },
    });
}

// Convenience: housing doughnut
export function housingDoughnut(canvasId, data) {
    const labels = Object.keys(data);
    const values = Object.values(data);
    const colors = labels.map(k => HOUSING_COLORS[k] || COLORS.muted);
    return doughnutChart(canvasId, labels, values, colors);
}

export function destroyAll() {
    chartInstances.forEach(chart => chart.destroy());
    chartInstances.clear();
}
