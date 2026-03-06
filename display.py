# display.py
"""Terminal formatting for HiredScore output."""

import sys


def _supports_color():
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


USE_COLOR = _supports_color()


def _color(text, code):
    if not USE_COLOR:
        return text
    return f"\033[{code}m{text}\033[0m"


def red(text):
    return _color(text, "31")


def green(text):
    return _color(text, "32")


def yellow(text):
    return _color(text, "33")


def blue(text):
    return _color(text, "34")


def bold(text):
    return _color(text, "1")


def grade_color(grade):
    colors = {"A": green, "B": blue, "C": yellow, "D": red}
    return colors.get(grade, lambda x: x)(grade)


def bar(value, max_value, width=20):
    filled = int(width * value / max(max_value, 1))
    return green("#" * filled) + red("-" * (width - filled))


def header(text):
    line = "=" * 60
    print(f"\n{bold(line)}")
    print(f"  {bold(text)}")
    print(bold(line))


def print_score_breakdown(result):
    grade = result["grade"]
    total = result["total_score"]

    header(f"HIREDSCORE SIMULATION — Grade: {grade_color(grade)} ({total}/100)")

    print(f"\n  {bold('Factor Breakdown:')}\n")
    for factor in result["factors"]:
        name = factor["name"]
        score = factor["score"]
        max_score = factor["max_score"]
        comment = factor["comment"]
        print(f"    {name:<25s} {bar(score, max_score)} {score}/{max_score}  {comment}")

    if result.get("improvements"):
        print(f"\n  {bold('Top Improvements:')}\n")
        for i, imp in enumerate(result["improvements"], 1):
            pts = imp.get("estimated_points", "?")
            print(f"    {i}. {imp['action']} ({green(f'+{pts} pts')})")

    if result.get("suggested_rewrites"):
        print(f"\n  {bold('Suggested Rewrites:')}\n")
        for rw in result["suggested_rewrites"]:
            print(f"    >> {bold(rw['section'])}\n")
            for line in rw["text"].split("\n"):
                print(f"    {line}")
            print()


def print_bias_audit(result):
    raw = result["raw_score"]
    fair = result["fair_score"]
    delta = fair - raw

    header("BIAS AUDIT")
    print(f"\n  Raw ATS Score:   {grade_color(result['raw_grade'])} ({raw}/100)")
    print(f"  Fair Score:      {grade_color(result['fair_grade'])} ({fair}/100)")
    print(f"  Bias Impact:     {red(f'{delta:+d} pts') if delta > 0 else f'{delta:+d} pts'}")

    print(f"\n  {bold('Signals Detected:')}\n")
    for signal in result["signals"]:
        status = yellow("!") if signal["detected"] else green("ok")
        impact = red(f"{signal['impact']:+d} pts") if signal["impact"] else green("no impact")
        print(f"    [{status}] {signal['name']:<35s} {impact}")
        if signal.get("detail"):
            print(f"        {signal['detail']}")

    if result.get("adversarial_suggestions"):
        print(f"\n  {bold('Adversarial Suggestions:')}\n")
        for i, sug in enumerate(result["adversarial_suggestions"], 1):
            print(f"    {i}. {sug}")


def print_advisor_response(response):
    print(f"\n  {bold('Avoid:')}")
    for avoid in response.get("avoid", []):
        print(f"    {red('x')} {avoid['text']}")
        if avoid.get("reason"):
            print(f"      Reason: {avoid['reason']}")

    print(f"\n  {bold('Suggested Response:')}")
    print()
    for line in response["suggested_response"].split("\n"):
        print(f"    {green('|')} {line}")

    if response.get("why_it_works"):
        print(f"\n  {bold('Why this works:')}")
        print(f"    {response['why_it_works']}")

    if response.get("bias_signals_neutralized"):
        print(f"\n  {bold('Bias signals neutralized:')}")
        for sig in response["bias_signals_neutralized"]:
            print(f"    {green('ok')} {sig}")
