// Small physically based path tracer used for the interior perspectives (salon + staff room).
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <vector>
#include <string>
#include <fstream>
#include <sstream>
#include <algorithm>
#include <random>
#ifdef _OPENMP
#include <omp.h>
#endif

struct V3 { float x, y, z; V3(){x=y=z=0;} V3(float a,float b,float c){x=a;y=b;z=c;} };
static inline V3 operator+(V3 a, V3 b){return V3(a.x+b.x,a.y+b.y,a.z+b.z);}
static inline V3 operator-(V3 a, V3 b){return V3(a.x-b.x,a.y-b.y,a.z-b.z);}
static inline V3 operator*(V3 a, float s){return V3(a.x*s,a.y*s,a.z*s);}
static inline V3 operator*(V3 a, V3 b){return V3(a.x*b.x,a.y*b.y,a.z*b.z);}
static inline V3 operator-(V3 a){return V3(-a.x,-a.y,-a.z);}
static inline float dot(V3 a, V3 b){return a.x*b.x+a.y*b.y+a.z*b.z;}
static inline V3 cross(V3 a, V3 b){return V3(a.y*b.z-a.z*b.y,a.z*b.x-a.x*b.z,a.x*b.y-a.y*b.x);}
static inline float len(V3 a){return std::sqrt(dot(a,a));}
static inline V3 norm(V3 a){float l=len(a);return l>0?a*(1.f/l):a;}
static inline float lum(V3 c){return 0.2126f*c.x+0.7152f*c.y+0.0722f*c.z;}
static inline float clampf(float x,float a,float b){return x<a?a:(x>b?b:x);}
static inline float smooth(float a,float b,float x){float t=clampf((x-a)/(b-a),0,1);return t*t*(3-2*t);}
static inline float fractf(float x){return x-std::floor(x);}
static inline V3 mixv(V3 a,V3 b,float t){return a*(1-t)+b*t;}

// ---------- noise ----------
static inline float hash3(int x,int y,int z){unsigned h=(unsigned)x*374761393u+(unsigned)y*668265263u+(unsigned)z*2147483647u;h=(h^(h>>13))*1274126177u;h^=h>>16;return (h&0xffffff)/16777215.0f;}
static inline float hash1(float x){return fractf(std::sin(x*127.1f+311.7f)*43758.5453f);}
static float vnoise(V3 p){int ix=(int)std::floor(p.x),iy=(int)std::floor(p.y),iz=(int)std::floor(p.z);float fx=p.x-ix,fy=p.y-iy,fz=p.z-iz;
 float ux=fx*fx*(3-2*fx),uy=fy*fy*(3-2*fy),uz=fz*fz*(3-2*fz);float r=0;
 for(int k=0;k<8;k++){int dx=k&1,dy=(k>>1)&1,dz=(k>>2)&1;float w=(dx?ux:1-ux)*(dy?uy:1-uy)*(dz?uz:1-uz);r+=w*hash3(ix+dx,iy+dy,iz+dz);}return r;}
static float fbm(V3 p,int oct=4){float a=0.5f,s=0;for(int i=0;i<oct;i++){s+=a*vnoise(p);p=p*2.03f+V3(17.1f,3.7f,9.2f);a*=0.5f;}return s;}

static V3 srgb(float r,float g,float b){auto f=[](float c){c/=255.f;return c<=0.04045f?c/12.92f:std::pow((c+0.055f)/1.055f,2.4f);};return V3(f(r),f(g),f(b));}

// ---------- materials ----------
enum { MT_DIFF=0, MT_MIRROR=1, MT_GLASS=2, MT_TRANS=3, MT_METAL=4 };
enum { TX_NONE=0, TX_FLOOR=1, TX_WAINS=2, TX_PLASTER=3, TX_WOOD=4, TX_PICTURE=5, TX_CHECK=6, TX_LEATHER=7, TX_PAPER=8 };
struct Mat { V3 alb; int type=MT_DIFF; int tex=TX_NONE; float ks=0; float ex=50; V3 emit; float bump=0; int axis=-1; };
std::vector<Mat> mats;

// ---------- primitives ----------
enum { P_BOX=0, P_CYL=1, P_ELL=2, P_RBOX=3 };
struct Prim {
 int kind, mat; bool hide=false, noshadow=false, noclip=false;
 V3 c, h; float cy=1, sy=0; float R[9]={1,0,0,0,1,0,0,0,1};
 V3 p0, p1; float r=0;                // cyl
 float M[9];                           // ellipsoid inverse transform (world->unit)
 V3 bmin, bmax; int seed=0;
};
std::vector<Prim> prims;

struct Hit { float t; V3 n; V3 lp; int prim; };

