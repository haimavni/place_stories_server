from sse import Publisher

publisher = Publisher()

@serve_json
def subscribe(vars):
    comment(f"entered subscribe. {vars.channel}")
    publisher.subscribe(vars.channel or "default channel")
    return dict()

@serve_json
def tease(vars):
    publisher.publish(vars.data, vars.channel)
    return dict()
