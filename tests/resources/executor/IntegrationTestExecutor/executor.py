from jina import DocumentArray, Executor, requests


class IntegrationTestExecutor(Executor):
    """For integration testing"""

    @requests
    def foo(self, docs: DocumentArray, **kwargs):
        docs[0].text = 'from IntegrationTestExecutor'
