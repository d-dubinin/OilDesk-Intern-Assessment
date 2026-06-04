const API = "http://localhost:8000";

let activeCommodity = null;
let chartPrice = null;
let chartRsi = null;
let chartMacd = null;
let chartPnl = null;
let chartDd = null;

const COMMODITY_LABELS = {
    copper: "Copper",
    zinc: "Zinc",
    crude_oil: "Crude Oil",
};

const COMMODITY_UNITS = {
    copper: "USD/t",
    zinc: "USD/t",
    crude_oil: "USD/bbl",
};

// --- Clock ---

function updateClock() {
    document.getElementById("clock").textContent =
        new Date().toUTCString().replace("GMT", "UTC");
}
setInterval(updateClock, 1000);
updateClock();

// --- API ---

async function apiFetch(path) {
    const res = await fetch(`${API}${path}`);
    if (!res.ok) throw new Error(`API error: ${res.status}`);
    return res.json();
}

// --- Init ---

async function init() {
    try {
        await apiFetch("/health");
        const el = document.getElementById("api-status");
        el.textContent = "● LIVE";
        el.classList.add("connected");
    } catch {
        document.getElementById("api-status").textContent = "● OFFLINE";
        return;
    }

    const { commodities } = await apiFetch("/commodities");
    renderTabs(commodities);
    loadCommodity(commodities[0]);
}

// --- Tabs ---

function renderTabs(commodities) {
    const container = document.getElementById("commodity-tabs");
    commodities.forEach(c => {
        const btn = document.createElement("button");
        btn.className = "tab";
        btn.textContent = COMMODITY_LABELS[c] || c.toUpperCase();
        btn.dataset.commodity = c;
        btn.addEventListener("click", () => loadCommodity(c));
        container.appendChild(btn);
    });
}

function setActiveTab(commodity) {
    document.querySelectorAll(".tab").forEach(t => {
        t.classList.toggle("active", t.dataset.commodity === commodity);
    });
}

// --- Load ---

async function loadCommodity(commodity) {
    activeCommodity = commodity;
    setActiveTab(commodity);

    let indicatorRes, summaryRes, backtestRes;
    try {
        [indicatorRes, summaryRes, backtestRes] = await Promise.all([
            apiFetch(`/indicators/${commodity}`),
            apiFetch(`/summary/${commodity}`),
            apiFetch(`/backtest/${commodity}`),
        ]);
    } catch (err) {
        document.getElementById("explanation-body").textContent =
            `Failed to load data for ${commodity}: ${err.message}`;
        return;
    }

    const data = indicatorRes.data;
    const summary = summaryRes.summary;
    const bt = backtestRes;

    renderSummary(summary, commodity);
    renderCharts(data, commodity);
    renderTable(data);
    renderExplanation(summary, commodity, data);
    renderBacktest(bt);
}

// --- Formatting ---

function fmt(val, decimals = 2) {
    if (val === null || val === undefined) return "—";
    return Number(val).toLocaleString("en-US", {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals,
    });
}

function fmtPct(val) {
    if (val === null || val === undefined) return "—";
    const sign = val >= 0 ? "+" : "";
    return `${sign}${Number(val).toFixed(2)}%`;
}

function setStatValue(id, value, cls) {
    const el = document.getElementById(id);
    el.textContent = value;
    el.className = "stat-value" + (cls ? ` ${cls}` : "");
}

// --- Summary ---

function renderSummary(summary, commodity) {
    const unit = COMMODITY_UNITS[commodity] || "";

    setStatValue("stat-latest", `${fmt(summary.latest_price)} ${unit}`, "accent");
    setStatValue("stat-daily", fmtPct(summary.daily_change_pct),
        summary.daily_change_pct >= 0 ? "positive" : "negative");
    setStatValue("stat-weekly", fmtPct(summary.weekly_change_pct),
        summary.weekly_change_pct >= 0 ? "positive" : "negative");
    setStatValue("stat-period", fmtPct(summary.period_change_pct),
        summary.period_change_pct >= 0 ? "positive" : "negative");
    setStatValue("stat-rsi", fmt(summary.latest_rsi, 1));
    setStatValue("stat-macd", fmt(summary.latest_macd, 2));
    setStatValue("stat-low", `${fmt(summary.min_price)} ${unit}`);
    setStatValue("stat-high", `${fmt(summary.max_price)} ${unit}`);

    document.getElementById("price-range").textContent =
        `${summary.start_date} → ${summary.end_date}`;
}

