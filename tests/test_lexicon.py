from flowlocal.lexicon import Lexicon
from flowlocal.app import process_text


def test_add_list_remove():
    lex = Lexicon()
    lex.add("Kubernetes", aliases=["kubernetes", "cooper netties"])
    assert [t.term for t in lex.terms()] == ["Kubernetes"]
    assert lex.remove("Kubernetes")
    assert lex.terms() == []


def test_bias_prompt():
    lex = Lexicon()
    lex.add("PostgreSQL")
    lex.add("Anthropic")
    prompt = lex.bias_prompt()
    assert prompt.startswith("Glossary:")
    assert "PostgreSQL" in prompt and "Anthropic" in prompt
    assert Lexicon().bias_prompt() == ""


def test_alias_resolution():
    lex = Lexicon()
    lex.add("Kubernetes", aliases=["cooper netties"])
    assert lex.resolve_aliases("deploy to cooper netties") == "deploy to Kubernetes"


def test_correction_mining_promotes_after_threshold():
    lex = Lexicon()
    for _ in range(3):
        lex.record_correction("wisper", "Whisper")
    assert lex.promote_corrections(threshold=3) == ["Whisper"]
    terms = lex.terms()
    assert terms[0].term == "Whisper" and "wisper" in terms[0].aliases


def test_pipeline_text_path_end_to_end():
    lex = Lexicon()
    lex.add("FlowLocal", aliases=["flow local"])
    out = process_text("um so flow local uses whisper period", lex, "polished")
    assert "FlowLocal" in out
    assert "um" not in out.lower().split()
