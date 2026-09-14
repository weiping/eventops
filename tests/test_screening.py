from scripts.screening import domain_of, screen, summarise

ACCOUNTS = {"acme.co.jp", "hanwha.co.kr"}
COMPETITORS = {"rival.dev"}


def d(email):
    return screen({"name": "x", "email": email}, ACCOUNTS, COMPETITORS)


def test_known_account_is_approved():
    assert d("a@acme.co.jp").verdict == "approve"


def test_competitor_is_rejected():
    assert d("a@rival.dev").verdict == "reject"


def test_student_is_rejected():
    assert d("a@u-tokyo.ac.jp").verdict == "reject"


def test_free_mail_goes_to_review():
    assert d("a@gmail.com").verdict == "review"


def test_unknown_corporate_goes_to_review():
    assert d("a@newco.io").verdict == "review"


def test_missing_email_is_rejected():
    assert d("").verdict == "reject"


def test_domain_case_is_normalised():
    assert domain_of("A@ACME.CO.JP") == "acme.co.jp"


def test_summary_hides_approvals():
    rows = [({"name": "n", "email": "a@acme.co.jp"}, d("a@acme.co.jp")),
            ({"name": "m", "email": "b@gmail.com"}, d("b@gmail.com"))]
    out = summarise(rows)
    assert "approve 1" in out and "gmail.com" in out and "acme.co.jp" not in out
