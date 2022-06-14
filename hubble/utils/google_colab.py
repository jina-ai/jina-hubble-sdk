import sys


def in_google_colab():
    """
    Returns True if the code is running in Google Colab.
    """
    return 'google.colab' in sys.modules
