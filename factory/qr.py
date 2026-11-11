"""순수 파이썬 QR 코드 생성기 (외부 라이브러리 없음)
- 바이트 모드(UTF-8), 오류정정 M, 버전 1~10 자동, 마스크 8개 중 벌점 가장 낮은 것 선택
사용: from qr import qr_matrix, qr_image
      m = qr_matrix("https://example.com")      # [[True(검정)/False]...]
      img = qr_image("https://example.com", scale=4, border=4)   # PIL 흑백 그림(PIL 있을 때)
"""

# 버전별 (전체 코드워드, 블록당 오류정정 코드워드, [(블록 수, 블록당 데이터 코드워드), ...]) — 오류정정 M
_M = {1: (26, 10, [(1, 16)]), 2: (44, 16, [(1, 28)]), 3: (70, 26, [(1, 44)]), 4: (100, 18, [(2, 32)]),
      5: (134, 24, [(2, 43)]), 6: (172, 16, [(4, 27)]), 7: (196, 18, [(4, 31)]),
      8: (242, 22, [(2, 38), (2, 39)]), 9: (292, 22, [(3, 36), (2, 37)]), 10: (346, 26, [(4, 43), (1, 44)])}
_ALIGN = {1: [], 2: [6, 18], 3: [6, 22], 4: [6, 26], 5: [6, 30], 6: [6, 34],
          7: [6, 22, 38], 8: [6, 24, 42], 9: [6, 26, 46], 10: [6, 28, 50]}
_EC_M = 0   # 형식 정보의 오류정정 M 비트(00)

# ---------- GF(256) · 리드-솔로몬 ----------
_EXP = [0] * 512; _LOG = [0] * 256
_x = 1
for _i in range(255):
    _EXP[_i] = _x; _LOG[_x] = _i; _x <<= 1
    if _x & 0x100: _x ^= 0x11D
for _i in range(255, 512): _EXP[_i] = _EXP[_i - 255]

def _mul(a, b): return 0 if a == 0 or b == 0 else _EXP[_LOG[a] + _LOG[b]]

def _rs_gen(n):
    g = [1]
    for i in range(n):   # g *= (x - α^i)
        ng = [0] * (len(g) + 1)
        for j, c in enumerate(g): ng[j] ^= c; ng[j + 1] ^= _mul(c, _EXP[i])
        g = ng
    return g             # 최고차 계수 1 포함, 길이 n+1

def _rs_ecc(data, n):
    g = _rs_gen(n); r = list(data) + [0] * n
    for i in range(len(data)):
        c = r[i]
        if c:
            for j in range(1, n + 1): r[i + j] ^= _mul(g[j], c)
    return r[len(data):]

# ---------- 데이터 → 코드워드 ----------
def _capacity(v): return sum(b * d for b, d in _M[v][2])

def _codewords(payload, ver):
    cnt_bits = 8 if ver <= 9 else 16
    bits = []
    def put(val, n): bits.extend((val >> (n - 1 - i)) & 1 for i in range(n))
    put(0b0100, 4); put(len(payload), cnt_bits)
    for b in payload: put(b, 8)
    cap = _capacity(ver) * 8
    put(0, min(4, cap - len(bits)))            # 끝 표시
    while len(bits) % 8: bits.append(0)
    data = [int("".join(map(str, bits[i:i + 8])), 2) for i in range(0, len(bits), 8)]
    pad = 0xEC
    while len(data) < _capacity(ver): data.append(pad); pad ^= 0xEC ^ 0x11
    total, ecn, groups = _M[ver]
    blocks, k = [], 0
    for nb, nd in groups:
        for _ in range(nb): blocks.append(data[k:k + nd]); k += nd
    eccs = [_rs_ecc(b, ecn) for b in blocks]
    out = []
    for i in range(max(len(b) for b in blocks)):      # 데이터 열 단위 섞기
        for b in blocks:
            if i < len(b): out.append(b[i])
    for i in range(ecn):
        for e in eccs: out.append(e[i])
    assert len(out) == total
    return out

