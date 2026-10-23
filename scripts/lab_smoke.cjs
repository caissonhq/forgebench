// Optional browser QA. Run against an isolated local bench; creates demo runs.
const assert = require("node:assert/strict");
const path = require("node:path");
const os = require("node:os");
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || "playwright");

(async () => {
  const browser = await chromium.launch({
    headless: true,
    ...(process.env.CHROME_PATH
      ? { executablePath: process.env.CHROME_PATH }
      : {}),
  });
  const errors = [];
  const httpErrors = [];
  const page = await browser.newPage({
    viewport: { width: 1440, height: 1000 },
  });
  page.on("pageerror", (error) => errors.push(error.message));
  page.on("console", (message) => {
    if (
      message.type() === "error" &&
      !message.text().includes("400 (Bad Request)")
    )
      errors.push(message.text());
  });
  page.on("response", (response) => {
    if (response.status() >= 400)
      httpErrors.push({
        path: new URL(response.url()).pathname,
        status: response.status(),
      });
  });
  const url = process.env.FORGEBENCH_LAB_URL || "http://127.0.0.1:8765";
  const shot = (name) =>
    path.join(
      process.env.FORGEBENCH_QA_DIR || os.tmpdir(),
      `forgebench-${name}.png`,
    );
  try {
    await page.goto(url);
    await page
      .getByRole("heading", { name: "Test bench", exact: true })
      .waitFor();
    await page.evaluate(() => document.fonts.ready);
    assert.equal(await page.locator(".trial-row").count(), 12);
    await page.getByRole("tab", { name: "Assertions" }).click();
    assert.match(
      await page.getByRole("tabpanel").innerText(),
      /EXPECTED VALUE/,
    );
    await page.getByRole("tab", { name: "Assertions" }).press("ArrowLeft");
    assert.equal(
      await page
        .getByRole("tab", { name: "Prompt" })
        .getAttribute("aria-selected"),
      "true",
    );
    assert.equal(
      await page
        .getByRole("tab", { name: "Prompt" })
        .evaluate((el) => el === document.activeElement),
      true,
    );
    await page.screenshot({ path: shot("bench-desktop"), fullPage: true });
    await page.getByRole("button", { name: "Run 12 trials" }).click();
    await page.getByRole("button", { name: "Export JSON" }).waitFor();
    let data = await page.evaluate(
      async () => await (await fetch("/api/bootstrap")).json(),
    );
    assert.equal(data.runs[0].passed, 11);
    assert.equal(data.runs[0].failed, 1);
    await page.getByRole("button", { name: "Failed", exact: true }).click();
    assert.equal(await page.locator(".trial-row").count(), 1);
    await page.locator(".trial-info").first().click();
    assert.match(await page.locator("#detail-region").innerText(), /13/);
    assert.match(await page.locator("#detail-region").innerText(), /14/);
    assert.equal(
      await page
        .getByRole("tab", { name: "Result", exact: true })
        .getAttribute("aria-selected"),
      "true",
    );
    await page.screenshot({ path: shot("result-desktop"), fullPage: true });
    const downloadPromise = page.waitForEvent("download");
    await page.getByRole("button", { name: "Export JSON" }).click();
    const download = await downloadPromise;
    assert.equal(download.suggestedFilename(), "forgebench-run.json");
    await page.getByRole("button", { name: "Clear view" }).click();
    await page.locator("#profile").selectOption("baseline");
    await page.getByRole("button", { name: "Run 12 trials" }).click();
    await page.getByRole("button", { name: "Export JSON" }).waitFor();
    data = await page.evaluate(
      async () => await (await fetch("/api/bootstrap")).json(),
    );
    assert.equal(data.runs[0].passed, 3);
    await page.locator("a[data-view=compare]").click();
    await page.locator("#comparison .data-table").waitFor();
    assert.match(await page.locator("#comparison").innerText(), /8 regressed/);
    await page.screenshot({ path: shot("compare-desktop"), fullPage: true });
    await page.locator("a[data-view=history]").click();
    await page
      .getByRole("heading", { name: "Run history", exact: true })
      .waitFor();
    assert.equal(await page.locator("tbody tr").count(), 2);
    await page.locator("[data-action=open-run]").first().click();
    await page.getByRole("button", { name: "Clear view" }).click();
    await page.getByRole("button", { name: "Run 12 trials" }).click();
    await page.getByRole("button", { name: "Stop", exact: true }).click();
    await page.getByRole("button", { name: "Export JSON" }).waitFor();
    assert.match(await page.locator("#run-region").innerText(), /Cancelled/);
    await page.getByRole("button", { name: "Clear view" }).click();

    await page.getByRole("button", { name: "New trial" }).click();
    await page.locator("input[name=title]").fill("Browser QA trial");
    await page.locator("textarea[name=prompt]").fill("Return the word READY.");
    await page.locator("textarea[name=expected]").fill("READY");
    await page.getByRole("button", { name: "Save trial" }).click();
    await page.locator("#trial-dialog").waitFor({ state: "hidden" });
    assert.equal(await page.locator(".trial-row").count(), 13);
    await page.getByRole("button", { name: "Edit trial", exact: true }).click();
    page.once("dialog", (dialog) => dialog.accept());
    await page
      .getByRole("button", { name: "Delete trial", exact: true })
      .click();
    await page.locator("#trial-dialog").waitFor({ state: "hidden" });
    assert.equal(await page.locator(".trial-row").count(), 12);

    await page.locator("a[data-view=settings]").click();
    await page
      .getByRole("heading", { name: "Model connection", exact: true })
      .waitFor();
    await page.locator("input[name=base_url]").fill("https://example.test/v1");
    await page.locator("input[name=model]").fill("qa-model");
    await page.getByRole("button", { name: "Save connection" }).click();
    await page.locator("#settings-error .inline-alert").waitFor();
    await page.screenshot({ path: shot("settings-desktop"), fullPage: true });
    assert.match(
      await page.locator("#settings-error").innerText(),
      /explicit permission/,
    );
    // Saving a local connection must not contact it.
    await page
      .locator("input[name=base_url]")
      .fill("http://localhost:11434/v1");
    await page.getByRole("button", { name: "Save connection" }).click();
    await page
      .getByRole("heading", { name: "Test bench", exact: true })
      .waitFor();
    assert.match(await page.locator(".panel-body").innerText(), /qa-model/);
    await page
      .getByRole("button", { name: "Demo fixtures", exact: true })
      .click();

    for (const width of [390, 768, 1440]) {
      await page.setViewportSize({ width, height: 900 });
      await page.screenshot({ path: shot(`bench-${width}`), fullPage: true });
      const sizes = await page.evaluate(() => ({
        scroll: document.documentElement.scrollWidth,
        width: window.innerWidth,
      }));
      assert.ok(sizes.scroll <= sizes.width, `Horizontal overflow at ${width}`);
      const overlaps = await page.locator(".trial-row").evaluateAll((rows) =>
        rows.some((row) => {
          const checkbox = row
            .querySelector('input[type="checkbox"]')
            .getBoundingClientRect();
          const info = row.querySelector(".trial-info").getBoundingClientRect();
          return checkbox.right > info.left;
        }),
      );
      assert.equal(overlaps, false, `Checkbox overlaps trial at ${width}`);
      const broken = await page
        .locator("img")
        .evaluateAll((images) =>
          images
            .filter((img) => !img.complete || !img.naturalWidth)
            .map((img) => img.src),
        );
      assert.deepEqual(broken, []);
    }
    await page.setViewportSize({ width: 390, height: 844 });
    await page.locator(".trial-info").first().click();
    await page.getByRole("dialog").waitFor();
    assert.match(
      await page.getByRole("dialog").innerText(),
      /SYSTEM INSTRUCTION/,
    );
    await page
      .getByRole("dialog")
      .getByRole("tab", { name: "Assertions" })
      .click();
    assert.match(
      await page.getByRole("dialog").getByRole("tabpanel").innerText(),
      /EXPECTED VALUE/,
    );
    await page.screenshot({ path: shot("inspector-mobile"), fullPage: true });
    await page.getByRole("button", { name: "Close", exact: true }).click();
    for (const view of ["library", "history", "compare", "settings"]) {
      await page.locator(`a[data-view=${view}]`).click();
      await page.screenshot({ path: shot(`${view}-mobile`), fullPage: true });
      assert.equal(
        await page.evaluate(
          () => document.documentElement.scrollWidth <= innerWidth,
        ),
        true,
        `Horizontal overflow in mobile ${view}`,
      );
    }
    assert.deepEqual(errors, []);
    assert.deepEqual(httpErrors, [{ path: "/api/settings", status: 400 }]);
    console.log(
      "PASS: demo runs, evidence tabs, keyboard navigation, filters, export, comparison, history, cancellation, trial editing, endpoint consent, 3 viewports, mobile views, no overlaps, and no unexpected browser errors.",
    );
  } finally {
    await page.close();
    await browser.close();
  }
})().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
