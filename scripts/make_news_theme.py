"""이슈브리프 뉴스 테마(시그니처 오프닝 곡)를 직접 합성한다 — 외부 음원 없음, 저작권 걱정 없는 자작곡.
대표 결정(2026-11-02 00:47): "우리만의 뉴스풍 오프닝 곡을 만들어서 사용하자".

python scripts/make_news_theme.py [--sec 29]
  → music/news_theme.m4a  : 기본(경제·해외·사회 브리핑). 시계 똑딱 + 상승 화음 + 시그니처 4음 '딩-딩-딩-딩' → 박자감 있는 배경
  → music/news_calm.m4a   : 같은 4음 모티프를 느리고 부드럽게(사건·사고·추모). 드럼 없음
시그니처 모티프: D5 → A5 → F5 → E5 (짧은 종소리). 모든 편에서 같은 모티프를 써서 '이슈브리프 소리'로 기억되게 한다.
릴스에 입히기: python scripts/make_news_theme.py --mux <영상.mp4> --theme news|calm --out <결과.mp4>
"""
import argparse
import pathlib
import subprocess
import tempfile
import wave

import numpy as np

SR = 44100
ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "music"
rng = np.random.default_rng(11)
BPM = 120
BEAT = 60 / BPM
MOTIF = [74, 81, 77, 76]  # D5 A5 F5 E5


def hz(n):
    return 440.0 * 2 ** ((n - 69) / 12)


def env(n, a=0.005, r=0.2):
    e = np.ones(n)
    ai, ri = min(n, int(a * SR)), min(n, int(r * SR))
    if ai: e[:ai] = np.linspace(0, 1, ai)
    if ri: e[-ri:] *= np.linspace(1, 0, ri)
    return e


def add(buf, sig, at):
    i = int(at * SR)
    if i >= len(buf): return
    j = min(len(buf), i + len(sig))
    buf[i:j] += sig[: j - i]


def bell(n, dur=1.2, amp=0.22):
    t = np.arange(int(dur * SR)) / SR
    f = hz(n)
    s = (np.sin(2 * np.pi * f * t) + 0.45 * np.sin(2 * np.pi * f * 2.76 * t) * np.exp(-t * 6)
         + 0.25 * np.sin(2 * np.pi * f * 5.4 * t) * np.exp(-t * 10))
    return amp * s * np.exp(-t * 3.2) * env(len(t), 0.002, 0.05)


def brass(notes, dur, amp=0.16, attack=0.04):
    """톱니파 + 낮은 통과 필터 느낌(배음 줄이기)으로 만든 금관 화음."""
    t = np.arange(int(dur * SR)) / SR
    s = np.zeros_like(t)
    for n in notes:
        f = hz(n)
        for k in range(1, 9):
            s += np.sin(2 * np.pi * f * k * t * (1 + 0.0015 * np.sin(2 * np.pi * 5 * t))) / k ** 1.4
    s *= env(len(t), attack, min(0.5, dur * 0.6))
    return amp * s / len(notes)


def pad(notes, dur, amp=0.07):
    t = np.arange(int(dur * SR)) / SR
    s = np.zeros_like(t)
    for n in notes:
        for d in (-0.1, 0, 0.1):
            f = hz(n) * 2 ** (d / 12)
            s += np.sin(2 * np.pi * f * t) + 0.2 * np.sin(4 * np.pi * f * t)
    return amp * s * env(len(t), 0.8, 1.0) / (len(notes) * 3)


def bass(n, dur, amp=0.28):
    t = np.arange(int(dur * SR)) / SR
    f = hz(n)
    s = np.sin(2 * np.pi * f * t) + 0.3 * np.sin(4 * np.pi * f * t)
    return amp * s * env(len(t), 0.005, 0.08)


def kick(amp=0.55):
    n = int(0.3 * SR); t = np.arange(n) / SR
    f = 120 * np.exp(-t * 20) + 42
    return amp * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 9)


