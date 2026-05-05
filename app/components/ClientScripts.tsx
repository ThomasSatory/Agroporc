"use client";

import { useEffect } from "react";
import { usePathname } from "next/navigation";

export function ClientScripts() {
  const pathname = usePathname();

  useEffect(() => {
    // Theme switching
    const saved = localStorage.getItem("pdj-theme") || "normal";
    document.documentElement.setAttribute("data-theme", saved);

    const themeBtns = document.querySelectorAll<HTMLButtonElement>(".theme-btn");
    themeBtns.forEach((btn) => {
      if (btn.dataset.theme === saved) {
        btn.classList.add("active");
        btn.style.background = "var(--accent)";
        btn.style.color = "var(--accent-text)";
        btn.style.boxShadow = "0 1px 4px rgba(0,0,0,0.2)";
      }
      btn.onclick = () => {
        const theme = btn.dataset.theme!;
        document.documentElement.setAttribute("data-theme", theme);
        localStorage.setItem("pdj-theme", theme);
        themeBtns.forEach((b) => {
          b.classList.remove("active");
          b.style.background = "transparent";
          b.style.color = "var(--text-muted)";
          b.style.boxShadow = "none";
        });
        btn.classList.add("active");
        btn.style.background = "var(--accent)";
        btn.style.color = "var(--accent-text)";
        btn.style.boxShadow = "0 1px 4px rgba(0,0,0,0.2)";
      };
    });

    // Active nav link
    const links = document.querySelectorAll<HTMLAnchorElement>("#nav-links a");
    links.forEach((a) => {
      a.classList.remove("active");
      a.style.color = "";
      a.style.background = "";
      const href = a.getAttribute("href") || "";
      if (
        (href === "/" && pathname === "/") ||
        (href !== "/" && pathname.startsWith(href))
      ) {
        a.classList.add("active");
        a.style.color = "var(--accent)";
        a.style.background = "var(--accent-glow)";
      }
    });

    // Mode switching
    const savedMode = localStorage.getItem("pdj-mode") || "sportif";
    applyMode(savedMode);

    const modeBtns = document.querySelectorAll<HTMLButtonElement>(".mode-btn");
    modeBtns.forEach((btn) => {
      btn.onclick = () => applyMode(btn.dataset.mode!);
    });

    // Day tab switching
    const dayTabs = document.querySelectorAll<HTMLButtonElement>(".day-tab");
    dayTabs.forEach((tab) => {
      tab.onclick = () => {
        const idx = tab.dataset.dayIndex;
        dayTabs.forEach((t) => {
          t.classList.remove("active");
          t.style.background = "transparent";
          t.style.color = "var(--text-muted)";
          t.style.boxShadow = "none";
          const dot = t.querySelector<HTMLElement>(".today-dot");
          if (dot) dot.style.background = "var(--accent)";
        });
        tab.classList.add("active");
        tab.style.background = "var(--accent)";
        tab.style.color = "var(--accent-text)";
        tab.style.boxShadow = "0 1px 4px rgba(0,0,0,0.2)";
        const activeDot = tab.querySelector<HTMLElement>(".today-dot");
        if (activeDot) activeDot.style.background = "var(--accent-text)";
        document.querySelectorAll<HTMLElement>("[data-day-panel]").forEach((panel) => {
          panel.style.display = panel.dataset.dayPanel === idx ? "" : "none";
        });
        const currentMode = localStorage.getItem("pdj-mode") || "sportif";
        applyMode(currentMode);
      };
    });
    initCart();
  }, [pathname]);

  return null;
}

const RESTAURANT_ORDER_URLS: Record<string, string> = {
  "Le Bistrot Trèfle": "https://bistrot-trefle.com/commander-emporter-livraison-gratuite-restaurant-bistrot-trefle-avignon-agroparc/",
  "La Pause Gourmande": "https://lapausegourmandeagroparc.foxorders.com",
  "Le Truck Muche": "https://www.facebook.com/letruckmuche/",
};

type CartItem = { restaurant: string; plat: string; prix: string; qty: number };

function getCart(): CartItem[] {
  try { return JSON.parse(localStorage.getItem("pdj-cart") || "[]"); } catch { return []; }
}

function saveCart(cart: CartItem[]) {
  localStorage.setItem("pdj-cart", JSON.stringify(cart));
}

function parsePrice(prixStr: string): number {
  const match = prixStr.replace(",", ".").match(/[\d.]+/);
  return match ? parseFloat(match[0]) : 0;
}

function formatPrice(cents: number): string {
  return cents.toFixed(2).replace(".", ",") + " €";
}

