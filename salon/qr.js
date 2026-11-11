/* 단골 수첩 QR 만들기 — index.html 안의 QR 코드(factory/qr.py 이식)를 그대로 떼어 낸 것.
   partner.html이 씀. index.html은 지금처럼 자기 안의 같은 코드를 씀(둘을 고칠 땐 함께). */
/* ── QR 코드 만들기 (factory/qr.py를 그대로 옮김, 외부 라이브러리 없음) ──
   바이트 모드(UTF-8), 오류정정 M, 버전 1~15 자동, 마스크 8개 중 벌점 가장 낮은 것 */
const QR=(()=>{
  const M={1:[26,10,[[1,16]]],2:[44,16,[[1,28]]],3:[70,26,[[1,44]]],4:[100,18,[[2,32]]],5:[134,24,[[2,43]]],6:[172,16,[[4,27]]],7:[196,18,[[4,31]]],8:[242,22,[[2,38],[2,39]]],9:[292,22,[[3,36],[2,37]]],10:[346,26,[[4,43],[1,44]]],
    11:[404,30,[[1,50],[4,51]]],12:[466,22,[[6,36],[2,37]]],13:[532,22,[[8,37],[1,38]]],14:[581,24,[[4,40],[5,41]]],15:[655,24,[[5,41],[5,42]]]};
  const AL={1:[],2:[6,18],3:[6,22],4:[6,26],5:[6,30],6:[6,34],7:[6,22,38],8:[6,24,42],9:[6,26,46],10:[6,28,50],11:[6,30,54],12:[6,32,58],13:[6,34,62],14:[6,26,46,66],15:[6,26,48,70]};
  const EXP=new Array(512), LOG=new Array(256); let x=1; for(let i=0;i<255;i++){ EXP[i]=x; LOG[x]=i; x<<=1; if(x&256) x^=0x11D } for(let i=255;i<512;i++) EXP[i]=EXP[i-255];
  const mul=(a,b)=>a&&b?EXP[LOG[a]+LOG[b]]:0;
  function gen(n){ let g=[1]; for(let i=0;i<n;i++){ const ng=new Array(g.length+1).fill(0); g.forEach((c,j)=>{ ng[j]^=c; ng[j+1]^=mul(c,EXP[i]) }); g=ng } return g }
  function ecc(d,n){ const g=gen(n), r=[...d,...new Array(n).fill(0)]; for(let i=0;i<d.length;i++){ const c=r[i]; if(c) for(let j=1;j<=n;j++) r[i+j]^=mul(g[j],c) } return r.slice(d.length) }
  const cap=v=>M[v][2].reduce((a,[b,d])=>a+b*d,0);
  function words(p,v){ const bits=[], put=(val,n)=>{ for(let i=n-1;i>=0;i--) bits.push((val>>i)&1) };
    put(4,4); put(p.length,v<=9?8:16); p.forEach(b=>put(b,8)); const C=cap(v)*8; put(0,Math.min(4,C-bits.length)); while(bits.length%8) bits.push(0);
    const data=[]; for(let i=0;i<bits.length;i+=8) data.push(parseInt(bits.slice(i,i+8).join(""),2)); let pad=0xEC; while(data.length<cap(v)){ data.push(pad); pad^=0xEC^0x11 }
    const [tot,en,gr]=M[v], bl=[]; let k=0; gr.forEach(([nb,nd])=>{ for(let i=0;i<nb;i++){ bl.push(data.slice(k,k+nd)); k+=nd } });
    const ec=bl.map(b=>ecc(b,en)), out=[], mx=Math.max(...bl.map(b=>b.length));
    for(let i=0;i<mx;i++) bl.forEach(b=>{ if(i<b.length) out.push(b[i]) }); for(let i=0;i<en;i++) ec.forEach(e=>out.push(e[i]));
    if(out.length!==tot) throw new Error("QR 코드워드 수가 맞지 않아요"); return out }
  function grid(v){ const n=v*4+17, m=[], f=[]; for(let i=0;i<n;i++){ m.push(new Array(n).fill(false)); f.push(new Array(n).fill(false)) } return {v,n,m,f,set:(x,y,d)=>{ m[y][x]=d; f[y][x]=true }} }
  function fmt(g,mask){ const {n,set}=g, data=mask; let rem=data; for(let i=0;i<10;i++) rem=(rem<<1)^((rem>>9)*0x537);   /* 오류정정 M = 00 */
    const bits=((data<<10)|rem)^0x5412, b=i=>((bits>>i)&1)===1;
    for(let i=0;i<6;i++) set(8,i,b(i)); set(8,7,b(6)); set(8,8,b(7)); set(7,8,b(8)); for(let i=9;i<15;i++) set(14-i,8,b(i));
    for(let i=0;i<8;i++) set(n-1-i,8,b(i)); for(let i=8;i<15;i++) set(8,n-15+i,b(i)); set(8,n-8,true) }
  function funcs(g){ const {n,set}=g;
    for(let i=0;i<n;i++){ set(6,i,i%2===0); set(i,6,i%2===0) }
    [[3,3],[n-4,3],[3,n-4]].forEach(([cx,cy])=>{ for(let dy=-4;dy<=4;dy++) for(let dx=-4;dx<=4;dx++){ const X=cx+dx, Y=cy+dy, d=Math.max(Math.abs(dx),Math.abs(dy)); if(X>=0&&X<n&&Y>=0&&Y<n) set(X,Y,d!==2&&d!==4) } });
    const al=AL[g.v], L=al.length;
    for(let i=0;i<L;i++) for(let j=0;j<L;j++){ if((i===0&&j===0)||(i===0&&j===L-1)||(i===L-1&&j===0)) continue;
      for(let dy=-2;dy<=2;dy++) for(let dx=-2;dx<=2;dx++) set(al[i]+dx,al[j]+dy,Math.max(Math.abs(dx),Math.abs(dy))!==1) }
    fmt(g,0);
    if(g.v>=7){ let rem=g.v; for(let i=0;i<12;i++) rem=(rem<<1)^((rem>>11)*0x1F25); const bits=(g.v<<12)|rem;
      for(let i=0;i<18;i++){ const b=((bits>>i)&1)===1, a=n-11+i%3, c=Math.floor(i/3); set(a,c,b); set(c,a,b) } } }
  function place(g,cw){ const {n,m,f}=g, total=cw.length*8; let i=0, right=n-1;
    while(right>=1){ if(right===6) right=5;
      for(let vert=0;vert<n;vert++) for(let j=0;j<2;j++){ const X=right-j, up=((right+1)&2)===0, Y=up?n-1-vert:vert;
        if(!f[Y][X]){ m[Y][X]=i<total&&((cw[i>>3]>>(7-(i&7)))&1)===1; i++ } }
      right-=2 } }
  const MK=[(x,y)=>(x+y)%2===0,(x,y)=>y%2===0,(x,y)=>x%3===0,(x,y)=>(x+y)%3===0,(x,y)=>(Math.floor(x/3)+Math.floor(y/2))%2===0,(x,y)=>x*y%2+x*y%3===0,(x,y)=>(x*y%2+x*y%3)%2===0,(x,y)=>((x+y)%2+x*y%3)%2===0];
  function mask(g,k){ const f=MK[k]; for(let y=0;y<g.n;y++) for(let x=0;x<g.n;x++) if(!g.f[y][x]&&f(x,y)) g.m[y][x]=!g.m[y][x] }
  function pen(m){ const n=m.length; let p=0; const cols=[]; for(let x=0;x<n;x++){ const c=[]; for(let y=0;y<n;y++) c.push(m[y][x]); cols.push(c) }
    const pat=[1,0,1,1,1,0,1];
    [...m,...cols].forEach(line=>{ let run=0, prev=null; for(const c of line){ if(c===prev) run++; else { if(run>=5) p+=3+run-5; run=1; prev=c } } if(run>=5) p+=3+run-5;
      const e=[0,0,0,0,...line.map(Number),0,0,0,0];
      for(let i=0;i<e.length-6;i++){ let hit=true; for(let k=0;k<7;k++) if(e[i+k]!==pat[k]){ hit=false; break } if(!hit) continue;
        if((i>=4&&!e.slice(Math.max(0,i-4),i).some(Boolean))||(i+11<=e.length&&!e.slice(i+7,i+11).some(Boolean))) p+=40 } });
    for(let y=0;y<n-1;y++) for(let x=0;x<n-1;x++){ const c=m[y][x]; if(c===m[y][x+1]&&c===m[y+1][x]&&c===m[y+1][x+1]) p+=3 }
    let dark=0; m.forEach(r=>r.forEach(c=>{ if(c) dark++ })); p+=Math.floor(Math.abs(dark*100/(n*n)-50)/5)*10; return p }
  function matrix(text,mk){ const p=[...new TextEncoder().encode(String(text))]; let v=0;
    for(let k=1;k<=15;k++) if(4+(k<=9?8:16)+8*p.length<=cap(k)*8){ v=k; break }
    if(!v) throw new Error("QR에 담기엔 글이 너무 길어요");
    const cw=words(p,v); let best=null;
    for(const k of (mk!=null?[mk]:[0,1,2,3,4,5,6,7])){ const g=grid(v); funcs(g); place(g,cw); mask(g,k); fmt(g,k); const s=pen(g.m); if(!best||s<best[0]) best=[s,g] }
    return best[1].m }
  function draw(cv,text,scale,border){ const m=matrix(text), n=m.length; scale=scale||8; border=border==null?4:border; const s=(n+border*2)*scale;
    cv.width=cv.height=s; const g=cv.getContext("2d"); g.fillStyle="#fff"; g.fillRect(0,0,s,s); g.fillStyle="#000";
    for(let y=0;y<n;y++) for(let x=0;x<n;x++) if(m[y][x]) g.fillRect((x+border)*scale,(y+border)*scale,scale,scale); return n }
  return {matrix,draw};
})();
window.QR=QR;
