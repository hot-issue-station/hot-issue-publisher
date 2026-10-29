"""카드 문구(round JSON)로 카드 7장(JPG)과 게시 묶음을 만든다.

사용법:  python scripts/make_post.py rounds/20261028_PM.json [--approve3 "대표 (채팅 승인)"]
결과:    posts/YYYYMMDD_SLOT/01.jpg … 07.jpg, caption.txt, post.json

round JSON 형식(모든 문구는 승인 2를 거친 최종 문구):
{
  "date": "2026-10-28", "slot": "PM",            # AM 출근 07:30 · PM 점심 12:00 · NT 퇴근 18:30 · RS 리센느 응원 특집 20:00
  "category": "국내",                             # 1장 분야 태그
  "hook": "…", "sub": "…",                        # 1장 (훅에 \n을 넣으면 그 자리에서 줄바꿈)
  "big": {"number": "25", "lines": ["년 만의", "*잉글랜드*", "발롱도르"],   # 1장 C안(기본): 가장 강한 숫자 강조
          "caption": "해리 케인, 생애 첫 수상", "icon": "trophy"},   # icon: trophy ball wave shark star heart globe chart music
  "summary": "…",                                 # 2장
  "facts": [{"title": "…", "desc": "…", "source": "경향신문 · 2026.10.27"}, ×3],   # 3~5장
  "interp": "…", "interpSub": "…",                # 6장
  "sources": [{"outlet": "…", "title": "…", "date": "2026.10.27", "url": "https://…"}],  # 7장
  "cta": "… 저장해 두세요",                        # 7장 유도 문구
  "caption": "…",                                 # 해시태그 포함 캡션 전체
  "music": "pulse",                                # 릴스 배경음: pulse(기본) warm bright calm 또는 music/ 폴더의 다른 곡 이름
  "topic": "…"
}
카드 모양은 카드 템플릿 캔버스(케인 AM 시험 카드)와 같다. 글꼴: Noto Sans CJK KR.
"""
import argparse
import html
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SLOTS = {"AM": ("출근길", "07:30"), "PM": ("점심", "12:00"), "NT": ("퇴근길", "18:30"), "RS": ("리센느 응원 특집", "20:00")}
NAVY, CYAN, PINK, VIOLET = "#0B1220", "#35E0FF", "#FF4FA3", "#6C7BFF"
# 회차별 템플릿(색 묶음): 출근길은 해 뜨는 아침(크림+주황), 점심은 산뜻한 민트(민트+초록), 퇴근길은 밤(남색+청록, 기본)
THEMES = {
    "NT": dict(BG="#0B1220", BGRGB="11,18,32", INK="#F4F7FF", MUTED="#A9B6CF", SOFT="#C9D4EA", BODY="#D7E0F2", LINE="#2A3A59",
               BOX="#151F33", CYAN="#35E0FF", PINK="#FF4FA3", VIOLET="#6C7BFF", ONACC="#0B1220", ONACC2="#123049"),
    "AM": dict(BG="#FFF8EE", BGRGB="255,248,238", INK="#15233D", MUTED="#7A7F8C", SOFT="#3C4458", BODY="#2A3245", LINE="#EADFCB",
               BOX="#FFFFFF", CYAN="#FF7A3D", PINK="#1FB5A9", VIOLET="#FFC24B", ONACC="#FFFFFF", ONACC2="#FFF1E4"),
    "PM": dict(BG="#EAF7F2", BGRGB="234,247,242", INK="#0F2A2A", MUTED="#5E7C77", SOFT="#24443F", BODY="#1E3A36", LINE="#CDE6DE",
               BOX="#FFFFFF", CYAN="#00A88F", PINK="#FF5C8A", VIOLET="#FFC24B", ONACC="#FFFFFF", ONACC2="#E8FFF8"),
    # 리센느 데일리(20:00, 2026-10-29~12-31 고정 코너): 보랏빛 밤. 로고·멤버 사진 없이 색으로만 코너를 구분한다.
    "RS": dict(BG="#140F24", BGRGB="20,15,36", INK="#F6F2FF", MUTED="#B3A8CF", SOFT="#D6CCF0", BODY="#E2DAF7", LINE="#33285A",
               BOX="#1E1736", CYAN="#B98CFF", PINK="#FF7FB6", VIOLET="#7FD4FF", ONACC="#140F24", ONACC2="#2A2050"),
}
BG = BGRGB = INK = MUTED = SOFT = BODY = LINE = BOX = ONACC = ONACC2 = None


def apply_theme(slot):
    """회차(AM/PM/NT)에 맞는 색 묶음을 적용한다. round JSON에 "theme"이 있으면 그것을 쓴다."""
    g = globals()
    for k, v in THEMES.get(slot, THEMES["NT"]).items():
        g[k] = v


