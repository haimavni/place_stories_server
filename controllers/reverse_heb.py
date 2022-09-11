with open('/home/haim/pdf-games/yoman.txt') as f:
    with open('/home/haim/pdf-games/yoman-rev.txt', 'w', encoding="utf-8") as g:
        for s in f:
            s = s.strip()
            s = s[::-1]
            g.write(s + '\n')
