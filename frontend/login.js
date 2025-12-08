//const API = "http://127.0.0.1:8000";
const API = "https://factory-yield-dashboard.onrender.com";

document.getElementById("btnLogin").addEventListener("click", async () => {
    const username = document.getElementById("username").value.trim();
    const password = document.getElementById("password").value.trim();

    const form = new URLSearchParams();
    form.append("username", username);
    form.append("password", password);

    const res = await fetch(`${API}/auth/login`, {
        method: "POST",
        headers: {
            "Content-Type": "application/x-www-form-urlencoded",
        },
        body: form.toString(),
    });

    const data = await res.json();

    if (!res.ok) {
        document.getElementById("msg").textContent = data.detail ?? "登入失敗";
        return;
    }

    localStorage.setItem("token", data.access_token);
    localStorage.setItem("role", data.role);

    location.href = "index.html";
});