apply_theme("NT")
LOGO = ('<svg width="68" height="68" viewBox="0 0 68 68" style="display:block">'
        '<path d="M25.51 43.51 A12 12 0 0 1 42.49 43.51" fill="none" stroke="#35E0FF" stroke-width="5" stroke-linecap="round"/>'
        '<path d="M18.44 36.44 A22 22 0 0 1 49.56 36.44" fill="none" stroke="#6C7BFF" stroke-width="5" stroke-linecap="round"/>'
        '<path d="M11.37 29.37 A32 32 0 0 1 56.63 29.37" fill="none" stroke="#FF4FA3" stroke-width="5" stroke-linecap="round"/>'
        '<circle cx="34" cy="52" r="5" fill="#FFC857"/></svg>')
E = html.escape


# 화면 틀: 피드 카드(1080×1350)와 릴스(1080×1920). 릴스는 Instagram 화면 위 글자·버튼에 가리지 않게
# 위 240px, 아래 440px, 오른쪽 160px(좋아요·댓글 버튼 자리)을 비운다.
LAYOUT = {"h": 1350, "pad": "96px"}
FEED = {"h": 1350, "pad": "96px"}
REEL = {"h": 1920, "pad": "240px 160px 440px 90px"}


def frame(inner, date_label, page, footer_right="", light=False, deco="", total=7):
    bg, fg, muted = (CYAN, ONACC, ONACC2) if light else (BG, INK, MUTED)
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
body{{margin:0;word-break:keep-all;font-family:'Noto Sans CJK KR','Noto Sans KR',sans-serif}}</style></head><body>
<div style="position:relative;width:1080px;height:{LAYOUT['h']}px;overflow:hidden;background:{bg};color:{fg}">{deco}
<div style="position:relative;width:100%;height:100%;box-sizing:border-box;padding:{LAYOUT['pad']};display:flex;flex-direction:column">
<div style="display:flex;justify-content:space-between;align-items:center">
<div style="display:flex;align-items:center;gap:20px">{LOGO}<div style="font-size:36px;font-weight:700;color:{fg}">hot.issue.station</div></div>
<div style="font-size:32px;color:{muted}">{date_label}</div></div>
{inner}
<div style="display:flex;justify-content:space-between;align-items:center;font-size:32px;color:{muted}">
<div>{page} / {total}</div><div>{footer_right}</div></div></div></div></body></html>"""


def rings(colors, sizes, offset_ratio=0.5):
    out = ""
    for c, s in zip(colors, sizes):
        off = int(s * offset_ratio)
        out += (f'<div style="position:absolute;right:-{off}px;bottom:-{off}px;width:{s}px;height:{s}px;'
                f'box-sizing:border-box;border-radius:50%;border:6px solid {c}"></div>')
    return out


def dots(i):
    return "".join(f'<div style="width:24px;height:24px;border-radius:50%;background:{CYAN if k == i else LINE}"></div>'
                   for k in range(3))

# 야구공(직접 그린 그림). 맞대결 표지와 1장 그림에 쓴다.
BASEBALL_SVG = ('<svg viewBox="0 0 120 120" width="120" height="120"><circle cx="60" cy="60" r="54" fill="#FFFFFF" stroke="#D5DEEA" stroke-width="3"/>'
                '<path d="M28 18c16 24 16 60 0 84M92 18c-16 24-16 60 0 84" fill="none" stroke="#E0453A" stroke-width="4"/>'
                '<path d="M26 30l8-3M30 44l8-2M31 58h8M30 72l8 2M26 86l8 3M94 30l-8-3M90 44l-8-2M89 58h-8M90 72l-8 2M94 86l-8 3" stroke="#E0453A" stroke-width="3" stroke-linecap="round"/></svg>')

# 1장 C안(숫자 강조)에 쓰는 작은 그림. 실존 인물 사진 대신 Claude가 그린 그림만 쓴다.
ICONS = {
    "trophy": '<svg viewBox="0 0 400 460" width="120" height="138"><path d="M90 40H310V110C310 200 260 250 200 260 140 250 90 200 90 110Z" fill="#FFC857"/><path d="M90 70H40C40 150 80 180 120 185M310 70H360C360 150 320 180 280 185" fill="none" stroke="#FFC857" stroke-width="18" stroke-linecap="round"/><rect x="180" y="255" width="40" height="70" fill="#E0A030"/><rect x="120" y="320" width="160" height="40" rx="8" fill="#FFC857"/><rect x="95" y="360" width="210" height="60" rx="10" fill="#151F33" stroke="#35E0FF" stroke-width="6"/><path d="M200 105l12 26 28 3-21 19 6 28-25-14-25 14 6-28-21-19 28-3z" fill="#FFF6D6"/></svg>',
    "ball": '<svg viewBox="0 0 120 120" width="120" height="120"><circle cx="60" cy="60" r="54" fill="#F4F7FF"/><path d="M60 30l26 19-10 30H44L34 49z" fill="#0B1220"/><path d="M60 30V8M86 49l20-9M76 79l14 22M44 79L30 101M34 49L14 40" stroke="#0B1220" stroke-width="5"/></svg>',
    "wave": '<svg viewBox="0 0 140 120" width="140" height="120"><path d="M10 70c20-20 40-20 60 0s40 20 60 0" fill="none" stroke="#35E0FF" stroke-width="10" stroke-linecap="round"/><path d="M10 95c20-20 40-20 60 0s40 20 60 0" fill="none" stroke="#6C7BFF" stroke-width="10" stroke-linecap="round"/><path d="M50 52L78 14 92 52z" fill="#A9B6CF"/></svg>',
    "shark": '<svg viewBox="0 0 320 180" width="300" height="169"><path d="M0 150c30-14 60-14 90 0s60 14 90 0 60-14 90 0 40 10 50 6" fill="none" stroke="#6C7BFF" stroke-width="8" stroke-linecap="round"/><path d="M30 120c40-46 120-62 190-40 30 10 52 24 70 40-30 8-66 14-104 12-60-2-110-6-156-12z" fill="#7F93B8"/><path d="M40 118c60 8 130 12 200 6 18-2 34-5 48-8-26 14-70 24-120 24-50 0-92-10-128-22z" fill="#DCE6F5"/><path d="M128 74l28-58 22 64z" fill="#7F93B8"/><path d="M30 120l-26-34 10 40-14 26 30-26z" fill="#7F93B8"/><circle cx="248" cy="106" r="5" fill="#0B1220"/><path d="M262 120c-8 4-18 5-28 4" stroke="#0B1220" stroke-width="3" fill="none" stroke-linecap="round"/><path d="M200 104l4 14M190 104l4 14M180 104l4 14" stroke="#5A6E92" stroke-width="3" stroke-linecap="round"/><path d="M0 168c30-14 60-14 90 0s60 14 90 0 60-14 90 0 40 10 50 6" fill="none" stroke="#35E0FF" stroke-width="8" stroke-linecap="round"/></svg>',
    "star": '<svg viewBox="0 0 120 120" width="120" height="120"><path d="M60 8l15 33 36 4-27 24 8 36-32-19-32 19 8-36L9 45l36-4z" fill="#FFC857"/></svg>',
    "heart": '<svg viewBox="0 0 120 110" width="120" height="110"><path d="M60 104S8 72 8 36C8 18 22 6 38 6c10 0 18 6 22 14 4-8 12-14 22-14 16 0 30 12 30 30 0 36-52 68-52 68z" fill="#FF4FA3"/></svg>',
    "globe": '<svg viewBox="0 0 120 120" width="120" height="120"><circle cx="60" cy="60" r="52" fill="none" stroke="#35E0FF" stroke-width="7"/><ellipse cx="60" cy="60" rx="24" ry="52" fill="none" stroke="#35E0FF" stroke-width="6"/><path d="M10 60h100M18 32h84M18 88h84" stroke="#35E0FF" stroke-width="6"/></svg>',
    "chart": '<svg viewBox="0 0 120 120" width="120" height="120"><rect x="12" y="70" width="22" height="40" rx="4" fill="#6C7BFF"/><rect x="49" y="45" width="22" height="65" rx="4" fill="#FF4FA3"/><rect x="86" y="15" width="22" height="95" rx="4" fill="#35E0FF"/></svg>',
    "music": '<svg viewBox="0 0 120 120" width="120" height="120"><path d="M45 20l60-12v70" fill="none" stroke="#FF4FA3" stroke-width="8"/><path d="M45 20v72" stroke="#FF4FA3" stroke-width="8"/><ellipse cx="33" cy="94" rx="16" ry="12" fill="#FF4FA3"/><ellipse cx="93" cy="80" rx="16" ry="12" fill="#FF4FA3"/></svg>',
    "baseball": BASEBALL_SVG,
}


def accent_html(line):
    """*단어*는 분홍색으로 강조한다."""
    import re
    return re.sub(r"\*(.+?)\*", lambda m: f'<span style="color:{PINK}">{m.group(1)}</span>', E(line))


def cover_big(r, label):
    """1장 C안: 가장 강한 숫자를 크게. round JSON의 "big" 사용."""
    b = r["big"]
    lines = "<br>".join(accent_html(x) for x in b.get("lines", []))
    n = E(b["number"])
    size = 300 if len(b["number"]) <= 2 else 240 if len(b["number"]) <= 3 else 190
    icon = ICONS.get(b.get("icon", "star"), ICONS["star"])
    cap = E(b.get("caption", r.get("sub", "")))
    return frame(f"""<div style="flex:1;display:flex;flex-direction:column;justify-content:center;gap:30px">
