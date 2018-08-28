raws = [
    #horizontal
    [0, 1, 2],
    [3, 4, 5],
    [6, 7, 8],
    #vertical
    [0, 3, 6],
    [1, 4, 7],
    [2, 5, 8],
    #diagonal nw-se
    [0, 9, 4, 12, 8],
    [1, 10, 5],
    [3, 11, 7],
    #diagonal sw-ne
    [2, 10, 4, 11, 6],
    [1, 9, 3],
    [5, 12, 7]
]

def index_of_first(lst, pred):
    for i,v in enumerate(lst):
        if pred(v):
            return i
    return None

def get_potential_steps(white_locs, black_loc, i):
    for r1 in raws:
        for b in (False, True):
            r = r1[:]
            if b:
                r.reverse()
            if i not in r:
                continue
            idx = r.index(i)
            if idx <= 0 or idx == len(r) -1:
                continue
            loc_remover = index_of_first(r[idx+1:], lambda loc: loc in white_locs | set([black_loc]))
            if loc_remover is None:
                continue
            black = r[idx+1:][loc_remover] == black_loc
            loc_space = idx - 1
            while loc_space >= 0 and r[loc_space] not in white_locs  | set([black_loc]):
                src = r[idx+1:][loc_remover]
                dst = r[loc_space]
                yield (black, i, src, dst)
                if len(white_locs) == 1:
                    break
                loc_space -= 1

def solve(white_locs, black_loc, steps = None):
    if not steps:
        steps = []
    for i in white_locs:
        potential_steps = get_potential_steps(white_locs, black_loc, i)
        for step in potential_steps:
            new_white_locs, new_black_loc = apply_step(white_locs, black_loc, step)
            if len(new_white_locs) == 0:
                emit_solution(steps + [step])
            else:
                solve(new_white_locs, new_black_loc, steps + [step])

def apply_step(white_locs, black_loc, step):
    black, removed, remover, target = step
    new_white_locs = white_locs - set([removed])
    if black:
        new_black_loc = target
    else:
        new_black_loc = black_loc
        new_white_locs -= set([remover])
        new_white_locs |= set([target])
    return new_white_locs, new_black_loc

def emit_solution(steps):
    print steps


def main():
    black_loc = 5;
    white_locs = set([0,1,2,9,10,4,11,12,6,7,8])
    solve(white_locs, black_loc)
    print "finito"

if __name__ == "__main__"    :
    main()

