"""
Estrazione e pulizia del dataset gold dal MIT AI Risk Repository v4.

Sorgente: files/data/mit_ai_risk_repository_v4.xlsx, foglio "AI Risk Database v4".
Ogni riga del foglio è un rischio estratto dai paper, con descrizione + etichette
esperte secondo le DUE tassonomie usate dal progetto:
  - Domain Taxonomy : Domain (1-7) + Sub-domain (es. "6.5 > Governance failure")
  - Causal Taxonomy : Entity / Intent / Timing

Lo script produce un dataset pulito e normalizzato sullo schema del progetto
([utils/models.py]) e due dataset task-specifici (classificazione dominio e
classificazione causale), con split deterministico train/eval. È pensato come base
comune sia per il RAG sia per il fine-tuning (vedi PIANO_RAG_FINETUNING.md).

NOTA: questo script NON è ancora stato eseguito. Vedi la sezione "Esecuzione" nel
file PIANO_RAG_FINETUNING.md per requisiti e comando.

Uso:
    python data_prep/extract_dataset.py \
        --xlsx files/data/mit_ai_risk_repository_v4.xlsx \
        --out-dir files/data/processed \
        --eval-frac 0.1
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

# Dipendenza non in requirements.txt del runtime: installare in ambiente di data-prep.
# (vedi PIANO_RAG_FINETUNING.md → "Requisiti")
import openpyxl


SHEET_NAME = "AI Risk Database v4"
HEADER_ROW = 3  # intestazioni reali nel foglio (righe 1-2 sono metadati/merge)

# ----------------------------------------------------------------------------
# Mappature dai valori MIT verso i Literal dello schema del progetto
# (coerenti con utils/models.py e agents/heuristic_analyzer/...).
# Il valore None significa "scartare la riga per quel task".
# ----------------------------------------------------------------------------
ENTITY_MAP = {
    "1 - Human": "human",
    "2 - AI": "ai",
    "3 - Other": "other",
    "4 - Not coded": None,
}
INTENT_MAP = {
    "1 - Intentional": "intentional",
    "2 - Unintentional": "unintentional",
    "3 - Other": "other",
    "4 - Not coded": None,
}
TIMING_MAP = {
    "1 - Pre-deployment": "pre-deployment",
    "2 - Post-deployment": "post-deployment",
    "3 - Other": "other",
    "4 - Not coded": None,
}

# Solo i livelli che rappresentano unità classificabili (no "Additional evidence"/"Paper").
CLASSIFIABLE_LEVELS = {"Risk Category", "Risk Sub-Category"}


def _norm(v: Any) -> Optional[str]:
    """Normalizza una cella in stringa pulita o None."""
    if v is None:
        return None
    s = str(v).strip()
    return s or None


def _parse_domain(raw: Optional[str]) -> Optional[Dict[str, str]]:
    """
    '6. Socioeconomic and Environmental' -> {'id': '6', 'name': 'Socioeconomic and Environmental'}
    """
    if not raw:
        return None
    m = re.match(r"^\s*(\d+)\s*\.\s*(.+?)\s*$", raw)
    if not m:
        return None
    return {"id": m.group(1), "name": m.group(2)}


def _parse_subdomain(raw: Optional[str]) -> Optional[Dict[str, str]]:
    """
    '6.5 > Governance failure' -> {'id': '6.5', 'name': 'Governance failure'}
    """
    if not raw:
        return None
    m = re.match(r"^\s*(\d+\.\d+)\s*>\s*(.+?)\s*$", raw)
    if not m:
        # talvolta solo l'id senza nome
        m2 = re.match(r"^\s*(\d+\.\d+)\s*$", raw)
        if m2:
            return {"id": m2.group(1), "name": ""}
        return None
    return {"id": m.group(1), "name": m.group(2)}


def _split_bucket(key: str, eval_frac: float) -> str:
    """
    Split deterministico e riproducibile basato su hash della chiave:
    nessuna casualità -> stessi esempi sempre nello stesso bucket.
    """
    h = int(hashlib.sha1(key.encode("utf-8")).hexdigest(), 16)
    return "eval" if (h % 1000) < int(eval_frac * 1000) else "train"


def load_rows(xlsx_path: Path) -> List[Dict[str, Any]]:
    """Carica le righe del foglio mappando per nome di colonna (header alla riga HEADER_ROW)."""
    wb = openpyxl.load_workbook(str(xlsx_path), data_only=True, read_only=True)
    ws = wb[SHEET_NAME]

    rows = list(ws.iter_rows(values_only=True))
    header = [(_norm(c) or "") for c in rows[HEADER_ROW - 1]]
    idx = {name: i for i, name in enumerate(header)}

    def cell(row, name):
        i = idx.get(name)
        return _norm(row[i]) if i is not None and i < len(row) else None

    records = []
    for row in rows[HEADER_ROW:]:
        records.append(
            {
                "ev_id": cell(row, "Ev_ID"),
                "paper_id": cell(row, "Paper_ID"),
                "title": cell(row, "Title"),
                "level": cell(row, "Category level"),
                "risk_category": cell(row, "Risk category"),
                "risk_subcategory": cell(row, "Risk subcategory"),
                "description": cell(row, "Description"),
                "domain_raw": cell(row, "Domain"),
                "subdomain_raw": cell(row, "Sub-domain"),
                "entity_raw": cell(row, "Entity"),
                "intent_raw": cell(row, "Intent"),
                "timing_raw": cell(row, "Timing"),
            }
        )
    return records


def clean(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Filtra unità non classificabili e normalizza le etichette sullo schema del progetto."""
    out = []
    for r in records:
        if r["level"] not in CLASSIFIABLE_LEVELS:
            continue
        if not r["description"]:
            continue

        domain = _parse_domain(r["domain_raw"])
        subdomain = _parse_subdomain(r["subdomain_raw"])
        entity = ENTITY_MAP.get(r["entity_raw"]) if r["entity_raw"] else None
        intent = INTENT_MAP.get(r["intent_raw"]) if r["intent_raw"] else None
        timing = TIMING_MAP.get(r["timing_raw"]) if r["timing_raw"] else None

        out.append(
            {
                "ev_id": r["ev_id"],
                "paper_id": r["paper_id"],
                "source_title": r["title"],
                "risk_category": r["risk_category"],
                "risk_subcategory": r["risk_subcategory"],
                "description": r["description"],
                # domain taxonomy
                "domain_id": domain["id"] if domain else None,
                "domain_name": domain["name"] if domain else None,
                "subdomain_id": subdomain["id"] if subdomain else None,
                "subdomain_name": subdomain["name"] if subdomain else None,
                # causal taxonomy (None = non codificato per quell'asse)
                "entity": entity,
                "intent": intent,
                "timing": timing,
            }
        )
    return out


