from sse import Publisher

publisher = Publisher()

@serve_json
def subscribe(vars):
    publisher.subscribe(vars.channel)
    return dict()

@serve_json
def tease(vars):
    publisher.publish(vars.data, vars.channel)
    return dict()
