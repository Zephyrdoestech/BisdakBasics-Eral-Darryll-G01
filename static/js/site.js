const autoDismissTimers = new WeakMap();

document.addEventListener("click", (event) => {
  const dismissButton = event.target.closest("[data-message-dismiss]");
  if (dismissButton) {
    dismissMessage(dismissButton.closest(".message"));
    return;
  }

  const toggle = event.target.closest("[data-password-toggle]");
  if (!toggle) return;

  const input = document.getElementById(toggle.dataset.passwordToggle);
  if (!input) return;

  const showing = input.type === "password";
  input.type = showing ? "text" : "password";
  toggle.textContent = showing ? "Hide" : "Show";
  toggle.setAttribute("aria-label", `${showing ? "Hide" : "Show"} ${input.labels?.[0]?.textContent?.toLowerCase() || "password"}`);
});

document.querySelectorAll("[data-auto-dismiss]").forEach((message) => {
  const delay = Number(message.dataset.autoDismiss) || 5000;

  const clearTimer = () => {
    window.clearTimeout(autoDismissTimers.get(message));
    autoDismissTimers.delete(message);
  };

  const scheduleDismissal = () => {
    clearTimer();
    if (!message.matches(":hover") && !message.contains(document.activeElement)) {
      autoDismissTimers.set(message, window.setTimeout(() => dismissMessage(message), delay));
    }
  };

  message.addEventListener("mouseenter", clearTimer);
  message.addEventListener("mouseleave", scheduleDismissal);
  message.addEventListener("focusin", clearTimer);
  message.addEventListener("focusout", scheduleDismissal);
  scheduleDismissal();
});

function dismissMessage(message) {
  if (!message || message.classList.contains("message--dismissed")) return;
  window.clearTimeout(autoDismissTimers.get(message));
  autoDismissTimers.delete(message);
  message.classList.add("message--dismissed");
  window.setTimeout(() => message.remove(), 200);
}
