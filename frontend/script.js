// frontend/script.js
const API_BASE = "http://127.0.0.1:8000";

const dateFromSel = document.getElementById("dateFrom");
const dateToSel = document.getElementById("dateTo");
const stationSel = document.getElementById("stationSelect");
const productSel = document.getElementById("productSelect");
const lotSel = document.getElementById("lotSelect");
const btnApply = document.getElementById("btnApply");
const btnSeed = document.getElementById("btnSeed");
const btnLogout = document.getElementById("btnLogout");
const messageEl = document.getElementById("message");
const userInfoEl = document.getElementById("userInfo");
const detailTableBody = document.querySelector("#detailTable tbody");

let yieldTrendChart = null;
let defectParetoChart = null;
let defectMapChart = null;

// ------- 啟動時檢查登入 -------

window.addEventListener("load", () => {
  const token = localStorage.getItem("token");
  const role = localStorage.getItem("role");
  const username = localStorage.getItem("username");

  if (!token) {
    window.location.href = "login.html";
    return;
  }

  userInfoEl.textContent = `${username || ""} (${role || ""})`;
  if (role !== "admin") {
    btnSeed.style.display = "none";
  }

  init();
});

btnLogout.addEventListener("click", () => {
  localStorage.removeItem("token");
  localStorage.removeItem("role");
  localStorage.removeItem("username");
  window.location.href = "login.html";
});

function authHeaders() {
  const token = localStorage.getItem("token");
  return {
    "Authorization": "Bearer " + token,
  };
}

// ------- 工具：支援陣列 lot_ids -------

function buildQuery(params) {
  const usp = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v === undefined || v === null || v === "") return;
    if (Array.isArray(v)) {
      v.forEach(val => usp.append(k, val));
    } else {
      usp.append(k, v);
    }
  });
  return usp.toString();
}

// ------- 初始化 -------

async function init() {
  await loadDates();
}

// ------- 1) 日期 -------

async function loadDates() {
  try {
    const res = await fetch(`${API_BASE}/filter/dates`, {
      headers: authHeaders(),
    });
    if (!res.ok) {
      messageEl.textContent = "取得日期失敗";
      return;
    }
    const dates = await res.json();
    dateFromSel.innerHTML = "";
    dateToSel.innerHTML = "";

    dates.forEach((d) => {
      const opt1 = document.createElement("option");
      opt1.value = opt1.textContent = d;
      dateFromSel.appendChild(opt1);

      const opt2 = document.createElement("option");
      opt2.value = opt2.textContent = d;
      dateToSel.appendChild(opt2);
    });

    if (dates.length > 0) {
      dateFromSel.value = dates[0];
      dateToSel.value = dates[dates.length - 1];
    }

    await loadMachines();
  } catch (e) {
    messageEl.textContent = "無法連線到伺服器 (dates)";
  }
}

// ------- 2) 機台 -------

async function loadMachines() {
  const from = dateFromSel.value;
  const to = dateToSel.value;
  stationSel.innerHTML = "";
  productSel.innerHTML = "";
  lotSel.innerHTML = "";

  if (!from || !to) return;

  const qs = buildQuery({ date_from: from, date_to: to });
  try {
    const res = await fetch(`${API_BASE}/filter/machines?${qs}`, {
      headers: authHeaders(),
    });
    if (!res.ok) {
      messageEl.textContent = "取得機台失敗";
      return;
    }
    const machines = await res.json();
    machines.forEach((m) => {
      const opt = document.createElement("option");
      opt.value = opt.textContent = m;
      stationSel.appendChild(opt);
    });

    if (machines.length > 0) {
      stationSel.value = machines[0];
      await loadRecipes();
    }
  } catch (e) {
    messageEl.textContent = "無法連線到伺服器 (machines)";
  }
}

// ------- 3) Recipe -------

async function loadRecipes() {
  const from = dateFromSel.value;
  const to = dateToSel.value;
  const station = stationSel.value;

  productSel.innerHTML = "";
  lotSel.innerHTML = "";

  if (!from || !to || !station) return;

  const qs = buildQuery({ date_from: from, date_to: to, station });
  try {
    const res = await fetch(`${API_BASE}/filter/recipes?${qs}`, {
      headers: authHeaders(),
    });
    if (!res.ok) {
      messageEl.textContent = "取得 Recipe 失敗";
      return;
    }
    const recipes = await res.json();
    recipes.forEach((p) => {
      const opt = document.createElement("option");
      opt.value = opt.textContent = p;
      productSel.appendChild(opt);
    });

    if (recipes.length > 0) {
      productSel.value = recipes[0];
      await loadLots(true); // Recipe 改變 → 第一次載入全選
    }
  } catch (e) {
    messageEl.textContent = "無法連線到伺服器 (recipes)";
  }
}

// ------- 4) Lots (多選) -------

