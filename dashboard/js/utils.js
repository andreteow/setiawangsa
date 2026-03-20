// Utility functions for formatting and data helpers

export function formatNumber(n) {
    if (n == null) return "—";
    return n.toLocaleString("en-MY");
}

export function formatPct(n, decimals = 1) {
    if (n == null) return "—";
    return n.toFixed(decimals) + "%";
}

export function slugify(name) {
    return name.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
}

export function shortenAgeBand(band) {
    return band.replace(/ \(.+?\)/, "");
}

export const AGE_BANDS = ["22-27 (Youth)", "28-39 (Young Adult)", "40-59 (Middle Age)", "60+ (Senior)"];
export const AGE_LABELS = ["22-27", "28-39", "40-59", "60+"];
export const ETHNICITY_KEYS = ["Malay", "Chinese", "Indian", "Other"];

export const COLORS = {
    primary: "#6366f1",
    primaryLight: "#818cf8",
    accent: "#f59e0b",
    success: "#10b981",
    danger: "#ef4444",
    muted: "#71717a",
    bg: "#18181b",
    card: "#27272a",
    border: "#3f3f46",
    text: "#fafafa",
    textMuted: "#a1a1aa",
};

export const ETHNICITY_COLORS = {
    Malay: "#6366f1",
    Chinese: "#f59e0b",
    Indian: "#10b981",
    Other: "#71717a",
};

export const AGE_COLORS = ["#818cf8", "#6366f1", "#4f46e5", "#3730a3"];

export const HOUSING_COLORS = {
    PPR: "#ef4444",
    Flat: "#f59e0b",
    Taman: "#10b981",
    "Condo/Apartment": "#6366f1",
    Institutional: "#71717a",
    Other: "#3f3f46",
};

// Data fetching with caching
const cache = new Map();

export async function fetchJSON(path) {
    if (cache.has(path)) return cache.get(path);
    const resp = await fetch(`data/${path}`);
    if (!resp.ok) throw new Error(`Failed to fetch ${path}: ${resp.status}`);
    const data = await resp.json();
    cache.set(path, data);
    return data;
}

// Create a stat card HTML
export function statCard(label, value, sub) {
    return `
        <div class="stat-card">
            <div class="stat-value">${value}</div>
            <div class="stat-label">${label}</div>
            ${sub ? `<div class="stat-sub">${sub}</div>` : ""}
        </div>
    `;
}

// Create a sortable table
export function sortableTable(id, headers, rows, defaultSort = 0, defaultDir = "asc") {
    let sortCol = defaultSort;
    let sortDir = defaultDir;

    function render() {
        const sorted = [...rows].sort((a, b) => {
            let va = a[sortCol], vb = b[sortCol];
            if (typeof va === "string") {
                return sortDir === "asc" ? va.localeCompare(vb) : vb.localeCompare(va);
            }
            va = va ?? -Infinity;
            vb = vb ?? -Infinity;
            return sortDir === "asc" ? va - vb : vb - va;
        });

        const table = document.getElementById(id);
        if (!table) return;
        table.innerHTML = `
            <thead>
                <tr>
                    ${headers.map((h, i) => `<th data-col="${i}" class="${i === sortCol ? "sorted " + sortDir : ""}">${h}</th>`).join("")}
                </tr>
            </thead>
            <tbody>
                ${sorted.map(row => `<tr>${row.map((cell, i) => `<td${i === 0 ? ' class="name-col"' : ""}>${cell ?? "—"}</td>`).join("")}</tr>`).join("")}
            </tbody>
        `;

        table.querySelectorAll("th").forEach(th => {
            th.addEventListener("click", () => {
                const col = parseInt(th.dataset.col);
                if (col === sortCol) {
                    sortDir = sortDir === "asc" ? "desc" : "asc";
                } else {
                    sortCol = col;
                    sortDir = typeof rows[0]?.[col] === "string" ? "asc" : "desc";
                }
                render();
            });
        });
    }

    return { render };
}
