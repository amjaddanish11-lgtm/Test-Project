/* ============================================================
   SITE CONFIG — edit these two values and the whole site updates.
   ============================================================ */
const SITE = {
  // WhatsApp number in international format, digits only (placeholder — replace!)
  whatsapp: "971500000000",
  // Default prefilled message for WhatsApp links that don't set their own
  defaultMessage: "Hi! I'd like a quote for a custom neon sign. I'll send my logo / idea here.",
};

/* ---------- WhatsApp links: build from config ---------- */
document.querySelectorAll("a[data-wa]").forEach((a) => {
  const msg = a.dataset.waMsg || SITE.defaultMessage;
  a.href = `https://wa.me/${SITE.whatsapp}?text=${encodeURIComponent(msg)}`;
  a.target = "_blank";
  a.rel = "noopener";
});

/* ---------- header border on scroll ---------- */
const header = document.querySelector(".site-header");
addEventListener("scroll", () => {
  header.classList.toggle("scrolled", scrollY > 8);
}, { passive: true });

/* ---------- scroll reveal ---------- */
const reveals = document.querySelectorAll(".reveal");
if ("IntersectionObserver" in window) {
  const io = new IntersectionObserver((entries) => {
    entries.forEach((e) => {
      if (e.isIntersecting) {
        e.target.classList.add("in");
        io.unobserve(e.target);
      }
    });
  }, { threshold: 0.12, rootMargin: "0px 0px -40px 0px" });
  reveals.forEach((el) => io.observe(el));
} else {
  reveals.forEach((el) => el.classList.add("in"));
}

/* ---------- footer year ---------- */
document.getElementById("year").textContent = new Date().getFullYear();
