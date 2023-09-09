import re

def message_to_link(message):
    pat = r"(?P<url>https?:\/\/([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:\/~+#-]*[\w@?^=%&\/~+#-]))"
    match = re.search(pat, s)
    if not match:
        return message
    url = match.group(0)
    msg = message.replace(url, '')
    return f'<a href="{url}">{msg}</a>'

s = "my message http://tol.life/rishpon?key=MTM1MjY0NTk0MDkxODkwMDcyOTM end of my message"
link = message_to_link(s)
print(link)