# ---------- 그리기 ----------
class _Grid:
    def __init__(self, ver):
        self.v = ver; self.n = n = ver * 4 + 17
        self.m = [[False] * n for _ in range(n)]; self.f = [[False] * n for _ in range(n)]   # m[y][x], f = 기능 영역
    def set(self, x, y, dark): self.m[y][x] = dark; self.f[y][x] = True

    def functions(self):
        n = self.n
        for i in range(n): self.set(6, i, i % 2 == 0); self.set(i, 6, i % 2 == 0)       # 타이밍
        for cx, cy in ((3, 3), (n - 4, 3), (3, n - 4)):                              # 위치 찾기 무늬 + 분리 띠
            for dy in range(-4, 5):
                for dx in range(-4, 5):
                    x, y = cx + dx, cy + dy
                    if 0 <= x < n and 0 <= y < n: self.set(x, y, max(abs(dx), abs(dy)) not in (2, 4))
        al = _ALIGN[self.v]; L = len(al)
        for i in range(L):                                                            # 정렬 무늬
            for j in range(L):
                if (i == 0 and j == 0) or (i == 0 and j == L - 1) or (i == L - 1 and j == 0): continue
                for dy in range(-2, 3):
                    for dx in range(-2, 3): self.set(al[i] + dx, al[j] + dy, max(abs(dx), abs(dy)) != 1)
        self.format_bits(0)
        if self.v >= 7:                                                               # 버전 정보
            rem = self.v
            for _ in range(12): rem = (rem << 1) ^ ((rem >> 11) * 0x1F25)
            bits = self.v << 12 | rem
            for i in range(18):
                b = (bits >> i) & 1 == 1; a, c = n - 11 + i % 3, i // 3
                self.set(a, c, b); self.set(c, a, b)

    def format_bits(self, mask):
        n = self.n; data = _EC_M << 3 | mask; rem = data
        for _ in range(10): rem = (rem << 1) ^ ((rem >> 9) * 0x537)
        bits = (data << 10 | rem) ^ 0x5412
        g = lambda i: (bits >> i) & 1 == 1
        for i in range(6): self.set(8, i, g(i))
        self.set(8, 7, g(6)); self.set(8, 8, g(7)); self.set(7, 8, g(8))
        for i in range(9, 15): self.set(14 - i, 8, g(i))
        for i in range(8): self.set(n - 1 - i, 8, g(i))
        for i in range(8, 15): self.set(8, n - 15 + i, g(i))
        self.set(8, n - 8, True)                                                      # 항상 검정 모듈

    def place(self, cw):
        n = self.n; i = 0; total = len(cw) * 8; right = n - 1
        while right >= 1:
            if right == 6: right = 5
            for vert in range(n):
                for j in range(2):
                    x = right - j; up = ((right + 1) & 2) == 0; y = n - 1 - vert if up else vert
                    if not self.f[y][x]:
                        self.m[y][x] = i < total and ((cw[i >> 3] >> (7 - (i & 7))) & 1) == 1   # 남는 칸(나머지 비트)은 0
                        i += 1
            right -= 2

_MASKS = [lambda x, y: (x + y) % 2 == 0, lambda x, y: y % 2 == 0, lambda x, y: x % 3 == 0, lambda x, y: (x + y) % 3 == 0,
          lambda x, y: (x // 3 + y // 2) % 2 == 0, lambda x, y: x * y % 2 + x * y % 3 == 0,
          lambda x, y: (x * y % 2 + x * y % 3) % 2 == 0, lambda x, y: ((x + y) % 2 + x * y % 3) % 2 == 0]

def _apply_mask(g, k):
    f = _MASKS[k]
    for y in range(g.n):
        for x in range(g.n):
            if not g.f[y][x] and f(x, y): g.m[y][x] = not g.m[y][x]

def _penalty(m):
    n = len(m); p = 0; cols = [[m[y][x] for y in range(n)] for x in range(n)]
    pat = [True, False, True, True, True, False, True]
    for line in list(m) + cols:
        run, prev = 0, None
        for c in line:                                   # 규칙 1: 같은 색 5개 이상
            if c == prev: run += 1
            else:
                if run >= 5: p += 3 + run - 5
                run, prev = 1, c
        if run >= 5: p += 3 + run - 5
        ext = [False] * 4 + line + [False] * 4            # 규칙 3: 위치 무늬 닮은꼴 1:1:3:1:1 + 밝은 4칸
        for i in range(len(ext) - 6):
            if ext[i:i + 7] == pat and (not any(ext[max(0, i - 4):i]) and i >= 4 or not any(ext[i + 7:i + 11]) and i + 11 <= len(ext)): p += 40
    for y in range(n - 1):                                # 규칙 2: 2x2 같은 색
        for x in range(n - 1):
            c = m[y][x]
            if c == m[y][x + 1] == m[y + 1][x] == m[y + 1][x + 1]: p += 3
    dark = sum(sum(r) for r in m); pct = dark * 100 / (n * n)   # 규칙 4: 검정 비율
    p += int(abs(pct - 50) // 5) * 10
    return p

def qr_matrix(text, mask=None, version=None):
    payload = text.encode("utf-8") if isinstance(text, str) else bytes(text)
    ver = version
    if ver is None:
        for v in range(1, 11):
            if 4 + (8 if v <= 9 else 16) + 8 * len(payload) <= _capacity(v) * 8: ver = v; break
        else: raise ValueError(f"QR 버전 10(오류정정 M)에 담을 수 있는 길이를 넘었습니다: {len(payload)}바이트(최대 213바이트)")
    cw = _codewords(payload, ver)
    best = None
    for k in ([mask] if mask is not None else range(8)):
        g = _Grid(ver); g.functions(); g.place(cw); _apply_mask(g, k); g.format_bits(k)
        sc = _penalty(g.m)
        if best is None or sc < best[0]: best = (sc, k, g)
    return best[2].m

def qr_info(text):
    """(버전, 한 변 모듈 수) — 크기 계산용."""
    n = len(qr_matrix(text)); return (n - 17) // 4, n

def qr_image(text, scale=4, border=4, dark=(0, 0, 0), light=(255, 255, 255)):
    from PIL import Image
    m = qr_matrix(text); n = len(m); s = (n + 2 * border) * scale
    im = Image.new("RGB", (s, s), light); px = im.load()
    for y in range(n):
        for x in range(n):
            if m[y][x]:
                for yy in range(scale):
                    for xx in range(scale): px[(x + border) * scale + xx, (y + border) * scale + yy] = dark
    return im

if __name__ == "__main__":
    import sys
    t = sys.argv[1] if len(sys.argv) > 1 else "https://example.com"
    out = sys.argv[2] if len(sys.argv) > 2 else "qr.png"
    qr_image(t, 8).save(out); print("QR 저장:", out, "버전", qr_info(t)[0])
