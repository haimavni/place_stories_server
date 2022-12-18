from sse import Publisher

publisher = Publisher()

def subscribe():
    channel = request.vars.channel or "default channel"
    comment(f"entered subscribe. {channel}")
    publisher.subscribe(channel)
    response.headers['Content-Type'] = 'text/event-stream'
    
@serve_json
def tease(vars):
    publisher.publish(vars.data, vars.channel or "default channel")
    return dict()
