from jina import Executor, requests


class {{exec_name}}(Executor):
    """{{exec_description}}"""
    @requests
    def foo(self, docs, **kwargs):
        pass