<div style="align-self:flex-start;padding:12px 28px;border:3px solid {CYAN};border-radius:999px;color:{CYAN};font-size:34px;font-weight:700">{E(r['category'])}</div>
<div style="display:flex;align-items:center;gap:30px"><div style="font-size:{size}px;font-weight:900;line-height:.9;color:{CYAN};letter-spacing:-4px">{n}</div>
<div style="font-size:64px;font-weight:900;line-height:1.2">{lines}</div></div>
<div style="font-size:84px;font-weight:900;line-height:1.2">{hook_html(r['hook'])}</div>
<div style="display:flex;align-items:center;gap:24px">{icon}<div style="font-size:42px;color:{SOFT};line-height:1.45">{cap}</div></div></div>""" if b.get("icon") != "shark" else f"""<div style="flex:1;display:flex;flex-direction:column;justify-content:center;gap:30px">
<div style="align-self:flex-start;padding:12px 28px;border:3px solid {CYAN};border-radius:999px;color:{CYAN};font-size:34px;font-weight:700">{E(r['category'])}</div>
<div style="display:flex;align-items:center;gap:30px"><div style="font-size:{size}px;font-weight:900;line-height:.9;color:{CYAN};letter-spacing:-4px">{n}</div>
<div style="font-size:64px;font-weight:900;line-height:1.2">{lines}</div></div>
<div style="font-size:84px;font-weight:900;line-height:1.2">{hook_html(r['hook'])}</div>
<div style="display:flex;align-items:flex-end;gap:24px">{icon.replace('width="300" height="169"','width="400" height="225"')}<div style="font-size:40px;color:{SOFT};line-height:1.45">{cap}</div></div></div>""",
                 label, 1, "밀어서 다음 장 →")


def cover_vs(r, label):
    """1장 맞대결 표지: 두 팀(또는 두 선수·두 나라)을 팀 색으로 나눠 이름을 크게. 로고·실제 사진은 쓰지 않는다.
    round JSON "vs": {"left": "삼성", "right": "KIA", "leftColor": "#1E5BC6", "rightColor": "#D7263D",
                      "center": "VS" 또는 "3 : 2" 같은 점수, "caption": 띠 아래 한 줄(선택)}"""
    v = r["vs"]
    reel = LAYOUT["h"] > 1500
    top, bh = (330, 760) if reel else (170, 600)
    lc, rc = v.get("leftColor", "#1E5BC6"), v.get("rightColor", "#D7263D")
    def name_size(t):
        n = len(t)
        return 150 if n <= 2 else 124 if n <= 3 else 100 if n <= 4 else 80
    L, R = v.get("left", ""), v.get("right", "")
    center = E(v.get("center", "VS") or "VS")
    csz = 92 if len(v.get("center", "VS") or "VS") <= 2 else 64 if len(v.get("center", "")) <= 5 else 48
    mid = top + bh // 2
    ball = BASEBALL_SVG.replace('width="120" height="120"', 'width="92" height="92"') if v.get("icon", "baseball") == "baseball" else ""
    deco = (f'<div style="position:absolute;left:0;top:{top}px;width:1080px;height:{bh}px;background:{lc};clip-path:polygon(0 0,590px 0,490px 100%,0 100%)"></div>'
            f'<div style="position:absolute;left:0;top:{top}px;width:1080px;height:{bh}px;background:{rc};clip-path:polygon(590px 0,1080px 0,1080px 100%,490px 100%)"></div>'
            f'<div style="position:absolute;left:0;top:{top}px;width:1080px;height:{bh}px;background:linear-gradient(180deg,rgba(0,0,0,0) 60%,rgba(0,0,0,.18) 100%)"></div>'
            f'<div style="position:absolute;left:40px;width:480px;top:{mid - 120}px;text-align:center;color:#FFFFFF;font-size:{name_size(L)}px;font-weight:900;line-height:1;letter-spacing:-2px;text-shadow:0 6px 24px rgba(0,0,0,.25)">{E(L)}</div>'
            f'<div style="position:absolute;right:40px;width:480px;top:{mid - 120}px;text-align:center;color:#FFFFFF;font-size:{name_size(R)}px;font-weight:900;line-height:1;letter-spacing:-2px;text-shadow:0 6px 24px rgba(0,0,0,.25)">{E(R)}</div>'
            f'<div style="position:absolute;left:{540 - 110}px;top:{mid + 30}px;width:220px;height:220px;border-radius:50%;background:#FFFFFF;box-shadow:0 10px 40px rgba(0,0,0,.25);display:flex;align-items:center;justify-content:center;color:#0B1220;font-size:{csz}px;font-weight:900;letter-spacing:-2px">{center}</div>'
            f'<div style="position:absolute;left:{540 - 46}px;top:{mid - 210}px">{ball}</div>')
    cap = E(v.get("caption", ""))
    sub = E(r.get("sub", ""))
    return frame(f"""<div style="flex:1;display:flex;flex-direction:column;justify-content:flex-end;gap:22px;padding-bottom:20px">
