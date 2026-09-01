import { expect, test } from "@playwright/test";

const BEFORE_ID = "89284e7a-04bc-4917-9467-502f2ff3bece";
const AFTER_ID = "f784904e-b115-4a2c-b5d5-9a94ed075e94";

test("public Explore search opens the approved real-derived review bundle", async ({
  page,
}) => {
  await page.goto("/");

  await expect(
    page.getByRole("heading", {
      name: "Explore provider-reported SAR availability",
    }),
  ).toBeVisible();
  await expect(
    page.getByRole("region", { name: /Map centered on/ }),
  ).toBeVisible();

  await page
    .getByRole("button", { name: "Search reported acquisitions" })
    .click();
  await expect(
    page.getByText("complete · 2 records", { exact: true }),
  ).toBeVisible();
  await expect(
    page.getByText(/complete · \d+ records/, { exact: true }),
  ).toHaveCount(2);

  await page
    .getByRole("button", { name: `Use ${BEFORE_ID} as Before` })
    .click();
  await page.getByRole("button", { name: `Use ${AFTER_ID} as After` }).click();
  await page.getByRole("button", { name: "Review pair" }).click();
  await expect(
    page.getByRole("dialog", { name: "Review candidate pair" }),
  ).toBeVisible();
  await page.screenshot({
    path: "../../docs/qa/evidence/eat-021/vercel-pair-review.png",
  });

  await page.getByRole("button", { name: "Check comparability" }).click();
  await expect(
    page.getByRole("heading", { name: "Comparability evidence" }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Start deterministic preparation" })
    .click();

  await expect(
    page.getByRole("heading", {
      name: "Bingham Canyon mine surface-change review",
    }),
  ).toBeVisible();
  const imagery = page.locator(".image-view img");
  await expect(imagery).toHaveCount(2);
  await expect
    .poll(() =>
      imagery.evaluateAll((images) =>
        images.every(
          (image) =>
            image instanceof HTMLImageElement &&
            image.complete &&
            image.naturalWidth > 0,
        ),
      ),
    )
    .toBe(true);
  await page.evaluate("window.scrollTo(0, 0)");
  await page.screenshot({
    path: "../../docs/qa/evidence/eat-021/vercel-analyze.png",
  });
});
