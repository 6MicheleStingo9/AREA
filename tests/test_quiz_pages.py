"""The question pages of the web interface (api/routes_quiz.py, api/templates/)."""

from fastapi.testclient import TestClient

from api.main import app

REFRESH = 'hx-trigger="change from:#answer-area"'


def question_page(client, step, htmx=False):
    """A question of a new English questionnaire: the whole page, or the card htmx swaps in."""
    first = client.post("/quiz/start", data={"lang": "en"}, follow_redirects=False).headers["location"]
    headers = {"HX-Request": "true"} if htmx else {}
    return client.get(f"{first.rsplit('/', 1)[0]}/{step}", headers=headers).text


def test_the_follow_up_of_a_written_answer_is_there_from_the_start():
    # Shown once the answer was written, it appeared on the click on Next and moved the button
    page = question_page(TestClient(app), 0)   # 1.1, a written answer
    assert 'id="followup_1.1_0"' in page
    assert REFRESH not in page


def test_the_follow_ups_of_a_choice_follow_the_answer():
    page = question_page(TestClient(app), 2)   # 1.3, a choice: its follow-up opens with "Yes"
    shown = page.split("<noscript>")[0]
    assert REFRESH in shown
    assert 'name="followup_1.3_0"' not in shown


def test_the_no_js_fallback_stays_out_of_the_cards_htmx_swaps_in():
    # htmx turns <noscript> into real fields: hidden copies of the follow-ups, sent after the visible
    # ones, so the server kept their empty answers
    client = TestClient(app)
    assert "<noscript>" in question_page(client, 1)   # 1.2: "Other" and a follow-up not shown yet
    assert "<noscript>" not in question_page(client, 1, htmx=True)