<div style="align-self:flex-start;padding:10px 26px;border:3px solid {CYAN};border-radius:999px;color:{CYAN};font-size:32px;font-weight:700">{E(r['category'])}</div>
{f'<div style="font-size:40px;font-weight:700;color:{SOFT}">{cap}</div>' if cap else ''}
<div style="font-size:80px;font-weight:900;line-height:1.2">{hook_html(r.get("hookCover", r["hook"]))}</div>
{f'<div style="font-size:42px;line-height:1.45;color:{SOFT}">{sub}</div>' if sub and not cap else ''}</div>""", label, 1, "밀어서 다음 장 →", deco=deco)


def photo_uri(path):
    import base64, mimetypes
    pth = pathlib.Path(path)
    if not pth.is_absolute():
        pth = ROOT / pth
    mt = mimetypes.guess_type(str(pth))[0] or "image/jpeg"
    return f"data:{mt};base64," + base64.b64encode(pth.read_bytes()).decode()


def inset_html(r, ph, reel):
    """1장 사진형 표지 안의 작은 사진(예: 가운데는 한 멤버, 오른쪽 아래 작은 칸에 단체 사진).
    round JSON: "photoInset": 파일 경로, "photoInsetPos": 배경 위치, "photoInsetLabel": 작은 칸 아래 글(예: "RESCENE 다섯 멤버")."""
    if not r.get("photoInset"):
        return ""
    w, h = (300, 200) if reel else (330, 220)
    right = 180 if reel else 40
    top = ph + 10   # 사진 칸 바로 아래 오른쪽(얼굴을 가리지 않게)
    lab = E(r.get("photoInsetLabel", ""))
    return (f'<div style="position:absolute;right:{right}px;top:{top}px;width:{w}px;height:{h}px;border-radius:22px;overflow:hidden;'
            f'border:4px solid {CYAN};box-shadow:0 12px 40px rgba(0,0,0,.45);background:url({photo_uri(r["photoInset"])}) {r.get("photoInsetPos", "50% 50%")}/cover no-repeat">'
            + (f'<div style="position:absolute;left:0;right:0;bottom:0;padding:8px 14px;background:linear-gradient(0deg,rgba({BGRGB},.85),rgba({BGRGB},0));color:{INK};font-size:22px;font-weight:700">{lab}</div>' if lab else "")
            + '</div>')


def cover_photo(r, label):
    """1장 사진형: 위쪽에 사진(권리 있는 사진 또는 AI 생성 이미지), 아래로 남색에 녹아들고 큰 숫자 + 훅.
    round JSON: "photo": 파일 경로, "photoLabel": 사진 위 작은 표기(예: "AI 생성 이미지"), "photoPos": 배경 위치(예: "50% 40%"),
    "hookCover": 1장 전용 훅(\n 줄바꿈). 숫자 장식은 "big"을 그대로 쓴다."""
    b = r.get("big") or {}
    reel = LAYOUT["h"] > 1500
    ph = 1000 if reel else (640 if r.get("photoInset") else 620)
    uri = photo_uri(r["photo"])
    pos = r.get("photoPos", "50% 45%")
    tag = E(r.get("photoLabel", ""))
    deco = (f'<div style="position:absolute;left:0;top:0;width:1080px;height:{ph}px;background:url({uri}) {pos}/cover no-repeat"></div>'
            f'<div style="position:absolute;left:0;top:0;width:1080px;height:{ph}px;background:linear-gradient(180deg,rgba({BGRGB},.92) 0%,rgba({BGRGB},.7) 14%,rgba({BGRGB},0) 32%,rgba({BGRGB},0) 55%,{BG} 100%)"></div>'
            + (f'<div style="position:absolute;right:{180 if reel else 40}px;top:{ph - (300 if reel else 250)}px;padding:8px 18px;border-radius:999px;background:rgba({BGRGB},.7);color:{SOFT};font-size:24px">{tag}</div>' if tag else "")
            + inset_html(r, ph, reel))
    n = E(b.get("number", ""))
    size = 190 if len(b.get("number", "")) <= 2 else 160
    lines = "<br>".join(accent_html(x) for x in b.get("lines", []))
    numrow = (f'<div style="display:flex;align-items:center;gap:26px"><div style="font-size:{size}px;font-weight:900;line-height:.9;color:{CYAN};letter-spacing:-4px">{n}</div>'
              f'<div style="font-size:52px;font-weight:900;line-height:1.2">{lines}</div></div>') if n else ""
    hook = hook_html(r.get("hookCover", r["hook"]))
    return frame(f"""<div style="flex:1;display:flex;flex-direction:column;justify-content:flex-end;gap:22px;padding-bottom:24px">
