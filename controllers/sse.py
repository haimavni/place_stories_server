from sse import get_publisher
import time

def subscribe():
    channel = request.vars.channel or "default channel"
    comment(f"entered subscribe. {channel}")
    publisher = get_publisher()
    publisher.subscribe(channel)
    response.headers['Content-Type'] = 'text/event-stream'
    
@serve_json
def tease(vars):
    publisher = get_publisher()
    publisher.publish(vars.data, vars.channel or "default channel")
    return dict(data=vars.data, channel=vars.channel)

@serve_json
def close(vars):
    publisher = get_publisher()
    publisher.close()
    return dict()