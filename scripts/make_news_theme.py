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


def news(sec):
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
