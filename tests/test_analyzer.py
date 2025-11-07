from sensei_lua.analyzer import analyze_source


def collect_messages(source: str):
    return {(issue.code, issue.message) for issue in analyze_source(source)}


def test_missing_final_newline_detected():
    issues = analyze_source("print('hello world')")
    assert any(issue.code == "FORMAT" and "Missing final newline" in issue.message for issue in issues)


def test_trailing_whitespace_detected():
    assert ("FORMAT", "Trailing whitespace") in collect_messages("print('hi')  \n")


def test_mixed_indentation_detected():
    source = "if true then\n\t  print('oops')\nend\n"
    issues = analyze_source(source)
    assert any(issue.code == "INDENT" and "Mixed tabs and spaces" in issue.message for issue in issues)


def test_unmatched_end_detected():
    source = "if true then\n  print('oops')\n"
    issues = analyze_source(source)
    assert any(issue.code == "SYNTAX" and "Unclosed block" in issue.message for issue in issues)


def test_balanced_blocks_are_clean():
    source = """\
function greet(name)
    if name then
        print('Hello '..name)
    end
end
"""
    issues = analyze_source(source)
    assert issues == []


def test_until_matches_repeat():
    source = """\
repeat
    if ready then
        done = true
    end
until done
"""
    issues = analyze_source(source)
    assert issues == []


def test_unexpected_until_reports_issue():
    source = """\
if true then
    print('hi')
until false
end
"""
    issues = analyze_source(source)
    assert any(issue.code == "SYNTAX" and "Expected 'end'" in issue.message for issue in issues)


def test_tabs_allowed_when_requested():
    from sensei_lua.analyzer import analyze_source as analyze_source_local

    source = "if true then\n\tprint('ok')\nend\n"
    issues = analyze_source_local(source, prefer_spaces=False)
    assert all(issue.code != "INDENT" or "Tab indentation" not in issue.message for issue in issues)
