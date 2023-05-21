import os

model_name_aliases = {
    "chatgpt": "openai/gpt-3.5-turbo",
    "gpt-4": "openai/gpt-4",
}
class LMQLModelRegistry: 
    autoconnect = False
    backend_configuration = None

    @staticmethod
    def get(model):
        client = LMQLModelRegistry.clients.get(model, None)

        if client is None:
            # use auto connector to obtain model connection
            if LMQLModelRegistry.autoconnect and model not in LMQLModelRegistry.registry:
                autoregister(model)

            client = LMQLModelRegistry.registry[model]()
            LMQLModelRegistry.clients[model] = client

        return client

def autoregister(model_name):
    """
    Automatically registers a model backend implementation for the provided
    model name, deriving the implementation from the model name.
    """
    if model_name.startswith("openai/"):
        from lmql.runtime.openai_integration import openai_model

        # hard-code openai/ namespace to be openai-API-based
        Model = openai_model(model_name[7:])
        register_model(model_name, Model)
        register_model("*", Model)
    else:
        if "LMQL_BROWSER" in os.environ:
            assert False, "Cannot use HuggingFace Transformers models in browser. Please use openai/ models or install lmql on your local machine."

        if LMQLModelRegistry is not None:
            backend: str = LMQLModelRegistry.backend_configuration
            if backend != "legacy":
                from lmql.runtime.openai_integration import openai_model
                
                if backend is None:
                    backend = "localhost:8080"
                
                # use provided inference server as mocked OpenAI API
                endpoint = backend
                Model = openai_model(model_name, endpoint=endpoint, mock=True)
                register_model(model_name, Model)
                register_model("*", Model)
                return
            else:
                assert False, "Unknown backend configuration string '" + backend + "'"

        from lmql.runtime.hf_integration import transformers_model

        default_server = "http://localhost:8080"
        Model = transformers_model(default_server, model_name)
        register_model(model_name, Model)
        register_model("*", Model)

def register_model(identifier, ModelClass):
    LMQLModelRegistry.registry[identifier] = ModelClass

LMQLModelRegistry.autoconnect = None

LMQLModelRegistry.registry = {}
# instance of model clients in this process
LMQLModelRegistry.clients = {}