const API = "http://127.0.0.1:8000";

document.getElementById("btnLogin").addEventListener("click", async () => {
    const username = document.getElementById("username").value.trim();
    const password = document.getElementById("password").value.trim();

    const res = await fetch(`${API}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
    });

    const data = await res.json();

    if (!res.ok) {
        document.getElementById("msg").textContent = data.detail ?? "登入失敗";
        return;
    }

    // 儲存 JWT token 與角色
    localStorage.setItem("token", data.access_token);
    localStorage.setItem("role", data.role);

    location.href = "index.html";
});