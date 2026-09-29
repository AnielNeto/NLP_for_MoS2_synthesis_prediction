import argparse
import json
import logging
import sys
from pathlib import Path
import pandas as pd
from DataExtractionFunctions import Filtering 
from patterns import PATTERNS, KEYWORDS

log = logging.getLogger(__name__)

# ============== #
# Data filtering #
# ============== #

"""
filter_abstracts.py

Etapa de filtragem: lê um conjunto de planilhas com abstracts brutos,
combina tudo num único dataset, roda a filtragem por REGEX/palavras-chave
(spaCy) e salva o resultado filtrado — pronto para ser consumido por
extract_data.py.

Uso:
    python filter_abstracts.py --input-dir dados_brutos/ --raw-text-column Abstract
"""

# --- Defining Initial Paramaters --- 

def parse_args():
    parser = argparse.ArgumentParser(description="Filtragem de abstracts brutos sobre síntese de MoS2.")
    parser.add_argument("--input-dir", type=Path, required=True, help="Pasta com as planilhas brutas.")
    parser.add_argument("--glob", type=str, default="*.xlsx", help="Padrão dos arquivos a buscar (ex: '*.csv', '*.xlsx').")
    parser.add_argument("--raw-text-column", type=str, default="Abstract", help="Coluna com o texto bruto do abstract.")
    parser.add_argument("--id-column", type=str, default="Autor", help="Coluna usada como identificador único do documento.")
    parser.add_argument("--filtered-column", type=str, default="Filtered Abstracts", help="Nome da coluna de saída com o texto filtrado.")
    parser.add_argument("--window", type=int, default=1)
    parser.add_argument("--output", type=Path, default=Path("filtered_abstracts.csv"))
    parser.add_argument("--log-file", type=Path, default=Path("filter.log"))
    return parser.parse_args()

# --- Starting the Log ---

def setup_logging(log_file):
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )

# --- Retrieving the Data ---

def load_spreadsheets(input_dir, glob_pattern):
    """Lê todas as planilhas que casam com glob_pattern em input_dir e
    devolve um único DataFrame concatenado. Suporta .csv, .xlsx e .xls.
    Registra o arquivo de origem em cada linha, para rastreabilidade."""

    files = sorted(input_dir.glob(glob_pattern))
    if not files:
        log.error(f"Nenhum arquivo encontrado em '{input_dir}' com o padrão '{glob_pattern}'")
        sys.exit(1)

    frames = []
    for file in files:
        try:
            if file.suffix.lower() == ".csv":
                df = pd.read_csv(file)
            elif file.suffix.lower() in (".xlsx", ".xls"):
                df = pd.read_excel(file)
            else:
                log.warning(f"Formato não suportado, pulando: '{file}'")
                continue
        except Exception as error:
            log.error(f"Falha ao ler '{file}': {error}")
            continue

        df["source_file"] = file.name
        frames.append(df)
        log.info(f"Carregado '{file}' ({len(df)} linhas)")

    if not frames:
        log.error("Nenhuma planilha pôde ser lida com sucesso.")
        sys.exit(1)

    combined = pd.concat(frames, ignore_index=True)
    log.info(f"Total combinado: {len(combined)} linhas de {len(frames)} arquivo(s)")
    return combined


def main():
    args = parse_args()
    setup_logging(args.log_file)

# --- Accessing Data ---

    log.info(f"Carregando planilhas de '{args.input_dir}' (padrão: '{args.glob}')")
    data = load_spreadsheets(args.input_dir, args.glob)

    if args.raw_text_column not in data.columns:
        log.error(f"Coluna de texto '{args.raw_text_column}' não encontrada em {list(data.columns)}")
        sys.exit(1)
    if args.id_column not in data.columns:
        log.error(f"Coluna de id '{args.id_column}' não encontrada em {list(data.columns)}")
        sys.exit(1)

    before = len(data)
    data = data.dropna(subset=[args.raw_text_column]).reset_index(drop=True)
    dropped = before - len(data)
    if dropped:
        log.warning(f"{dropped} linha(s) sem texto em '{args.raw_text_column}' foram descartadas.")

    duplicated = data[args.id_column].duplicated().sum()
    if duplicated:
        log.warning(
            f"{duplicated} valor(es) duplicado(s) em '{args.id_column}'. "
            f"Isso pode causar ambiguidade no checkpoint da etapa de extração."
        )
    
    log.info(f"{len(PATTERNS)} padrão(ões) REGEX e {len(KEYWORDS)} palavra(s)-chave carregados.")

# --- Filtering Data ---
    
    filterer = Filtering(
        corpus=data[args.raw_text_column],
        patterns=PATTERNS,
        keywords=KEYWORDS,
        window=args.window,
    )

    log.info(f"Filtrando {len(data)} abstracts (window={args.window})...")
    data[args.filtered_column] = filterer.filter()

    empty_after_filter = (data[args.filtered_column].str.strip() == "").sum()
    if empty_after_filter:
        log.warning(
            f"{empty_after_filter} documento(s) ficaram com texto filtrado vazio "
            f"(nenhum padrão/palavra-chave encontrado)."
        )

# --- Saving Data ---
    
    data.to_csv(args.output, index=False, encoding="utf-8-sig")
    log.info(f"Dataset filtrado salvo em '{args.output}' ({len(data)} linhas).")


if __name__ == "__main__":
    main()