def tick(amp=0.06, dur=0.03, bright=True):
    n = int(dur * SR)
    s = rng.uniform(-1, 1, n)
    if bright: s = np.diff(np.concatenate([[0], s]))  # 고역만 남겨 '똑' 소리
    return amp * s * np.exp(-np.arange(n) / SR * 120)


def timp(n=38, amp=0.45, dur=1.6):
    t = np.arange(int(dur * SR)) / SR
    f = hz(n)
    s = np.sin(2 * np.pi * f * t) + 0.5 * np.sin(2 * np.pi * f * 1.5 * t) + 0.2 * rng.uniform(-1, 1, len(t)) * np.exp(-t * 30)
    return amp * s * np.exp(-t * 2.5)


def roll(start, length, buf, amp=0.18):
    k = 0
    tt = start
    while tt < start + length:
        a = amp * (0.3 + 0.7 * (tt - start) / length)
        add(buf, timp(38, a, 0.25), tt)
        tt += 0.045 + 0.01 * rng.random()
        k += 1


def strings(notes, dur, amp=0.1, attack=0.02):
    """여러 겹 톱니파(살짝 어긋난 음) = 현악 합주."""
    t = np.arange(int(dur * SR)) / SR
    s = np.zeros_like(t)
    for n in notes:
        for d in (-0.08, -0.03, 0.03, 0.08):
            f = hz(n) * 2 ** (d / 12)
            for k in range(1, 7):
                s += np.sin(2 * np.pi * f * k * t + k) / k ** 1.6
    return amp * s * env(len(t), attack, min(0.12, dur * 0.4)) / (len(notes) * 4)


def cymbal(dur=1.5, amp=0.12, swell=True):
    n = int(dur * SR)
    s = np.diff(np.concatenate([[0], rng.uniform(-1, 1, n)]))
    e = np.linspace(0, 1, n) ** 2 if swell else np.exp(-np.arange(n) / SR * 2.5)
    return amp * s * e


def news(sec):
    """보도국 오프닝 '분위기'(웅장한 금관 팡파르 + 현악 16분 반복 + 팀파니)를 따른 자작곡.
    특정 방송 테마의 멜로디·화성 진행은 쓰지 않는다 — 선율은 우리 시그니처 4음(D-A-F-E)으로만 만든다."""
    buf = np.zeros(int(sec * SR) + SR)
    beat = 60 / 112
    # 0~1.6 심벌 스웰 + 팀파니 롤
    add(buf, cymbal(1.6, 0.16, True), 0.0)
    roll(0.4, 1.2, buf, 0.22)
    # 1.6 쾅: 금관 + 현악 + 팀파니 + 심벌
    hit = 1.6
    add(buf, brass([38, 50, 57, 62, 65, 69], 1.3, 0.26, 0.015), hit)
    add(buf, strings([62, 69, 74], 1.0, 0.12), hit)
    add(buf, timp(38, 0.7, 2.0), hit)
    add(buf, cymbal(2.0, 0.14, False), hit)
    add(buf, kick(0.6), hit)
    # 팡파르: 시그니처 4음을 금관으로 크게 (D A F E → 길게 D)
    fan = hit + 1.0
    lens = [0.5, 0.5, 0.5, 0.5, 1.4]
    notes = MOTIF + [74]
    harm = [[62, 66, 69], [65, 69, 72], [62, 65, 70], [64, 67, 72], [62, 66, 69]]  # D Fm? → 장엄하게 움직이는 화음
    tt = fan
    for n, L, h in zip(notes, lens, harm):
        add(buf, brass([n, n - 12], L * beat * 2 + 0.1, 0.22, 0.03), tt)
        add(buf, brass(h, L * beat * 2 + 0.1, 0.12, 0.05), tt)
        add(buf, timp(38 if n != 81 else 45, 0.35, 0.8), tt)
        tt += L * beat * 2
    # 본문: 현악 16분 반복 + 낮은 금관 + 팀파니, 진행 Dm - Bb - Gm - A (4마디 반복)
    prog = [(50, [62, 65, 69]), (46, [58, 62, 65]), (43, [55, 58, 62]), (45, [57, 61, 64])]
    t0, bar = tt, 4 * beat
    k = 0
    while t0 < sec - 3.2:
        root, chord = prog[k % 4]
        add(buf, brass([root - 12, root], bar, 0.10, 0.2), t0)  # 낮은 금관 지속음
        add(buf, strings([c + 12 for c in chord], bar + 0.2, 0.05, 0.3), t0)  # 높은 현 패드
        arp = [chord[0] + 12, chord[1] + 12, chord[2] + 12, chord[1] + 12]
        for s in range(16):  # 16분 현악 반복(긴장감)
            add(buf, strings([arp[s % 4]], beat / 4 * 0.9, 0.09 if s % 4 == 0 else 0.06, 0.005), t0 + s * beat / 4)
        for b in range(4):
            add(buf, timp(root - 12 if root - 12 >= 33 else root, 0.28 if b == 0 else 0.14, 0.6), t0 + b * beat)
            add(buf, tick(0.035, 0.02), t0 + b * beat + beat / 2)
        if k % 4 == 3:  # 4마디 끝마다 팡파르 짧게
            for i, n in enumerate(MOTIF):
                add(buf, brass([n], beat * 0.5, 0.11, 0.02), t0 + 2 * beat + i * beat / 2)
        t0 += bar
        k += 1
    # 마무리: 팡파르 + 큰 화음
    end = sec - 3.0
    for i, n in enumerate(MOTIF):
        add(buf, brass([n, n - 12], beat * 0.5, 0.18, 0.02), end + i * beat / 2)
    add(buf, brass([38, 50, 57, 62, 66, 69], 2.0, 0.22, 0.02), end + 2 * beat)
    add(buf, timp(38, 0.6, 2.0), end + 2 * beat)
    add(buf, cymbal(2.0, 0.12, False), end + 2 * beat)
    return buf


