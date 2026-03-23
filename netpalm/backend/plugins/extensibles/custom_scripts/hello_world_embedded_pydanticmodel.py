from netpalm.backend.core.models.models import ScriptCustom


class MyCustomScriptModel(ScriptCustom):
    script: str
    test: str | None = None


def run(payload: MyCustomScriptModel):
    try:
        # mandatory get of kwargs - payload comes through as {"kwargs": {"hello": "world"}}
        args = payload.test
        # reutn "world"
        return args
    except Exception as e:
        raise Exception(e)
