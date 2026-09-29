import pandas as pd
import spacy 
import re

import logging
import json
import os
from openai import OpenAI

log = logging.getLogger(__name__)

# ================== #
# Abstract Filtering #
# ================== #

class Filtering(): 
    def __init__(self, corpus, patterns, keywords, window=1):
        self.corpus = corpus
        self.patterns = patterns
        self.keywords = keywords
        assert window >= 0 and isinstance(window, int), "Window deve ser um inteiro não negativo."
        self.window = window
        self.nlp = spacy.load("en_core_web_sm")
        self.filtered_corpus = []
        
    
    def _tokenize_split(self, text): 
        """Recebe um texto e retorna uma lista com os seus períodos."""
    
        doc = self.nlp(text)
        periods = [period.text.strip() for period in doc.sents]
        
        return periods 
        

    def _select_periods(self, periods):
        """
        Recebe uma lista de períodos, uma lista de padrões em REGEX e uma lista de palavras chave.
        Retorna uma lista com os índices dos períodos que possuem expressões da lista de padrões ou palavras chave.
        """
 
        
        relevant_indices = []
    
        for i, period in enumerate(periods): 
    
            lower_period = period.lower()
    
            # Avalia se houve um match entre padrões de REGEX e alguma palavra do periodo
            # retorna True se houver ao menos um match no periodo
            regex_match = any(
                re.search(pattern, period, re.IGNORECASE)
                for pattern in self.patterns 
            )
            
            # Avalia se houve um match entre padrões de REGEX e alguma palavra do periodo
            # retorna True se houver ao menos um match no periodo
            keyword_match = any(
                keyword.lower() in lower_period
                for keyword in self.keywords
            )
    
            # Adiciona o índice do período à lista de períodos relevantes
            if regex_match or keyword_match:
                relevant_indices.append(i)
    
        return relevant_indices 


    def _add_context(self, periods, relevant_indices):
        """
        Recebe uma lista de períodos, uma lista de índices e um inteiro referente ao número de períodos de contexto.
        Retorna um conjunto de índices referente aos períodos relevantes e suas janelas de contexto.
        """
    
        if self.window == 0: 
            return sorted(set(relevant_indices))
            
        selected_indices = set()    
    
        for index in relevant_indices:
            start = max(0, index - self.window)
            end = min(len(periods), index + self.window + 1)
    
            for i in range(start, end):
                selected_indices.add(i)

    
        return sorted(selected_indices)

    
    def _join_periods(self, periods): 
        """Une as senteças em um único texto."""

        return " ".join(periods)


    def filter(self):
        """Realiza o processo de filtragem do abstract.
 
        Retorna filtered_corpus com o mesmo tamanho e mesma ordem de
        self.corpus (um texto filtrado por documento, podendo ser uma
        string vazia se nada relevante foi encontrado) — isso é
        importante para manter o alinhamento com os doc_ids na etapa
        de extração.
        """

        for doc in self.corpus:
            periods = self._tokenize_split(doc)
            relevant_indices = self._select_periods(periods)
            selected_indices = self._add_context(periods, relevant_indices)
            filtered_text = self._join_periods([periods[i] for i in selected_indices])
            self.filtered_corpus.append(filtered_text)

        return self.filtered_corpus
    

# ==================== #
# LLM Based Extraction #
# ==================== #

