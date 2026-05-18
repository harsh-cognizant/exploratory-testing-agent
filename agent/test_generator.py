"""
Module: agent/test_generator.py
Purpose: Generate Pytest test functions for high/critical findings using the
         Claude API. Validates syntax before writing to tests/generated/.
         Per CLAUDE.md §4.14.
Author: Team / Claude Code
Created: 2026-05-14
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import anthropic
from dotenv import load_dotenv

from agent.gap_analyser import safe_parse_json

load_dotenv()

logger = logging.getLogger(__name__)

# Constants per CLAUDE.md §1 and §13.
CLAUDE_MODEL: str = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")
MAX_TOKENS_TEST_GEN: int = 1500
TESTS_OUTPUT_DIR: str = os.getenv("TESTS_OUTPUT_DIR", "./tests/generated")
PROMPT_PATH: Path = Path(__file__).parent / "prompts" / "test_generation.txt"
BASE_URL: str = os.getenv("APP_URL", "http://localhost:3001")

# Standard imports for generated test files.
TEST_FILE_HEADER: str = """import pytest
from playwright.sync_api import Page


"""


def _get_client() -> anthropic.Anthropic:
    """Construct an Anthropic-SDK-compatible client.

    Supports both direct Anthropic (ANTHROPIC_API_KEY → x-api-key) and proxy /
    OpenRouter (ANTHROPIC_AUTH_TOKEN + ANTHROPIC_BASE_URL → Bearer auth).
    """
    auth_token = (os.getenv("ANTHROPIC_AUTH_TOKEN") or "").strip()
    api_key = (os.getenv("ANTHROPIC_API_KEY") or "").strip()
    base_url = (os.getenv("ANTHROPIC_BASE_URL") or "").strip() or None

    if auth_token:
        return anthropic.Anthropic(auth_token=auth_token, base_url=base_url)
    if api_key and api_key != "your_key_here":
        return anthropic.Anthropic(api_key=api_key, base_url=base_url)
    raise RuntimeError(
        "No Anthropic credentials set. Set ANTHROPIC_API_KEY or "
        "ANTHROPIC_AUTH_TOKEN + ANTHROPIC_BASE_URL in .env."
    )


def _load_prompt_template() -> str:
    """Load the test generation prompt template.

    Returns:
        Raw prompt string with placeholders.

    Raises:
        FileNotFoundError: If the prompt template is missing.
    """
    if not PROMPT_PATH.is_file():
        raise FileNotFoundError(
            f"Prompt file missing: {PROMPT_PATH}. Restore from CLAUDE.md §7."
        )
    return PROMPT_PATH.read_text(encoding="utf-8")


def _validate_syntax(code: str) -> bool:
    """Check if generated Python code is syntactically valid.

    Args:
        code: Python source code string.

    Returns:
        True if code compiles without syntax errors.
    """
    try:
        compile(code, "<string>", "exec")
        return True
    except SyntaxError as exc:
        logger.warning("Generated test has syntax error: %s", exc)
        return False


def _extract_function_code(raw_text: str) -> str:
    """Extract just the function code from Claude's response.

    Strips markdown fences, import statements, and any preamble.

    Args:
        raw_text: Raw Claude response text.

    Returns:
        Cleaned function code starting with 'def test_'.
    """
    import re

    # Strip markdown code fences.
    cleaned = re.sub(r"```(?:python)?", "", raw_text).strip()
    cleaned = cleaned.rstrip("`").strip()

    # Remove import lines (they're added automatically in the header).
    lines = cleaned.split("\n")
    filtered = []
    in_function = False
    for line in lines:
        if line.strip().startswith("import ") or line.strip().startswith("from "):
            continue
        if line.strip().startswith("def test_"):
            in_function = True
        if in_function:
            filtered.append(line)

    return "\n".join(filtered).strip()


def _is_offline() -> bool:
    """Return True when LLM_OFFLINE=1 in env (see agent/personas.py for context)."""
    return (os.getenv("LLM_OFFLINE") or "").strip().lower() in ("1", "true", "yes")


def _build_offline_test(finding: Dict[str, Any], severity: str) -> Dict[str, Any]:
    """Build a deterministic placeholder Pytest function for offline mode.

    The generated test is a real, syntactically valid stub that documents
    the finding and asserts a TODO. It's not LLM-quality but it lets the
    test-generation slot in the report render correctly.
    """
    page_slug = (finding.get("page") or "/").strip("/").replace("/", "_") or "home"
    safe_id = finding["id"].replace("-", "_")
    func_name = f"test_{page_slug}_{safe_id}"
    page_url = finding.get("page", "/")
    anomaly = (finding.get("anomaly") or "").replace('"""', "'''")
    steps_lines = "\n".join(
        f"    # {s}" for s in (finding.get("reproduction_steps") or [])
    ) or "    # (no reproduction steps recorded)"
    code = (
        f"def {func_name}(page):\n"
        f"    \"\"\"Regression for finding {finding['id']} on {page_url}.\n\n"
        f"    Anomaly: {anomaly}\n"
        f"    Severity: {severity}\n"
        f"    \"\"\"\n"
        f"{steps_lines}\n"
        f"    page.goto(\"http://localhost:3001{page_url}\")\n"
        f"    # TODO: encode the precise assertion that catches this regression.\n"
        f"    assert False, \"Replace with real assertion once LLM backend is reachable\"\n"
    )
    return {
        "finding_id": finding["id"],
        "test_function_name": func_name,
        "test_code": code,
        "severity": severity,
        "page": page_url,
    }