<div style="align-self:flex-start;padding:10px 26px;border:3px solid {CYAN};border-radius:999px;color:{CYAN};font-size:32px;font-weight:700;background:rgba({BGRGB},.6)">{E(r['category'])}</div>
{numrow}
<div style="font-size:72px;font-weight:900;line-height:1.2">{hook}</div></div>""", label, 1, "밀어서 다음 장 →", deco=deco)


def hook_html(h):
    """줄바꿈(\n)을 넣은 훅은 그대로, 아니면 첫 쉼표 뒤에서 한 번 줄을 바꾼다."""
    if "\n" in h:
        return "<br>".join(E(x) for x in h.split("\n"))
    return E(h).replace(", ", ",<br>", 1) if len(h) > 9 else E(h)


def cards(r):
    apply_theme(r.get("theme", r["slot"]))
    m, d = r["date"][5:7], r["date"][8:10]
    label = f"{m}.{d} · {SLOTS[r['slot']][0]}"
    out = []
    # 1 훅 — "big"이 있으면 C안(숫자 강조), 없으면 기본형
    if r.get("photo"):
        out.append(cover_photo(r, label))
    elif r.get("vs"):
        out.append(cover_vs(r, label))
    elif r.get("big"):
        out.append(cover_big(r, label))
    else:
      out.append(frame(f"""<div style="flex:1;display:flex;flex-direction:column;justify-content:center;gap:48px">