static bool isectBox(const Prim& p, V3 o, V3 d, float tmax, Hit& H){
 V3 q=o-p.c; const float*R=p.R; // R columns = local axes in world
 V3 lo(R[0]*q.x+R[3]*q.y+R[6]*q.z, R[1]*q.x+R[4]*q.y+R[7]*q.z, R[2]*q.x+R[5]*q.y+R[8]*q.z);
 V3 ld(R[0]*d.x+R[3]*d.y+R[6]*d.z, R[1]*d.x+R[4]*d.y+R[7]*d.z, R[2]*d.x+R[5]*d.y+R[8]*d.z);
 float t0=1e-4f,t1=tmax; int ax=-1; float sg=0; int ax1=-1; float sg1=0;
 float O[3]={lo.x,lo.y,lo.z},D[3]={ld.x,ld.y,ld.z},HH[3]={p.h.x,p.h.y,p.h.z};
 for(int i=0;i<3;i++){ if(std::fabs(D[i])<1e-12f){ if(O[i]<-HH[i]||O[i]>HH[i]) return false; continue; }
  float inv=1.f/D[i]; float ta=(-HH[i]-O[i])*inv, tb=(HH[i]-O[i])*inv; float sa=-1;
  if(ta>tb){std::swap(ta,tb);sa=1;}
  if(ta>t0){t0=ta;ax=i;sg=sa;} if(tb<t1){t1=tb;ax1=i;sg1=-sa;} if(t0>t1) return false; }
 float t; int a; float s;
 if(ax>=0){t=t0;a=ax;s=sg;} else { if(t1>=tmax||ax1<0) return false; t=t1;a=ax1;s=sg1; }
 if(t<=1e-4f||t>=tmax) return false;
 V3 ln(0,0,0); if(a==0) ln.x=s; else if(a==1) ln.y=s; else ln.z=s;
 H.t=t; H.n=V3(R[0]*ln.x+R[1]*ln.y+R[2]*ln.z, R[3]*ln.x+R[4]*ln.y+R[5]*ln.z, R[6]*ln.x+R[7]*ln.y+R[8]*ln.z); H.lp=lo+ld*t; return true;
}
static bool isectCyl(const Prim& p, V3 o, V3 d, float tmax, Hit& H){
 V3 ax=p.p1-p.p0; float L=len(ax); V3 a=ax*(1.f/L); V3 oc=o-p.p0;
 float da=dot(d,a), oa=dot(oc,a); V3 dp=d-a*da, op=oc-a*oa;
 float A=dot(dp,dp),B=2*dot(dp,op),C=dot(op,op)-p.r*p.r; float best=tmax; bool hit=false; V3 n;
 if(A>1e-12f){ float disc=B*B-4*A*C; if(disc>=0){ float sq=std::sqrt(disc);
  for(int k=0;k<2;k++){ float t=(-B+(k?sq:-sq))/(2*A); if(t>1e-4f&&t<best){ float y=oa+da*t; if(y>=0&&y<=L){best=t;hit=true; n=norm(op+dp*t);} } } } }
 if(std::fabs(da)>1e-12f){ for(int k=0;k<2;k++){ float y=k?L:0; float t=(y-oa)/da; if(t>1e-4f&&t<best){ V3 q=op+dp*t; if(dot(q,q)<=p.r*p.r){best=t;hit=true;n=k?a:-a;} } } }
 if(!hit) return false; H.t=best; H.n=n; V3 hp=oc+d*best; H.lp=V3(dot(hp,a),0,0); return true;
}
static inline V3 mulM(const float* M, V3 v){return V3(M[0]*v.x+M[1]*v.y+M[2]*v.z, M[3]*v.x+M[4]*v.y+M[5]*v.z, M[6]*v.x+M[7]*v.y+M[8]*v.z);}
static inline V3 mulMT(const float* M, V3 v){return V3(M[0]*v.x+M[3]*v.y+M[6]*v.z, M[1]*v.x+M[4]*v.y+M[7]*v.z, M[2]*v.x+M[5]*v.y+M[8]*v.z);}
static bool isectEll(const Prim& p, V3 o, V3 d, float tmax, Hit& H){
 V3 lo=mulM(p.M,o-p.c), ld=mulM(p.M,d); float A=dot(ld,ld),B=2*dot(lo,ld),C=dot(lo,lo)-1; float disc=B*B-4*A*C; if(disc<0) return false;
 float sq=std::sqrt(disc); float t=(-B-sq)/(2*A); if(t<=1e-4f) t=(-B+sq)/(2*A); if(t<=1e-4f||t>=tmax) return false;
 V3 lp=lo+ld*t; H.t=t; H.n=norm(mulMT(p.M,lp)); H.lp=lp; return true;
}
static inline float sdRB(V3 p, V3 b, float r){ V3 q(std::fabs(p.x)-b.x+r,std::fabs(p.y)-b.y+r,std::fabs(p.z)-b.z+r);
 V3 mq(std::max(q.x,0.f),std::max(q.y,0.f),std::max(q.z,0.f)); return len(mq)+std::min(std::max(q.x,std::max(q.y,q.z)),0.f)-r; }