def generate_test_for_finding(
    finding: Dict[str, Any],
    app_url: str = BASE_URL,
) -> Optional[Dict[str, Any]]:
    """Generate a Pytest test function for a single finding.

    Only generates for severity 'high' or 'critical' per §4.14.

    Args:
        finding: Finding dict matching the Finding schema.
        app_url: Application base URL.

    Returns:
        Dict with finding_id, test_function_name, test_code, severity, page.
        None if generation fails.
    """
    severity = finding.get("severity", "medium")
    if hasattr(severity, "value"):
        severity = severity.value
    if severity not in ("high", "critical"):
        logger.debug("Skipping test gen for %s (severity=%s)", finding.get("id"), severity)
        return None

    if _is_offline():
        return _build_offline_test(finding, severity)

    try:
        template = _load_prompt_template()
        client = _get_client()
    except (FileNotFoundError, RuntimeError) as exc:
        logger.error("Cannot generate test: %s", exc)
        return None

    page_url = finding.get("page", "/")
    prompt = template.format(
        finding_json=json.dumps(finding, indent=2),
        base_url=app_url,
        page_url=page_url,
    )

    # Two-attempt generation with retry on syntax error.
    strict_suffix = "\n\nReturn ONLY valid Python code. No markdown, no explanation."
    for attempt in (1, 2):
        try:
            message = client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=MAX_TOKENS_TEST_GEN,
                messages=[{
                    "role": "user",
                    "content": prompt if attempt == 1 else prompt + strict_suffix,
                }],
            )
            raw_text = ""
            for block in message.content:
                if getattr(block, "type", None) == "text":
                    raw_text = block.text
                    break

            func_code = _extract_function_code(raw_text)
            full_code = TEST_FILE_HEADER + func_code

            if _validate_syntax(full_code):
                # Extract function name.
                import re
                name_match = re.search(r"def (test_\w+)", func_code)
                func_name = name_match.group(1) if name_match else f"test_{finding['id']}"

                return {
                    "finding_id": finding["id"],
                    "test_function_name": func_name,
                    "test_code": func_code,
                    "severity": severity,
                    "page": page_url,
                }

            logger.warning(
                "Test gen attempt %d: syntax invalid for finding %s",
                attempt, finding.get("id"),
            )

        except anthropic.AnthropicError as exc:
            logger.error("Claude API error on test gen attempt %d: %s", attempt, exc)
            return None

    logger.error(
        "Test generation failed for finding %s after 2 attempts",
        finding.get("id"),
    )
    return None


def generate_tests_for_findings(
    findings: List[Dict[str, Any]],
    app_url: str = BASE_URL,
) -> List[Dict[str, Any]]:
    """Generate Pytest test files for all high/critical findings.

    Writes each test to tests/generated/test_{finding_id}.py.
    Per §4.14: never overwrites existing test files — appends suffix.

    Args:
        findings: List of finding dicts.
        app_url: Application base URL.

    Returns:
        List of generated test dicts (finding_id, test_function_name, test_code, severity, page).
    """
    output_dir = Path(TESTS_OUTPUT_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)

    generated: List[Dict[str, Any]] = []

    for finding in findings:
        result = generate_test_for_finding(finding, app_url)
        if not result:
            continue

        # Write to file per §4.14.
        filename = f"test_{result['finding_id']}.py"
        filepath = output_dir / filename

        # Never overwrite per §4.14.
        if filepath.exists():
            suffix = 1
            while filepath.exists():
                filename = f"test_{result['finding_id']}_{suffix}.py"
                filepath = output_dir / filename
                suffix += 1

        full_code = TEST_FILE_HEADER + result["test_code"]
        filepath.write_text(full_code, encoding="utf-8")
        logger.info("Generated test: %s", filepath)

        generated.append(result)

    logger.info("Generated %d test files from %d findings", len(generated), len(findings))
    return generated