async function loadLots(autoSelectAll) {
  const from = dateFromSel.value;
  const to = dateToSel.value;
  const station = stationSel.value;
  const product = productSel.value;

  lotSel.innerHTML = "";

  if (!from || !to || !station || !product) return;

  const qs = buildQuery({ date_from: from, date_to: to, station, product });
  try {
    const res = await fetch(`${API_BASE}/filter/lots?${qs}`, {
      headers: authHeaders(),
    });
    if (!res.ok) {
      messageEl.textContent = "取得批號失敗";
      return;
    }
    const lots = await res.json();
    lots.forEach((l) => {
      const opt = document.createElement("option");
      opt.value = opt.textContent = l;
      lotSel.appendChild(opt);
    });

    // 只有第一次載入/Recipe 改變時全選
    if (autoSelectAll) {
      Array.from(lotSel.options).forEach((o) => (o.selected = true));
    }
  } catch (e) {
    messageEl.textContent = "無法連線到伺服器 (lots)";
  }
}

// ------- 5) Dashboard 查詢 -------

async function loadDashboard() {
  const from = dateFromSel.value;
  const to = dateToSel.value;
  const station = stationSel.value || "";
  const product = productSel.value || "";

  const selectedLots = Array.from(lotSel.selectedOptions).map((o) => o.value);

  if (!from || !to) {
    alert("請先選日期區間");
    return;
  }

  const qs = buildQuery({
    date_from: from,
    date_to: to,
    station,
    product,
    lots: selectedLots,  // ★ 這裡用陣列，後端會解析成 List[str]
  });

  try {
    const res = await fetch(`${API_BASE}/yield/trend?${qs}`, {
      headers: authHeaders(),
    });
    if (!res.ok) {
      messageEl.textContent = "查詢失敗";
      return;
    }
    const data = await res.json();
    updateYieldTrendChart(data);
    updateDefectParetoChart(data);
    updateDefectMapChart(data);
    updateDetailTable(data);
    messageEl.textContent = `共 ${data.defect_details?.length || 0} 筆 defect`;
  } catch (e) {
    messageEl.textContent = "無法連線到伺服器 (trend)";
  }
}

// ------- Chart 更新 -------

function updateYieldTrendChart(data) {
  const ctx = document.getElementById("yieldTrendChart").getContext("2d");
  if (yieldTrendChart) yieldTrendChart.destroy();

  yieldTrendChart = new Chart(ctx, {
    type: "line",
    data: {
      labels: data.dates,
      datasets: [
        {
          label: "Average Yield (%)",
          data: data.avg_yield,
          tension: 0.2,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: {
          min: 0,
          max: 100,
          ticks: {
            callback: (v) => v + "%",
          },
        },
      },
      plugins: {
        legend: { display: false },
      },
    },
  });
}

function updateDefectParetoChart(data) {
  const ctx = document.getElementById("defectParetoChart").getContext("2d");
  if (defectParetoChart) defectParetoChart.destroy();

  const labels = data.defect_pareto.map((d) => d.defect_type);
  const counts = data.defect_pareto.map((d) => d.count);

  defectParetoChart = new Chart(ctx, {
    type: "bar",
    data: {
      labels,
      datasets: [
        {
          label: "Defect Count",
          data: counts,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
      },
      scales: {
        x: { ticks: { autoSkip: false } },
      },
    },
  });
}

function updateDefectMapChart(data) {
  const ctx = document.getElementById("defectMapChart").getContext("2d");
  if (defectMapChart) defectMapChart.destroy();

  const points = (data.defect_details || []).map((d) => ({
    x: d.x,
    y: d.y,
  }));

  defectMapChart = new Chart(ctx, {
    type: "scatter",
    data: {
      datasets: [
        {
          label: "Defect Location",
          data: points,
          pointRadius: 3,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: { title: { display: true, text: "X" } },
        y: { title: { display: true, text: "Y" } },
      },
      plugins: {
        legend: { display: false },
      },
    },
  });
}

function updateDetailTable(data) {
  detailTableBody.innerHTML = "";
  (data.defect_details || []).forEach((d) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${d.lot_id ?? ""}</td>
      <td>${d.defect_type ?? ""}</td>
      <td>${d.x ?? ""}</td>
      <td>${d.y ?? ""}</td>
      <td>${d.severity ?? ""}</td>
      <td>${d.wafer ?? ""}</td>
    `;
    detailTableBody.appendChild(tr);
  });
}

// ------- Event binding -------

dateFromSel.addEventListener("change", async () => {
  await loadMachines();
});

dateToSel.addEventListener("change", async () => {
  await loadMachines();
});

stationSel.addEventListener("change", async () => {
  await loadRecipes();
});

productSel.addEventListener("change", async () => {
  await loadLots(true);  // Recipe 切換 → 全選
});

btnApply.addEventListener("click", async () => {
  await loadDashboard(); // 只用目前勾選的 lot
});

btnSeed.addEventListener("click", async () => {
  if (!confirm("確定要重建測試資料？現有資料會被清空")) return;

  try {
    const res = await fetch(`${API_BASE}/seed/all`, {
      method: "GET",
      headers: authHeaders(),
    });
    if (!res.ok) {
      messageEl.textContent = "重建失敗 (權限或伺服器錯誤)";
      return;
    }
    const data = await res.json();
    messageEl.textContent = `重建完成，產生 ${data.lots} 個 lots，請重新選擇條件`;
    await loadDates();
  } catch (e) {
    messageEl.textContent = "無法連線到伺服器 (seed)";
  }
});
