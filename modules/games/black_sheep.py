raws = [
    #horizontal
    [00, 01, 02],
    [10, 11, 12],
    [20, 21, 22],
    #vertical
    [00, 10, 20],
    [01, 11, 21],
    [02, 12, 22],
    #diagonal nw-se
    [00, 100, 11, 111, 22],
    [01, 101, 12],
    [10, 110, 21],
    #diagonal sw-ne
    [20, 110, 11, 101, 20],
    [01, 100, 10],
    [12, 111, 21]
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
                yield(steps + [step])
            else:
                for steps in solve(new_white_locs, new_black_loc, steps + [step]):
                    yield(steps)

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

def main():
    black_loc = 12;
    white_locs = set([00,01,02,100,101,11,110,111,12,21,22])
    i = 0
    for steps in solve(white_locs, black_loc):
        print '\nSolution #{}'.format(i)
        for step in steps:
            print '{:3} --> {:3}'.format(step[1], step[2])
        if i > 3:
            break;
        i += 1
    print "finito"

if __name__ == "__main__"    :
    main()

