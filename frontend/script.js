// ===== 設定後端 API URL =====
const API_BASE = "http://127.0.0.1:8000";

// ===== 取得 DOM =====
const dateFromSel = document.getElementById("dateFrom");
const dateToSel = document.getElementById("dateTo");
const stationSel = document.getElementById("stationSelect");
const productSel = document.getElementById("productSelect");
const lotSel = document.getElementById("lotSelect");
const btnApply = document.getElementById("btnApply");

const detailTableBody = document.querySelector("#detailTable tbody");

// ===== Chart 物件 =====
let yieldTrendChart = null;
let defectParetoChart = null;
let defectMapChart = null;

// ===== Helper =====
function buildQuery(params) {
    const usp = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
        if (v !== undefined && v !== null && v !== "") {
            usp.append(k, v);
        }
    });
    return usp.toString();
}

// ------------------------ 1. 載入日期 ------------------------
async function loadDates() {
    const res = await fetch(`${API_BASE}/filter/dates`);
    const dates = await res.json();

    dateFromSel.innerHTML = "";
    dateToSel.innerHTML = "";

    dates.forEach(d => {
        let opt1 = document.createElement("option");
        opt1.value = opt1.textContent = d;
        dateFromSel.appendChild(opt1);

        let opt2 = document.createElement("option");
        opt2.value = opt2.textContent = d;
        dateToSel.appendChild(opt2);
    });

    if (dates.length > 0) {
        dateFromSel.value = dates[0];
        dateToSel.value = dates[dates.length - 1];
    }

    await loadMachines();
}

// ------------------------ 2. 日期 → 機台 ------------------------
async function loadMachines() {
    const from = dateFromSel.value;
    const to = dateToSel.value;

    stationSel.innerHTML = "";
    productSel.innerHTML = "";
    lotSel.innerHTML = "";

    if (!from || !to) return;

    const qs = buildQuery({ date_from: from, date_to: to });

    const res = await fetch(`${API_BASE}/filter/machines?${qs}`);
    const machines = await res.json();

    machines.forEach(m => {
        const opt = document.createElement("option");
        opt.value = opt.textContent = m;
        stationSel.appendChild(opt);
    });

    if (machines.length > 0) {
        stationSel.value = machines[0];
        await loadRecipes();
    }
}

// ------------------------ 3. 機台 → Recipe ------------------------
async function loadRecipes() {
    const from = dateFromSel.value;
    const to = dateToSel.value;
    const station = stationSel.value;

    productSel.innerHTML = "";
    lotSel.innerHTML = "";

    if (!from || !to || !station) return;

    const qs = buildQuery({ date_from: from, date_to: to, station });

    const res = await fetch(`${API_BASE}/filter/recipes?${qs}`);
    const recipes = await res.json();

    recipes.forEach(p => {
        const opt = document.createElement("option");
        opt.value = opt.textContent = p;
        productSel.appendChild(opt);
    });

    if (recipes.length > 0) {
        productSel.value = recipes[0];
        await loadLots();
    }
}

// ------------------------ 4. Recipe → Lot ------------------------
let isFirstLoadLots = true;

async function loadLots() {
    const from = dateFromSel.value;
    const to = dateToSel.value;
    const station = stationSel.value;
    const product = productSel.value;

    if (!from || !to || !station || !product) return;

    const previousSelected = new Set(
        Array.from(lotSel.selectedOptions).map(o => o.value)
    );

    lotSel.innerHTML = "";

    const qs = buildQuery({ date_from: from, date_to: to, station, product });
    const res = await fetch(`${API_BASE}/filter/lots?${qs}`);
    const lots = await res.json();

    lots.forEach(l => {
        const opt = document.createElement("option");
        opt.value = opt.textContent = l;

        if (isFirstLoadLots) {
            opt.selected = true;
        } else {
            opt.selected = previousSelected.has(l);
        }

        lotSel.appendChild(opt);
    });

    if (isFirstLoadLots) isFirstLoadLots = false;
}