def news_v1(sec):
    buf = np.zeros(int(sec * SR) + SR)
    # 0.0~1.2 시계 똑딱 4번(뉴스 시작 느낌)
    for i in range(4):
        add(buf, tick(0.09, 0.025), i * 0.3)
    # 0.6~1.5 팀파니 롤 → 1.5 큰 화음 + 팀파니
    roll(0.6, 0.9, buf)
    add(buf, brass([50, 57, 62, 65, 69], 1.6, 0.22, 0.02), 1.5)  # Dm(add) 큰 화음
    add(buf, timp(38, 0.6), 1.5)
    add(buf, kick(0.7), 1.5)
    # 2.2~ 시그니처 4음
    for i, n in enumerate(MOTIF):
        add(buf, bell(n, 1.4, 0.26), 2.2 + i * BEAT / 2)
        add(buf, bell(n - 12, 1.0, 0.08), 2.2 + i * BEAT / 2)
    add(buf, brass([53, 57, 60, 64], 1.2, 0.16, 0.06), 3.2)  # F 화음으로 풀어 줌
    # 4.0~ 배경 진행: Dm - Bb - F - C 반복 (한 마디 = 4박 = 2초)
    prog = [([50, 57, 62, 65], 38), ([46, 53, 58, 62], 34), ([41, 48, 53, 57], 41), ([48, 55, 60, 64], 36)]
    t0, bar = 4.0, 4 * BEAT
    k = 0
    while t0 < sec - 0.5:
        notes, b = prog[k % 4]
        add(buf, pad([x + 12 for x in notes], bar + 0.6, 0.06), t0)
        for beat in range(4):
            tb = t0 + beat * BEAT
            add(buf, kick(0.4 if beat % 2 == 0 else 0.22), tb)
            add(buf, bass(b, BEAT * 0.45, 0.22), tb)
            add(buf, bass(b, BEAT * 0.3, 0.14), tb + BEAT / 2)
            for s in range(4):  # 16분 시계 똑딱(뉴스 긴장감)
                add(buf, tick(0.05 if s % 2 == 0 else 0.03, 0.02), tb + s * BEAT / 4)
        if k % 4 == 3:  # 4마디마다 모티프 한 번 더(작게)
            for i, n in enumerate(MOTIF):
                add(buf, bell(n, 1.0, 0.12), t0 + 2 * BEAT + i * BEAT / 2)
        t0 += bar
        k += 1
    # 끝 마무리: 모티프 + 화음
    end = sec - 2.6
    for i, n in enumerate(MOTIF):
        add(buf, bell(n, 1.6, 0.2), end + i * BEAT / 2)
    add(buf, brass([50, 57, 62, 65, 69], 1.8, 0.14, 0.05), end + 1.0)
    return buf