// --- Charts ---

function destroyCharts() {
    if (chartPrice) { chartPrice.destroy(); chartPrice = null; }
    if (chartRsi) { chartRsi.destroy(); chartRsi = null; }
    if (chartMacd) { chartMacd.destroy(); chartMacd = null; }
    if (chartPnl) { chartPnl.destroy(); chartPnl = null; }
    if (chartDd) { chartDd.destroy(); chartDd = null; }
}

const ZOOM_PLUGIN = {
    zoom: {
        wheel: { enabled: true },
        pinch: { enabled: true },
        mode: "x",
    },
    pan: {
        enabled: true,
        mode: "x",
    },
};

const BASE_SCALES = {
    x: {
        ticks: {
            color: "#444",
            font: { family: "'IBM Plex Mono'", size: 9 },
            maxTicksLimit: 8,
            autoSkip: true,
        },
        grid: { color: "#1a1a1a" },
        border: { color: "#222" },
    },
    y: {
        ticks: { color: "#444", font: { family: "'IBM Plex Mono'", size: 9 } },
        grid: { color: "#1a1a1a" },
        border: { color: "#222" },
    },
};

const BASE_TOOLTIP = {
    mode: "index",
    intersect: false,
    backgroundColor: "#111",
    borderColor: "#333",
    borderWidth: 1,
    titleColor: "#666",
    bodyColor: "#e0e0e0",
    titleFont: { family: "'IBM Plex Mono'" },
    bodyFont: { family: "'IBM Plex Mono'" },
};

