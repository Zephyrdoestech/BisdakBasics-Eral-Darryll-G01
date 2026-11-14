document.addEventListener("click", (event) => {
  const toggle = event.target.closest("[data-password-toggle]");
  if (!toggle) return;

  const input = document.getElementById(toggle.dataset.passwordToggle);
  if (!input) return;

  const showing = input.type === "password";
  input.type = showing ? "text" : "password";
  toggle.textContent = showing ? "Hide" : "Show";
  toggle.setAttribute("aria-label", `${showing ? "Hide" : "Show"} ${input.labels?.[0]?.textContent?.toLowerCase() || "password"}`);
});