<div style="align-self:flex-start;padding:14px 32px;border:3px solid {CYAN};border-radius:999px;color:{CYAN};font-size:36px;font-weight:700">{E(r['category'])}</div>
<div style="font-size:108px;font-weight:900;line-height:1.25">{hook_html(r['hook'])}</div>
<div style="display:flex;gap:12px"><div style="width:160px;height:16px;border-radius:8px;background:{CYAN}"></div><div style="width:48px;height:16px;border-radius:8px;background:{PINK}"></div></div>
<div style="font-size:52px;font-weight:500;line-height:1.5;color:{SOFT};max-width:760px">{E(r['sub'])}</div></div>""",
                     label, 1, "밀어서 다음 장 →", deco=rings([VIOLET, PINK, CYAN], [900, 680, 460])))
    # 2 요약 — "summaryPhotos"(사진 경로 목록, 최대 5장)가 있으면 요약 위에 사진 줄을 놓는다
    sp = r.get("summaryPhotos") or []
    if sp:
        n = len(sp[:5])
        tw = (1080 - 192 - 16 * (n - 1)) // n
        row = "".join(f'<div style="width:{tw}px;height:{int(tw * 1.45)}px;border-radius:24px;background:url({photo_uri(x)}) 50% 20%/cover no-repeat;border:2px solid {LINE}"></div>' for x in sp[:5])
        tag = f'<div style="font-size:28px;color:{MUTED}">{E(r.get("summaryPhotosLabel", ""))}</div>' if r.get("summaryPhotosLabel") else ""
        out.append(frame(f"""<div style="flex:1;display:flex;flex-direction:column;justify-content:center;gap:30px">
<div style="display:flex;align-items:center;gap:20px"><div style="width:64px;height:8px;border-radius:4px;background:{PINK}"></div><div style="font-size:44px;font-weight:700;color:{CYAN}">한 줄 요약</div></div>
<div style="display:flex;flex-direction:column;gap:10px"><div style="display:flex;gap:16px">{row}</div>{tag}</div>
<div style="padding:52px 60px;border:3px solid {LINE};border-radius:40px;background:{BOX}"><div style="font-size:58px;font-weight:700;line-height:1.45">{E(r['summary'])}</div></div></div>""", label, 2))
    else:
        out.append(frame(f"""<div style="flex:1;display:flex;flex-direction:column;justify-content:center;gap:40px">
<div style="display:flex;align-items:center;gap:20px"><div style="width:64px;height:8px;border-radius:4px;background:{PINK}"></div><div style="font-size:44px;font-weight:700;color:{CYAN}">한 줄 요약</div></div>
<div style="padding:80px 72px;border:3px solid {LINE};border-radius:40px;background:{BOX}"><div style="font-size:72px;font-weight:700;line-height:1.45">{E(r['summary'])}</div></div>
<div style="font-size:44px;line-height:1.5;color:{SOFT}">이어서 핵심 사실 3가지를 알려드려요 →</div></div>""", label, 2))
    # 3~5 사실 — 사실마다 "photo"(경로), "photoPos", "photoLabel"이 있으면 위쪽에 사진 칸을 놓는다
    for i, f in enumerate(r["facts"][:3]):
        if f.get("photo"):
            ftag = (f'<div style="position:absolute;right:16px;bottom:16px;padding:6px 14px;border-radius:999px;background:rgba({BGRGB},.75);color:{SOFT};font-size:24px">{E(f["photoLabel"])}</div>' if f.get("photoLabel") else "")
            out.append(frame(f"""<div style="flex:1;display:flex;flex-direction:column;justify-content:center;gap:24px">
<div style="position:relative;height:430px;border-radius:32px;overflow:hidden;background:url({photo_uri(f['photo'])}) {f.get('photoPos', '50% 25%')}/cover no-repeat">{ftag}</div>
<div style="display:flex;align-items:baseline;gap:20px"><div style="font-size:96px;font-weight:900;line-height:1;color:{CYAN}">{i + 1:02d}</div><div style="font-size:36px;font-weight:700;color:{MUTED}">핵심 사실</div></div>
<div style="font-size:58px;font-weight:900;line-height:1.3">{E(f['title'])}</div>
<div style="font-size:42px;line-height:1.55;color:{BODY}">{E(f['desc'])}</div>
<div style="font-size:32px;color:{MUTED}">출처 {E(f['source'])}</div></div>""",
                             label, 3 + i, f'<div style="display:flex;gap:16px">{dots(i)}</div>'))
            continue
        out.append(frame(f"""<div style="flex:1;display:flex;flex-direction:column;justify-content:center;gap:32px">
