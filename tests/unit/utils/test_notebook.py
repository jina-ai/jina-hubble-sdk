from hubble.utils.notebook import is_notebook


async def test_is_notebook():
    is_notebook_env = is_notebook()
    assert is_notebook_env is False
