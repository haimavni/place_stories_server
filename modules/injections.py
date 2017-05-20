from gluon import current

def inject(*a):
    result = []
    for s in a:
        result.append(current.globalenv[s])
    if len(result) == 1:
        result = result[0]
    return result
