document.body.addEventListener("htmx:responseError", (event) => {
  const target = event.detail.target;
  if (!target) return;
  const notice = document.createElement("p");
  notice.className = "empty-note";
  notice.setAttribute("role", "alert");
  notice.textContent = document.body.dataset.requestError || "The list could not be refreshed.";
  target.replaceChildren(notice);
});

document.addEventListener("click", (event) => {
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
