import { isAuthenticated, renderLoginScreen } from "./auth.js";
import { destroyAll } from "./charts.js";

// View imports
import { renderOverview } from "./views/overview.js";
import { renderDmDetail } from "./views/dm-detail.js";
import { renderLokaliti } from "./views/lokaliti-detail.js";
import { renderCompare } from "./views/compare.js";
import { renderPriority } from "./views/priority.js";
import { renderHousing } from "./views/housing.js";

const content = () => document.getElementById("content");

const NAV_ITEMS = [
    { hash: "#/overview", label: "Overview", icon: "home" },
    { hash: "#/priority", label: "Priority", icon: "target" },
    { hash: "#/housing", label: "Housing", icon: "building" },
    { hash: "#/compare", label: "Compare", icon: "columns" },
];

function renderNav() {
    const nav = document.getElementById("nav-links");
    if (!nav) return;
    const currentHash = window.location.hash || "#/overview";
    nav.innerHTML = NAV_ITEMS.map(item => `
        <a href="${item.hash}" class="nav-link ${currentHash.startsWith(item.hash) ? "active" : ""}">
            <span class="nav-icon">${getIcon(item.icon)}</span>
            <span class="nav-label">${item.label}</span>
        </a>
    `).join("");
}

function getIcon(name) {
    const icons = {
        home: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>`,
        target: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/></svg>`,
        building: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="4" y="2" width="16" height="20" rx="2"/><path d="M9 22v-4h6v4"/><path d="M8 6h.01M16 6h.01M12 6h.01M8 10h.01M16 10h.01M12 10h.01M8 14h.01M16 14h.01M12 14h.01"/></svg>`,
        columns: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="18" rx="1"/><rect x="14" y="3" width="7" height="18" rx="1"/></svg>`,
    };
    return icons[name] || "";
}

async function route() {
    if (!isAuthenticated()) {
        document.getElementById("app").innerHTML = "";
        renderLoginScreen(startApp);
        return;
    }

    const hash = window.location.hash || "#/overview";
    const el = content();
    if (!el) return;

    // Destroy old charts
    destroyAll();

    // Show loading
    el.innerHTML = `<div class="loading"><div class="spinner"></div></div>`;

    try {
        if (hash === "#/overview" || hash === "#/" || hash === "") {
            await renderOverview(el);
        } else if (hash.match(/^#\/dm\/([^/]+)\/lokaliti\/(.+)$/)) {
            const [, dmSlug, lokName] = hash.match(/^#\/dm\/([^/]+)\/lokaliti\/(.+)$/);
            await renderLokaliti(el, dmSlug, lokName);
        } else if (hash.match(/^#\/dm\/(.+)$/)) {
            const [, slug] = hash.match(/^#\/dm\/(.+)$/);
            await renderDmDetail(el, slug);
        } else if (hash.startsWith("#/compare")) {
            const params = hash.includes("?") ? hash.split("?")[1] : "";
            await renderCompare(el, params);
        } else if (hash === "#/priority") {
            await renderPriority(el);
        } else if (hash === "#/housing") {
            await renderHousing(el);
        } else {
            await renderOverview(el);
        }
    } catch (err) {
        el.innerHTML = `<div class="error-page"><h2>Error</h2><p>${err.message}</p><a href="#/overview">Back to Overview</a></div>`;
        console.error(err);
    }

    renderNav();
    window.scrollTo(0, 0);
}

function startApp() {
    const app = document.getElementById("app");
    app.innerHTML = `
        <div class="dashboard">
            <nav class="sidebar" id="sidebar">
                <div class="sidebar-header">
                    <h1>P.118</h1>
                    <span>Setiawangsa</span>
                </div>
                <div id="nav-links" class="nav-links"></div>
                <div class="sidebar-footer">
                    <small>MUDA Internal</small>
                </div>
            </nav>
            <main class="main-content" id="content"></main>
            <nav class="bottom-nav" id="bottom-nav"></nav>
        </div>
    `;

    // Bottom nav for mobile
    const bottomNav = document.getElementById("bottom-nav");
    bottomNav.innerHTML = NAV_ITEMS.map(item => `
        <a href="${item.hash}" class="bottom-nav-link">
            ${getIcon(item.icon)}
            <span>${item.label}</span>
        </a>
    `).join("");

    renderNav();
    route();
}

// Listen for hash changes
window.addEventListener("hashchange", route);

// Initial load
if (isAuthenticated()) {
    startApp();
} else {
    renderLoginScreen(startApp);
}
