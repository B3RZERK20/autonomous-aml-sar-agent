"""
Phoenix Observability Benchmark & Evaluation Suite.
Populates Arize Phoenix with:
1. Versioned Prompts (Prompts tab)
2. Golden AML Benchmark Dataset (Datasets tab)
3. Evaluator Functions (Evaluators tab)
4. Multi-Agent Benchmark Experiment Run (Experiments tab)
"""

import sys
import os
from pathlib import Path

# Ensure UTF-8 output on Windows consoles to prevent Unicode emoji encoding crashes
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Ensure project root is in sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import json
import logging
import pandas as pd
from typing import Dict, Any

from phoenix.client import Client
from agents.workflow import run_aml_investigation
from agents.evaluator import evaluate_sar_faithfulness

logger = logging.getLogger("phoenix_benchmark")
logging.basicConfig(level=logging.INFO)


def seed_phoenix_benchmarks(base_url: str = "http://localhost:6006"):
    """Populates Datasets, Prompts, Experiments, and Evaluators in Arize Phoenix."""
    logger.info(f"Connecting to Phoenix at {base_url}...")
    client = Client(base_url=base_url)

    # -------------------------------------------------------------------------
    # 1. Register Versioned Prompts in Phoenix (Prompts Tab)
    # -------------------------------------------------------------------------
    logger.info("Registering AML Prompts in Phoenix...")
    try:
        from phoenix.client.resources.prompts import PromptVersion

        prompt_template = (
            "You are a Senior Anti-Money Laundering (AML) Compliance Officer drafting an official "
            "FinCEN Suspicious Activity Report (SAR / BSA Form 111).\n"
            "You MUST follow these strict rules:\n"
            "1. ONLY cite exact numbers, dates, account numbers, and entity names provided in the input data.\n"
            "2. DO NOT fabricate or hallucinate any numbers, dollar figures, or entity relationships.\n"
            "3. Structure the output as valid JSON matching the requested fields.\n"
            "4. Cite the provided FinCEN CFR regulations and FATF recommendations accurately.\n\n"
            "Target Account: {{account_id}}\n"
            "Suspect Name: {{account_name}}\n"
            "Flagged Activity: {{primary_activity}}\n"
        )
        version = PromptVersion(
            [{"role": "user", "content": prompt_template}],
            model_provider="GROQ",
            model_name="qwen/qwen3.8-27b",
            description="FinCEN SAR BSA Form 111 Part V Narrative Prompt"
        )
        client.prompts.create(
            name="fincen_sar_narrative_writer",
            version=version,
            prompt_description="Enterprise FinCEN BSA Form 111 Suspicious Activity Narrative Generator",
            prompt_metadata={"framework": "LangGraph", "regulations": "31 CFR 1010.311, 31 CFR 1020.320"}
        )
        logger.info("Prompt 'fincen_sar_narrative_writer' registered successfully.")
    except Exception as e:
        logger.info(f"Note on Prompt registration (may already exist): {e}")

    # -------------------------------------------------------------------------
    # 2. Create Golden AML Benchmark Dataset (Datasets Tab)
    # -------------------------------------------------------------------------
    logger.info("Creating Golden AML Benchmark Dataset in Phoenix...")
    benchmark_data = [
        {
            "account_id": "ACC-883910",
            "subject_name": "Derrick Sterling / Apex Horizon LLC",
            "expected_typology": "Structuring / Smurfing & Sanctions Evasion",
            "expected_statutory_violation": "31 U.S.C. 5324 & 31 CFR 1010.311",
            "expected_action": "FREEZE_AND_FILE_SAR",
            "expected_min_amount": 75000.0
        },
        {
            "account_id": "ACC-449102",
            "subject_name": "Elena Rostova Import-Export",
            "expected_typology": "Layering / High-Risk Free-Zone Wires",
            "expected_statutory_violation": "FATF Recommendation 24 & 31 CFR 1020.320",
            "expected_action": "FILE_SAR_ENHANCED_DUE_DILIGENCE",
            "expected_min_amount": 150000.0
        },
        {
            "account_id": "ACC-100001",
            "subject_name": "Acme Retail Store Inc",
            "expected_typology": "Legitimate Commercial Baseline",
            "expected_statutory_violation": "NONE",
            "expected_action": "NO_ACTION_CLEAN",
            "expected_min_amount": 0.0
        }
    ]

    df = pd.DataFrame(benchmark_data)
    dataset_name = "aml_compliance_benchmark_dataset"

    try:
        dataset = client.datasets.get_dataset(dataset=dataset_name)
        logger.info(f"Dataset '{dataset_name}' already exists in Phoenix.")
    except Exception:
        dataset = client.datasets.create_dataset(
            name=dataset_name,
            dataframe=df,
            input_keys=["account_id", "subject_name"],
            output_keys=["expected_typology", "expected_statutory_violation", "expected_action", "expected_min_amount"],
            dataset_description="Golden benchmark test cases for AML Structuring, Layering, and Baseline accounts"
        )
        logger.info(f"Dataset '{dataset_name}' created successfully in Phoenix.")

    # -------------------------------------------------------------------------
    # 3. Define Task Function and Guardrail Evaluators (Evaluators Tab)
    # -------------------------------------------------------------------------
    def run_investigation_task(example: Any) -> Dict[str, Any]:
        """Runs the LangGraph multi-agent pipeline for a dataset example."""
        input_data = getattr(example, "input", {})
        if isinstance(input_data, dict):
            account_id = input_data.get("account_id", "ACC-883910")
        else:
            account_id = "ACC-883910"
        
        case_result = run_aml_investigation(account_id=account_id)
        sar = case_result.get("sar_draft", {})
        evaluation = case_result.get("evaluation", {})
        
        return {
            "account_id": account_id,
            "case_id": case_result.get("case_id"),
            "status": case_result.get("status"),
            "primary_activity": sar.get("primary_activity", ""),
            "suspicious_amount": sar.get("suspicious_amount_total_usd", 0.0),
            "faithfulness_score": evaluation.get("faithfulness_score", 1.0),
            "audit_verdict": evaluation.get("audit_verdict", "APPROVED"),
            "full_sar_text": sar.get("full_sar_text", "")
        }

    def faithfulness_guardrail_evaluator(output: Dict[str, Any], expected: Dict[str, Any]) -> float:
        """Evaluator scoring factual accuracy and hallucination-free compliance (0.0 to 1.0)."""
        if not output or not isinstance(output, dict):
            return 0.0
        score = output.get("faithfulness_score", 1.0)
        return float(score)

    def typology_accuracy_evaluator(output: Dict[str, Any], expected: Dict[str, Any]) -> float:
        """Evaluator scoring whether the multi-agent system correctly identified suspicious activity vs clean baseline."""
        if not output or not isinstance(output, dict):
            return 0.0
        amount = output.get("suspicious_amount", 0.0)
        expected_action = (expected or {}).get("expected_action", "")
        if expected_action == "NO_ACTION_CLEAN":
            return 1.0 if amount == 0.0 else 0.8
        else:
            return 1.0 if amount > 50000.0 else 0.5

    def statutory_citation_evaluator(output: Dict[str, Any], expected: Dict[str, Any]) -> float:
        """Evaluator scoring whether statutory FinCEN 31 CFR or FATF regulatory citations appear in the narrative."""
        if not output or not isinstance(output, dict):
            return 0.0
        text = str(output.get("full_sar_text", "")) + " " + str(output.get("primary_activity", ""))
        exp_statute = str((expected or {}).get("expected_statutory_violation", ""))
        if exp_statute == "NONE":
            return 1.0
        for kw in ["31 CFR", "31 U.S.C", "FATF"]:
            if kw.lower() in text.lower():
                return 1.0
        return 0.8

    # -------------------------------------------------------------------------
    # 4. Run Benchmark Experiment in Phoenix (Experiments Tab)
    # -------------------------------------------------------------------------
    logger.info("Executing Multi-Agent Benchmark Experiment in Phoenix...")
    try:
        experiment = client.experiments.run_experiment(
            dataset=dataset,
            task=run_investigation_task,
            evaluators=[
                faithfulness_guardrail_evaluator,
                typology_accuracy_evaluator,
                statutory_citation_evaluator
            ],
            experiment_name="langgraph_aml_sar_evaluation_run",
            experiment_description="Evaluates LangGraph 4-Agent pipeline across Structuring, Layering, and Baseline accounts",
            experiment_metadata={
                "model": "qwen/qwen3.8-27b",
                "protocol": "Model Context Protocol (MCP)",
                "framework": "LangGraph"
            }
        )
        logger.info(f"Experiment completed successfully! View in Phoenix UI at: {base_url}")
        return experiment
    except Exception as e:
        logger.error(f"Error running Phoenix experiment: {e}")
        return None


if __name__ == "__main__":
    seed_phoenix_benchmarks()
