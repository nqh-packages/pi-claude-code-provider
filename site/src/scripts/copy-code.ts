export {};

const copyButton = document.querySelector<HTMLButtonElement>("#copy-code");
const selectButton = document.querySelector<HTMLButtonElement>("#select-code");
const codeBlock = document.querySelector<HTMLPreElement>("#install-code");
const code = codeBlock?.querySelector("code");
const status = document.querySelector<HTMLParagraphElement>("#copy-status");

if (copyButton && selectButton && codeBlock && code && status) {
  copyButton.hidden = false;
  selectButton.hidden = false;

  selectButton.addEventListener("click", () => {
    const selection = window.getSelection();
    if (!selection) {
      status.textContent = "Select the command text manually, then use your browser's Copy command.";
      return;
    }
    const range = document.createRange();
    range.selectNodeContents(code);
    codeBlock.focus();
    selection.removeAllRanges();
    selection.addRange(range);
    status.textContent = "Commands selected. Press Cmd+C on macOS or Ctrl+C elsewhere to copy.";
  });

  copyButton.addEventListener("click", async () => {
    copyButton.disabled = true;
    try {
      if (!navigator.clipboard?.writeText) {
        throw new Error("Clipboard unavailable");
      }
      await navigator.clipboard.writeText(code.textContent ?? "");
      status.textContent = "Commands copied. Review them before running.";
    } catch {
      status.textContent = "Clipboard unavailable. Choose Select code, then copy the commands manually.";
    } finally {
      copyButton.disabled = false;
    }
  });
}
