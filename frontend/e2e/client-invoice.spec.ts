import { expect, test } from "@playwright/test";

/**
 * Smoke: client sign-in sees their invoices.
 *
 * Skipped unless ``RUN_E2E=1`` is set; requires the docker compose
 * stack + a seeded client user.
 */
test("client sign-in sees their invoices", async ({ page }) => {
  test.skip(process.env.RUN_E2E !== "1", "E2E requires RUN_E2E=1 + docker compose stack");
  await page.goto("/login");
  await page.getByLabel("Email").fill("client@acme.io");
  await page.getByLabel("Password").fill("password");
  await page.getByRole("button", { name: /sign in/i }).click();
  await expect(page.getByRole("heading", { name: "My invoices" })).toBeVisible();
});
