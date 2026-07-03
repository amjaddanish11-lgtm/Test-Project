/* ============================================================
   SITE CONFIG — edit these two values and the whole site updates.
   ============================================================ */
const SITE = {
  // Reliable Sources LLC FZ — WhatsApp number, international format, digits only
  whatsapp: "971563659384",
  // Default prefilled message for WhatsApp links that don't set their own
  defaultMessage: "Hi Reliable Sources! I'd like a custom quote for a neon sign. I'll send my logo / idea here.",
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

/* ---------- hero pointer-tracked glow ---------- */
const hero = document.querySelector(".hero");
if (hero && matchMedia("(pointer: fine)").matches) {
  hero.addEventListener("pointermove", (e) => {
    const r = hero.getBoundingClientRect();
    hero.style.setProperty("--mx", ((e.clientX - r.left) / r.width) * 100 + "%");
    hero.style.setProperty("--my", ((e.clientY - r.top) / r.height) * 100 + "%");
  }, { passive: true });
}

/* ============================================================
   Neon Design Studio
   ============================================================ */
(() => {
  const stage = document.getElementById("studioStage");
  if (!stage) return;

  const sign = document.getElementById("studioSign");
  const img = document.getElementById("studioImg");
  const drop = document.getElementById("studioDrop");
  const file = document.getElementById("studioFile");
  const note = document.getElementById("studioNote");
  const cta = document.getElementById("studioCta");

  const GLOWS = [
    { name: "Ice Cyan", rgb: "45,226,255" },
    { name: "Hot Pink", rgb: "255,94,200" },
    { name: "Ultra Violet", rgb: "167,139,250" },
    { name: "Signal Green", rgb: "74,255,128" },
    { name: "Warm White", rgb: "255,236,196" },
    { name: "Sunset Orange", rgb: "255,138,76" },
  ];
  const SIZES = [
    { name: "30 cm", w: "38%" },
    { name: "60 cm", w: "58%" },
    { name: "100 cm", w: "76%" },
    { name: "Custom", w: "58%" },
  ];
  const WALLS = [
    { name: "Studio", cls: "scene-studio" },
    { name: "Brick", cls: "scene-brick" },
  ];

  const state = { glow: GLOWS[0], size: SIZES[1], wall: WALLS[0], art: "none yet" };

  function buildChips(rowId, items, render, onPick, startIndex) {
    const row = document.getElementById(rowId);
    items.forEach((item, i) => {
      const b = document.createElement("button");
      b.type = "button";
      b.className = "chip";
      b.innerHTML = render(item);
      b.setAttribute("aria-pressed", i === startIndex ? "true" : "false");
      b.addEventListener("click", () => {
        row.querySelectorAll(".chip").forEach((c) => c.setAttribute("aria-pressed", "false"));
        b.setAttribute("aria-pressed", "true");
        onPick(item);
        update();
      });
      row.appendChild(b);
    });
  }

  buildChips("glowRow", GLOWS,
    (g) => `<span class="dot" style="--sw:rgb(${g.rgb})"></span>${g.name}`,
    (g) => (state.glow = g), 0);
  buildChips("sizeRow", SIZES, (s) => s.name, (s) => (state.size = s), 1);
  buildChips("wallRow", WALLS, (w) => w.name, (w) => (state.wall = w), 0);

  function update() {
    stage.style.setProperty("--glow-rgb", state.glow.rgb);
    stage.style.setProperty("--signw", state.size.w);
    stage.className = "studio-stage " + state.wall.cls;
    note.textContent = state.size.name === "Custom"
      ? "custom size — tell us on WhatsApp"
      : "approx. " + state.size.name + " wide";
    const msg =
      "Hi Reliable Sources! I designed my sign in your online Design Studio:\n" +
      "• Artwork: " + state.art + "\n" +
      "• Neon glow: " + state.glow.name + "\n" +
      "• Approx. size: " + state.size.name + "\n" +
      "Please send me a mockup and custom quote. I'm attaching my logo/idea image here:";
    cta.href = `https://wa.me/${SITE.whatsapp}?text=${encodeURIComponent(msg)}`;
  }

  function setImage(src, label) {
    img.src = src;
    img.hidden = false;
    drop.hidden = true;
    state.art = label;
    update();
  }

  file.addEventListener("change", () => {
    if (file.files && file.files[0]) {
      setImage(URL.createObjectURL(file.files[0]), "my own logo (attached)");
    }
  });
  document.getElementById("btnUpload").addEventListener("click", () => file.click());
  document.getElementById("btnSample").addEventListener("click", () => {
    setImage("assets/img/sample-logo.svg", "sample logo (I will send mine)");
  });
  // clicking the sign re-opens the picker once an image is loaded
  sign.addEventListener("click", (e) => {
    if (!drop.hidden || e.target.closest(".studio-drop")) return;
    file.click();
  });

  ["dragover", "dragenter"].forEach((ev) =>
    stage.addEventListener(ev, (e) => { e.preventDefault(); stage.classList.add("dragover"); }));
  ["dragleave", "drop"].forEach((ev) =>
    stage.addEventListener(ev, (e) => { e.preventDefault(); stage.classList.remove("dragover"); }));
  stage.addEventListener("drop", (e) => {
    const f = e.dataTransfer.files && e.dataTransfer.files[0];
    if (f && f.type.startsWith("image/")) {
      setImage(URL.createObjectURL(f), "my own logo (attached)");
    }
  });

  cta.target = "_blank";
  cta.rel = "noopener";
  update();
})();
