from flowlocal.cleanup import cleanup, find_protected_spans


def test_verbatim_untouched():
    raw = "um so like the the URL is https://example.com ok"
    assert cleanup(raw, "verbatim").text == raw


def test_light_removes_fillers():
    r = cleanup("um I think uh we should ship it", "light")
    assert r.text == "I think we should ship it"
    assert r.removed_fillers == 2


def test_light_capitalizes_and_spaces_punctuation():
    r = cleanup("hello ,world .this is fine", "light")
    assert r.text == "Hello, world. This is fine"


def test_polished_collapses_repeats_and_false_starts():
    r = cleanup("I went to the- to the store store", "polished")
    assert "to the store" in r.text
    assert "store store" not in r.text


def test_polished_spoken_commands():
    r = cleanup("hello comma world period new paragraph next", "polished")
    assert "hello," in r.text.lower()
    assert "\n\n" in r.text


def test_protected_url_and_email_survive():
    raw = "email me at a.b+c@test.io or see https://ex.com/x?y=1 um thanks"
    r = cleanup(raw, "polished")
    assert "a.b+c@test.io" in r.text
    assert "https://ex.com/x?y=1" in r.text
    assert " um " not in f" {r.text} "


def test_numbers_never_altered():
    raw = "the total is 1,234.56 on 2026-07-06"
    r = cleanup(raw, "polished")
    assert "1,234.56" in r.text
    assert "2026-07-06" in r.text


def test_lexicon_terms_are_protected():
    spans = find_protected_spans("deploy to Kubernetes now", ["Kubernetes"])
    assert any(lit == "Kubernetes" for _, _, lit in spans)


def test_empty_input():
    assert cleanup("", "light").text == ""
