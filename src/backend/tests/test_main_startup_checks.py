"""main.py startup checks.

The Turnstile secret-key startup requirement (issue #570) was removed in turnover Phase 3
together with the civilian/public portal it protected.
"""

import main


def test_turnstile_startup_hook_removed():
    assert not hasattr(main, "_require_turnstile_secret_key")
