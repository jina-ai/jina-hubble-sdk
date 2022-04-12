import os

import pytest


@pytest.fixture(autouse=True)
def environment():
    """Test should be performed on staging environment."""
    os.environ['HUBBLE_ENVIRONMENT'] = 'STAGING'
    yield
    del os.environ['HUBBLE_ENVIRONMENT']
