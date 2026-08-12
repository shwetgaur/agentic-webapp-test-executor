from src.agent.parser import parse_plain_text_case
from src.common.models import StepAction


SAMPLE = """
## TC01_login_success
Module: login
1. Open https://www.saucedemo.com/
2. Fill username with standard_user
3. Fill password with secret_sauce
4. Click the Login button
5. Verify URL contains inventory.html
6. Verify text Products is visible
"""


def test_parse_login_case():
    suite = parse_plain_text_case(SAMPLE)
    assert suite.suite_id == "TC01_login_success"
    assert suite.module == "login"
    assert len(suite.steps) == 6
    assert suite.steps[0].action == StepAction.GOTO
    assert suite.steps[1].action == StepAction.FILL
    assert suite.steps[1].selector == "#user-name"
    assert suite.steps[3].action == StepAction.CLICK
    assert suite.steps[4].action == StepAction.ASSERT_URL
    assert suite.steps[5].action == StepAction.ASSERT_TEXT
