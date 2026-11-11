import assert from "node:assert/strict";
import { test } from "node:test";
import { escapeHtml, renderAnswer } from "./render.ts";

test("escapes markup from the model", () => {
  const html = renderAnswer('<img src=x onerror="alert(1)"> hi', "m1", 0);
  assert.ok(!html.includes("<img"));
  assert.ok(html.includes("&lt;img"));
});

test("citation chips link to source cards, out-of-range markers vanish", () => {
  const html = renderAnswer("Fee is Rs 30,000 [1], [3].", "m2", 2);
  assert.ok(html.includes('href="#src-m2-1"'));
  assert.ok(!html.includes("#src-m2-3"));
  assert.ok(!html.includes("[3]"));
});

test("bold, bullets and numbered lists", () => {
  const html = renderAnswer("**Fees:**\n* BS: Rs. 12,000\n* MS: Rs. 12,000\n\n1. Apply\n2. Pay", "m3", 0);
  assert.equal(html, "<p><strong>Fees:</strong></p><ul><li>BS: Rs. 12,000</li><li>MS: Rs. 12,000</li></ul><ol><li>Apply</li><li>Pay</li></ol>");
});

test("urls become links without trailing punctuation", () => {
  const html = renderAnswer("See https://nu.edu.pk.", "m4", 0);
  assert.ok(html.includes('<a href="https://nu.edu.pk" target="_blank" rel="noopener noreferrer">https://nu.edu.pk</a>.'));
});

test("escapeHtml quotes", () => {
  assert.equal(escapeHtml(`"'&`), "&quot;&#39;&amp;");
});