<div style="display:flex;align-items:baseline;gap:24px"><div style="font-size:140px;font-weight:900;line-height:1;color:{CYAN}">{i + 1:02d}</div><div style="font-size:40px;font-weight:700;color:{MUTED}">핵심 사실</div></div>
<div style="font-size:68px;font-weight:900;line-height:1.35">{E(f['title'])}</div>
<div style="width:100%;height:2px;background:{LINE}"></div>
<div style="font-size:48px;line-height:1.65;color:{BODY}">{E(f['desc'])}</div>
<div style="font-size:36px;color:{MUTED}">출처 {E(f['source'])}</div></div>""",
                         label, 3 + i, f'<div style="display:flex;gap:16px">{dots(i)}</div>'))
    # 6 해석
    out.append(frame(f"""<div style="flex:1;display:flex;flex-direction:column;justify-content:center;gap:36px">
<div style="font-size:48px;font-weight:900">그래서, 나에게는?</div>
<div style="font-size:84px;font-weight:900;line-height:1.35">{E(r['interp'])}</div>
<div style="font-size:46px;font-weight:500;line-height:1.55;color:{ONACC2}">{E(r['interpSub'])}</div></div>""",
                     label, 6, light=True, deco=rings([ONACC] * 3, [640, 440, 240])))
    # 7 출처
    nums = "①②③④"
    src = "".join(f'<div style="padding:22px 0;border-bottom:2px solid {LINE};font-size:36px;line-height:1.4;color:{BODY}">'
                  f'{nums[k]} {E(s["outlet"])} · {E(s["title"])} · {E(s["date"])}</div>' for k, s in enumerate(r["sources"][:4]))
    out.append(frame(f"""<div style="flex:1;display:flex;flex-direction:column;justify-content:center;gap:36px">
<div style="display:flex;align-items:center;gap:20px"><div style="width:64px;height:8px;border-radius:4px;background:{PINK}"></div><div style="font-size:44px;font-weight:700;color:{CYAN}">출처</div></div>
<div style="display:flex;flex-direction:column">{src}</div>
<div style="padding:56px 64px;border:3px solid {CYAN};border-radius:40px;background:{BOX};display:flex;flex-direction:column;gap:32px">
<div style="font-size:60px;font-weight:900;line-height:1.35">{E(r['cta'])}</div>
<div style="display:flex;gap:24px"><div style="padding:20px 56px;border-radius:999px;background:{CYAN};color:{ONACC};font-size:48px;font-weight:900">저장</div>
<div style="padding:20px 56px;border-radius:999px;background:{PINK};color:{ONACC};font-size:48px;font-weight:900">팔로우</div></div></div>
<div style="font-size:32px;line-height:1.5;color:{MUTED}">광고·협찬 없음</div></div>""", label, 7, "매일 따뜻한 이슈는 @hot.issue.station"))
    return out


def cards_read(r):
    """읽는 카드뉴스(대표 결정 10/28): 1장 강한 표지 + 3줄 요약 + 기사형 본문 3~5장 + 출처·저장.
    round JSON의 "read": {"lead": [3줄], "sections": [{"kicker","title","body"(260자 이내)}, …3~5개]}."""
    rd = r["read"]
    secs = rd["sections"][:5]
    total = 3 + len(secs)
    apply_theme(r.get("theme", r["slot"]))
    m, d = r["date"][5:7], r["date"][8:10]
    label = f"{m}.{d} · {SLOTS[r['slot']][0]}"
    cover = cards(r)[0].replace("<div>1 / 7</div>", f"<div>1 / {total}</div>")
    out = [cover]
    lead = "".join(f'<div style="display:flex;gap:28px;align-items:flex-start"><div style="flex:none;width:20px;height:20px;margin-top:26px;border-radius:50%;background:{CYAN if k == 0 else PINK if k == 1 else VIOLET}"></div>'
                   f'<div style="font-size:54px;font-weight:700;line-height:1.5">{E(x)}</div></div>' for k, x in enumerate(rd["lead"][:3]))
    out.append(frame(f"""<div style="flex:1;display:flex;flex-direction:column;justify-content:center;gap:56px">
<div style="font-size:40px;font-weight:700;color:{CYAN}">3줄 요약</div>{lead}
<div style="font-size:38px;color:{MUTED}">넘기면서 천천히 읽어 보세요 →</div></div>""", label, 2, total=total))
    for i, sec in enumerate(secs):
        out.append(frame(f"""<div style="flex:1;display:flex;flex-direction:column;justify-content:center;gap:36px">
<div style="font-size:38px;font-weight:700;color:{PINK}">{E(sec.get("kicker", ""))}</div>
<div style="font-size:64px;font-weight:900;line-height:1.35">{E(sec["title"])}</div>
<div style="width:120px;height:8px;border-radius:4px;background:{CYAN}"></div>
<div style="font-size:44px;line-height:1.8;color:{BODY}">{E(sec["body"])}</div></div>""", label, 3 + i, total=total))
    nums = "①②③④"
    src = "".join(f'<div style="padding:20px 0;border-bottom:2px solid {LINE};font-size:34px;line-height:1.4;color:{BODY}">'
                  f'{nums[k]} {E(s_["outlet"])} · {E(s_["title"])} · {E(s_["date"])}</div>' for k, s_ in enumerate(r["sources"][:4]))
    out.append(frame(f"""<div style="flex:1;display:flex;flex-direction:column;justify-content:center;gap:36px">