function escapeAttr(s: string): string {
  return s.replace(/&/g, "&amp;").replace(/"/g, "&quot;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function updateCartUI() {
  const cart = getCart();
  const totalQty = cart.reduce((sum, item) => sum + item.qty, 0);

  const countEl = document.getElementById("cart-count");
  if (countEl) {
    countEl.textContent = String(totalQty);
    countEl.style.display = totalQty > 0 ? "" : "none";
  }

  const itemsEl = document.getElementById("cart-items");
  if (!itemsEl) return;

  if (cart.length === 0) {
    itemsEl.innerHTML = `<p style="color:var(--text-muted);text-align:center;padding:40px 0;font-size:0.875rem">Votre panier est vide</p>`;
    const footerEl = document.getElementById("cart-footer");
    if (footerEl) footerEl.style.display = "none";
    return;
  }

  const grouped: Record<string, CartItem[]> = {};
  for (const item of cart) {
    if (!grouped[item.restaurant]) grouped[item.restaurant] = [];
    grouped[item.restaurant].push(item);
  }

  let html = "";
  for (const [restaurant, items] of Object.entries(grouped)) {
    const restaurantTotal = items.reduce((sum, item) => sum + parsePrice(item.prix) * item.qty, 0);
    const orderUrl = RESTAURANT_ORDER_URLS[restaurant] || "#";
    const isTruck = restaurant === "Le Truck Muche";

    html += `<div style="margin-bottom:24px">
      <div style="font-weight:700;font-size:0.75rem;text-transform:uppercase;letter-spacing:0.08em;color:var(--text-secondary);margin-bottom:8px;padding-bottom:6px;border-bottom:1px solid var(--border)">${escapeAttr(restaurant)}</div>`;

    for (const item of items) {
      html += `<div style="display:flex;justify-content:space-between;align-items:center;padding:8px 0;gap:8px">
        <div style="flex:1;min-width:0">
          <div style="font-size:0.875rem;font-weight:600;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${escapeAttr(item.plat)}</div>
          <div style="font-size:0.75rem;color:var(--accent);font-weight:700;margin-top:2px">${escapeAttr(item.prix)}</div>
        </div>
        <div style="display:flex;align-items:center;gap:8px;flex-shrink:0">
          <button class="cart-qty-btn" data-action="decrease" data-restaurant="${escapeAttr(restaurant)}" data-plat="${escapeAttr(item.plat)}" style="width:26px;height:26px;border-radius:50%;border:1px solid var(--border);background:transparent;cursor:pointer;font-size:1.1rem;line-height:1;display:flex;align-items:center;justify-content:center;color:var(--text)">−</button>
          <span style="font-size:0.875rem;font-weight:700;min-width:18px;text-align:center">${item.qty}</span>
          <button class="cart-qty-btn" data-action="increase" data-restaurant="${escapeAttr(restaurant)}" data-plat="${escapeAttr(item.plat)}" style="width:26px;height:26px;border-radius:50%;border:1px solid var(--border);background:transparent;cursor:pointer;font-size:1.1rem;line-height:1;display:flex;align-items:center;justify-content:center;color:var(--text)">+</button>
        </div>
      </div>`;
    }

    html += `<div style="display:flex;justify-content:space-between;align-items:center;padding-top:10px;margin-top:4px;border-top:1px solid var(--border);gap:8px">
      <span style="font-size:0.8rem;color:var(--text-secondary)">Total&nbsp;: <strong>${formatPrice(restaurantTotal)}</strong></span>
      <a href="${escapeAttr(orderUrl)}" target="_blank" rel="noopener noreferrer" style="display:inline-flex;align-items:center;gap:4px;font-size:0.75rem;font-weight:700;padding:6px 14px;border-radius:var(--radius);background:var(--accent);color:var(--accent-text);text-decoration:none;white-space:nowrap">
        ${isTruck ? "Voir sur Facebook" : "Commander"}
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" width="12" height="12"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>
      </a>
    </div></div>`;
  }

  itemsEl.innerHTML = html;

  const globalTotal = cart.reduce((sum, item) => sum + parsePrice(item.prix) * item.qty, 0);
  const footerEl = document.getElementById("cart-footer");
  if (footerEl) {
    footerEl.style.display = "";
    const totalEl = document.getElementById("cart-total");
    if (totalEl) totalEl.textContent = formatPrice(globalTotal);
  }

  document.querySelectorAll<HTMLButtonElement>(".cart-qty-btn").forEach((btn) => {
    btn.onclick = () => {
      const action = btn.dataset.action!;
      const restaurant = btn.dataset.restaurant!;
      const plat = btn.dataset.plat!;
      const c = getCart();
      const idx = c.findIndex((i) => i.restaurant === restaurant && i.plat === plat);
      if (idx === -1) return;
      if (action === "increase") { c[idx].qty++; } else { c[idx].qty--; if (c[idx].qty <= 0) c.splice(idx, 1); }
      saveCart(c);
      updateCartUI();
    };
  });
}

function initCart() {
  updateCartUI();

  const cartBtn = document.getElementById("cart-btn");
  const cartOverlay = document.getElementById("cart-overlay");
  const cartDrawer = document.getElementById("cart-drawer");
  const cartCloseBtn = document.getElementById("cart-close-btn");
  const cartClearBtn = document.getElementById("cart-clear-btn");

  function openCart() {
    if (cartOverlay) cartOverlay.style.display = "";
    if (cartDrawer) cartDrawer.style.transform = "translateX(0)";
    document.body.style.overflow = "hidden";
  }
  function closeCart() {
    if (cartOverlay) cartOverlay.style.display = "none";
    if (cartDrawer) cartDrawer.style.transform = "translateX(100%)";
    document.body.style.overflow = "";
  }

  if (cartBtn) cartBtn.onclick = openCart;
  if (cartOverlay) cartOverlay.onclick = closeCart;
  if (cartCloseBtn) cartCloseBtn.onclick = closeCart;
  if (cartClearBtn) cartClearBtn.onclick = () => { saveCart([]); updateCartUI(); };

  document.querySelectorAll<HTMLButtonElement>(".add-to-cart-btn").forEach((btn) => {
    btn.onclick = () => {
      const restaurant = btn.dataset.restaurant!;
      const plat = btn.dataset.plat!;
      const prix = btn.dataset.prix!;
      const c = getCart();
      const existing = c.find((i) => i.restaurant === restaurant && i.plat === plat);
      if (existing) { existing.qty++; } else { c.push({ restaurant, plat, prix, qty: 1 }); }
      saveCart(c);
      updateCartUI();

      const originalHTML = btn.innerHTML;
      const originalStyle = { background: btn.style.background, borderColor: btn.style.borderColor, color: btn.style.color };
      btn.textContent = "Ajouté !";
      btn.style.background = "var(--good-bg)";
      btn.style.borderColor = "var(--good-border)";
      btn.style.color = "var(--good)";
      setTimeout(() => {
        btn.innerHTML = originalHTML;
        btn.style.background = originalStyle.background;
        btn.style.borderColor = originalStyle.borderColor;
        btn.style.color = originalStyle.color;
      }, 1200);
    };
  });
}

function applyMode(mode: string) {
  document.querySelectorAll<HTMLElement>(".mode-sportif").forEach((el) => {
    el.style.display = mode === "sportif" ? "" : "none";
  });
  document.querySelectorAll<HTMLElement>(".mode-goulaf").forEach((el) => {
    el.style.display = mode === "goulaf" ? "" : "none";
  });
  document.querySelectorAll<HTMLElement>(".plat-card").forEach((card) => {
    card.classList.remove("recommended");
    if (mode === "sportif" && card.classList.contains("recommended-sportif")) {
      card.classList.add("recommended");
      card.style.borderColor = "var(--good-border)";
    } else if (mode === "goulaf" && card.classList.contains("recommended-goulaf")) {
      card.classList.add("recommended");
      card.style.borderColor = "var(--good-border)";
    } else {
      card.style.borderColor = "";
    }
  });

  // Sort plat cards by note (best first) within each day panel
  document.querySelectorAll<HTMLElement>("[data-day-panel]").forEach((panel) => {
    const cards = Array.from(panel.querySelectorAll<HTMLElement>(".plat-card"));
    if (cards.length < 2) return;
    const noteSelector = mode === "sportif" ? ".note.mode-sportif" : ".note.mode-goulaf";
    cards.sort((a, b) => {
      const noteA = parseFloat(a.querySelector<HTMLElement>(noteSelector)?.dataset.note || "0");
      const noteB = parseFloat(b.querySelector<HTMLElement>(noteSelector)?.dataset.note || "0");
      return noteB - noteA;
    });
    cards.forEach((card) => panel.appendChild(card));
  });
  document.querySelectorAll<HTMLButtonElement>(".mode-btn").forEach((b) => {
    b.classList.remove("active");
    b.style.background = "transparent";
    b.style.color = "var(--text-muted)";
    b.style.boxShadow = "none";
    if (b.dataset.mode === mode) {
      b.classList.add("active");
      b.style.background = "var(--accent)";
      b.style.color = "var(--accent-text)";
      b.style.boxShadow = "0 1px 4px rgba(0,0,0,0.2)";
    }
  });
  localStorage.setItem("pdj-mode", mode);
}
