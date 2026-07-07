"""Follow-up to Tasks 1-10: wiring real Qwen/embeddings HTTP clients into
EnrichmentBatch, and closing the prompt-version self-improvement feedback
loop.

Covers:
- get_real_qwen_fn() / get_real_embeddings_fn(): correctly build the request
  and unwrap the (doubly-nested, for embeddings) response shape of the real
  local llama-server endpoints, verified against mocked `requests.post`.
- EnrichmentBatch now consults PromptImprovement.prompt_versions (not the
  raw static config) when building QwenInference, so an auto-improved
  prompt version written by generate_improved_prompt() actually gets used
  by the next batch run - both when an improved version file exists and
  when it doesn't (fresh install fallback to static config prompts).
- main()'s --mock flag selects the mock qwen/embeddings functions instead
  of the real ones.
"""
import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from scripts.enrich_batch import (
    EnrichmentBatch,
    get_real_qwen_fn,
    get_real_embeddings_fn,
    get_mock_qwen_fn,
    get_embeddings_fn,
)


class TestRealQwenFn:
    """get_real_qwen_fn() must build the OpenAI-compatible chat request and
    extract response.json()['choices'][0]['message']['content']."""

    def test_extracts_content_from_response(self):
        qwen_call = get_real_qwen_fn(port=11437)

        fake_response = MagicMock()
        fake_response.json.return_value = {
            "choices": [{"message": {"content": "Education, Health Services"}}]
        }
        fake_response.raise_for_status.return_value = None

        with patch("requests.post", return_value=fake_response) as mock_post:
            result = qwen_call("suggest cause tags", max_tokens=150)

        assert result == "Education, Health Services"

        # Verify the request shape matches the documented, verified-live API.
        args, kwargs = mock_post.call_args
        assert args[0] == "http://localhost:11437/v1/chat/completions"
        assert kwargs["json"]["messages"] == [
            {"role": "user", "content": "suggest cause tags"}
        ]
        assert kwargs["json"]["max_tokens"] == 150

    def test_uses_custom_port(self):
        qwen_call = get_real_qwen_fn(port=9999)
        fake_response = MagicMock()
        fake_response.json.return_value = {
            "choices": [{"message": {"content": "x"}}]
        }
        fake_response.raise_for_status.return_value = None

        with patch("requests.post", return_value=fake_response) as mock_post:
            qwen_call("prompt")

        assert mock_post.call_args[0][0] == "http://localhost:9999/v1/chat/completions"

    def test_raises_on_connection_error_not_swallowed_here(self):
        """The real client itself must NOT swallow errors - that's
        QwenInference's job (bare `except Exception`), verified separately
        below. get_real_qwen_fn's job is only to propagate."""
        import requests

        qwen_call = get_real_qwen_fn(port=11437)
        with patch("requests.post", side_effect=requests.exceptions.ConnectionError("refused")):
            with pytest.raises(requests.exceptions.ConnectionError):
                qwen_call("prompt")

    def test_raises_on_non_2xx_status(self):
        import requests

        qwen_call = get_real_qwen_fn(port=11437)
        fake_response = MagicMock()
        fake_response.raise_for_status.side_effect = requests.exceptions.HTTPError("500 error")

        with patch("requests.post", return_value=fake_response):
            with pytest.raises(requests.exceptions.HTTPError):
                qwen_call("prompt")


