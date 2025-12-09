from locust import HttpUser, task, between
import random

class DashboardUser(HttpUser):
    # host = "http://localhost:8000"  # <--- 你 backend 的 API 位置
    host = "https://factory-yield-dashboard.onrender.com"  # <--- 你 backend 的 API 位置
    wait_time = between(1, 4)

    def on_start(self):
        """ 每個使用者啟動時登入取得 JWT """
        resp = self.client.post(
            "/auth/login",
            data={"username": "admin", "password": "admin"}
        )
        if resp.status_code == 200:
            self.token = resp.json()["access_token"]
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            self.token = None
            self.headers = {}

    @task(1)
    def filter_machines(self):
        self.client.get(
            "/filter/machines",
            params={"date_from": "2025-12-02", "date_to": "2025-12-07"},
            headers=self.headers
        )

    @task(2)
    def filter_recipes(self):
        self.client.get(
            "/filter/recipes",
            params={"date_from": "2025-12-02", "date_to": "2025-12-07",  "station": "AOI-01"},
            headers=self.headers
        )

    @task(3)
    def filter_lots(self):
        self.client.get(
            "/filter/lots",
            params={"date_from": "2025-12-02", "date_to": "2025-12-07", "station": "AOI-01", "product": "PKG-A"},
            headers=self.headers
        )

    @task(4)
    def yield_trend(self):
        self.client.get(
            "/yield/trend",
            params={"date_from": "2025-11-30", "date_to": "2025-12-06", "station": "AOI-01", "product": "PKG-A", "lots": "LOT01000"},
            headers=self.headers
        )