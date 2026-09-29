from DataExtractionFunctions import Extracting 
from schema import ExperimentSchema
from prompts import SYSTEM_PROMPT
import pandas as pd
import json
from typing import Optional
from pydantic import BaseModel
import argparse
import logging
import sys
from pathlib import Path

# =============== #
# Data extraction #
# =============== #

"""
DataExtraction.py

Etapa de extração de dados via LLM a partir dos abstracts já filtrados
(saída de filter_abstracts.py). Roda a extração com checkpoint/resume,
salva o dataset final e um relatório dos documentos que falharam.

Pensado para rodar em HPC como job não-interativo:
    python extract_data.py --input filtered_abstracts.csv
"""

# --- Defining Initial Paramaters --- 

def parse_args():
    parser = argparse.ArgumentParser(description="Extração de dados de síntese de MoS2 via LLM.")
    parser.add_argument("--input", type=Path, required=True, help="CSV com abstracts filtrados.")
    parser.add_argument("--text-column", type=str, default="Filtered Abstracts")
    parser.add_argument("--id-column", type=str, default="Autor")
    parser.add_argument("--output", type=Path, default=Path("mos2_dataset.xlsx"))
    parser.add_argument("--failed-output", type=Path, default=Path("failed_docs.xlsx"))
    parser.add_argument("--checkpoint", type=Path, default=Path("checkpoint.jsonl"))
    parser.add_argument("--log-file", type=Path, default=Path("extract.log"))
    parser.add_argument("--base-url", type=str, default="https://iluma.cnpem.br:4000/v1")
    parser.add_argument("--model", type=str, default="iluma")
    parser.add_argument("--api-key-file", type=Path, default=Path("api_key.txt"))
    parser.add_argument(
        "--max-retries", type=int, default=1,
        help="Quantas vezes tentar reprocessar falhas automaticamente ao final."
    )
    return parser.parse_args()

# --- Starting the Log ---

def setup_logging(log_file):
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )

def main():
    args = parse_args()
    setup_logging(args.log_file)
    log = logging.getLogger(__name__)

# --- Retrieving the Data ---
    
    log.info(f"Carregando abstracts filtrados de '{args.input}'")
    
    data = pd.read_csv(args.input)

    if args.text_column not in data.columns:
        log.error(f"Coluna de texto '{args.text_column}' não encontrada em {list(data.columns)}")
        sys.exit(1)

# --- Extracting the Data --- 
    
    extractor = Extracting(
        base_url=args.base_url,
        model=args.model,
        corpus=data[args.text_column],
        system=SYSTEM_PROMPT,
        schema=ExperimentSchema,
        doc_ids=data[args.id_column],
        api_archive=str(args.api_key_file),
        checkpoint_path=str(args.checkpoint),
    )

    log.info(f"Iniciando extração de {len(data)} documentos...")
    df = extractor.extract()

# --- Retrying in Case of Error ---
    
    attempt = 0
    while extractor.failed_ids and attempt < args.max_retries:
        attempt += 1
        log.warning(
            f"Tentativa {attempt}/{args.max_retries} de reprocessar "
            f"{len(extractor.failed_ids)} falha(s)..."
        )
        df = extractor.retry_failed()

# --- Saving Extracted Data ---
    
    df.to_csv(args.output, index=False, encoding="utf-8-sig")
    log.info(f"Dataset salvo em '{args.output}' ({len(df)} linhas).")

# --- Saving Failed Data ---    
    
    if extractor.failed_ids:
        failed_mask = data[args.id_column].isin(extractor.failed_ids)
        failed_df = data.loc[failed_mask]
        failed_df.to_csv(args.failed_output, index=False, encoding="utf-8-sig")
        log.warning(
            f"{len(extractor.failed_ids)} documento(s) continuam falhando após "
            f"{args.max_retries} tentativa(s) de retry. "
            f"Detalhes salvos em '{args.failed_output}'."
        )
    else:
        log.info("Nenhuma falha restante.")

if __name__ == "__main__":
    main()