def calm(sec):
    buf = np.zeros(int(sec * SR) + SR)
    slow = BEAT * 1.6
    add(buf, pad([62, 65, 69], 4.0, 0.08), 0.0)
    for i, n in enumerate(MOTIF):
        add(buf, bell(n, 2.6, 0.16), 0.6 + i * slow)
    prog = [[50, 57, 62, 65], [46, 53, 58, 62], [41, 48, 53, 57], [45, 52, 57, 61]]  # Dm Bb F A
    t0, bar = 4.0, 4.0
    k = 0
    while t0 < sec - 0.5:
        add(buf, pad([x + 12 for x in prog[k % 4]], bar + 1.2, 0.07), t0)
        add(buf, bass(prog[k % 4][0] - 12, bar * 0.9, 0.12) * np.linspace(1, 0.3, int(bar * 0.9 * SR)), t0)
        for j, n in enumerate([prog[k % 4][3] + 12, prog[k % 4][2] + 12]):
            add(buf, bell(n, 2.0, 0.07), t0 + 1.0 + j * 1.5)
        t0 += bar
        k += 1
    for i, n in enumerate(MOTIF):
        add(buf, bell(n, 2.6, 0.12), sec - 5.5 + i * slow)
    return buf


def finish(buf, sec):
    buf = buf[: int(sec * SR)]
    # 아주 간단한 잔향
    d = int(0.09 * SR)
    wet = np.zeros_like(buf)
    wet[d:] += buf[:-d] * 0.25
    wet[2 * d:] += buf[: -2 * d] * 0.12
    buf = buf + wet
    fade = int(1.5 * SR)
    buf[-fade:] *= np.linspace(1, 0, fade)
    buf /= max(1e-9, np.max(np.abs(buf))) / 0.89
    return buf


def save(buf, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as td:
        w = pathlib.Path(td) / "a.wav"
        st = np.stack([buf, np.roll(buf, int(0.012 * SR)) * 0.96], 1)  # 살짝 넓은 스테레오
        with wave.open(str(w), "wb") as f:
            f.setnchannels(2); f.setsampwidth(2); f.setframerate(SR)
            f.writeframes((st * 32767).astype(np.int16).tobytes())
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(w), "-af", "acompressor=threshold=0.125:ratio=3:attack=5:release=120,loudnorm=I=-16:TP=-1.5:LRA=9", "-ar", "44100", "-c:a", "aac", "-b:a", "192k", str(path)], check=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sec", type=float, default=29.0)
    ap.add_argument("--mux")
    ap.add_argument("--theme", default="news", choices=["news", "calm"])
    ap.add_argument("--out")
    a = ap.parse_args()
    if a.mux:
        dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", a.mux]).strip())
        tmp = pathlib.Path(tempfile.gettempdir()) / f"_{a.theme}_{dur:.1f}.m4a"
        save(finish((news if a.theme == "news" else calm)(dur), dur), tmp)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", a.mux, "-i", str(tmp), "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                        "-c:a", "aac", "-shortest", a.out], check=True)
        print("완료:", a.out)
        return
    save(finish(news(a.sec), a.sec), OUT / "news_theme.m4a")
    save(finish(calm(a.sec), a.sec), OUT / "news_calm.m4a")
    print("완료: music/news_theme.m4a, music/news_calm.m4a")


if __name__ == "__main__":
    main()
