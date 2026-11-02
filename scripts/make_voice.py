"""한국어 내레이션 만들기 (0원, 공개 음성 엔진 MeloTTS · MIT 라이선스, 대표 결정 2026-11-02 영상 콘텐츠).

GitHub Actions 「내레이션 만들기」(.github/workflows/make_voice.yml)에서 돈다(모델 내려받기에 인터넷 필요).
입력: voice/<이름>.txt — 한 줄 = 자막 한 장면. "자막 || 읽는 글" 로 쓰면 자막과 읽기를 나눈다(숫자는 읽는 글에 한글로). 빈 줄은 무시.
출력: assets/voice/<이름>/NN.wav (줄마다) + assets/voice/<이름>/lines.json [{i, text, sec}]
나중에 대표 목소리로 바꿀 때는 같은 이름으로 NN.wav 만 바꿔 넣으면 된다.
"""
import json, os, pathlib, wave

ROOT = pathlib.Path(__file__).resolve().parent.parent


def main():
    name = os.environ["VOICE_NAME"]
    speed = float(os.environ.get("VOICE_SPEED", "1.1"))
    src = ROOT / "voice" / f"{name}.txt"
    lines = [x.strip() for x in src.read_text(encoding="utf-8").splitlines() if x.strip()]
    out = ROOT / "assets" / "voice" / name
    out.mkdir(parents=True, exist_ok=True)
    from melo.api import TTS
    model = TTS(language="KR", device="cpu")
    spk = model.hps.data.spk2id["KR"]
    meta = []
    for i, line in enumerate(lines, 1):
        t, _, say = line.partition("||")
        t, say = t.strip(), (say.strip() or t.strip())
        p = out / f"{i:02d}.wav"
        model.tts_to_file(say, spk, str(p), speed=speed)
        with wave.open(str(p)) as w:
            sec = w.getnframes() / w.getframerate()
        meta.append({"i": i, "text": t, "sec": round(sec, 2)})
        print(i, round(sec, 2), t)
    (out / "lines.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