static bool isectRBox(const Prim& p, V3 o, V3 d, float tmax, Hit& H){
 V3 q=o-p.c; const float*R=p.R;
 V3 lo(R[0]*q.x+R[3]*q.y+R[6]*q.z, R[1]*q.x+R[4]*q.y+R[7]*q.z, R[2]*q.x+R[5]*q.y+R[8]*q.z);
 V3 ld(R[0]*d.x+R[3]*d.y+R[6]*d.z, R[1]*d.x+R[4]*d.y+R[7]*d.z, R[2]*d.x+R[5]*d.y+R[8]*d.z);
 float t0=0,t1=tmax; float O[3]={lo.x,lo.y,lo.z},D[3]={ld.x,ld.y,ld.z},HH[3]={p.h.x+1e-3f,p.h.y+1e-3f,p.h.z+1e-3f};
 for(int i=0;i<3;i++){ if(std::fabs(D[i])<1e-12f){ if(O[i]<-HH[i]||O[i]>HH[i]) return false; continue; }
  float inv=1.f/D[i]; float ta=(-HH[i]-O[i])*inv, tb=(HH[i]-O[i])*inv; if(ta>tb) std::swap(ta,tb); t0=std::max(t0,ta); t1=std::min(t1,tb); if(t0>t1) return false; }
 float t=std::max(t0,1e-4f); float d0=sdRB(lo+ld*t,p.h,p.r);
 if(d0<0){ // started inside: march to exit
   for(int i=0;i<96&&t<t1;i++){ float dd=sdRB(lo+ld*t,p.h,p.r); if(dd>-2e-5f) break; t+=std::max(-dd,2e-4f);} }
 else { bool hit=false; for(int i=0;i<128&&t<t1;i++){ float dd=sdRB(lo+ld*t,p.h,p.r); if(dd<2e-5f){hit=true;break;} t+=dd; } if(!hit) return false; }
 if(t<=1e-4f||t>=tmax||t>t1+1e-3f) return false;
 V3 lp=lo+ld*t; float e=1e-4f;
 V3 ln(sdRB(lp+V3(e,0,0),p.h,p.r)-sdRB(lp-V3(e,0,0),p.h,p.r), sdRB(lp+V3(0,e,0),p.h,p.r)-sdRB(lp-V3(0,e,0),p.h,p.r), sdRB(lp+V3(0,0,e),p.h,p.r)-sdRB(lp-V3(0,0,e),p.h,p.r)); ln=norm(ln);
 H.t=t; H.n=V3(R[0]*ln.x+R[1]*ln.y+R[2]*ln.z, R[3]*ln.x+R[4]*ln.y+R[5]*ln.z, R[6]*ln.x+R[7]*ln.y+R[8]*ln.z); H.lp=lp; return true;
}
static inline bool isect(const Prim& p, V3 o, V3 d, float tmax, Hit& H){
 if(p.kind==P_RBOX) return isectRBox(p,o,d,tmax,H);
 if(p.kind==P_BOX) return isectBox(p,o,d,tmax,H); if(p.kind==P_CYL) return isectCyl(p,o,d,tmax,H); return isectEll(p,o,d,tmax,H);
}

