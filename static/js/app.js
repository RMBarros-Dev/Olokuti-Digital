const CONTRAST_STORAGE_KEY = "olokuti_high_contrast";

function isHighContrastStored() {
  try {
    return window.localStorage && localStorage.getItem(CONTRAST_STORAGE_KEY) === "true";
  } catch (e) {
    return document.documentElement.getAttribute("data-contrast") === "high";
  }
}

function applyHighContrastState(enabled, announce = false) {
  if (enabled) {
    document.documentElement.setAttribute("data-contrast", "high");
  } else {
    document.documentElement.removeAttribute("data-contrast");
  }

  try {
    if (window.localStorage) {
      localStorage.setItem(CONTRAST_STORAGE_KEY, enabled ? "true" : "false");
    }
  } catch (e) {}

  document.querySelectorAll("[data-contrast-toggle]").forEach((btn) => {
    btn.setAttribute("aria-pressed", enabled ? "true" : "false");
    btn.classList.toggle("is-active", enabled);
    const stateBadge = btn.querySelector("[data-contrast-state]");
    if (stateBadge) {
      stateBadge.textContent = enabled ? "✓ ON" : "OFF";
    }
  });

  if (announce) {
    const liveRegion = document.getElementById("a11y-contrast-status");
    if (liveRegion) {
      liveRegion.textContent = enabled
        ? liveRegion.dataset.msgOn || "Modo de alto contraste ativado."
        : liveRegion.dataset.msgOff || "Modo de alto contraste desativado.";
    }
  }
}

applyHighContrastState(isHighContrastStored(), false);

document.addEventListener("click", (event) => {
  const toggleBtn = event.target.closest("[data-contrast-toggle]");
  if (toggleBtn) {
    const currentlyEnabled = document.documentElement.getAttribute("data-contrast") === "high";
    applyHighContrastState(!currentlyEnabled, true);
    return;
  }

  const button = event.target.closest(".js-load-translation");
  if (!button) return;
  const form = document.getElementById("translation-editor-form");
  if (!form) return;
  const localeField = form.querySelector('[name="locale"]');
  const nameField = form.querySelector('[name="name"]');
  const descField = form.querySelector('[name="description"]');
  const sustField = form.querySelector('[name="sustainability_info"]');
  if (localeField) localeField.value = button.dataset.locale || "";
  if (nameField) {
    nameField.value = button.dataset.name || "";
    nameField.focus();
  }
  if (descField) descField.value = button.dataset.description || "";
  if (sustField) sustField.value = button.dataset.sustainability || "";
});

document.addEventListener("change", (event) => {
  const select = event.target.closest("[data-auto-submit='true']");
  if (select && select.form) {
    select.form.submit();
  }
});

window.addEventListener("storage", (event) => {
  if (event.key === CONTRAST_STORAGE_KEY) {
    applyHighContrastState(event.newValue === "true", false);
  }
});

document.body.addEventListener("htmx:responseError", (event) => {
  const target = event.detail.target;
  if (!target) return;
  const notice = document.createElement("p");
  notice.className = "empty-note";
  notice.setAttribute("role", "alert");
  notice.textContent = document.body.dataset.requestError || "The list could not be refreshed.";
  target.replaceChildren(notice);
});
