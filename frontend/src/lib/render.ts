/** Tiny, safe renderer for model answers: paragraphs, lists, **bold**, bare URLs and [n] citation chips.
 *  All input is HTML-escaped first, so nothing from the model can inject markup. */

export function escapeHtml(s: string): string {
  return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#39;");
}

function inline(escaped: string, msgId: string, sourceCount: number): string {
  return escaped
    .replace(/\*\*([^*\n]+)\*\*/g, "<strong>$1</strong>")
    .replace(/https?:\/\/[^\s<]+[^\s<.,;:!?)]/g, (url) => `<a href="${url}" target="_blank" rel="noopener noreferrer">${url}</a>`)
    .replace(/\[(\d+)\]/g, (whole, n) => {
      const i = Number(n);
      return i >= 1 && i <= sourceCount ? `<a class="cite" href="#src-${msgId}-${i}" data-cite="${i}" aria-label="Source ${i}">${i}</a>` : "";
    });
}

export function renderAnswer(text: string, msgId: string, sourceCount: number): string {
  const out: string[] = [];
  let list: "ul" | "ol" | null = null;
  const closeList = () => {
    if (list) out.push(`</${list}>`);
    list = null;
  };
  for (const raw of escapeHtml(text.trim()).split("\n")) {
    const line = raw.trim();
    const bullet = line.match(/^[*-]\s+(.*)/);
    const numbered = line.match(/^\d+\.\s+(.*)/);
    if (bullet || numbered) {
      const kind = bullet ? "ul" : "ol";
      if (list !== kind) {
        closeList();
        out.push(`<${kind}>`);
        list = kind;
      }
      out.push(`<li>${inline((bullet ?? numbered)![1], msgId, sourceCount)}</li>`);
    } else if (line === "") {
      closeList();
    } else {
      closeList();
      out.push(`<p>${inline(line, msgId, sourceCount)}</p>`);
    }
  }
  closeList();
  return out.join("");
}