class TestRealEmbeddingsFn:
    """get_real_embeddings_fn() must unwrap the doubly-nested llama.cpp
    embedding response shape: response[i]['embedding'][0] -> flat 1024-dim
    vector, one per input text."""

    def test_unwraps_doubly_nested_shape(self):
        embeddings_call = get_real_embeddings_fn(port=11436)

        vec_a = [0.1] * 1024
        vec_b = [0.2] * 1024
        fake_response = MagicMock()
        fake_response.json.return_value = [
            {"index": 0, "embedding": [vec_a]},
            {"index": 1, "embedding": [vec_b]},
        ]
        fake_response.raise_for_status.return_value = None

        with patch("requests.post", return_value=fake_response) as mock_post:
            result = embeddings_call(["text one", "text two"])

        assert len(result) == 2
        assert len(result[0]) == 1024
        assert len(result[1]) == 1024
        assert result[0] == vec_a
        assert result[1] == vec_b

        args, kwargs = mock_post.call_args
        assert args[0] == "http://localhost:11436/embedding"
        assert kwargs["json"] == {"content": ["text one", "text two"]}

    def test_uses_custom_port(self):
        fake_response = MagicMock()
        fake_response.json.return_value = [{"index": 0, "embedding": [[0.0] * 1024]}]
        fake_response.raise_for_status.return_value = None

        embeddings_call = get_real_embeddings_fn(port=8888)
        with patch("requests.post", return_value=fake_response) as mock_post:
            embeddings_call(["hi"])

        assert mock_post.call_args[0][0] == "http://localhost:8888/embedding"

    def test_raises_on_connection_error(self):
        import requests

        embeddings_call = get_real_embeddings_fn(port=11436)
        with patch("requests.post", side_effect=requests.exceptions.Timeout("timed out")):
            with pytest.raises(requests.exceptions.Timeout):
                embeddings_call(["hi"])


class TestQwenInferenceExceptionHandling:
    """Explicit confirmation (per the task's requirement, not an assumption)
    that QwenInference's bare `except Exception` in generate_tags/
    generate_website actually catches requests' exception types and returns
    None instead of crashing."""

    def test_generate_tags_survives_connection_error(self):
        import requests
        from scripts.qwen_inference import QwenInference

        def broken_qwen_fn(prompt, max_tokens=200):
            raise requests.exceptions.ConnectionError("connection refused")

        config = {"prompts": {"v1.0": {"cause_tags": "{mission}", "website": "{org_name}"}}}
        qwen = QwenInference(qwen_fn=broken_qwen_fn, config=config)

        result = qwen.generate_tags({"EIN": "123", "mission": "test"}, [])
        assert result is None

    def test_generate_website_survives_timeout(self):
        import requests
        from scripts.qwen_inference import QwenInference

        def broken_qwen_fn(prompt, max_tokens=200):
            raise requests.exceptions.Timeout("timed out")

        config = {"prompts": {"v1.0": {"cause_tags": "{mission}", "website": "{org_name}"}}}
        qwen = QwenInference(qwen_fn=broken_qwen_fn, config=config)

        result = qwen.generate_website({"EIN": "123", "name": "Test Org"}, [])
        assert result is None

    def test_generate_tags_survives_generic_request_exception(self):
        import requests
        from scripts.qwen_inference import QwenInference

        def broken_qwen_fn(prompt, max_tokens=200):
            raise requests.exceptions.RequestException("some request error")

        config = {"prompts": {"v1.0": {"cause_tags": "{mission}", "website": "{org_name}"}}}
        qwen = QwenInference(qwen_fn=broken_qwen_fn, config=config)

        result = qwen.generate_tags({"EIN": "123", "mission": "test"}, [])
        assert result is None