// ---------- BVH ----------
struct Node { V3 bmin,bmax; int left,right,start,count; };
std::vector<Node> nodes; std::vector<int> pidx;
static int build(int s,int e){
 Node nd; nd.bmin=V3(1e9,1e9,1e9); nd.bmax=V3(-1e9,-1e9,-1e9);
 for(int i=s;i<e;i++){const Prim&p=prims[pidx[i]]; nd.bmin=V3(std::min(nd.bmin.x,p.bmin.x),std::min(nd.bmin.y,p.bmin.y),std::min(nd.bmin.z,p.bmin.z)); nd.bmax=V3(std::max(nd.bmax.x,p.bmax.x),std::max(nd.bmax.y,p.bmax.y),std::max(nd.bmax.z,p.bmax.z));}
 int id=nodes.size(); nodes.push_back(nd);
 if(e-s<=3){nodes[id].left=nodes[id].right=-1;nodes[id].start=s;nodes[id].count=e-s;return id;}
 V3 ext=nd.bmax-nd.bmin; int ax=ext.x>ext.y?(ext.x>ext.z?0:2):(ext.y>ext.z?1:2);
 auto cen=[&](int i){const Prim&p=prims[i];V3 c=(p.bmin+p.bmax)*0.5f;return ax==0?c.x:(ax==1?c.y:c.z);};
 int m=(s+e)/2; std::nth_element(pidx.begin()+s,pidx.begin()+m,pidx.begin()+e,[&](int a,int b){return cen(a)<cen(b);});
 int l=build(s,m), r=build(m,e); nodes[id].left=l;nodes[id].right=r;nodes[id].count=0; return id;
}
static inline bool boxHit(const Node& n, V3 o, V3 inv, float tmax){
 float t0=0,t1=tmax; float O[3]={o.x,o.y,o.z},I[3]={inv.x,inv.y,inv.z},A[3]={n.bmin.x,n.bmin.y,n.bmin.z},B[3]={n.bmax.x,n.bmax.y,n.bmax.z};
 for(int i=0;i<3;i++){float ta=(A[i]-O[i])*I[i],tb=(B[i]-O[i])*I[i]; if(ta>tb)std::swap(ta,tb); t0=ta>t0?ta:t0; t1=tb<t1?tb:t1; if(t0>t1) return false;} return true;
}
static bool trace(V3 o, V3 d, Hit& best, bool primary){
 V3 inv(1.f/(std::fabs(d.x)>1e-9f?d.x:1e-9f),1.f/(std::fabs(d.y)>1e-9f?d.y:1e-9f),1.f/(std::fabs(d.z)>1e-9f?d.z:1e-9f));
 best.t=1e30f; best.prim=-1; int st[64]; int sp=0; st[sp++]=0;
 while(sp){ const Node& n=nodes[st[--sp]]; if(!boxHit(n,o,inv,best.t)) continue;
  if(n.left<0){ for(int i=0;i<n.count;i++){int pi=pidx[n.start+i]; const Prim&p=prims[pi]; if(primary&&p.hide) continue; Hit h; if(isect(p,o,d,best.t,h)){best=h;best.prim=pi;}} }
  else { st[sp++]=n.left; st[sp++]=n.right; } }
 return best.prim>=0;
}
// transmittance along a shadow ray
static float shadowT(V3 o, V3 d, float tmax){
 V3 inv(1.f/(std::fabs(d.x)>1e-9f?d.x:1e-9f),1.f/(std::fabs(d.y)>1e-9f?d.y:1e-9f),1.f/(std::fabs(d.z)>1e-9f?d.z:1e-9f));
 float T=1; int st[64]; int sp=0; st[sp++]=0;
 while(sp){ const Node& n=nodes[st[--sp]]; if(!boxHit(n,o,inv,tmax)) continue;
  if(n.left<0){ for(int i=0;i<n.count;i++){int pi=pidx[n.start+i]; const Prim&p=prims[pi]; if(p.noshadow) continue; Hit h; if(isect(p,o,d,tmax,h)){ int ty=mats[p.mat].type; if(ty==MT_GLASS) T*=0.88f; else if(ty==MT_TRANS) T*=0.35f; else return 0; } } }
  else { st[sp++]=n.left; st[sp++]=n.right; } }
 return T;
}

// ---------- lights ----------
struct Light { V3 p, dir; V3 I; float cosIn, cosOut, rad; float upFrac; };
std::vector<Light> lights;
static inline float coneF(const Light& L, V3 toP){ float c=dot(L.dir,toP); float f=smooth(L.cosOut,L.cosIn,c); if(L.upFrac>0) f=std::max(f,L.upFrac); return f; }

// ---------- textures ----------
static V3 woodCol(V3 base, float u, float v, float w, float seed){
 V3 q(u*1.1f+seed, v*28.f, w*28.f); float g=fbm(q,4); float g2=fbm(V3(u*0.25f+seed*1.7f, v*3.f, w*3.f),3);
 float ring=0.5f+0.5f*std::sin(v*70.f + w*35.f + g*9.f + g2*6.f);
 float pores=fbm(V3(u*6.f+seed, v*160.f, w*160.f),2);
 float k=(0.80f+0.34f*g2)*(0.86f+0.20f*ring)*(0.93f+0.12f*pores);
 return base*k;
}
static V3 pictureCol(float s, float t){ // s,t in [0,1], t up
 float m=0.07f; if(s<m||s>1-m||t<m*1.4f||t>1-m*1.4f) return srgb(238,236,230);
 float x=(s-m)/(1-2*m), y=(t-m*1.4f)/(1-2.8f*m);
 float horizon=0.42f;
 V3 sky=mixv(srgb(222,214,200), srgb(150,170,188), smooth(0.45f,1.0f,y));
 float ridge1=horizon+0.20f+0.12f*fbm(V3(x*3.f,0.5f,1.f),4)-0.08f*std::fabs(x-0.35f);
 float ridge2=horizon+0.07f+0.08f*fbm(V3(x*5.f,3.5f,2.f),4);
 V3 c=sky;
 if(y<ridge1) c=mixv(srgb(120,132,142), srgb(150,160,168), smooth(horizon,ridge1,y));
 if(y<ridge2) c=srgb(78,92,98)*(0.85f+0.3f*fbm(V3(x*20,y*20,1),3));
 if(y<horizon){ float yy=horizon-(y); float ry=horizon+yy; V3 refl=sky; if(ry<ridge1) refl=srgb(120,132,142); if(ry<ridge2) refl=srgb(78,92,98);
  c=mixv(refl*0.8f, srgb(60,78,88), smooth(0,horizon,yy*1.4f)); c=c*(0.95f+0.08f*std::sin(y*300.f+fbm(V3(x*8,y*40,0),2)*4)); }
 return c;
}

