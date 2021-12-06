# all functions need to be wrapped in the "run" function and pass in kwargs
# JSON example to send into the /script route is as below
#
# {
# 	"script":"hello_world",
# 	"args":{
# 		"hello":"world"
# 	}
# }
#
def run(**kwargs):
    try:
        # mandatory get of kwargs - payload comes through as {"kwargs": {"hello": "world"}}
        args = kwargs.get("kwargs")
        # access your vars here in a dict format - payload is now {"hello": "world"}
        world = args["hello"]
        # reutn "world"
        return world
    except KeyError as e:
        raise Exception(f"Required args: {e}")
    except Exception as e:
        raise Exception(e)
