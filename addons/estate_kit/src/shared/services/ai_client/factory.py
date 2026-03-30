from .anthropic_client import AnthropicClient


class Factory:
    @staticmethod
    def create(env) -> AnthropicClient:
        return AnthropicClient(env)
