/* Ember Shell ribbon egg: procedural ribbons, glyph texture, torn ends and attached flame tongues. */
(function () {
  'use strict';
  const TAU=Math.PI*2,HEAT=[[.718,.2,.102],[.91,.314,.059],[1,.541,0],[1,.824,.29],[1,.957,.878]];
  // glyph colour per tier is the next tier up; past white-hot it is the kit's cyan, deepened to read on white
  const GLYPH_HOT=[[1,.45,.1],[1,.62,.12],[1,.86,.36],[1,.98,.86],[.3,.78,1]],GLYPH_KEY=[[.2,.04,.02],[.24,.05,.02],[.36,.1,.02],[.55,.2,.03],[.04,.16,.42]];
  const clamp=(x,a,b)=>Math.max(a,Math.min(b,x));
  const rand=i=>{const x=Math.sin(i*127.1+39.7)*43758.5453;return x-Math.floor(x);};
  function glyphTexture(){
    const c=document.createElement('canvas');c.width=2048;c.height=128;
    const x=c.getContext('2d');x.fillStyle='#000';x.fillRect(0,0,2048,128);
    let u=8,i=0;
    while(u<2040){
      const w=52+rand(i+20)*58,spacing=10+rand(i+53)*20;
      x.save();x.translate(u,0);x.scale(w/100,1);
      x.strokeStyle='rgba(255,255,255,'+(.50+rand(i+13)*.50)+')';
      x.lineWidth=12+rand(i+41)*3;x.lineJoin='round';x.lineCap='round';x.beginPath();
      const top=28+rand(i+8)*10,bot=99-rand(i+19)*8;
      if(i%4===0){x.moveTo(5,bot);x.lineTo(5,top);x.lineTo(88,top);x.quadraticCurveTo(98,top,98,top+12);x.lineTo(98,72);x.lineTo(40,72);x.lineTo(40,54);}
      if(i%4===1){x.moveTo(5,bot);x.lineTo(72,bot);x.quadraticCurveTo(96,bot,96,75);x.lineTo(96,top);x.lineTo(26,top);x.lineTo(26,66);x.lineTo(62,66);}
      if(i%4===2){x.moveTo(12,top);x.lineTo(82,top);x.quadraticCurveTo(95,top,95,43);x.lineTo(95,bot);x.lineTo(19,bot);x.lineTo(19,58);x.lineTo(56,58);}
      if(i%4===3){x.moveTo(2,bot);x.lineTo(36,bot);x.lineTo(36,top);x.lineTo(96,top);x.lineTo(96,69);x.lineTo(64,69);}
      x.stroke();x.restore();u+=w+spacing;i++;
    }
    const t=new THREE.CanvasTexture(c);t.wrapS=THREE.RepeatWrapping;t.minFilter=THREE.LinearMipMapLinearFilter;return t;
  }
  function radiusAt(y,r){
    // A smooth asymmetric egg of revolution: fullest below the middle, narrow
    // open ends. Cubic Hermite interpolation preserves a continuous tangent.
    const x=[-.06,0,.10,.25,.40,.50,.75,.90,1,1.06];
    const v=[0,.20,.42,.93,1,.88,.65,.54,.20,0];
    const t=(y-.20)/2.30;let i=0;while(i<x.length-2&&t>x[i+1])i++;
    const h=x[i+1]-x[i],u=clamp((t-x[i])/h,0,1);
    const m=j=>j===0?0:j===x.length-1?0:(v[j+1]-v[j-1])/(x[j+1]-x[j-1]);
    return 1.16*r*Math.max(0,(2*u*u*u-3*u*u+1)*v[i]+(u*u*u-2*u*u+u)*h*m(i)+(-2*u*u*u+3*u*u)*v[i+1]+(u*u*u-u*u)*h*m(i+1));
  }
  function smooth(x){x=clamp(x,0,1);return x*x*(3-2*x);}
  function taper(t){return 1;}
  function edgeOffset(t,side){
    return (.003*Math.sin(t*397+side*17)+.005*Math.sin(t*193+side*9)-side*.015*Math.pow(Math.max(0,Math.sin(t*283+side*3)*Math.cos(t*59)),6))*taper(t);
  }
  // Surface construction: each cross-section follows the egg radius
  // at its own height. No banking, camera-dependent deformation or height bend.
  function ribbonPoint(t,s,r,w,turns,offset,halo){
    t=Math.min(t,(2.38-.20)/2.30);
    const distance=s*w*.5*taper(t)*(halo?1.85:1)+(halo?0:edgeOffset(t,s)*Math.abs(s));
    const y=Math.min(2.38,.20+2.30*t+distance),theta=t*TAU*turns+offset;
    const rr=radiusAt(y,r)+(halo?.004:0);
    return new THREE.Vector3(Math.sin(theta)*rr,y,Math.cos(theta)*rr);
  }
  function geometry(r,w,turns,offset,halo,n){
    n=n||112;const p=[],uv=[],ts=[],ix=[],m=halo?1:3;
    for(let i=0;i<=n;i++){
      const t=i/n;
      for(let j=0;j<=m;j++){
        const v=j/m,point=ribbonPoint(t,v*2-1,r,w,turns,offset,halo);
        p.push(point.x,point.y,point.z);uv.push(t,v);ts.push(t);
        if(i<n&&j<m){const a=i*(m+1)+j,b=a+m+1;ix.push(a,b,a+1,b,b+1,a+1);}
      }
    }
    return buffer(p,uv,ts,ix);
  }
  function buffer(p,uv,ts,ix){const g=new THREE.BufferGeometry();g.setAttribute('position',new THREE.Float32BufferAttribute(p,3));g.setAttribute('uv',new THREE.Float32BufferAttribute(uv,2));g.setAttribute('aT',new THREE.Float32BufferAttribute(ts,1));g.setIndex(ix);g.computeVertexNormals();return g;}
  function terminalDistances(r,w,turns){
    const arc=[0],n=1024;let previous=ribbonPoint(0,0,r,w,turns,0,false);
    for(let i=1;i<=n;i++){const next=ribbonPoint(i/n,0,r,w,turns,0,false);arc.push(arc[i-1]+next.distanceTo(previous));previous=next;}
    return g=>{const ts=g.attributes.aT.array,distances=Array.from(ts,t=>{const f=clamp(t,0,1)*n,i=Math.min(n-1,Math.floor(f)),s=arc[i]+(arc[i+1]-arc[i])*(f-i);return Math.min(s,arc[n]-s);});g.setAttribute('aEndDistance',new THREE.Float32BufferAttribute(distances,1));};
  }
  function licks(r,w,turns,offset){
    const p=[],uv=[],ts=[],ix=[],anchors=[],seeds=[],fs=[];
    for(let k=0;k<36;k++){
      const end=k>=32,side=k%2?1:-1,t=end?([.004,.034,.966,.996][k-32]):.025+.95*(Math.floor(k/2)+rand(k+91)*.7)/16;
      const root=ribbonPoint(t,side,r,w,turns,offset,false),theta=Math.atan2(root.x,root.z),y0=root.y,r0=Math.hypot(root.x,root.z);
      const anchor=[root.x,root.y,root.z],length=end?.18+rand(k)*.12:.10+rand(k+12)*.12;
      const n=end?6:4,base=p.length/3;
      for(let j=0;j<=n;j++){
        const f=j/n,a=theta-f*length/Math.max(.15,r0);
        const fall=length*f*(2.30/(TAU*turns*Math.max(.15,r0)));
        const y=y0-Math.min(fall,Math.max(.025,y0-.16))+side*.018*f*f;
        const rr=Math.max(r0*.65,radiusAt(y,r)+(r0-radiusAt(y0,r)))+.045*f*f;
        const width=(end?.022:.011+rand(k+8)*.008)*Math.pow(1-f,1.15);
        for(let v=0;v<2;v++){
          p.push(Math.sin(a)*rr,y+(v*2-1)*width,Math.cos(a)*rr);uv.push(f,v);ts.push(t);anchors.push(...anchor);seeds.push(k*1.618);fs.push(f);
        }
        if(j<n){const b=base+j*2;ix.push(b,b+2,b+1,b+2,b+3,b+1);}
      }
    }
    const g=buffer(p,uv,ts,ix);g.setAttribute('aAnchor',new THREE.Float32BufferAttribute(anchors,3));g.setAttribute('aSeed',new THREE.Float32BufferAttribute(seeds,1));g.setAttribute('aF',new THREE.Float32BufferAttribute(fs,1));return g;
  }
  const vertex=`attribute float aT,aEndDistance;varying vec2 vUv;varying float vT,vEndDistance;varying vec3 vWorld;varying float vFacing;
    void main(){vUv=uv;vT=aT;vEndDistance=aEndDistance;vec4 p=modelMatrix*vec4(position,1.);vWorld=p.xyz;
      vec4 vp=viewMatrix*p;vFacing=abs(dot(normalize(normalMatrix*normal),normalize(-vp.xyz)));
      gl_Position=projectionMatrix*vp;}`;
  const flameVertex=`attribute float aT,aSeed,aF,aEndDistance;attribute vec3 aAnchor;uniform float cycle;
    varying vec2 vUv;varying float vT,vEndDistance;varying vec3 vWorld;varying float vPulse;
    void main(){vUv=uv;vT=aT;vEndDistance=aEndDistance;float pulse=.76+.24*sin(cycle*2.+aSeed);
      vec3 p=aAnchor+(position-aAnchor)*(.68+.45*pulse);
      p.y+=aF*.010*sin(cycle*3.+aSeed*2.);vPulse=pulse;
      vec4 wp=modelMatrix*vec4(p,1.);vWorld=wp.xyz;gl_Position=projectionMatrix*viewMatrix*wp;}`;
  const common=`uniform float tier,grow,charring,halfShell,cool;uniform vec3 heat;
    varying vec2 vUv;varying float vT,vEndDistance;varying vec3 vWorld;
    float terminalFade(){return pow(smoothstep(0.,.35,vEndDistance),1.35);}
    float hash(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);}
    void clipShell(){if(vT>grow||grow<=0.)discard;if(halfShell>.5&&vWorld.z<0.)discard;if(halfShell<-.5&&vWorld.z>=0.)discard;}`;
  const fragment=common+`
    uniform sampler2D glyphs;uniform float halo,backFace,glyphScale;uniform vec3 glyphHot,keyCol;varying float vFacing;
    // the top tier burns white-blue: remap by luminance onto a cool ramp
    vec3 coolMap(vec3 c){float l=clamp(dot(c,vec3(.3,.59,.11)),0.,1.);return mix(vec3(.22,.52,.95),vec3(.94,.98,1.),smoothstep(.25,.95,l));}
    void main(){clipShell();float q=abs(vUv.y*2.-1.);float grain=hash(floor(vUv*vec2(1700.,80.)));
      float scorch=smoothstep(.05,.97,charring+(grain-.5)*.27);
      if(halo>.5){float a=pow(max(0.,1.-q),2.)*.32*(.08+.92*tier/5.)*(1.-scorch);if(!gl_FrontFacing)a*=.60;
        a*=terminalFade();if(a<.015)discard;
        gl_FragColor=vec4(mix(vec3(1.,.40,.005),vec3(.30,.62,1.),cool),a);return;}
      vec2 gu=vec2(vUv.x*.95*glyphScale,vUv.y);float mask=texture2D(glyphs,gu).r;
      float near=max(max(texture2D(glyphs,gu+vec2(.0012,0.)).r,texture2D(glyphs,gu-vec2(.0012,0.)).r),max(texture2D(glyphs,gu+vec2(0.,.03)).r,texture2D(glyphs,gu-vec2(0.,.03)).r));
      float key=clamp(near-mask,0.,1.);
      float high=smoothstep(3.,4.,tier),white=smoothstep(4.,5.,tier);
      float radialFacing=abs(vWorld.z)/max(.1,length(vWorld.xz));
      float facing=clamp(vFacing*.60+radialFacing*.40,0.,1.);
      float endHeat=pow(max(0.,sin(vT*3.14159265)),.40);
      float furnace=smoothstep(.02,.56,facing)*mix(.85,1.,endHeat);
      vec3 body=mix(heat,mix(vec3(1.,.54,.075),vec3(1.,.98,.36),furnace),high);body=mix(body,heat,white*furnace);
      vec3 rim=mix(heat*.70,vec3(1.,.45,.05),high);rim=mix(rim,vec3(1.,.76,.30),white);
      vec3 hot=mix(heat,vec3(1.,1.,.87),high);hot=mix(hot,vec3(1.),white);
      float line=(1.-smoothstep(.20,.92,q))*furnace;
      vec3 color=mix(body,rim,smoothstep(.72,1.,q));color=mix(color,hot,line);
      color=mix(color,coolMap(color),cool);
      // glyphs burn one heat tier hotter than their ribbon, set off by a thin dark keyline
      color=mix(color,keyCol,key*.85);color=mix(color,glyphHot,mask);color*=.95+.05*grain;
      float strength=mix(.30,1.,pow(clamp((tier-1.)/3.,0.,1.),.7));
      float a=1.-smoothstep(.94,1.,q);
      if(backFace>.5){
        color=mix(heat*.72,vec3(1.,.62,.10),high);color=mix(color,vec3(1.,.73,.30),white);
        color=mix(color,coolMap(color)*.8,cool);color=mix(color,glyphHot*.7,mask*.45);a*=.50;
      }
      color*=strength;color=mix(color,vec3(.027,.012,.006),scorch*.985);a*=1.-.60*pow(charring,3.);
      a*=terminalFade();if(a<.015)discard;
      gl_FragColor=vec4(color,a);
    }`;
  const flameFragment=common+`varying float vPulse;
    void main(){clipShell();float q=abs(vUv.y*2.-1.);float a=pow(max(0.,1.-q),.40)*(1.-vUv.x*.45)*vPulse*(1.-charring);
      a*=terminalFade()*mix(1.-smoothstep(.25,1.,vUv.x),1.,smoothstep(.30,.35,vEndDistance));if(a<.015)discard;
      vec3 c=mix(heat*.55,heat,1.-q);c=mix(c,vec3(1.,.45,.05),vUv.x*.65*smoothstep(2.,4.,tier));c=mix(c,mix(vec3(.45,.75,1.),vec3(.95,.98,1.),1.-q),cool);
      gl_FragColor=vec4(c,a*(.2+.8*tier/5.)*1.35);}`;
  window.emberEggShape={radiusAt,ribbonPoint,turnsFor:n=>n===1?1.8:1.3,width:(r,rw)=>(rw===undefined?.28:rw)*(r/.85)};
  window.buildEmberEgg=function(opts){
    opts=opts||{};const count=clamp(Math.round(opts.strands||2),1,3),tier=clamp(Math.round(opts.tier||4),1,5);
    const r=opts.radius===undefined?.85:opts.radius,w=(opts.ribW===undefined?.28:opts.ribW)*(r/.85),turns=count===1?1.8:1.3;
    const group=new THREE.Group(),glyphs=glyphTexture(),geometries=[],materials=[];
    const addTerminalDistances=terminalDistances(r,w,turns);
    const shared={glyphs:{value:glyphs},heat:{value:new THREE.Vector3(...HEAT[tier-1])},tier:{value:tier},grow:{value:1},charring:{value:0},halfShell:{value:0},cycle:{value:0},glyphScale:{value:.28/(opts.ribW===undefined?.28:opts.ribW)},cool:{value:tier>=5?1:0},
      glyphHot:{value:new THREE.Vector3(...GLYPH_HOT[tier-1])},keyCol:{value:new THREE.Vector3(...GLYPH_KEY[tier-1])}};
    for(let k=0;k<count;k++){
      const offset=k*TAU/count,band=geometry(r,w,turns,offset,false,opts.facets),glow=geometry(r,w,turns,offset,true),flame=licks(r,w,turns,offset);geometries.push(band,glow,flame);
      [band,glow,flame].forEach(addTerminalDistances);
      for(let layer=0;layer<(opts.game?2:4);layer++){
        const back=layer===0,halo=layer===2,fire=layer===3;
        const uniforms=Object.assign({},shared,{backFace:{value:back?1:0},halo:{value:halo?1:0}});
        const material=new THREE.ShaderMaterial({uniforms,vertexShader:fire?flameVertex:vertex,fragmentShader:fire?flameFragment:fragment,
          side:halo||fire?THREE.DoubleSide:back?THREE.BackSide:THREE.FrontSide,transparent:true,depthWrite:layer===1,blending:halo||fire?THREE.AdditiveBlending:THREE.NormalBlending});
        const mesh=new THREE.Mesh(fire?flame:halo?glow:band,material);mesh.renderOrder=layer;mesh.frustumCulled=false;group.add(mesh);materials.push(material);
      }
    }
    group.userData.triangles=group.children.reduce((s,m)=>s+m.geometry.index.count/3,0);
    group.userData.uniqueTriangles=geometries.reduce((s,g)=>s+g.index.count/3,0);group.userData.drawCalls=materials.length;
    let disposed=false;
    function set(p){p=p||{};if(p.phase!==undefined){group.rotation.y=p.phase;shared.cycle.value=p.phase*count;}
      if(p.grow!==undefined)shared.grow.value=clamp(p.grow,0,1);if(p.char!==undefined)shared.charring.value=clamp(p.char,0,1);
      if(p.half!==undefined)shared.halfShell.value=p.half==='F'?1:p.half==='B'?-1:0;}
    set(opts);return {group,set,dispose(){if(disposed)return;disposed=true;geometries.forEach(g=>g.dispose());materials.forEach(m=>m.dispose());glyphs.dispose();if(group.parent)group.parent.remove(group);}};
  };
})();
