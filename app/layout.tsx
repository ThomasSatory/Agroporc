import type { Metadata } from "next";
import "./globals.css";
import { ClientScripts } from "./components/ClientScripts";

export const metadata: Metadata = {
  title: "Plats du Jour",
  description: "Les plats du jour évalués chaque matin",
  icons: {
    icon: "/favicon.png",
    apple: "/apple-touch-icon.png",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="fr" data-theme="normal" suppressHydrationWarning>
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link
          rel="preconnect"
          href="https://fonts.gstatic.com"
          crossOrigin="anonymous"
        />
        <link
          href="https://fonts.googleapis.com/css2?family=Karla:wght@300;400;500;600;700&family=Playfair+Display:wght@400;600;700&display=swap"
          rel="stylesheet"
        />
        <script
          dangerouslySetInnerHTML={{
            __html: `(function(){var t=localStorage.getItem('pdj-theme')||'normal';document.documentElement.setAttribute('data-theme',t)})()`,
          }}
        />
      </head>
      <body>
        <nav className="sticky top-0 z-50 border-b border-[var(--border)] px-3 sm:px-6 backdrop-blur-xl" style={{ background: "var(--nav-bg)" }}>
          <div className="mx-auto flex h-14 max-w-[860px] items-center justify-between">
            <div className="nav-left flex items-center gap-3 sm:gap-8">
              <a href="/" className="flex items-center gap-2 text-lg sm:text-xl font-bold text-[var(--accent)] no-underline tracking-wide shrink-0" style={{ fontFamily: "var(--font-heading)" }}>
                <img src="/logo.jpg" alt="Logo Plats du Jour" className="w-8 h-8 sm:w-9 sm:h-9 rounded-full object-cover" />
                <span className="hidden sm:inline">Plats du Jour</span>
                <span className="sm:hidden">PDJ</span>
              </a>
              <div className="nav-links flex gap-1" id="nav-links">
                <a href="/" className="text-[var(--text-secondary)] no-underline text-xs sm:text-sm font-medium px-2 sm:px-3 py-1.5 rounded-lg transition-colors hover:text-[var(--text)] hover:bg-[var(--surface-hover)]">
                  Aujourd&apos;hui
                </a>
<a href="/idees" className="text-[var(--text-secondary)] no-underline text-xs sm:text-sm font-medium px-2 sm:px-3 py-1.5 rounded-lg transition-colors hover:text-[var(--text)] hover:bg-[var(--surface-hover)]">
                  Idées
                </a>
                <a href="/ia" className="text-[var(--text-secondary)] no-underline text-xs sm:text-sm font-medium px-2 sm:px-3 py-1.5 rounded-lg transition-colors hover:text-[var(--text)] hover:bg-[var(--surface-hover)]">
                  IA
                </a>
              </div>
            </div>
            <button id="cart-btn" className="relative flex items-center justify-center w-9 h-9 rounded-[var(--radius)] border border-[var(--border)] bg-[var(--surface)] text-[var(--text-secondary)] hover:text-[var(--text)] hover:border-[var(--border-accent)] transition-colors" aria-label="Panier">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-4 h-4">
                <path d="M6 2L3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z" />
                <line x1="3" y1="6" x2="21" y2="6" />
                <path d="M16 10a4 4 0 0 1-8 0" />
              </svg>
              <span id="cart-count" style={{ display: "none" }} className="absolute -top-1.5 -right-1.5 flex items-center justify-center w-4 h-4 rounded-full text-[0.6rem] font-bold bg-[var(--accent)] text-[var(--accent-text)]">0</span>
            </button>
            <div className="theme-selector flex items-center gap-1 bg-[var(--surface)] border border-[var(--border)] rounded-full p-[3px]">
              <button
                className="theme-btn flex items-center justify-center gap-1.5 px-3 py-1.5 border-none rounded-full bg-transparent text-[var(--text-muted)] text-xs font-semibold cursor-pointer transition-all min-h-8"
                data-theme="normal"
                aria-label="Thème normal"
              >
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-3.5 h-3.5">
                  <circle cx="12" cy="12" r="5" />
                  <path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42" />
                </svg>
                <span className="label-text hidden sm:inline">Normal</span>
              </button>
              <button
                className="theme-btn flex items-center justify-center gap-1.5 px-3 py-1.5 border-none rounded-full bg-transparent text-[var(--text-muted)] text-xs font-semibold cursor-pointer transition-all min-h-8"
                data-theme="tigre"
                aria-label="Thème tigre"
              >
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" className="w-3.5 h-3.5">
                  <path d="M3 7c3-3 7-4 9-2s1 6-2 9" />
                  <path d="M21 7c-3-3-7-4-9-2s-1 6 2 9" />
                  <circle cx="12" cy="16" r="5" />
                  <path d="M12 11v2" />
                  <circle cx="10" cy="15" r="0.5" fill="currentColor" />
                  <circle cx="14" cy="15" r="0.5" fill="currentColor" />
                </svg>
                <span className="label-text hidden sm:inline">Tigre</span>
              </button>
              <button
                className="theme-btn flex items-center justify-center gap-1.5 px-3 py-1.5 border-none rounded-full bg-transparent text-[var(--text-muted)] text-xs font-semibold cursor-pointer transition-all min-h-8"
                data-theme="terrasse"
                aria-label="Thème terrasse"
              >
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-3.5 h-3.5">
                  <path d="M17 8h1a4 4 0 1 1 0 8h-1" />
                  <path d="M3 8h14v9a4 4 0 0 1-4 4H7a4 4 0 0 1-4-4Z" />
                  <line x1="6" y1="2" x2="6" y2="4" />
                  <line x1="10" y1="2" x2="10" y2="4" />
                  <line x1="14" y1="2" x2="14" y2="4" />
                </svg>
                <span className="label-text hidden sm:inline">Terrasse</span>
              </button>
            </div>
          </div>
        </nav>
        <div className="relative z-[2] mx-auto max-w-[860px] px-3 py-5 sm:px-6 sm:py-10">{children}</div>
        <div className="relative z-[1] text-center text-[var(--text-muted)] text-xs py-8 px-4 border-t border-[var(--border)] mt-8 flex flex-col items-center gap-3">
          <div>Plats du Jour &mdash; Mis à jour automatiquement chaque matin</div>
          <a
            href="https://github.com/ThomasSatory/Agroporc"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-[var(--border)] bg-[var(--surface)] text-[var(--text-secondary)] no-underline text-xs font-medium transition-colors hover:text-[var(--text)] hover:bg-[var(--surface-hover)]"
          >
            <svg viewBox="0 0 24 24" fill="currentColor" className="w-4 h-4" aria-hidden="true">
              <path d="M12 .5C5.73.5.5 5.73.5 12c0 5.08 3.29 9.39 7.86 10.91.58.11.79-.25.79-.56 0-.28-.01-1.02-.02-2-3.2.7-3.88-1.54-3.88-1.54-.52-1.33-1.28-1.69-1.28-1.69-1.05-.72.08-.7.08-.7 1.16.08 1.77 1.19 1.77 1.19 1.03 1.77 2.71 1.26 3.37.96.11-.75.41-1.26.74-1.55-2.55-.29-5.23-1.28-5.23-5.7 0-1.26.45-2.29 1.19-3.1-.12-.29-.52-1.46.11-3.05 0 0 .97-.31 3.18 1.18a11.1 11.1 0 0 1 5.79 0c2.21-1.49 3.18-1.18 3.18-1.18.63 1.59.23 2.76.11 3.05.74.81 1.19 1.84 1.19 3.1 0 4.43-2.69 5.41-5.25 5.69.42.36.79 1.08.79 2.18 0 1.57-.01 2.84-.01 3.23 0 .31.21.68.8.56C20.22 21.38 23.5 17.07 23.5 12 23.5 5.73 18.27.5 12 .5Z" />
            </svg>
            <span>Le projet est open source &mdash; viens contribuer sur GitHub&nbsp;!</span>
          </a>
        </div>
        {/* Cart overlay */}
        <div id="cart-overlay" style={{ display: "none", position: "fixed", inset: 0, background: "rgba(0,0,0,0.5)", zIndex: 100 }} />
        {/* Cart drawer */}
        <div id="cart-drawer" style={{ position: "fixed", top: 0, right: 0, height: "100%", width: "360px", maxWidth: "100%", zIndex: 101, display: "flex", flexDirection: "column", transform: "translateX(100%)", transition: "transform 0.3s ease" }} className="bg-[var(--surface)] border-l border-[var(--border)]">
          <div className="flex items-center justify-between px-5 py-4 border-b border-[var(--border)]">
            <span className="font-bold text-base" style={{ fontFamily: "var(--font-heading)" }}>Mon panier</span>
            <button id="cart-close-btn" className="w-8 h-8 flex items-center justify-center rounded-full border border-[var(--border)] bg-transparent text-[var(--text-muted)] hover:text-[var(--text)] cursor-pointer transition-colors" aria-label="Fermer le panier">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-4 h-4">
                <line x1="18" y1="6" x2="6" y2="18" />
                <line x1="6" y1="6" x2="18" y2="18" />
              </svg>
            </button>
          </div>
          <div id="cart-items" className="flex-1 overflow-y-auto px-5 py-4" />
          <div id="cart-footer" style={{ display: "none" }} className="px-5 py-4 border-t border-[var(--border)]">
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm text-[var(--text-secondary)]">Total estimé</span>
              <span id="cart-total" className="font-bold text-base text-[var(--accent)]">0,00 €</span>
            </div>
            <button id="cart-clear-btn" className="w-full text-xs font-medium py-2 px-4 rounded-[var(--radius)] border border-[var(--border)] bg-transparent text-[var(--text-muted)] hover:text-[var(--bad)] hover:border-[var(--bad)] transition-colors cursor-pointer">
              Vider le panier
            </button>
          </div>
        </div>
        <ClientScripts />
      </body>
    </html>
  );
}
