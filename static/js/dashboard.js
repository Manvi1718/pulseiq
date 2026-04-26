/* ═══════════════════════════════════════════════════════════════
   PULSEIQ — Dashboard JavaScript
   Handles: Charts, Flash messages, UI interactions
═══════════════════════════════════════════════════════════════ */

// ─── CHART DEFAULTS ───────────────────────────────────────────
const COLORS = {
  cyan: "#00d4ff",
  blue: "#58a6ff",
  green: "#3fb950",
  yellow: "#d29922",
  red: "#f85149",
  purple: "#bc8cff",
  orange: "#ffa657",
  muted: "#8b949e",
  border: "rgba(255,255,255,0.08)",
  surface: "#1c2330",
};

// Apply global Chart.js defaults once
if (typeof Chart !== "undefined") {
  Chart.defaults.color = "#8b949e";
  Chart.defaults.borderColor = "rgba(255,255,255,0.08)";
  Chart.defaults.font.family = "'Inter', system-ui, sans-serif";
  Chart.defaults.font.size = 12;
  Chart.defaults.plugins.legend.labels.boxWidth = 12;
  Chart.defaults.plugins.legend.labels.padding = 16;
  Chart.defaults.plugins.tooltip.backgroundColor = "#1c2330";
  Chart.defaults.plugins.tooltip.borderColor = "rgba(255,255,255,0.12)";
  Chart.defaults.plugins.tooltip.borderWidth = 1;
  Chart.defaults.plugins.tooltip.padding = 10;
  Chart.defaults.plugins.tooltip.titleColor = "#e6edf3";
  Chart.defaults.plugins.tooltip.bodyColor = "#8b949e";
}

// ─── CHART FACTORY FUNCTIONS ──────────────────────────────────

/**
 * Create a Doughnut / Pie chart
 * @param {string} canvasId - ID of <canvas> element
 * @param {string[]} labels
 * @param {number[]} data
 * @param {string[]} colors - optional array of hex colors
 */
function createDoughnutChart(canvasId, labels, data, colors) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return null;

  const palette = colors || [
    COLORS.green,
    COLORS.red,
    COLORS.muted,
    COLORS.cyan,
    COLORS.yellow,
  ];

  return new Chart(ctx, {
    type: "doughnut",
    data: {
      labels: labels,
      datasets: [
        {
          data: data,
          backgroundColor: palette.map((c) => c + "33"),
          borderColor: palette,
          borderWidth: 2,
          hoverOffset: 6,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: "68%",
      plugins: {
        legend: { position: "bottom" },
      },
    },
  });
}

/**
 * Create a Bar chart
 * @param {string} canvasId
 * @param {string[]} labels
 * @param {object[]} datasets  - [{ label, data, color }]
 * @param {boolean} horizontal
 */
function createBarChart(canvasId, labels, datasets, horizontal = false) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return null;

  return new Chart(ctx, {
    type: horizontal ? "bar" : "bar",
    data: {
      labels: labels,
      datasets: datasets.map((ds) => ({
        label: ds.label,
        data: ds.data,
        backgroundColor: (ds.color || COLORS.cyan) + "33",
        borderColor: ds.color || COLORS.cyan,
        borderWidth: 1.5,
        borderRadius: 6,
        borderSkipped: false,
      })),
    },
    options: {
      indexAxis: horizontal ? "y" : "x",
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: datasets.length > 1 },
      },
      scales: {
        x: {
          grid: { color: COLORS.border },
          ticks: { color: COLORS.muted },
        },
        y: {
          grid: { color: COLORS.border },
          ticks: { color: COLORS.muted },
        },
      },
    },
  });
}

/**
 * Create a Line chart
 * @param {string} canvasId
 * @param {string[]} labels
 * @param {object[]} datasets  - [{ label, data, color }]
 */
function createLineChart(canvasId, labels, datasets) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return null;

  return new Chart(ctx, {
    type: "line",
    data: {
      labels: labels,
      datasets: datasets.map((ds) => ({
        label: ds.label,
        data: ds.data,
        borderColor: ds.color || COLORS.cyan,
        backgroundColor: (ds.color || COLORS.cyan) + "18",
        borderWidth: 2,
        pointRadius: 4,
        pointHoverRadius: 6,
        pointBackgroundColor: ds.color || COLORS.cyan,
        tension: 0.4,
        fill: true,
      })),
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: datasets.length > 1 },
      },
      scales: {
        x: {
          grid: { color: COLORS.border },
          ticks: { color: COLORS.muted },
        },
        y: {
          grid: { color: COLORS.border },
          ticks: { color: COLORS.muted },
        },
      },
    },
  });
}

