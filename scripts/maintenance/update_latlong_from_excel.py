"""Atualiza coordenadas de clientes na tabela LatLong via hash_client.

Uso:
    python scripts/maintenance/update_latlong_from_excel.py [--arquivo caminho_excel]

Por padrao o script procura o arquivo tests/Clientes.xlsx.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

# Importa app Flask e modelos
sys.path.append(str(Path(__file__).resolve().parents[2]))
from app import create_app  # noqa: E402
from base.models import LatLong, db  # noqa: E402

DEFAULT_EXCEL_PATH = Path(__file__).resolve().parents[2] / "tests" / "Clientes.xlsx"


def carregar_planilha(caminho: Path) -> pd.DataFrame:
    if not caminho.exists():
        raise FileNotFoundError(f"Arquivo nao encontrado: {caminho}")

    df = pd.read_excel(caminho)
    df.columns = [str(col).strip().lower() for col in df.columns]

    # Permite aliases comuns vindos da planilha (ex.: "nome" em vez de "hash_client")
    alias_map = {
        "hash_client": ["hash", "hashcliente", "cliente", "nome", "id", "id_cliente"],
        "latitude": ["lat", "y"],
        "longitude": ["lng", "lon", "long", "x"],
    }

    for alvo, aliases in alias_map.items():
        if alvo in df.columns:
            continue
        for alias in aliases:
            if alias in df.columns:
                df.rename(columns={alias: alvo}, inplace=True)
                break

    campos_obrigatorios = {"hash_client", "latitude", "longitude"}
    ausentes = campos_obrigatorios.difference(df.columns)
    if ausentes:
        raise ValueError(f"Colunas ausentes na planilha: {', '.join(sorted(ausentes))}")

    df = df.dropna(subset=["hash_client", "latitude", "longitude"])
    df = df.drop_duplicates(subset=["hash_client"], keep="last")
    return df


def atualizar_coordenadas(df: pd.DataFrame) -> dict[str, int]:
    estatisticas = {"processados": 0, "atualizados": 0, "nao_encontrados": 0, "erros": 0}

    for registro in df.itertuples(index=False):
        estatisticas["processados"] += 1
        hash_client = str(registro.hash_client).strip()

        try:
            latitude = float(registro.latitude)
            longitude = float(registro.longitude)
        except (TypeError, ValueError):
            estatisticas["erros"] += 1
            continue

        latlong = LatLong.query.filter_by(hash_client=hash_client).first()
        if not latlong:
            estatisticas["nao_encontrados"] += 1
            continue

        latlong.latitude = latitude
        latlong.longitude = longitude
        db.session.add(latlong)
        estatisticas["atualizados"] += 1

    db.session.commit()
    return estatisticas


def main() -> None:
    parser = argparse.ArgumentParser(description="Atualiza lat/long por hash_client")
    parser.add_argument(
        "--arquivo",
        type=Path,
        default=DEFAULT_EXCEL_PATH,
        help="Caminho para o arquivo Excel com as colunas hash_client, latitude, longitude"
    )
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        df = carregar_planilha(args.arquivo)
        estatisticas = atualizar_coordenadas(df)

    print("Resumo da atualizacao:")
    for chave, valor in estatisticas.items():
        print(f"  {chave}: {valor}")


if __name__ == "__main__":
    main()
