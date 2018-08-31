from games.black_sheep import solve

@serve_json
def solve_black_sheep(vars):
    black_loc = vars.black_loc
    white_locs = set(vars.white_locs)
    result = dict(solution_steps = [])
    for steps in solve(white_locs, black_loc):
        result = dict(solution_steps=steps)
        break
    return result

    