<div style="font-size:40px;font-weight:700;color:{CYAN}">출처</div>
<div style="display:flex;flex-direction:column">{src}</div>
<div style="padding:52px 60px;border:3px solid {CYAN};border-radius:40px;background:{BOX};display:flex;flex-direction:column;gap:20px">
<div style="font-size:56px;font-weight:900;line-height:1.35">저장해 두고 다시 읽어 보세요</div>
<div style="font-size:38px;line-height:1.5;color:{SOFT}">매일 이슈를 짧은 릴스와 읽는 카드로 정리해요</div></div></div>""",
                     label, total, "@hot.issue.station", total=total))
    return out


def render(pages, outdir, h=1350, prefix=""):
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 1080, "height": h})
        overflow = []
        for i, h in enumerate(pages, 1):
            pg.set_content(h)
            pg.wait_for_timeout(200)
            # 글이 칸을 넘치면(세로 넘침) 알려 준다
            if pg.evaluate("Array.from(document.querySelectorAll('div')).some(d => d.style.flex.startsWith('1') && d.scrollHeight > d.clientHeight + 2)"):
                overflow.append(i)
            pg.screenshot(path=str(outdir / f"{prefix}{i:02d}.jpg"), type="jpeg", quality=92)
        b.close()
    return overflow


def reel_only(r, out):
    global LAYOUT
    LAYOUT = REEL
    over_r = render(cards(r), out, h=1920, prefix="reel_")
    LAYOUT = FEED
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
    import make_reel
    music = r.get("music", "pulse")
    rp, sec = make_reel.build(out, music)
    pj = out / "post.json"
    if pj.exists():
        meta = json.loads(pj.read_text(encoding="utf-8"))
        meta["reel"] = True; meta["music"] = music
        pj.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"릴스만 추가: {rp} ({sec:.1f}초, 음악 {music})" + (f" · 주의: 릴스 화면 {over_r}장 글 넘침" if over_r else ""))
    return 2 if over_r else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("round_json")
    ap.add_argument("--approve3", help="대표의 발행 직전 승인(승인 3)을 기록할 때 승인자 표기")
    ap.add_argument("--out", help="출력 폴더 (기본 posts/YYYYMMDD_SLOT)")
    ap.add_argument("--reel", action="store_true", help="카드로 릴스 영상(reel.mp4)도 만든다 (음악: round JSON의 music, 기본 pulse)")
    ap.add_argument("--reel-only", action="store_true", help="이미 있는 묶음(--out)에 릴스 화면과 reel.mp4만 더한다(피드 카드·캡션은 그대로). 스튜디오 예약 발송용")
    a = ap.parse_args()
    r = json.loads(pathlib.Path(a.round_json).read_text(encoding="utf-8"))
    ymd = r["date"].replace("-", "")
    out = pathlib.Path(a.out) if a.out else ROOT / "posts" / f"{ymd}_{r['slot']}"
    out.mkdir(parents=True, exist_ok=True)
    if a.reel_only:
        return reel_only(r, out)
    over = render(cards(r), out)
    (out / "caption.txt").write_text(r["caption"], encoding="utf-8")
    import datetime as dt
    meta = {"version": 1, "date": r["date"], "slot": r["slot"],
            "publishAt": f"{r['date']}T{SLOTS[r['slot']][1]}:00+09:00", "topic": r.get("topic", r["hook"].replace("\n", " ")),
            "images": [f"{i:02d}.jpg" for i in range(1, 8)], "caption": r["caption"],
            "sources": r["sources"]}
    if a.approve3:
        meta["approval3"] = {"approved": True, "at": dt.datetime.now(dt.timezone(dt.timedelta(hours=9))).isoformat(timespec="seconds"),
                             "by": a.approve3}
    if r.get("read"):
        over_rd = render(cards_read(r), out, prefix="r")
        meta["readImages"] = sorted(p.name for p in out.glob("r[0-9][0-9].jpg"))
        if over_rd:
            print(f"주의: 읽는 카드 {over_rd}장에서 글이 넘칩니다. 본문을 줄이세요.")
            over = (over or []) + [f"r{x}" for x in over_rd]
    (out / "post.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    if a.reel:
        # 릴스용 세로 화면(1080×1920)을 따로 그린다
        global LAYOUT
        LAYOUT = REEL
        over_r = render(cards(r), out, h=1920, prefix="reel_")
        LAYOUT = FEED
        if over_r:
            print(f"주의: 릴스 화면 {over_r}장에서 글이 넘칩니다.")
        sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
        import make_reel
        rp, sec = make_reel.build(out, r.get("music", "pulse"))
        meta["reel"] = True; meta["music"] = r.get("music", "pulse")
        (out / "post.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"릴스: {rp} ({sec:.1f}초)")
    print(f"완료: {out} (예약 {meta['publishAt']}, 승인 3 {'있음' if a.approve3 else '없음'})")
    if over:
        print(f"주의: {over}장에서 글이 카드 밖으로 넘칩니다. 문구를 줄이세요.")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
