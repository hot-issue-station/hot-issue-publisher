#!/usr/bin/env bash
# 덕심저장소 갤러리 배포 묶음 만들기 → site/dist/
#   gallery/hall.html → dist/index.html, curation.json·endorsements.json 복사,
#   안내 페이지 5개 + assets + netlify.toml + _headers(끌어 놓기 배포에서도 보안 헤더가 걸리도록) 복사.
#   gallery/ 원본은 읽기만 하고 고치지 않음.
set -euo pipefail
SITE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$SITE/.." && pwd)"
GAL="$ROOT/gallery"
SRC="$SITE/src"
DIST="$SITE/dist"

for f in hall.html curation.json endorsements.json; do
  [ -f "$GAL/$f" ] || { echo "없음: gallery/$f" >&2; exit 1; }
done
for p in notes guide about privacy terms ads takedown; do
  [ -f "$SRC/$p.html" ] || { echo "없음: site/src/$p.html" >&2; exit 1; }
done

rm -rf "$DIST"
mkdir -p "$DIST/assets"
cp "$GAL/hall.html"         "$DIST/index.html"
cp "$GAL/curation.json"     "$DIST/curation.json"
cp "$GAL/endorsements.json" "$DIST/endorsements.json"
cp "$SRC"/_worker.js "$SRC"/notes.html "$SRC"/stats.html "$SRC"/guide.html "$SRC"/about.html "$SRC"/privacy.html "$SRC"/terms.html "$SRC"/ads.html "$SRC"/takedown.html "$DIST/"
cp "$SRC"/assets/* "$DIST/assets/"

# 통계판 이름표(titles.json)
python3 "$SITE/gen_titles.py" "$GAL/hall.html" "$DIST/titles.json" >/dev/null

# JSON 깨짐 확인(파이썬이 있으면)
if command -v python3 >/dev/null 2>&1; then
  for j in curation.json endorsements.json; do python3 -c 'import json,sys; json.load(open(sys.argv[1]))' "$DIST/$j"; done
fi

# 끌어 놓기(Deploy manually) 배포용: dist 안에 netlify.toml(publish=".")과 _headers 를 함께 둔다
sed 's/^\(\s*publish\s*=\s*\)"dist"/\1"."/' "$SITE/netlify.toml" > "$DIST/netlify.toml"
cat > "$DIST/_headers" <<'H'
/*
  X-Content-Type-Options: nosniff
  Referrer-Policy: strict-origin-when-cross-origin
  X-Frame-Options: SAMEORIGIN
  Permissions-Policy: camera=(), microphone=(), geolocation=()
/*.html
  Cache-Control: public, max-age=0, must-revalidate
/
  Cache-Control: public, max-age=0, must-revalidate
/*.json
  Cache-Control: public, max-age=0, must-revalidate
/assets/*
  Cache-Control: public, max-age=3600
H

grep -rl 'FORM_URL"' "$DIST/assets/site-config.js" >/dev/null && echo "알림: assets/site-config.js 의 FORM_URL 이 아직 자리표시입니다(문의 버튼은 '준비 중'으로 잠김)."
echo "완료: $DIST"
ls -la "$DIST" "$DIST/assets"
