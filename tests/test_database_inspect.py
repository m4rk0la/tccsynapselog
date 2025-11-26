import os
import sys
import json
import argparse
import sqlite3

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DEFAULT_DB_DIR = os.path.join(ROOT, "databases")
DEFAULT_FILES = ["synapselLog_client_name.db", "synapselLog_latlong.db"]

def inspect_sqlite(path, sample_rows=5):
    if not os.path.isfile(path):
        return {"error": "file not found", "path": path}
    out = {"path": path, "tables": []}
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")
        tables = [r["name"] for r in cur.fetchall()]
        for t in tables:
            tbl = {"name": t, "columns": [], "foreign_keys": [], "indexes": [], "row_count": None, "sample_rows": []}
            # columns
            cur.execute(f"PRAGMA table_info('{t}')")
            cols = cur.fetchall()
            for c in cols:
                tbl["columns"].append({
                    "cid": c["cid"],
                    "name": c["name"],
                    "type": c["type"],
                    "notnull": bool(c["notnull"]),
                    "dflt_value": c["dflt_value"],
                    "pk": bool(c["pk"])
                })
            # foreign keys
            cur.execute(f"PRAGMA foreign_key_list('{t}')")
            fks = cur.fetchall()
            for fk in fks:
                tbl["foreign_keys"].append({k: fk[k] for k in fk.keys()})
            # indexes
            cur.execute(f"PRAGMA index_list('{t}')")
            idxs = cur.fetchall()
            for idx in idxs:
                idx_dict = {k: idx[k] for k in idx.keys()}
                name = idx_dict.get("name")
                if name:
                    cur.execute(f"PRAGMA index_info('{name}')")
                    idx_info = [dict(r) for r in cur.fetchall()]
                    idx_dict["columns"] = idx_info
                tbl["indexes"].append(idx_dict)
            # row count
            try:
                cur.execute(f"SELECT COUNT(1) AS c FROM '{t}'")
                tbl["row_count"] = cur.fetchone()["c"]
            except Exception:
                tbl["row_count"] = None
            # sample rows
            try:
                cur.execute(f"SELECT * FROM '{t}' LIMIT ?", (sample_rows,))
                rows = cur.fetchall()
                for r in rows:
                    tbl["sample_rows"].append({k: r[k] for k in r.keys()})
            except Exception:
                tbl["sample_rows"] = ["<could not fetch sample rows>"]
            out["tables"].append(tbl)
    finally:
        conn.close()
    return out

def main():
    p = argparse.ArgumentParser(description="Inspeciona bancos synapseLog na pasta databases")
    p.add_argument("--dir", "-d", default=DEFAULT_DB_DIR, help="pasta onde estão os .db")
    p.add_argument("--files", "-f", nargs="*", default=DEFAULT_FILES, help="nomes dos arquivos .db")
    p.add_argument("--sample", "-s", type=int, default=5, help="número de linhas de amostra por tabela")
    p.add_argument("--out", "-o", help="salvar resultado em arquivo JSON")
    args = p.parse_args()

    db_dir = os.path.abspath(args.dir)
    results = {"db_dir": db_dir, "databases": []}
    for fname in args.files:
        path = os.path.join(db_dir, fname)
        results["databases"].append(inspect_sqlite(path, sample_rows=args.sample))

    txt = json.dumps(results, indent=2, ensure_ascii=False)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(txt)
        print(f"Resumo salvo em {args.out}")
    else:
        print(txt)

if __name__ == "__main__":
    main()