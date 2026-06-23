const form = document.getElementById("generator-form");
const previewBtn = document.getElementById("preview-btn");
const previewImage = document.getElementById("preview-image");
const previewStatus = document.getElementById("preview-status");

function formDataFromForm() {
  const data = new FormData(form);
  const platforms = [...form.querySelectorAll('input[name="platform"]:checked')].map(
    (input) => input.value
  );
  data.delete("platform");
  data.set("platforms", platforms.join(","));
  data.set("show_safe_zone", document.getElementById("show_safe_zone").checked ? "true" : "false");
  return data;
}

let previewTimer;

async function runPreview() {
  previewStatus.textContent = "Rendering preview...";
  const data = formDataFromForm();
  const response = await fetch("/api/preview", { method: "POST", body: data });
  if (!response.ok) {
    previewStatus.textContent = "Preview failed.";
    previewImage.hidden = true;
    return;
  }
  const blob = await response.blob();
  previewImage.src = URL.createObjectURL(blob);
  previewImage.hidden = false;
  previewStatus.textContent = "Preview updated.";
}

previewBtn.addEventListener("click", () => {
  clearTimeout(previewTimer);
  runPreview();
});

form.addEventListener("input", () => {
  clearTimeout(previewTimer);
  previewTimer = setTimeout(runPreview, 700);
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  previewStatus.textContent = "Generating ZIP...";
  const data = formDataFromForm();
  const response = await fetch("/api/generate", { method: "POST", body: data });
  if (!response.ok) {
    previewStatus.textContent = "Generation failed.";
    return;
  }
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = "school-of-ai-templates.zip";
  anchor.click();
  URL.revokeObjectURL(url);
  previewStatus.textContent = "ZIP downloaded.";
});

runPreview();