/**
 * Create a Scatter chart
 * @param {string} canvasId
 * @param {object[]} points  - [{ x, y }]
 * @param {string} xLabel
 * @param {string} yLabel
 */
function createScatterChart(canvasId, points, xLabel, yLabel) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return null;

  return new Chart(ctx, {
    type: "scatter",
    data: {
      datasets: [
        {
          label: "Posts",
          data: points,
          backgroundColor: COLORS.cyan + "66",
          borderColor: COLORS.cyan,
          borderWidth: 1.5,
          pointRadius: 5,
          pointHoverRadius: 7,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: {
          title: { display: true, text: xLabel, color: COLORS.muted },
          grid: { color: COLORS.border },
          ticks: { color: COLORS.muted },
        },
        y: {
          title: { display: true, text: yLabel, color: COLORS.muted },
          grid: { color: COLORS.border },
          ticks: { color: COLORS.muted },
        },
      },
    },
  });
}

// ─── FLASH MESSAGES AUTO DISMISS ─────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  const alerts = document.querySelectorAll(".alert[data-autohide]");
  alerts.forEach((alert) => {
    setTimeout(() => {
      alert.style.transition = "opacity 0.4s ease, transform 0.4s ease";
      alert.style.opacity = "0";
      alert.style.transform = "translateY(-6px)";
      setTimeout(() => alert.remove(), 400);
    }, 4000);
  });
});

// ─── CONFIRM DELETE ───────────────────────────────────────────
function confirmDelete(formId, message) {
  const msg =
    message || "Are you sure you want to delete this? This cannot be undone.";
  if (confirm(msg)) {
    document.getElementById(formId).submit();
  }
}

// ─── LOADING BUTTON ───────────────────────────────────────────
function setLoading(btn, isLoading, loadingText = "Loading...") {
  if (isLoading) {
    btn.dataset.originalText = btn.innerHTML;
    btn.innerHTML = `<span class="spinner"></span> ${loadingText}`;
    btn.disabled = true;
  } else {
    btn.innerHTML = btn.dataset.originalText || btn.innerHTML;
    btn.disabled = false;
  }
}

// ─── DATA COLLECTION BUTTON ───────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  const collectForm = document.getElementById("collectDataForm");
  if (collectForm) {
    collectForm.addEventListener("submit", function (e) {
      const btn = this.querySelector('button[type="submit"]');
      if (btn) setLoading(btn, true, "Collecting data...");
    });
  }
});

// ─── ANIMATE KPI NUMBERS ──────────────────────────────────────
function animateNumber(el, target, duration = 1000) {
  const start = 0;
  const startTime = performance.now();

  function update(currentTime) {
    const elapsed = currentTime - startTime;
    const progress = Math.min(elapsed / duration, 1);
    // Ease out cubic
    const eased = 1 - Math.pow(1 - progress, 3);
    const current = Math.round(start + (target - start) * eased);
    el.textContent = current.toLocaleString();
    if (progress < 1) requestAnimationFrame(update);
  }

  requestAnimationFrame(update);
}

document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("[data-count]").forEach((el) => {
    const target = parseInt(el.dataset.count, 10);
    if (!isNaN(target)) animateNumber(el, target);
  });
});

// ─── SIDEBAR ACTIVE LINK ──────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  const currentPath = window.location.pathname;
  document.querySelectorAll(".sidebar-nav a").forEach((link) => {
    if (link.getAttribute("href") === currentPath) {
      link.classList.add("active");
    }
  });
});

// ─── COPY TO CLIPBOARD ────────────────────────────────────────
function copyToClipboard(text, btn) {
  navigator.clipboard.writeText(text).then(() => {
    const original = btn.textContent;
    btn.textContent = "Copied!";
    btn.style.color = "#3fb950";
    setTimeout(() => {
      btn.textContent = original;
      btn.style.color = "";
    }, 2000);
  });
}

// ─── EXPORT TABLE AS CSV ──────────────────────────────────────
function exportTableCSV(tableId, filename) {
  const table = document.getElementById(tableId);
  if (!table) return;

  const rows = Array.from(table.querySelectorAll("tr"));
  const csv = rows
    .map((row) => {
      return Array.from(row.querySelectorAll("th, td"))
        .map((cell) => `"${cell.textContent.trim().replace(/"/g, '""')}"`)
        .join(",");
    })
    .join("\n");

  const blob = new Blob([csv], { type: "text/csv" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename || "export.csv";
  a.click();
  URL.revokeObjectURL(url);
}
