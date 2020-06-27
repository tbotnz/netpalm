from marshmallow import Schema, fields

class model_getconfig(Schema):
    library = fields.Str(required=True)
    connection_args = fields.Dict(required=True)
    command = fields.Raw()
    args = fields.Dict()

class model_j2config(Schema):
    template = fields.Str(required=True)
    args = fields.Dict(required=True)

class model_setconfig_args(Schema):
    target = fields.Str()
    config = fields.Str()
    uri = fields.Str()
    action = fields.Str()
    payload = fields.Dict()

class model_setconfig(Schema):
    library = fields.Str(required=True)
    connection_args = fields.Dict(required=True)
    config = fields.Raw()
    j2config = fields.Nested(model_j2config)

class model_template_add(Schema):
    key = fields.Str()
    driver = fields.Str()
    command = fields.Str()

class model_template_remove(Schema):
    template = fields.Str()

class model_service(Schema):
    operation = fields.Str(required=True)
    args = fields.Dict(required=True)

class model_script(Schema):
    script = fields.Str(required=True)
    args = fields.Dict(required=True)