// ------------------------ 5. Dashboard ------------------------
async function loadDashboard() {
    const from = dateFromSel.value;
    const to = dateToSel.value;

    const lots = Array.from(lotSel.selectedOptions).map(o => o.value);

    if (!from || !to || lots.length === 0) {
        alert("請選擇日期區間與批號");
        return;
    }

    const usp = new URLSearchParams();
    usp.append("date_from", from);
    usp.append("date_to", to);
    usp.append("station", stationSel.value);
    usp.append("product", productSel.value);

    // ⭐ 多選批號正確傳給 FastAPI
    lots.forEach(l => usp.append("lots", l));

    const url = `${API_BASE}/yield/trend?${usp.toString()}`;
    console.log("REQ:", url);

    const res = await fetch(url);
    const data = await res.json();
    console.log("RES:", data);

    updateYieldTrendChart(data);
    updateDefectParetoChart(data);
    updateDefectMapChart(data);
    updateDetailTable(data);
}


// =============================================================
// Chart Functions
// =============================================================
function updateYieldTrendChart(data) {
    const ctx = document.getElementById("yieldTrendChart").getContext("2d");
    if (yieldTrendChart) yieldTrendChart.destroy();

    yieldTrendChart = new Chart(ctx, {
        type: "line",
        data: {
            labels: data.dates,
            datasets: [{
                label: "Yield (%)",
                data: data.avg_yield,
                borderColor: "#59a6ff",
                tension: 0.3,
            }],
        },
        options: {
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                y: {
                    min: 0,
                    max: 100,
                    ticks: {
                        callback: v => v + "%",
                    }
                }
            }
        }
    });
}

function updateDefectParetoChart(data) {
    const ctx = document.getElementById("defectParetoChart").getContext("2d");
    if (defectParetoChart) defectParetoChart.destroy();

    const labels = data.defect_pareto.map(d => d.defect_type);
    const counts = data.defect_pareto.map(d => d.count);

    defectParetoChart = new Chart(ctx, {
        type: "bar",
        data: {
            labels,
            datasets: [{
                label: "Count",
                data: counts,
                backgroundColor: "#59a6ff",
            }],
        },
        options: {
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
        },
    });
}

function updateDefectMapChart(data) {
    const ctx = document.getElementById("defectMapChart").getContext("2d");
    if (defectMapChart) defectMapChart.destroy();

    const points = data.defect_details.map(d => ({ x: d.x, y: d.y }));

    defectMapChart = new Chart(ctx, {
        type: "scatter",
        data: {
            datasets: [{
                label: "Defects",
                data: points,
                pointRadius: 3,
                backgroundColor: "#59a6ff",
            }],
        },
        options: {
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
        },
    });
}

// ------------------------ Detail Table ------------------------
function updateDetailTable(data) {
    console.log(data)
    detailTableBody.innerHTML = "";
    (data.defect_details || []).forEach(d => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td>${d.lot_id}</td>
            <td>${d.defect_type}</td>
            <td>${d.x}</td>
            <td>${d.y}</td>
            <td>${d.severity ?? ""}</td>
            <td>${d.wafer ?? ""}</td>
        `;
        detailTableBody.appendChild(tr);
    });
}

// ------------------------ Event Bindings ------------------------
dateFromSel.addEventListener("change", loadMachines);
dateToSel.addEventListener("change", loadMachines);
stationSel.addEventListener("change", loadRecipes);
productSel.addEventListener("change", loadLots);

// ⭐ Lot 多選更新 Dashboard（你之前缺少這段）
//lotSel.addEventListener("change", loadDashboard);

btnApply.addEventListener("click", async () => {
    const selectedLots = Array.from(lotSel.selectedOptions).map(o => o.value);
    if (selectedLots.length === 0) {
        alert("請至少選一個批號");
        return;
    }
    await loadDashboard(selectedLots);
});


// ------------------------ 初始化 ------------------------
loadDates();