struct Shade { V3 alb; V3 n; };
static Shade shadeAt(const Prim& p, const Hit& h, V3 P){
 const Mat& m=mats[p.mat]; Shade s; s.alb=m.alb; s.n=h.n; float seed=p.seed*7.31f;
 switch(m.tex){
 case TX_FLOOR:{ V3 Q=(m.axis==2)?V3(P.z,P.y,P.x):P; float pw=0.165f; float row=std::floor(Q.z/pw); float off=hash1(row)*1.8f; float plen=1.8f; float px=Q.x+off; float pid=std::floor(px/plen);
   float tone=hash1(row*13.1f+pid*7.7f); V3 base=s.alb*(0.80f+0.38f*tone); base=mixv(base, base*V3(1.05f,0.95f,0.85f), hash1(row+pid*3.3f));
   V3 c=woodCol(base,px*0.6f,Q.z*1.f,Q.y,row*3.1f+pid*1.3f);
   float fz=fractf(Q.z/pw)*pw, fx=fractf(px/plen)*plen; float gap=std::min(std::min(fz,pw-fz),std::min(fx,plen-fx));
   c=c*(0.45f+0.55f*smooth(0.0007f,0.0028f,gap)); s.alb=c; break; }
 case TX_WAINS:{ float hz = (p.h.x<p.h.z)? P.z : P.x; float bw=0.105f; float id=std::floor(hz/bw); float tone=hash1(id*5.3f+seed);
   V3 base=s.alb*(0.86f+0.26f*tone); V3 c=woodCol(base,P.y*0.9f,hz,(p.h.x<p.h.z?P.x:P.z),id*2.7f+seed);
   float f=fractf(hz/bw)*bw; float gap=std::min(f,bw-f); c=c*(0.40f+0.60f*smooth(0.0008f,0.0032f,gap));
   if(gap<0.0032f){ float sgn=(f<bw*0.5f)?1.f:-1.f; V3 tvec=(p.h.x<p.h.z)?V3(0,0,1):V3(1,0,0); s.n=norm(s.n+tvec*(sgn*0.35f*(1-smooth(0.0008f,0.0032f,gap)))); }
   s.alb=c; break; }
 case TX_PLASTER:{ float a=fbm(P*7.f,4), b=vnoise(P*90.f), c2=fbm(P*1.3f,3); s.alb=s.alb*(0.95f+0.06f*a+0.03f*b)*(0.97f+0.05f*c2);
   if(m.bump>0){ float e=0.004f; float n0=fbm(P*55.f,3); V3 gr((fbm((P+V3(e,0,0))*55.f,3)-n0)/e,(fbm((P+V3(0,e,0))*55.f,3)-n0)/e,(fbm((P+V3(0,0,e))*55.f,3)-n0)/e);
     gr=gr-s.n*dot(gr,s.n); s.n=norm(s.n-gr*(m.bump*0.004f)); } break; }
 case TX_WOOD:{ int ax=m.axis; float L[3]={p.h.x,p.h.y,p.h.z}; if(p.kind!=P_BOX&&p.kind!=P_RBOX){ s.alb=woodCol(s.alb,P.y,P.x,P.z,seed); break; }
   if(ax<0){ ax=0; if(L[1]>L[ax]) ax=1; if(L[2]>L[ax]) ax=2; }
   float lpv[3]={h.lp.x,h.lp.y,h.lp.z};
   { int fa=0; float best=-1; for(int i=0;i<3;i++){ float r=std::fabs(lpv[i])/std::max(L[i],1e-4f); if(r>best){best=r;fa=i;} }
     if(fa==ax){ int a1=(ax+1)%3,a2=(ax+2)%3; ax= L[a1]>=L[a2]?a1:a2; } } float u=lpv[ax], v=lpv[(ax+1)%3], w=lpv[(ax+2)%3];
   s.alb=woodCol(s.alb,u,v,w,seed); break; }
 case TX_PICTURE:{ float ss,tt; // faces +x (on west wall): horizontal coord is -z local
   ss=0.5f-h.lp.z/(2*p.h.z); tt=0.5f+h.lp.y/(2*p.h.y); if(std::fabs(h.lp.x)<p.h.x*0.99f){s.alb=srgb(30,28,26);break;} s.alb=pictureCol(ss,tt); break; }
 case TX_CHECK:{ float q=std::floor(P.x/0.2f)+std::floor(P.z/0.2f); bool w=((int)q)%2==0; s.alb= w? srgb(236,233,226): srgb(46,45,44); float fx=fractf(P.x/0.2f)*0.2f,fz=fractf(P.z/0.2f)*0.2f; float gap=std::min(std::min(fx,0.2f-fx),std::min(fz,0.2f-fz)); if(gap<0.0015f) s.alb=srgb(150,148,142); break; }
 case TX_LEATHER:{ s.alb=s.alb*(0.88f+0.18f*fbm(P*45.f,3)); break; }
 case TX_PAPER:{ s.alb=s.alb*(0.9f+0.15f*fbm(P*30.f+V3(seed,0,0),3)); break; }
 default: break; }
 return s;
}

