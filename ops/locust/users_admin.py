"""Admin user class for Locust load tests.

Simulates an agency admin hitting core Django REST endpoints. The
``on_start`` hook performs a token login and stores the bearer header
for subsequent requests. Run with:

    locust -f ops/locust/locustfile.py --host http://localhost:8000
"""

from locust import HttpUser, between, task


class AdminUser(HttpUser):
    """Simulates an agency admin hitting core APIs."""

    wait_time = between(1, 3)
    host = "http://localhost:8000"

    def on_start(self) -> None:
        """Login and store token.

        Raises:
            RuntimeError: if login fails.
        """
        r = self.client.post(
            "/api/auth/token/",
            json={"email": "load@test.io", "password": "load"},
            headers={"X-Tenant-Slug": "load"},
        )
        if r.status_code != 200:
            raise RuntimeError(f"login failed: {r.status_code}")
        self.token = r.json()["access"]
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "X-Tenant-Slug": "load",
        }

    @task(3)
    def list_clients(self) -> None:
        """GET clients list (heaviest read)."""
        self.client.get("/api/clients/", headers=self.headers)

    @task(1)
    def create_client(self) -> None:
        """POST a new client (triggers onboarding)."""
        self.client.post(
            "/api/clients/",
            json={"name": "Load Client", "email": "c@load.io"},
            headers=self.headers,
        )

    @task(2)
    def list_invoices(self) -> None:
        """GET invoices list."""
        self.client.get("/api/invoices/", headers=self.headers)

    @task(1)
    def list_followups(self) -> None:
        """GET follow-ups list."""
        self.client.get("/api/reminders/", headers=self.headers)