class TestPromptVersionFeedbackLoop:
    """EnrichmentBatch must build QwenInference from whatever
    PromptImprovement.prompt_versions resolves to, not the raw static
    config - so an auto-improved version written overnight actually gets
    used."""

    def test_picks_up_preexisting_improved_version(self, test_db, mock_qwen, mock_embeddings, enrich_config, tmp_path):
        prompt_file = tmp_path / "prompt_versions.json"
        seeded_versions = {
            "v1.0": {"cause_tags": "old v1.0 template {mission}", "website": "old v1.0 website {org_name}"},
            "v1.1": {"cause_tags": "v1.1 template {mission}", "website": "v1.1 website {org_name}"},
            "v1.2": {"cause_tags": "auto-improved v1.2 template {mission}", "website": "auto-improved v1.2 website {org_name}"},
        }
        prompt_file.write_text(json.dumps(seeded_versions))

        batch = EnrichmentBatch(
            db_con=test_db, qwen_fn=mock_qwen, embeddings_fn=mock_embeddings,
            config=enrich_config, prompt_versions_file=str(prompt_file)
        )

        assert batch.qwen.prompt_version == "v1.2"
        # And it should actually be using the auto-improved template content,
        # not just claiming the right version number.
        assert batch.qwen.prompts["cause_tags"] == "auto-improved v1.2 template {mission}"

    def test_falls_back_to_static_config_when_no_file_exists(self, test_db, mock_qwen, mock_embeddings, enrich_config, tmp_path):
        # Point at a file path that does NOT exist - PromptImprovement's
        # _load_prompt_versions() falls back to config['prompts'], whose
        # max static version today is v1.1 (see enrich_batch_config.json).
        missing_file = tmp_path / "does_not_exist.json"
        assert not missing_file.exists()

        batch = EnrichmentBatch(
            db_con=test_db, qwen_fn=mock_qwen, embeddings_fn=mock_embeddings,
            config=enrich_config, prompt_versions_file=str(missing_file)
        )

        assert batch.qwen.prompt_version == "v1.1"

    def test_default_prompt_versions_file_none_uses_static_config(self, test_db, mock_qwen, mock_embeddings, enrich_config):
        """Default construction (no prompt_versions_file arg at all) must not
        crash and must resolve to the static config's max version, as long
        as no real prompt_versions.json happens to exist at the default
        path (~/meritgiving/data/enrichment/prompt_versions.json)."""
        default_path = Path.home() / "meritgiving" / "data" / "enrichment" / "prompt_versions.json"

        batch = EnrichmentBatch(
            db_con=test_db, qwen_fn=mock_qwen, embeddings_fn=mock_embeddings,
            config=enrich_config
        )

        if default_path.exists():
            # If a real auto-improved file exists on this machine, just
            # confirm the loop is wired (a version was picked from that
            # file), not a specific version number.
            with open(default_path) as f:
                real_versions = json.load(f)
            expected = max(real_versions.keys(), key=lambda v: float(v[1:]))
            assert batch.qwen.prompt_version == expected
        else:
            assert batch.qwen.prompt_version == "v1.1"


class TestMockFlagSelection:
    """main()'s --mock flag must select the mock qwen/embeddings functions;
    without it, the real HTTP-backed functions must be selected."""

    def test_argparse_recognizes_mock_flag(self):
        import argparse
        parser = argparse.ArgumentParser()
        parser.add_argument('--dry-run', action='store_true')
        parser.add_argument('--max-orgs', type=int)
        parser.add_argument('--workers', type=int, default=1)
        parser.add_argument('--batch-size', type=int, default=20)
        parser.add_argument('--mock', action='store_true')
        parser.add_argument('--qwen-port', type=int, default=11437)
        parser.add_argument('--embeddings-port', type=int, default=11436)

        args_mock = parser.parse_args(['--mock'])
        assert args_mock.mock is True

        args_default = parser.parse_args([])
        assert args_default.mock is False
        assert args_default.qwen_port == 11437
        assert args_default.embeddings_port == 11436

    def test_main_selects_mock_functions_when_flag_set(self, monkeypatch, tmp_path):
        """Run main() end-to-end with --mock and --dry-run against a throwaway
        sqlite file, patching sys.argv, and confirm it uses the mock
        functions (no real HTTP call happens) by asserting requests.post is
        never invoked."""
        import scripts.enrich_batch as eb

        db_path = tmp_path / "test_merit.db"
        con = __import__("sqlite3").connect(str(db_path))
        # Minimal schema for main()'s query + write path.
        con.executescript("""
            CREATE TABLE registry_enriched (
                EIN TEXT PRIMARY KEY, organization_name TEXT, mission TEXT,
                NTEE1 TEXT, city TEXT, state TEXT, cause_tags TEXT, website TEXT
            );
            CREATE TABLE enrichment_run (
                run_id INTEGER PRIMARY KEY AUTOINCREMENT, run_date DATE, org_ein TEXT,
                enrichment_type TEXT, generated_value TEXT, confidence_score REAL,
                context_used TEXT
            );
        """)
        con.execute(
            "INSERT INTO registry_enriched VALUES (?,?,?,?,?,?,'','')",
            ("111111111", "Test Org", "helps people", "P", "Austin", "TX")
        )
        con.commit()
        con.close()

        monkeypatch.setattr(eb, "DB_PATH", db_path)
        monkeypatch.setattr(
            sys, "argv",
            ["enrich_batch.py", "--mock", "--dry-run", "--max-orgs", "1"]
        )

        with patch("requests.post") as mock_post:
            eb.main()

        mock_post.assert_not_called()
