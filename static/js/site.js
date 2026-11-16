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

document.querySelectorAll("[data-message-dismiss]").forEach((button) => {
  button.addEventListener("click", () => dismissMessage(button.closest(".message")));
});

document.querySelectorAll("[data-auto-dismiss]").forEach((message) => {
  const delay = Number(message.dataset.autoDismiss) || 5000;
  let timer;

  const scheduleDismissal = () => {
    window.clearTimeout(timer);
    if (!message.matches(":hover") && !message.contains(document.activeElement)) {
      timer = window.setTimeout(() => dismissMessage(message), delay);
    }
  };

  message.addEventListener("mouseenter", () => window.clearTimeout(timer));
  message.addEventListener("mouseleave", scheduleDismissal);
  message.addEventListener("focusin", () => window.clearTimeout(timer));
  message.addEventListener("focusout", scheduleDismissal);
  scheduleDismissal();
});

function dismissMessage(message) {
  if (!message || message.classList.contains("message--dismissed")) return;
  message.classList.add("message--dismissed");
  window.setTimeout(() => message.remove(), 200);
}
