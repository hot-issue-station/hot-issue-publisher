"""릴스 배경음을 직접 합성한다(외부 음원 없음 → 저작권 걱정 없는 자작곡).

python scripts/make_music.py  →  music/warm.m4a, music/bright.m4a, music/calm.m4a (각 약 24초)
- warm  : 따뜻한 로파이 (기본, 해외·국내 일반 소식)
- bright: 경쾌한 팝 느낌 (스포츠·축하·기록)
- calm  : 잔잔한 패드 (사건·사고·민감 이슈, 차분한 소식)
- pulse : 118BPM 박자감 있는 곡 (역동적인 릴스 기본, 카드가 박자에 맞춰 넘어감)
대표가 가진 곡(직접 만든 곡, 상업 이용이 허락된 곡)은 music/ 폴더에 넣고 round JSON의 "music"으로 고르면 된다.
"""
import pathlib
import subprocess
import tempfile
import wave

import numpy as np

SR = 44100
ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "music"
rng = np.random.default_rng(7)


def midi(n):
    return 440.0 * 2 ** ((n - 69) / 12)


def env(n, a=0.01, r=0.3):
    e = np.ones(n)
    ai, ri = int(a * SR), int(r * SR)
    if ai: e[:ai] = np.linspace(0, 1, ai)
    if ri: e[-ri:] *= np.linspace(1, 0, ri)
    return e


def pad(freqs, dur, amp=0.12):
    t = np.arange(int(dur * SR)) / SR
    s = np.zeros_like(t)
    for f in freqs:
        for det in (-0.12, 0.0, 0.12):  # 살짝 어긋난 음으로 부드럽게
            ff = f * 2 ** (det / 12)
            s += np.sin(2 * np.pi * ff * t) + 0.25 * np.sin(4 * np.pi * ff * t) + 0.08 * np.sin(6 * np.pi * ff * t)
    s *= env(len(t), 0.6, 0.8) * (1 + 0.04 * np.sin(2 * np.pi * 0.3 * t))
    return amp * s / (len(freqs) * 3)


def pluck(f, dur, amp=0.18):
    """카플러스-스트롱 현 소리."""
    n = int(dur * SR)
    p = max(2, int(SR / f))
    buf = rng.uniform(-1, 1, p)
    out = np.empty(n)
    for i in range(n):
        out[i] = buf[i % p]
        buf[i % p] = 0.5 * (buf[i % p] + buf[(i + 1) % p]) * 0.996
    return amp * out * env(n, 0.002, 0.1)


def kick(amp=0.5):
    n = int(0.35 * SR); t = np.arange(n) / SR
    f = 110 * np.exp(-t * 18) + 45
    return amp * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 9)


def hat(amp=0.06):
    n = int(0.06 * SR)
    x = rng.uniform(-1, 1, n)
    x = np.diff(np.concatenate([[0], x]))  # 고음만 남기기
    return amp * x * np.exp(-np.arange(n) / SR * 60)


def snare(amp=0.12):
    n = int(0.18 * SR); t = np.arange(n) / SR
    return amp * (rng.uniform(-1, 1, n) * np.exp(-t * 25) + 0.5 * np.sin(2 * np.pi * 190 * t) * np.exp(-t * 30))


def add(track, sig, start):
    i = int(start * SR)
    j = min(len(track), i + len(sig))
    if i < len(track):
        track[i:j] += sig[: j - i]


def song(chords, bpm, bars_per_chord, drums=True, arp=True, swing=0.0, length=24.0, pad_amp=0.12, seed=1, punch=False):
    global rng
    rng = np.random.default_rng(seed)
    beat = 60 / bpm
    total = np.zeros(int((length + 1) * SR))
    tpos, ci = 0.0, 0
    while tpos < length:
        ch = chords[ci % len(chords)]
        dur = beat * 4 * bars_per_chord
        add(total, pad([midi(n) for n in ch], dur + 0.6, pad_amp), tpos)
        add(total, pad([midi(ch[0] - 12)], dur + 0.4, pad_amp * 0.9), tpos)  # 베이스
        if arp:
            notes = [ch[0] + 12, ch[1] + 12, ch[2] + 12, ch[1] + 12] if len(ch) >= 3 else [ch[0] + 12]
            steps = int(4 * bars_per_chord * 2)
            for k in range(steps):
                off = (swing * beat / 2) if k % 2 else 0
                add(total, pluck(midi(notes[k % len(notes)]), beat * 0.9, 0.11), tpos + k * beat / 2 + off)
        if drums:
            for b in range(int(4 * bars_per_chord)):
                bt = tpos + b * beat
                if punch:
                    add(total, kick(0.75), bt)                       # 네 박 모두 킥(사두)
                    if b % 2 == 1: add(total, snare(0.2), bt)
                    for q in range(4): add(total, hat(0.05 if q % 2 else 0.03), bt + q * beat / 4)
                    if b % 2 == 0: add(total, pluck(midi(ch[0] - 12), beat * 0.45, 0.22), bt + beat / 2)   # 통통 튀는 베이스
                else:
                    if b % 4 in (0, 2) or (b % 8 == 7): add(total, kick(), bt)
                    if b % 4 in (1, 3): add(total, snare(), bt)
                    add(total, hat(), bt); add(total, hat(0.035), bt + beat / 2 + swing * beat / 2)
        tpos += dur; ci += 1
    total = total[: int(length * SR)]
    total += rng.normal(0, 0.0025, len(total))  # 아주 옅은 바늘 소리
    fade = int(2.0 * SR)
    total[:int(0.3 * SR)] *= np.linspace(0, 1, int(0.3 * SR))
    total[-fade:] *= np.linspace(1, 0, fade)
    total /= max(1e-9, np.abs(total).max()) / 0.8
    return total


def save(sig, name):
    OUT.mkdir(exist_ok=True)
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        tmp = f.name
    with wave.open(tmp, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        # 좌우를 아주 조금 다르게 해 넓게 들리게
        left = sig; right = np.roll(sig, int(0.008 * SR))
        st = np.stack([left, right], 1)
        w.writeframes((st * 32767).astype("<i2").tobytes())
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", tmp, "-c:a", "aac", "-b:a", "160k", str(OUT / f"{name}.m4a")], check=True)
    pathlib.Path(tmp).unlink()
    print("완료:", OUT / f"{name}.m4a")


if __name__ == "__main__":
    # C장조 기반: Cmaj7 – Am7 – Fmaj7 – G6
    warm = [[60, 64, 67, 71], [57, 60, 64, 67], [53, 57, 60, 64], [55, 59, 62, 64]]
    bright = [[62, 66, 69, 73], [59, 62, 66, 69], [55, 59, 62, 66], [57, 61, 64, 69]]   # D장조
    calm = [[57, 60, 64, 67], [53, 57, 60, 64], [48, 52, 55, 59], [55, 59, 62, 65]]    # 차분한 단조 느낌
    save(song(warm, 84, 1, drums=True, swing=0.33, seed=3), "warm")
    save(song(bright, 104, 1, drums=True, swing=0.0, seed=5), "bright")
    save(song(calm, 70, 1, drums=False, arp=True, pad_amp=0.14, seed=9), "calm")
    # pulse: 118BPM, 박자에 맞춰 카드가 넘어가는 역동적인 릴스용 (기본)
    pulse = [[57, 60, 64, 69], [53, 57, 60, 65], [48, 52, 55, 60], [55, 59, 62, 67]]   # Am – F – C – G
    save(song(pulse, 118, 1, drums=True, swing=0.0, pad_amp=0.10, seed=11, length=26.0, punch=True), "pulse")
