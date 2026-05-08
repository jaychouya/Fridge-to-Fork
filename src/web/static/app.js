function fileToBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const result = String(reader.result || "");
      const base64 = result.includes(",") ? result.split(",")[1] : result;
      resolve(base64);
    };
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}

function setText(id, text, className = "muted") {
  const el = document.getElementById(id);
  if (!el) return;
  if (el.tagName === "P") {
    el.className = className;
  }
  el.textContent = text;
}

function setHealth(ok) {
  const badge = document.getElementById("healthBadge");
  badge.textContent = ok ? "Server Online" : "Server Offline";
  badge.style.background = ok ? "#dcfce7" : "#fee2e2";
  badge.style.color = ok ? "#166534" : "#b91c1c";
}

function renderInventory(items) {
  const list = document.getElementById("inventoryList");
  const empty = document.getElementById("inventoryEmpty");
  list.innerHTML = "";
  if (!items || items.length === 0) {
    empty.style.display = "grid";
    return;
  }
  empty.style.display = "none";
  for (const item of items) {
    const li = document.createElement("li");
    li.className = "list-item";
    const exp = item.earliest_expires_on ? ` · expires ${item.earliest_expires_on}` : "";
    li.textContent = `${item.display_name} · ${item.total_quantity} ${item.unit}${exp}`;
    list.appendChild(li);
  }
}

function renderRecommendations(payload) {
  const list = document.getElementById("recommendList");
  const empty = document.getElementById("recommendEmpty");
  const message = document.getElementById("scanMessage");
  list.innerHTML = "";
  if (payload.message) {
    message.textContent = payload.message;
  }
  if (!payload.recipes || payload.recipes.length === 0) {
    empty.style.display = "grid";
    return;
  }
  empty.style.display = "none";
  for (const r of payload.recipes) {
    const li = document.createElement("li");
    li.className = "list-item";
    const title = document.createElement("strong");
    title.textContent = r.title;
    const why = document.createElement("small");
    why.textContent = r.why_recommended;
    const link = document.createElement("a");
    link.href = r.url;
    link.target = "_blank";
    link.rel = "noreferrer";
    link.textContent = "查看菜谱";
    li.appendChild(title);
    li.appendChild(document.createElement("br"));
    li.appendChild(why);
    li.appendChild(document.createElement("br"));
    li.appendChild(link);
    list.appendChild(li);
  }
}

function renderDetectedIngredients(items) {
  const wrap = document.getElementById("detectedIngredients");
  wrap.innerHTML = "";
  for (const x of items || []) {
    const span = document.createElement("span");
    span.className = "tag";
    span.textContent = `${x.name_norm} (${x.quantity_est} ${x.unit})`;
    wrap.appendChild(span);
  }
}

async function checkHealth() {
  try {
    const res = await fetch("/api/health");
    setHealth(res.ok);
  } catch {
    setHealth(false);
  }
}

function applyTheme(theme) {
  if (theme === "dark") {
    document.body.classList.add("dark");
  } else {
    document.body.classList.remove("dark");
  }
  const btn = document.getElementById("themeToggle");
  btn.textContent = document.body.classList.contains("dark") ? "Light" : "Dark";
}

function initTheme() {
  const stored = localStorage.getItem("ftf_theme");
  if (stored) {
    applyTheme(stored);
  } else {
    const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    applyTheme(prefersDark ? "dark" : "light");
  }
}

document.getElementById("scanForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  try {
    const fileInput = document.getElementById("image");
    const file = fileInput.files[0];
    if (!file) {
      setText("scanMessage", "请先选择图片", "muted warn");
      return;
    }
    setText("scanMessage", "识别中，请稍候...", "muted");
    const image_base64 = await fileToBase64(file);
    const res = await fetch("/api/scan", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ image_base64, filename: file.name }),
    });
    const data = await res.json();
    if (!data.ok) {
      setText("scanMessage", data.error || "Scan failed", "muted error");
      renderDetectedIngredients([]);
      return;
    }
    setText("scanMessage", data.message || "Scan complete", "muted ok");
    renderDetectedIngredients(data.ingredients);
    renderInventory(data.expiring || []);
    renderRecommendations(data);
  } catch {
    setText("scanMessage", "网络异常，请重试", "muted error");
  }
});

document.getElementById("refreshInventory").addEventListener("click", async () => {
  try {
    const res = await fetch("/api/inventory");
    const data = await res.json();
    renderInventory(data.items || []);
  } catch {
    setText("inventoryEmpty", "库存拉取失败", "muted error");
  }
});

document.getElementById("getRecommend").addEventListener("click", async () => {
  try {
    const res = await fetch("/api/recommend");
    const data = await res.json();
    renderRecommendations(data);
  } catch {
    setText("recommendEmpty", "推荐拉取失败", "muted error");
  }
});

document.getElementById("cookedForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  try {
    const ingredient = document.getElementById("ingredient").value.trim();
    const quantity = Number(document.getElementById("quantity").value);
    const res = await fetch("/api/cooked", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ingredient, quantity }),
    });
    const data = await res.json();
    if (data.ok) {
      setText("cookedResult", "库存扣减完成", "muted ok");
    } else {
      setText("cookedResult", `库存不足，剩余缺口：${data.leftover}`, "muted warn");
    }
  } catch {
    setText("cookedResult", "提交失败，请稍后重试", "muted error");
  }
});

document.getElementById("themeToggle").addEventListener("click", () => {
  const next = document.body.classList.contains("dark") ? "light" : "dark";
  applyTheme(next);
  localStorage.setItem("ftf_theme", next);
});

initTheme();
checkHealth();
document.getElementById("refreshInventory").click();
document.getElementById("getRecommend").click();