// ---------- sampling ----------
struct RNG { unsigned long long s; RNG(unsigned long long a){s=a*6364136223846793005ULL+1442695040888963407ULL;} inline float f(){s=s*6364136223846793005ULL+1442695040888963407ULL; return ((s>>40)&0xffffff)/16777216.0f;} };
static void onb(V3 n, V3& t, V3& b){ if(std::fabs(n.x)>0.5f) t=norm(cross(n,V3(0,1,0))); else t=norm(cross(n,V3(1,0,0))); b=cross(n,t); }
static V3 cosSample(V3 n, RNG& r){ float u1=r.f(),u2=r.f(); float rr=std::sqrt(u1),ph=6.2831853f*u2; V3 t,b; onb(n,t,b); return norm(t*(rr*std::cos(ph))+b*(rr*std::sin(ph))+n*std::sqrt(std::max(0.f,1-u1))); }
static V3 phongSample(V3 r, float ex, RNG& g){ float u1=g.f(),u2=g.f(); float ct=std::pow(u1,1.f/(ex+1)); float st=std::sqrt(std::max(0.f,1-ct*ct)),ph=6.2831853f*u2; V3 t,b; onb(r,t,b); return norm(t*(st*std::cos(ph))+b*(st*std::sin(ph))+r*ct); }
static inline V3 reflect(V3 d, V3 n){ return d-n*(2*dot(d,n)); }

// camera
struct Cam { V3 pos; float yaw, fovh, shiftY, shiftX; int W,H,spp; } cam;
V3 envCol(0.02f,0.02f,0.025f);

static void radiance(V3 o, V3 d, RNG& rng, V3& outC, V3& aovA, V3& aovN, float& aovD){
 V3 L(0,0,0), T(1,1,1); bool primary=true, lastSpec=true, aovSet=false; aovA=V3(0,0,0); aovN=V3(0,0,0); aovD=0;
 for(int depth=0; depth<7; depth++){
  Hit h; if(!trace(o,d,h,primary)){ L=L+T*envCol; if(!aovSet){aovA=V3(1,1,1);aovSet=true;} break; }
  const Prim& p=prims[h.prim]; const Mat& m=mats[p.mat]; V3 P=o+d*h.t;
  V3 ng=h.n; bool front=dot(ng,d)<0; V3 nf=front?ng:-ng;
  if(m.emit.x+m.emit.y+m.emit.z>0 && (lastSpec)){ L=L+T*m.emit; }
  if(m.type==MT_MIRROR){ if(!aovSet&&depth==0){} T=T*m.alb; d=reflect(d,nf); o=P+nf*1e-4f; primary=false; lastSpec=true; continue; }
  if(m.type==MT_GLASS){ float c=std::fabs(dot(d,nf)); float F=0.04f+0.96f*std::pow(1-c,5.f); if(rng.f()<F){ d=reflect(d,nf); o=P+nf*1e-4f; } else { o=P-nf*1e-4f; T=T*m.alb; } lastSpec=true; continue; }
  Shade s=shadeAt(p,h,P); V3 n=s.n; if(dot(n,nf)<0) n=-n; if(!front&&m.type!=MT_TRANS) n=nf;
  if(dot(n,-d)<0.0f) n=nf;
  if(!aovSet){ aovA=(m.emit.x+m.emit.y+m.emit.z>0)? V3(1,1,1): (m.type==MT_METAL? V3(0.6f,0.6f,0.6f): s.alb); aovN=n; aovD=len(P-cam.pos); aovSet=true; }
  if(m.emit.x+m.emit.y+m.emit.z>0 && !lastSpec && m.type==MT_TRANS) {}
  V3 wo=-d; float cosO=std::max(0.f,dot(n,wo));
  bool metal=(m.type==MT_METAL);
  float F= metal? 1.f : (m.ks>0? m.ks+(1-m.ks)*std::pow(1-cosO,5.f) : 0.f);
  V3 specC = metal? s.alb : V3(1,1,1);
  V3 diffC = metal? V3(0,0,0) : s.alb*(1-F);
  if(m.type==MT_TRANS) diffC=s.alb;
  // --- next event estimation ---
  if(!lights.empty()){
   float W[64]; float sum=0; int nl=lights.size();
   for(int i=0;i<nl;i++){ V3 v=lights[i].p-P; float d2=dot(v,v); V3 l=v*(1.f/std::sqrt(d2)); float cn=dot(n,l); if(m.type==MT_TRANS) cn=std::fabs(cn); float w= cn>0? lum(lights[i].I)*coneF(lights[i],-l)*cn/d2 : 0; W[i]=w+1e-6f*lum(lights[i].I)/d2; sum+=W[i]; }
   float u=rng.f()*sum; int li=0; for(;li<nl-1;li++){ if(u<W[li]) break; u-=W[li]; }
   const Light& Lt=lights[li]; float pdf=W[li]/sum;
   V3 t1,t2; onb(Lt.dir,t1,t2); float a=rng.f()*6.2831853f, rr=Lt.rad*std::sqrt(rng.f()); V3 lp=Lt.p+t1*(rr*std::cos(a))+t2*(rr*std::sin(a));
   V3 v=lp-P; float d2=dot(v,v); float dist=std::sqrt(d2); V3 l=v*(1.f/dist); float cn=dot(n,l);
   bool trans=(m.type==MT_TRANS);
   if((cn>0||trans) && pdf>0){ float cf=coneF(Lt,-l); if(cf>0){
     V3 so=P+(cn>0?n:-n)*2e-4f; float vis=shadowT(so,l,dist-2e-3f);
     if(vis>0){ float acn=std::fabs(cn); V3 f;
       if(trans) f=diffC*(0.5f/3.1415926f);
       else { f=diffC*(1.f/3.1415926f); if(F>0){ V3 r=reflect(-wo,n); float cr=std::max(0.f,dot(r,l)); f=f+specC*(F*(m.ex+2)/(6.2831853f)*std::pow(cr,m.ex)); } }
       L=L+T*f*Lt.I*(cf*acn*vis/(d2*pdf)); } } }
  }
  // --- continue path ---
  if(m.type==MT_TRANS){ T=T*diffC; d=cosSample(rng.f()<0.5f?n:-n,rng); o=P+d*2e-4f; primary=false; lastSpec=false; }
  else if(F>0 && rng.f()<(metal?1.f:F)){ V3 r=reflect(d,n); V3 nd=phongSample(r,m.ex,rng); if(dot(nd,n)<=0) break; T=T*specC; d=nd; o=P+n*2e-4f; lastSpec=(m.ex>800); primary=false; }
  else { if(metal) break; T=T*(diffC*(1.f/std::max(1e-3f,1-F))); d=cosSample(n,rng); o=P+n*2e-4f; lastSpec=false; primary=false; }
  if(depth>=2){ float q=std::min(0.95f,std::max(T.x,std::max(T.y,T.z))); if(rng.f()>q) break; T=T*(1.f/q); }
 }
 if(!aovSet){aovA=V3(1,1,1);}
 outC=L;
}

