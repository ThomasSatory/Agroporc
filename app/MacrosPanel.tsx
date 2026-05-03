"use client";

import { useState } from "react";
import type { IngredientDetail } from "@/lib/db";

interface Nutrition {
  calories: number;
  proteines_g: number;
  glucides_g: number;
  lipides_g: number;
}

export default function MacrosPanel({
  nutri,
  ingredients,
  source,
}: {
  nutri?: Nutrition;
  ingredients?: IngredientDetail[];
  source?: "ciqual" | "llm";
}) {
  const [open, setOpen] = useState(false);
  const hasDetail = (ingredients?.length ?? 0) > 0;

  const cells = [
    { value: nutri?.calories ?? "?", label: "kcal" },
    { value: `${nutri?.proteines_g ?? "?"}g`, label: "Protéines" },
    { value: `${nutri?.glucides_g ?? "?"}g`, label: "Glucides" },
    { value: `${nutri?.lipides_g ?? "?"}g`, label: "Lipides" },
  ];

  return (
    <div className="mb-4">
      <button
        type="button"
        onClick={() => hasDetail && setOpen((v) => !v)}
        disabled={!hasDetail}
        aria-expanded={open}
        className={`w-full grid grid-cols-2 sm:grid-cols-4 gap-2 ${
          hasDetail
            ? "cursor-pointer hover:opacity-90 transition-opacity"
            : "cursor-default"
        }`}
        title={hasDetail ? "Voir le détail des ingrédients" : undefined}
      >
        {cells.map((m) => (
          <div
            key={m.label}
            className="text-center py-2.5 px-1 bg-[var(--surface-accent)] rounded-[var(--radius-sm)] border border-[var(--border)]"
          >
            <span className="block font-bold text-base tabular-nums text-[var(--text)]">
              {m.value}
            </span>
            <span className="block text-[0.7rem] text-[var(--text-muted)] uppercase tracking-wider mt-0.5">
              {m.label}
            </span>
          </div>
        ))}
      </button>

      {hasDetail && open && (
        <div className="mt-2 rounded-[var(--radius-sm)] border border-[var(--border)] bg-[var(--surface-accent)] p-3 text-xs animate-[reply-slide-in_0.2s_ease-out]">
          <div className="flex items-center justify-between mb-2">
            <span className="font-semibold text-[var(--text-secondary)] uppercase tracking-wider text-[0.65rem]">
              Composition estimée
            </span>
            <span className="text-[var(--text-muted)] text-[0.65rem]">
              {source === "ciqual" ? "via table Ciqual" : "estimation IA"}
            </span>
          </div>
          <table className="w-full">
            <thead>
              <tr className="text-[var(--text-muted)] text-[0.65rem] uppercase tracking-wider">
                <th className="text-left font-medium pb-1">Ingrédient</th>
                <th className="text-right font-medium pb-1 w-12">g</th>
                <th className="text-right font-medium pb-1 w-14">kcal</th>
                <th className="text-right font-medium pb-1 w-10">P</th>
                <th className="text-right font-medium pb-1 w-10">G</th>
                <th className="text-right font-medium pb-1 w-10">L</th>
              </tr>
            </thead>
            <tbody>
              {ingredients!.map((ing, i) => (
                <tr key={i} className="border-t border-[var(--border)]/50">
                  <td className="py-1 pr-2">
                    <span className="text-[var(--text)]">{ing.nom_query}</span>
                    {ing.matched_nom ? (
                      <span
                        className="block text-[0.65rem] text-[var(--text-muted)] truncate max-w-[14rem]"
                        title={ing.matched_nom}
                      >
                        ↳ {ing.matched_nom}
                      </span>
                    ) : (
                      <span className="block text-[0.65rem] text-[var(--bad,_#c44)] italic">
                        ↳ non trouvé
                      </span>
                    )}
                  </td>
                  <td className="text-right tabular-nums text-[var(--text-secondary)]">{Math.round(ing.grammes)}</td>
                  <td className="text-right tabular-nums text-[var(--text-secondary)]">{Math.round(ing.kcal)}</td>
                  <td className="text-right tabular-nums text-[var(--text-secondary)]">{ing.prot.toFixed(1)}</td>
                  <td className="text-right tabular-nums text-[var(--text-secondary)]">{ing.gluc.toFixed(1)}</td>
                  <td className="text-right tabular-nums text-[var(--text-secondary)]">{ing.lip.toFixed(1)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
