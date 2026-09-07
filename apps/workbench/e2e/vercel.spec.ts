import { expect, test } from "@playwright/test";

const BEFORE_ID = "89284e7a-04bc-4917-9467-502f2ff3bece";
const AFTER_ID = "f784904e-b115-4a2c-b5d5-9a94ed075e94";

test("Analyze keeps page height bounded and scrolls candidate rows", async ({
  page,
}) => {
  await page.goto("/analyze");
  await expect(
    page.getByRole("heading", {
      name: "Bingham Canyon mine surface-change review",
    }),
  ).toBeVisible();

  const queue = page.getByRole("region", {
    name: "Scrollable candidate queue",
  });
  await expect(queue).toBeVisible();
  await expect
    .poll(() =>
      page.evaluate(
        () =>
          document.documentElement.scrollHeight -
          document.documentElement.clientHeight,
      ),
    )
    .toBeLessThanOrEqual(1);
  await expect
    .poll(() =>
      queue.evaluate((element) => ({
        clientHeight: element.clientHeight,
        overflowY: getComputedStyle(element).overflowY,
        scrollHeight: element.scrollHeight,
        tabIndex: element.tabIndex,
      })),
    )
    .toEqual({
      clientHeight: expect.any(Number),
      overflowY: "auto",
      scrollHeight: expect.any(Number),
      tabIndex: 0,
    });
  expect(
    await queue.evaluate((element) => element.scrollHeight),
  ).toBeGreaterThan(await queue.evaluate((element) => element.clientHeight));
  await queue.press("PageDown");
  await expect
    .poll(() => queue.evaluate((element) => element.scrollTop))
    .toBeGreaterThan(0);
  expect(await page.evaluate(() => window.scrollY)).toBe(0);
});

test("public Explore search opens the approved real-derived review bundle", async ({
  page,
}, testInfo) => {
  await page.goto("/explore");

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
    path: testInfo.outputPath("pair-review.png"),
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
    path: testInfo.outputPath("analyze.png"),
  });
});

test("Nepal-first investigation persists review state and exports a brief", async ({
  page,
}) => {
  await page.goto("/");
  await expect(
    page.getByRole("heading", {
      name: "Investigate the 2026 Nepal flood corridor",
    }),
  ).toBeVisible();
  await page.getByRole("link", { name: "Start investigation" }).click();
  await expect(page.getByText("Selected dates, shared camera")).toBeVisible();
  await expect(page.getByLabel("Before imagery date")).toBeVisible();
  const afterDate = page.getByLabel("After imagery date");
  await expect(afterDate).toBeVisible();
  await expect
    .poll(() => afterDate.locator("option").count())
    .toBeGreaterThan(1);
  await afterDate.selectOption("S2B_45RUM_20260903_0_L2A");
  await expect(
    page.getByText("After imagery updated to Sep 3, 2026."),
  ).toBeVisible();
  await expect(page.getByText("After · Sep 3, 2026")).toBeVisible();
  await expect(page.locator(".imagery-attribution")).toContainText(
    "Contains modified Copernicus Sentinel data",
  );

  await page.getByRole("radio", { name: "Needs context" }).check();
  await page
    .getByLabel("Notes")
    .fill("Cloud limits the visible eastern portion of this observation.");
  await page.getByRole("button", { name: "Record assessment" }).click();
  await expect(page.getByText("Assessment recorded.")).toBeVisible();
  await page.reload();
  await expect(
    page.getByRole("radio", { name: "Needs context" }),
  ).toBeChecked();
  await expect(page.getByLabel("Notes")).toHaveValue(
    "Cloud limits the visible eastern portion of this observation.",
  );

  await page.getByRole("button", { name: /Brief/ }).click();
  const downloadPromise = page.waitForEvent("download");
  await page.getByRole("button", { name: "Download JSON" }).click();
  const download = await downloadPromise;
  expect(download.suggestedFilename()).toBe("nepal-flood-2026-brief.json");
});

test("narrow Nepal context keeps the primary action in view", async ({
  page,
}) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/investigate/nepal-flood-2026");
  const context = page.locator(".step-intro");
  await expect(context).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Compare imagery" }),
  ).toBeVisible();
  expect((await context.boundingBox())?.height).toBeLessThan(260);
});
