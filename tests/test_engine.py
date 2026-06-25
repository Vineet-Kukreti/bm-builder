"""Unit tests for the engine's pure / near-pure functions.

Run with:  python -m unittest discover -s tests
These cover the logic that the package split made testable in isolation — no
network, no Streamlit, no real builds.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine import core, graph, reports, errors            # noqa: E402


class TestSafeJson(unittest.TestCase):
    def test_plain(self):
        self.assertEqual(core.safe_json('{"a": 1}'), {"a": 1})

    def test_code_fence(self):
        self.assertEqual(core.safe_json('```json\n{"a": 1}\n```'), {"a": 1})

    def test_embedded_in_prose(self):
        self.assertEqual(core.safe_json('Sure! {"a": 1} hope that helps'), {"a": 1})

    def test_array(self):
        self.assertEqual(core.safe_json("[1, 2, 3]", default=[]), [1, 2, 3])

    def test_junk_returns_default(self):
        self.assertEqual(core.safe_json("not json at all", default={"d": True}), {"d": True})

    def test_empty_returns_default(self):
        self.assertEqual(core.safe_json("", default={"x": 1}), {"x": 1})


class TestModelAssignment(unittest.TestCase):
    def test_model_for_ceo_is_fixed(self):
        self.assertEqual(core.model_for("CEO", {"CEO": "something-else"}), core.CEO_MODEL)

    def test_model_for_assignment_wins(self):
        self.assertEqual(core.model_for("CMO", {"CMO": "claude-haiku-4-5"}), "claude-haiku-4-5")

    def test_model_for_default(self):
        self.assertEqual(core.model_for("QA"), core.DEFAULT_ASSIGNMENT["QA"])

    def test_validate_fills_unknown_with_defaults(self):
        clean = core.validate_assignment({"CMO": "bogus-model"})
        self.assertEqual(clean["CMO"], core.DEFAULT_ASSIGNMENT["CMO"])
        for role in core.ASSIGNABLE_ROLES:
            self.assertIn(role, clean)

    def test_validate_forces_vision_designer(self):
        # An unknown designer model falls back to a vision-capable Claude default.
        clean = core.validate_assignment({"DESIGNER": "made-up-model"})
        self.assertIn(clean["DESIGNER"], core.MODEL_REGISTRY)
        self.assertTrue(core.MODEL_REGISTRY[clean["DESIGNER"]]["vision"])


class TestCostMath(unittest.TestCase):
    def test_model_cost(self):
        class U:                      # mimic the Anthropic usage object
            input_tokens, output_tokens = 1_000_000, 1_000_000
            cache_read_input_tokens = cache_creation_input_tokens = 0
        usd, inp, out = core._model_cost("claude-opus-4-8", U())
        # opus pricing is (5, 25) per 1M → 5 + 25 = 30
        self.assertAlmostEqual(usd, 30.0, places=4)
        self.assertEqual((inp, out), (1_000_000, 1_000_000))

    def test_unknown_model_is_free(self):
        class U:
            input_tokens = output_tokens = 1000
            cache_read_input_tokens = cache_creation_input_tokens = 0
        usd, _, _ = core._model_cost("some-local-model", U())
        self.assertEqual(usd, 0.0)


class TestVisionDetection(unittest.TestCase):
    def test_gpt4o_is_vision(self):
        self.assertTrue(core._openai_is_vision("gpt-4o"))

    def test_plain_text_model_is_not(self):
        self.assertFalse(core._openai_is_vision("llama-3.3-70b-versatile"))


class TestDemojibake(unittest.TestCase):
    def test_repairs_corruption(self):
        # "Söhne" encoded as UTF-8 then mis-decoded as cp1252 yields "SÃ¶hne".
        self.assertEqual(core._demojibake("SÃ¶hne"), "Söhne")

    def test_noop_on_clean_text(self):
        self.assertEqual(core._demojibake("Plain ASCII text"), "Plain ASCII text")

    def test_idempotent(self):
        once = core._demojibake("SÃ¶hne")
        self.assertEqual(core._demojibake(once), once)


class TestErrors(unittest.TestCase):
    def test_detects_sentinel(self):
        self.assertTrue(errors.is_engine_error("Claude Engine Error (claude-opus-4-8): timeout"))

    def test_ignores_normal_prose(self):
        self.assertFalse(errors.is_engine_error("This document explains common errors."))

    def test_engine_error_is_exception(self):
        self.assertTrue(issubclass(errors.EngineError, Exception))


class TestRoadmap(unittest.TestCase):
    def test_empty_roadmap_shape(self):
        rm = core._empty_roadmap()
        self.assertEqual(rm["items"], [])
        self.assertIn("v1 (MVP)", rm["versions"])

    def test_roadmap_to_md(self):
        rm = {"versions": ["v1 (MVP)"], "items": [{"title": "Login", "version": "v1 (MVP)"}]}
        md = core.roadmap_to_md(rm)
        self.assertIn("# Version Roadmap", md)
        self.assertIn("Login", md)


class TestGraph(unittest.TestCase):
    def test_build_graph_dot(self):
        dot = graph.build_graph_dot([{"agent": "CTO", "type": "question", "text": "Auth?"}], readiness=42)
        self.assertTrue(dot.startswith("digraph G {"))
        self.assertIn("readiness 42%", dot)
        self.assertIn("Auth?", dot)


class TestReports(unittest.TestCase):
    def test_md_to_html_escapes_and_wraps(self):
        html = reports._md_to_html_doc("Title", "# Hello `code`")
        self.assertIn("<!doctype html>", html)
        self.assertIn("Title", html)
        self.assertNotIn("</script>code", html)   # script-breakers are escaped


class TestProviderDispatch(unittest.TestCase):
    def test_call_agent_routes_to_registered_backend(self):
        saved_default = core._DEFAULT_MODEL
        saved_agents = core._AGENT_PROVIDERS
        saved_openai = core._PROVIDERS.get("openai")
        try:
            core._DEFAULT_MODEL = {"provider": "openai", "model": "fake", "base_url": "http://x/v1"}
            core._AGENT_PROVIDERS = {}      # CMO falls back to the default provider (openai)
            seen = []
            core.register_provider("openai", lambda *a: (seen.append(a), "FAKE")[1])
            out = core.call_agent("CMO", "sys", "hi")
            self.assertEqual(out, "FAKE")
            self.assertEqual(len(seen), 1)
        finally:
            core._DEFAULT_MODEL = saved_default
            core._AGENT_PROVIDERS = saved_agents
            if saved_openai is not None:
                core.register_provider("openai", saved_openai)


class TestUseCases(unittest.TestCase):
    """The use-cases run an LLM step + parse; here we stub the provider with canned JSON."""

    def setUp(self):
        from engine import usecases
        self.usecases = usecases
        self._saved_default = core._DEFAULT_MODEL
        self._saved_agents = core._AGENT_PROVIDERS
        self._saved_anthropic = core._PROVIDERS.get("anthropic")
        # Force the anthropic backend (not the subscription path) for all agents, then stub it.
        core._DEFAULT_MODEL = {"provider": "anthropic", "model": "claude-haiku-4-5", "base_url": ""}
        core._AGENT_PROVIDERS = {}      # all roles -> anthropic family (deterministic)
        self._canned = {"text": ""}
        core.register_provider("anthropic", lambda *a: self._canned["text"])

    def tearDown(self):
        core._DEFAULT_MODEL = self._saved_default
        core._AGENT_PROVIDERS = self._saved_agents
        if self._saved_anthropic is not None:
            core.register_provider("anthropic", self._saved_anthropic)

    def test_staff_team_parses_and_validates(self):
        self._canned["text"] = (
            '{"assignment": {"CMO": "claude-haiku-4-5", "DEVELOPER": "claude-sonnet-4-6", '
            '"QA": "claude-sonnet-4-6", "DESIGNER": "claude-opus-4-8", "PM": "claude-sonnet-4-6"}, '
            '"rationale": "balanced"}')
        out = self.usecases.staff_team("a budgeting app")
        self.assertEqual(out["assignment"]["CMO"], "claude-haiku-4-5")
        self.assertEqual(out["rationale"], "balanced")
        self.assertTrue(core.MODEL_REGISTRY[out["assignment"]["DESIGNER"]]["vision"])

    def test_next_batch_parses(self):
        self._canned["text"] = (
            '{"items": [{"type": "question", "agent": "CTO", "text": "Which DB?"}], '
            '"done": false, "readiness": 55, "coverage": {"scope": 50}, "missing": ["auth"]}')
        out = self.usecases.next_brainstorm_batch("brief so far")
        self.assertEqual(len(out["items"]), 1)
        self.assertEqual(out["items"][0]["agent"], "CTO")
        self.assertEqual(out["readiness"], 55)
        self.assertFalse(out["done"])
        self.assertEqual(out["error"], "")

    def test_next_batch_surfaces_engine_error(self):
        self._canned["text"] = "Claude Engine Error (claude-haiku-4-5): boom"
        out = self.usecases.next_brainstorm_batch("brief")
        self.assertTrue(out["error"])
        self.assertEqual(out["items"], [])

    def test_next_batch_empty_items_marks_done(self):
        self._canned["text"] = '{"items": [], "done": false, "readiness": 90}'
        out = self.usecases.next_brainstorm_batch("brief")
        self.assertTrue(out["done"])   # no items -> done, even if model said false


class TestPerAgentRouting(unittest.TestCase):
    """Per-agent provider resolution (role_provider / _resolve_call / call_agent)."""

    def setUp(self):
        self._dm = core._DEFAULT_MODEL
        self._ap = core._AGENT_PROVIDERS
        self._an = core._PROVIDERS.get("anthropic")
        self._oa = core._PROVIDERS.get("openai")

    def tearDown(self):
        core._DEFAULT_MODEL = self._dm
        core._AGENT_PROVIDERS = self._ap
        if self._an:
            core.register_provider("anthropic", self._an)
        if self._oa:
            core.register_provider("openai", self._oa)

    def test_role_provider_override_else_default(self):
        core._DEFAULT_MODEL = {"provider": "claude_subscription", "model": "", "base_url": ""}
        core._AGENT_PROVIDERS = {"QA": "openai"}
        self.assertEqual(core.role_provider("QA"), "openai")        # override
        self.assertEqual(core.role_provider("CEO"), "claude_subscription")  # default

    def test_subscription_routable_coerces_to_claude(self):
        # A routable agent on the subscription with a non-Claude model must be coerced to a
        # Claude model so it actually runs on Claude Code (provider 'anthropic').
        core._DEFAULT_MODEL = {"provider": "claude_subscription", "model": "", "base_url": ""}
        core._AGENT_PROVIDERS = {}
        mid, prov, _ = core._resolve_call("QA", "some-non-claude-model", False)
        self.assertEqual(prov, "anthropic")
        self.assertEqual(mid, core.CEO_MODEL)
        # The Claude defaults already resolve to anthropic without coercion.
        mid2, prov2, _ = core._resolve_call("CEO", None, False)
        self.assertEqual(prov2, "anthropic")

    def test_openai_agent_falls_back_to_shared_or_default(self):
        # No CEO-assigned OpenAI model passed → uses the shared field, else gpt-4o.
        core._DEFAULT_MODEL = {"provider": "claude_subscription", "model": "gpt-4o", "base_url": ""}
        core._AGENT_PROVIDERS = {"CMO": "openai"}
        mid, prov, base = core._resolve_call("CMO", None, False)
        self.assertEqual((mid, prov), ("gpt-4o", "openai"))
        self.assertTrue(base)

    def test_openai_assigned_model_wins(self):
        core._DEFAULT_MODEL = {"provider": "claude_subscription", "model": "", "base_url": ""}
        core._AGENT_PROVIDERS = {"CMO": "openai"}
        mid, prov, _ = core._resolve_call("CMO", "gpt-4o-mini", False)   # CEO assignment
        self.assertEqual((mid, prov), ("gpt-4o-mini", "openai"))

    def test_anthropic_api_agent_uses_assigned_model(self):
        core._DEFAULT_MODEL = {"provider": "claude_subscription", "model": "", "base_url": ""}
        core._AGENT_PROVIDERS = {"CTO": "anthropic"}
        # The CEO-assigned (passed) Claude model is used, on the API (provider 'anthropic').
        self.assertEqual(core._resolve_call("CTO", "claude-sonnet-4-6", False),
                         ("claude-sonnet-4-6", "anthropic", ""))

    def test_openai_compatible_uses_custom_endpoint(self):
        core._DEFAULT_MODEL = {"provider": "claude_subscription", "model": "llama-3.3-70b-versatile",
                               "base_url": "https://api.groq.com/openai/v1"}
        core._AGENT_PROVIDERS = {"PM": "openai_compatible"}
        self.assertEqual(core._resolve_call("PM", None, False),
                         ("llama-3.3-70b-versatile", "openai", "https://api.groq.com/openai/v1"))

    def test_provider_family(self):
        self.assertEqual(core.provider_family("claude_subscription"), "anthropic")
        self.assertEqual(core.provider_family("anthropic"), "anthropic")
        self.assertEqual(core.provider_family("openai"), "openai")
        self.assertEqual(core.provider_family("openai_compatible"), "openai")

    def test_subscription_roles_reflects_config(self):
        core._DEFAULT_MODEL = {"provider": "claude_subscription", "model": "", "base_url": ""}
        core._AGENT_PROVIDERS = {"QA": "openai", "CTO": "anthropic"}
        self.assertEqual(set(core.subscription_roles()), {"CEO", "CMO", "PM", "SKEPTIC"})

    def test_call_agent_routes_openai_agent_to_openai_backend(self):
        core._DEFAULT_MODEL = {"provider": "claude_subscription", "model": "gpt-4o", "base_url": ""}
        core._AGENT_PROVIDERS = {"CMO": "openai"}
        core.register_provider("openai", lambda *a: "OAI")
        self.assertEqual(core.call_agent("CMO", "sys", "hi"), "OAI")


class TestBuildModel(unittest.TestCase):
    """The autonomous Claude Code build runs on the CEO-assigned Developer model."""

    def test_cc_model_alias(self):
        self.assertEqual(core._cc_model_alias("claude-opus-4-8"), "opus")
        self.assertEqual(core._cc_model_alias("claude-sonnet-4-6"), "sonnet")
        self.assertEqual(core._cc_model_alias("claude-haiku-4-5"), "haiku")
        self.assertEqual(core._cc_model_alias("gpt-4o"), "")   # non-Claude -> let Claude Code default

    def test_build_model_alias_reads_developer_assignment(self):
        import tempfile, shutil
        d = tempfile.mkdtemp(prefix="bm_test_")
        try:
            core.save_project_state(d, "p", {"model_map": {"DEVELOPER": "claude-opus-4-8"}})
            self.assertEqual(core._build_model_alias(d, "p"), "opus")
            core.save_project_state(d, "p", {"model_map": {"DEVELOPER": "claude-sonnet-4-6"}})
            self.assertEqual(core._build_model_alias(d, "p"), "sonnet")
        finally:
            shutil.rmtree(d, ignore_errors=True)


if __name__ == "__main__":
    unittest.main(verbosity=2)