int main(int argc,char**argv){
 if(argc<3){fprintf(stderr,"usage: pt scene.txt out_prefix\n");return 1;}
 std::ifstream in(argv[1]); std::string line; std::vector<std::vector<float>> clips;
 while(std::getline(in,line)){ std::istringstream ss(line); std::string k; ss>>k; if(k.empty()||k[0]=='#') continue;
  if(k=="mat"){ Mat m; float r,g,b,er,eg,eb; ss>>r>>g>>b>>m.type>>m.tex>>m.ks>>m.ex>>er>>eg>>eb>>m.bump>>m.axis; m.alb=V3(r,g,b); m.emit=V3(er,eg,eb); mats.push_back(m); }
  else if(k=="box"){ Prim p; p.kind=P_BOX; int ns; ss>>p.c.x>>p.c.y>>p.c.z>>p.h.x>>p.h.y>>p.h.z; for(int i=0;i<9;i++) ss>>p.R[i]; ss>>p.mat>>ns; p.noshadow=ns&1; p.noclip=(ns&2)!=0;
    float e[3]; for(int r=0;r<3;r++) e[r]=std::fabs(p.R[r*3])*p.h.x+std::fabs(p.R[r*3+1])*p.h.y+std::fabs(p.R[r*3+2])*p.h.z;
    p.bmin=V3(p.c.x-e[0],p.c.y-e[1],p.c.z-e[2]); p.bmax=V3(p.c.x+e[0],p.c.y+e[1],p.c.z+e[2]); prims.push_back(p); }
  else if(k=="rbx"){ Prim p; p.kind=P_RBOX; int ns; ss>>p.c.x>>p.c.y>>p.c.z>>p.h.x>>p.h.y>>p.h.z>>p.r; for(int i=0;i<9;i++) ss>>p.R[i]; ss>>p.mat>>ns; p.noshadow=ns&1; p.noclip=(ns&2)!=0;
    float e[3]; for(int r=0;r<3;r++) e[r]=std::fabs(p.R[r*3])*p.h.x+std::fabs(p.R[r*3+1])*p.h.y+std::fabs(p.R[r*3+2])*p.h.z;
    p.bmin=V3(p.c.x-e[0],p.c.y-e[1],p.c.z-e[2]); p.bmax=V3(p.c.x+e[0],p.c.y+e[1],p.c.z+e[2]); prims.push_back(p); }
  else if(k=="cyl"){ Prim p; p.kind=P_CYL; int ns; ss>>p.p0.x>>p.p0.y>>p.p0.z>>p.p1.x>>p.p1.y>>p.p1.z>>p.r>>p.mat>>ns; p.noshadow=ns&1; p.noclip=(ns&2)!=0;
    p.bmin=V3(std::min(p.p0.x,p.p1.x)-p.r,std::min(p.p0.y,p.p1.y)-p.r,std::min(p.p0.z,p.p1.z)-p.r); p.bmax=V3(std::max(p.p0.x,p.p1.x)+p.r,std::max(p.p0.y,p.p1.y)+p.r,std::max(p.p0.z,p.p1.z)+p.r); p.c=(p.p0+p.p1)*0.5f; prims.push_back(p); }
  else if(k=="ell"){ Prim p; p.kind=P_ELL; int ns; float R; ss>>p.c.x>>p.c.y>>p.c.z; for(int i=0;i<9;i++) ss>>p.M[i]; ss>>R>>p.mat>>ns; p.noshadow=ns&1; p.noclip=(ns&2)!=0; p.bmin=p.c-V3(R,R,R); p.bmax=p.c+V3(R,R,R); prims.push_back(p); }
  else if(k=="light"){ Light l; float ci,co; ss>>l.p.x>>l.p.y>>l.p.z>>l.dir.x>>l.dir.y>>l.dir.z>>l.I.x>>l.I.y>>l.I.z>>ci>>co>>l.rad>>l.upFrac; l.dir=norm(l.dir); l.cosIn=std::cos(ci*3.1415926f/180); l.cosOut=std::cos(co*3.1415926f/180); lights.push_back(l); }
  else if(k=="cam"){ ss>>cam.pos.x>>cam.pos.y>>cam.pos.z>>cam.yaw>>cam.fovh>>cam.shiftX>>cam.shiftY>>cam.W>>cam.H>>cam.spp; }
  else if(k=="clip"){ std::vector<float> c(4); ss>>c[0]>>c[1]>>c[2]>>c[3]; clips.push_back(c); }
  else if(k=="env"){ ss>>envCol.x>>envCol.y>>envCol.z; }
 }
 for(size_t i=0;i<prims.size();i++){ Prim&p=prims[i]; p.seed=i; V3 c=(p.bmin+p.bmax)*0.5f; if(!p.noclip) for(auto&cl:clips){ if(c.x>=cl[0]&&c.x<=cl[1]&&c.z>=cl[2]&&c.z<=cl[3]) p.hide=true; } }
 // room shell never hidden: shell prims flagged by material index 0..? (caller avoids clip regions covering shell centers via 'keep' below)
 pidx.resize(prims.size()); for(size_t i=0;i<prims.size();i++) pidx[i]=i; build(0,prims.size());
 fprintf(stderr,"prims %zu nodes %zu lights %zu\n",prims.size(),nodes.size(),lights.size());
 int W=cam.W,H=cam.H; std::vector<float> col(W*H*3),alb(W*H*3),nrm(W*H*3),dep(W*H);
 V3 fwd(std::sin(cam.yaw),0,-std::cos(cam.yaw)); V3 right=norm(cross(fwd,V3(0,1,0))); V3 up(0,1,0);
 float tx=std::tan(cam.fovh*3.1415926f/360); float ty=tx*H/W;
 int done=0;
 #pragma omp parallel for schedule(dynamic,1)
 for(int y=0;y<H;y++){ RNG rng(y*7919+13);
  for(int x=0;x<W;x++){ V3 acc,aa,an; float ad=0;
   for(int s=0;s<cam.spp;s++){ float px=(2*((x+rng.f())/W)-1)*tx+cam.shiftX*tx, py=(1-2*((y+rng.f())/H))*ty+cam.shiftY*ty;
     V3 d=norm(fwd+right*px+up*py); V3 c,a,n; float dd; radiance(cam.pos,d,rng,c,a,n,dd);
     float lc=lum(c); if(lc>14) c=c*(14/lc); acc=acc+c; aa=aa+a; an=an+n; ad+=dd; }
   float inv=1.f/cam.spp; int i=y*W+x; col[i*3]=acc.x*inv;col[i*3+1]=acc.y*inv;col[i*3+2]=acc.z*inv; alb[i*3]=aa.x*inv;alb[i*3+1]=aa.y*inv;alb[i*3+2]=aa.z*inv;
   V3 nn=norm(an); nrm[i*3]=nn.x;nrm[i*3+1]=nn.y;nrm[i*3+2]=nn.z; dep[i]=ad*inv; }
  #pragma omp atomic
  done++;
  if(y%50==0) fprintf(stderr,"row %d/%d\n",done,H);
 }
 std::string pre=argv[2];
 auto wr=[&](const char* suf, std::vector<float>& v){ FILE* f=fopen((pre+suf).c_str(),"wb"); fwrite(v.data(),4,v.size(),f); fclose(f); };
 wr("_col.bin",col); wr("_alb.bin",alb); wr("_nrm.bin",nrm); wr("_dep.bin",dep);
 printf("%d %d\n",W,H);
 return 0;
}
