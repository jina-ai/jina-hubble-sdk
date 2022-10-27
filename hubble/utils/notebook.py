import re

import psutil

JUPYTER_NOTEBOOK = 'jupyter_notebook'
JUPYTER_LAB = 'jupyter_lab'
GOOGLE_COLAB = 'google_colab'


def is_notebook_lab():  # pragma: no cover
    return any(
        [re.search('jupyter-lab', x) for x in psutil.Process().parent().cmdline()]
    )


def get_python_environment():  # pragma: no cover
    """
    Check if we're running in a Jupyter notebook, using magic command `get_ipython` that only available in Jupyter.
    :return: True if run in a Jupyter notebook else False.
    """

    try:
        get_ipython  # noqa: F821
    except NameError:
        return None

    shell = get_ipython().__class__.__name__  # noqa: F821

    if shell == 'ZMQInteractiveShell':
        is_lab = is_notebook_lab()
        if is_lab:
            return JUPYTER_LAB
        else:
            return JUPYTER_NOTEBOOK

    elif shell == 'Shell':
        return GOOGLE_COLAB

    elif shell == 'TerminalInteractiveShell':
        return None

    else:
        return None
