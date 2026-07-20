import { expect, test } from "@playwright/test";

/**
 * Smoke: admin sign-in lands on the dashboard.
 *
 * Requires the full ``docker compose`` stack (Django + frontend) and a
 * pre-seeded admin user. Marked ``test.skip`` in environments without
 * the stack; flip to ``test`` locally once ``docker compose up -d`` is
 * running and seed users exist.
 */
test("admin sign-in lands on the dashboard", async ({ page }) => {
  test.skip(process.env.RUN_E2E !== "1", "E2E requires RUN_E2E=1 + docker compose stack");
  await page.goto("/login");
  await page.getByLabel("Email").fill("admin@acme.io");
  await page.getByLabel("Password").fill("password");
  await page.getByRole("button", { name: /sign in/i }).click();
  await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();
});