function renderCharts(data, commodity) {
    destroyCharts();

    const labels = data.map(d => d.date);
    const prices = data.map(d => d.price);
    const maFast = data.map(d => d.ma_fast);
    const maMedium = data.map(d => d.ma_medium);
    const maSlow = data.map(d => d.ma_slow);
    const rsi = data.map(d => d.rsi);
    const macd = data.map(d => d.macd);
    const signal = data.map(d => d.macd_signal);
    const hist = data.map(d => d.macd_hist);

    chartPrice = new Chart(document.getElementById("chart-price"), {
        type: "line",
        data: {
            labels,
            datasets: [
                { label: "Price", data: prices, borderColor: "#c8a84b", borderWidth: 1.5, pointRadius: 0, tension: 0 },
                { label: "MA20", data: maFast, borderColor: "#3498db", borderWidth: 1, pointRadius: 0, tension: 0 },
                { label: "MA50", data: maMedium, borderColor: "#e67e22", borderWidth: 1, pointRadius: 0, tension: 0, borderDash: [4, 2] },
                { label: "MA200", data: maSlow, borderColor: "#9b59b6", borderWidth: 1, pointRadius: 0, tension: 0, borderDash: [8, 4] },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: false,
            plugins: {
                tooltip: BASE_TOOLTIP,
                legend: {
                    display: true,
                    onClick: (e, legendItem, legend) => {
                        const meta = legend.chart.getDatasetMeta(legendItem.datasetIndex);
                        meta.hidden = !meta.hidden;
                        legend.chart.update();
                    },
                    labels: { color: "#666", font: { family: "'IBM Plex Mono'", size: 9 }, boxWidth: 12 },
                },
                zoom: ZOOM_PLUGIN,
            },
            scales: BASE_SCALES,
        },
    });

    chartRsi = new Chart(document.getElementById("chart-rsi"), {
        type: "line",
        data: {
            labels,
            datasets: [
                { label: "RSI", data: rsi, borderColor: "#2ecc71", borderWidth: 1.5, pointRadius: 0, tension: 0 },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: false,
            plugins: {
                tooltip: BASE_TOOLTIP,
                legend: { display: false },
                zoom: ZOOM_PLUGIN,
            },
            scales: {
                x: BASE_SCALES.x,
                y: {
                    ...BASE_SCALES.y,
                    min: 0,
                    max: 100,
                    ticks: {
                        ...BASE_SCALES.y.ticks,
                        callback: v => [30, 50, 70].includes(v) ? v : "",
                    },
                },
            },
        },
    });

    chartMacd = new Chart(document.getElementById("chart-macd"), {
        type: "bar",
        data: {
            labels,
            datasets: [
                {
                    label: "Histogram",
                    data: hist,
                    backgroundColor: hist.map(v => v >= 0 ? "rgba(46,204,113,0.5)" : "rgba(231,76,60,0.5)"),
                    borderWidth: 0,
                    order: 2,
                },
                { label: "MACD", data: macd, type: "line", borderColor: "#c8a84b", borderWidth: 1.5, pointRadius: 0, tension: 0, order: 1 },
                { label: "Signal", data: signal, type: "line", borderColor: "#e74c3c", borderWidth: 1, pointRadius: 0, tension: 0, order: 1, borderDash: [4, 2] },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: false,
            plugins: {
                tooltip: BASE_TOOLTIP,
                legend: {
                    display: true,
                    onClick: (e, legendItem, legend) => {
                        const meta = legend.chart.getDatasetMeta(legendItem.datasetIndex);
                        meta.hidden = !meta.hidden;
                        legend.chart.update();
                    },
                    labels: { color: "#666", font: { family: "'IBM Plex Mono'", size: 9 }, boxWidth: 12 },
                },
                zoom: ZOOM_PLUGIN,
            },
            scales: BASE_SCALES,
        },
    });
}

// --- Reset zoom ---

function resetZoom(which) {
    if (which === "price" && chartPrice) chartPrice.resetZoom();
    if (which === "rsi" && chartRsi) chartRsi.resetZoom();
    if (which === "macd" && chartMacd) chartMacd.resetZoom();
    if (which === "pnl" && chartPnl) chartPnl.resetZoom();
    if (which === "dd" && chartDd) chartDd.resetZoom();
}

// --- Table ---

function renderTable(data) {
    const tbody = document.getElementById("table-body");
    tbody.innerHTML = "";
    document.getElementById("table-count").textContent = `${data.length} ROWS`;

    [...data].reverse().forEach(d => {
        const tr = document.createElement("tr");
        const hasVal = v => v !== null && v !== undefined;
        tr.innerHTML = `
            <td>${d.date}</td>
            <td>${fmt(d.price)}</td>
            <td>${hasVal(d.ma_fast) ? fmt(d.ma_fast) : "—"}</td>
            <td>${hasVal(d.ma_medium) ? fmt(d.ma_medium) : "—"}</td>
            <td>${hasVal(d.ma_slow) ? fmt(d.ma_slow) : "—"}</td>
            <td class="${d.macd >= 0 ? "positive" : "negative"}">${hasVal(d.macd) ? fmt(d.macd, 2) : "—"}</td>
            <td>${hasVal(d.macd_signal) ? fmt(d.macd_signal, 2) : "—"}</td>
            <td class="${d.macd_hist >= 0 ? "positive" : "negative"}">${hasVal(d.macd_hist) ? fmt(d.macd_hist, 2) : "—"}</td>
            <td class="${d.rsi > 70 ? "negative" : d.rsi < 30 ? "positive" : ""}">${hasVal(d.rsi) ? fmt(d.rsi, 1) : "—"}</td>
        `;
        tbody.appendChild(tr);
    });
}

// --- Explanation ---

function renderExplanation(summary, commodity, data) {
    const name = COMMODITY_LABELS[commodity] || commodity;
    const unit = COMMODITY_UNITS[commodity] || "";
    const last = data[data.length - 1];
    const first = data[0];

    const direction = summary.period_change_pct >= 0 ? "gained" : "lost";

    const rsiSignal = summary.latest_rsi > 70
        ? "RSI is above 70 — the market is overbought and may be due for a pullback."
        : summary.latest_rsi < 30
            ? "RSI is below 30 — the market is oversold and may be approaching a bounce."
            : `RSI is at ${summary.latest_rsi?.toFixed(1)} — neutral momentum with no clear extreme.`;

    const macdSignal = summary.latest_macd > 0
        ? "MACD is positive — the short-term trend is bullish."
        : "MACD is negative — the short-term trend is bearish.";

    document.getElementById("explanation-body").innerHTML = `
        <p><strong style="color:#e0e0e0">${name}</strong> traded from
        <strong>${fmt(first.price)} ${unit}</strong> on ${first.date} to
        <strong>${fmt(last.price)} ${unit}</strong> on ${last.date},
        ${direction} <strong style="color:${summary.period_change_pct >= 0 ? '#2ecc71' : '#e74c3c'}">${Math.abs(summary.period_change_pct).toFixed(2)}%</strong>
        over the period. The average settlement price was <strong>${fmt(summary.avg_price)} ${unit}</strong>,
        with a low of <strong>${fmt(summary.min_price)}</strong> and a high of <strong>${fmt(summary.max_price)}</strong>.</p>
        <p>${rsiSignal} ${macdSignal}</p>
        <p>The 20-day moving average tracks short-term momentum (one trading month),
        the 50-day captures the medium-term trend (one quarter),
        and the 200-day represents the long-term structural trend (one year).
        Price above all three moving averages signals a bullish alignment.
        Click any legend item on the charts to toggle it on or off.
        Scroll to zoom, drag to pan.</p>
    `;
}

// --- Backtest ---

function renderBacktest(bt) {
    const m = bt.metrics;

    setStatValue("bt-total", fmtPct(m.total_return_pct), m.total_return_pct >= 0 ? "positive" : "negative");
    setStatValue("bt-ann", fmtPct(m.annualised_return_pct), m.annualised_return_pct >= 0 ? "positive" : "negative");
    setStatValue("bt-sharpe", fmt(m.sharpe_ratio, 3), m.sharpe_ratio >= 0 ? "positive" : "negative");
    setStatValue("bt-dd", fmtPct(m.max_drawdown_pct), "negative");
    setStatValue("bt-wr", fmtPct(m.win_rate_pct));
    setStatValue("bt-vol", fmtPct(m.annualised_vol_pct));
    setStatValue("bt-trades", m.n_trades);
    setStatValue("bt-days", m.n_days);

    const labels = bt.series.map(d => d.date);
    const buyHold = bt.series.map(d => (d.cumulative_return * 100).toFixed(2));
    const strategy = bt.series.map(d => (d.cumulative_strategy_return * 100).toFixed(2));
    const drawdown = bt.series.map(d => (d.drawdown * 100).toFixed(2));

    const pctScales = {
        x: BASE_SCALES.x,
        y: {
            ...BASE_SCALES.y,
            ticks: { ...BASE_SCALES.y.ticks, callback: v => `${v}%` },
        },
    };

    chartPnl = new Chart(document.getElementById("chart-pnl"), {
        type: "line",
        data: {
            labels,
            datasets: [
                { label: "Strategy", data: strategy, borderColor: "#c8a84b", borderWidth: 1.5, pointRadius: 0, tension: 0 },
                { label: "Buy & Hold", data: buyHold, borderColor: "#3498db", borderWidth: 1, pointRadius: 0, tension: 0, borderDash: [4, 2] },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: false,
            plugins: {
                tooltip: BASE_TOOLTIP,
                legend: {
                    display: true,
                    onClick: (e, legendItem, legend) => {
                        const meta = legend.chart.getDatasetMeta(legendItem.datasetIndex);
                        meta.hidden = !meta.hidden;
                        legend.chart.update();
                    },
                    labels: { color: "#666", font: { family: "'IBM Plex Mono'", size: 9 }, boxWidth: 12 },
                },
                zoom: ZOOM_PLUGIN,
            },
            scales: pctScales,
        },
    });

    chartDd = new Chart(document.getElementById("chart-dd"), {
        type: "line",
        data: {
            labels,
            datasets: [
                {
                    label: "Drawdown",
                    data: drawdown,
                    borderColor: "#e74c3c",
                    borderWidth: 1.5,
                    pointRadius: 0,
                    tension: 0,
                    fill: true,
                    backgroundColor: "rgba(231,76,60,0.1)",
                },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: false,
            plugins: {
                tooltip: BASE_TOOLTIP,
                legend: { display: false },
                zoom: ZOOM_PLUGIN,
            },
            scales: pctScales,
        },
    });
}

// --- Start ---
init();