def write_jsonl(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def build_outputs(rows: List[Dict[str, Any]], out_dir: Path, eval_frac: float) -> Dict[str, int]:
    """
    Produce:
      - full.jsonl                  : tutte le righe pulite (base per il RAG)
      - domain_clf.{train,eval}.jsonl : description -> {domain_id/name, subdomain_id/name}
      - causal_clf.{train,eval}.jsonl : description -> {entity, intent, timing}
    Split deterministico per ev_id (fallback: description).
    """
    stats: Dict[str, int] = {}

    write_jsonl(out_dir / "full.jsonl", rows)
    stats["full"] = len(rows)

    # Task 1 - classificazione dominio (richiede almeno domain_id)
    domain_rows = [r for r in rows if r["domain_id"]]
    # Task 2 - classificazione causale (richiede tutti e tre gli assi codificati)
    causal_rows = [r for r in rows if r["entity"] and r["intent"] and r["timing"]]

    for name, subset, fields in [
        ("domain_clf", domain_rows, ["domain_id", "domain_name", "subdomain_id", "subdomain_name"]),
        ("causal_clf", causal_rows, ["entity", "intent", "timing"]),
    ]:
        train, ev = [], []
        for r in subset:
            key = r["ev_id"] or r["description"][:120]
            example = {
                "input": r["description"],
                "labels": {k: r[k] for k in fields},
                "meta": {"ev_id": r["ev_id"], "paper_id": r["paper_id"]},
            }
            (ev if _split_bucket(key, eval_frac) == "eval" else train).append(example)
        write_jsonl(out_dir / f"{name}.train.jsonl", train)
        write_jsonl(out_dir / f"{name}.eval.jsonl", ev)
        stats[f"{name}.train"] = len(train)
        stats[f"{name}.eval"] = len(ev)

    return stats


def main() -> None:
    parser = argparse.ArgumentParser(description="Estrae il dataset gold dal MIT AI Risk Repository v4.")
    parser.add_argument(
        "--xlsx",
        default="files/data/mit_ai_risk_repository_v4.xlsx",
        help="Percorso del file .xlsx sorgente.",
    )
    parser.add_argument(
        "--out-dir",
        default="files/data/processed",
        help="Cartella di output per i .jsonl.",
    )
    parser.add_argument(
        "--eval-frac",
        type=float,
        default=0.1,
        help="Frazione hold-out per l'eval (default 0.1).",
    )
    args = parser.parse_args()

    xlsx_path = Path(args.xlsx)
    out_dir = Path(args.out_dir)

    records = load_rows(xlsx_path)
    rows = clean(records)
    stats = build_outputs(rows, out_dir, args.eval_frac)

    print("Dataset estratto in:", out_dir)
    for k, v in stats.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