class Extracting():
    def __init__(
        self,
        base_url,
        model,
        corpus,
        system,
        schema,
        doc_ids=None,
        api_archive="api_key.txt",
        checkpoint_path="checkpoint.jsonl",
    ):
        with open(api_archive, "r") as file:
            api_key = file.read().strip()

        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url,
	    
        )

        self.corpus = corpus

        # Cada documento precisa de um identificador único e estável para
        # que o checkpoint saiba o que já foi processado. Se não vier um,
        # usamos o índice na lista como id.
        self.doc_ids = doc_ids if doc_ids is not None else list(range(len(corpus)))
        assert len(self.doc_ids) == len(self.corpus), \
            "doc_ids deve ter o mesmo tamanho do corpus."

        self.system = system
        self.schema = schema
        self.model = model
        self.checkpoint_path = checkpoint_path

        self.extracted_rows = []
        self.failed_ids = []
        self.processed_ids = set()

        self._load_checkpoint()

    
    def _load_checkpoint(self):
        """Carrega o progresso salvo em checkpoint_path, se existir, e
        popula processed_ids/extracted_rows para retomar de onde parou."""

        if not os.path.exists(self.checkpoint_path):
            return

        with open(self.checkpoint_path, "r", encoding="utf-8") as file:
            for line in file:
                line = line.strip()
                if not line:
                    continue
                record = json.loads(line)
                self.processed_ids.add(record["doc_id"])
                self.extracted_rows.extend(record["rows"])

        if self.processed_ids:
            log.info(f"{len(self.processed_ids)} documentos já processados encontrados em '{self.checkpoint_path}', retomando...")

    
    def _save_checkpoint(self, doc_id, rows):
        """Acrescenta (append) o resultado de UM documento ao arquivo de
        checkpoint. Cada linha é um JSON independente (formato JSONL), então
        uma escrita não corrompe as anteriores mesmo se o processo cair."""

        record = {"doc_id": doc_id, "rows": rows}
        with open(self.checkpoint_path, "a", encoding="utf-8") as file:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")


    def _create_user_prompt(self, doc):
        """Recebe um abstract e retorna um prompt para ser processado por uma LLM."""

        return f"""
            Extract the experimental information from the following
            scientific text.

            TEXT:

            {doc}
            """

        
    def _extract_with_llm(self, doc):

        response = self.client.responses.parse(
            model=self.model,
            instructions=self.system,
            input=self._create_user_prompt(doc),
            text_format=self.schema,
  	    temperature=0.5
        )

        return response.output_parsed

        
    def _values_or_none(self, field):
        """Converte uma lista de Enum em lista de strings, preservando None."""
        return [item.value for item in field] if field else None
    
    
    def _result_to_rows(self, doc_id, result):
    
        rows = []
    
        for experiment_id, experiment in enumerate(result.experiments, start=1):
            row = {
                "doc_id": doc_id,
                "experiment_id": experiment_id,
                "synthesis_methods": self._values_or_none(experiment.synthesis_methods),
                "synthesis_direction": self._values_or_none(experiment.synthesis_direction),
                "post_synthesis_modifications": self._values_or_none(experiment.post_synthesis_modifications),
                "synthesis_engineering": self._values_or_none(experiment.synthesis_engineering),
                "num_sheets": self._values_or_none(experiment.num_sheets),
                "structure_format": self._values_or_none(experiment.structure_format),
                "specific_applications": self._values_or_none(experiment.specific_applications),
                "general_applications": self._values_or_none(experiment.general_applications),
            }
            rows.append(row)
    
        return rows
        

    def extract(self):
        """Executa a extração no corpus inteiro, pulando documentos já
        processados (presentes no checkpoint) e salvando o progresso a
        cada documento processado com sucesso. Se um documento falhar
        (erro de API, parsing, etc.), o erro é registrado e o loop
        continua para o próximo documento em vez de travar tudo."""

        total = len(self.corpus)

        for position, (doc_id, doc) in enumerate(zip(self.doc_ids, self.corpus), start=1):

            if doc_id in self.processed_ids:
                continue

            try:
                result = self._extract_with_llm(doc)
                rows = self._result_to_rows(doc_id, result)

            except Exception as error:
                log.error(f"doc_id={doc_id} ({position}/{total}): {error}")
                self.failed_ids.append(doc_id)
                continue

            self.extracted_rows.extend(rows)
            self.processed_ids.add(doc_id)
            self._save_checkpoint(doc_id, rows)

            log.info(f"doc_id={doc_id} ({position}/{total}) — {len(rows)} experimento(s) extraído(s)")

        if self.failed_ids:
            log.warning(f"{len(self.failed_ids)} documento(s) falharam: {self.failed_ids}")

        return pd.DataFrame(self.extracted_rows)

    
    def retry_failed(self):
        """Tenta reprocessar apenas os documentos que falharam na última
        chamada a extract(). Útil para rodar de novo só os erros, sem
        repetir o corpus inteiro."""

        if not self.failed_ids:
            print("[info] nenhum documento com falha para reprocessar.")
            return self.extracted_rows

        retry_ids = list(self.failed_ids)
        retry_corpus = [
            doc for doc_id, doc in zip(self.doc_ids, self.corpus)
            if doc_id in retry_ids
        ]

        self.failed_ids = []
        self.doc_ids, self.corpus = retry_ids, retry_corpus

        return self.extract()
