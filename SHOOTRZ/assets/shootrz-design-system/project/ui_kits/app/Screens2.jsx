// SHOOTRZ — Extended Screens: Onboarding, Results, Workouts, Achievements

// ─── Count-up hook for score reveals ──────────────────────
const useCountUp = (target, ms=1400, delay=200) => {
  const [v, setV] = React.useState(0)
  React.useEffect(()=>{
    const start = performance.now() + delay
    let raf
    const tick = (now) => {
      if (now < start) { raf = requestAnimationFrame(tick); return }
      const t = Math.min(1, (now-start)/ms)
      const eased = 1 - Math.pow(1-t, 3)
      setV(Math.round(target * eased))
      if (t<1) raf = requestAnimationFrame(tick)
    }
    raf = requestAnimationFrame(tick)
    return ()=>cancelAnimationFrame(raf)
  }, [target])
  return v
}

// ─── OnboardingScreen ────────────────────────────────────
const OnboardingScreen = ({ onDone }) => {
  const [step, setStep] = React.useState(0)
  const slides = [
    { kicker:'AI-POWERED', title:'Your pocket\nshot coach', body:'Record a shot. Get biomechanics, a score, and personalized drills in seconds.', icon:'camera', accent:C.brand.orange },
    { kicker:'TRACK', title:'See every\nrep improve', body:'Watch your score climb. Streaks, trends, and session history keep you honest.', icon:'chart', accent:C.brand.cyan },
    { kicker:'COACH J', title:'Never train\nalone again', body:'A 24/7 AI coach that knows your shot. Ask anything, get drills instantly.', icon:'chat', accent:C.score.elite },
  ]
  const s = slides[step]
  return (
    <div key={step} style={{flex:1,display:'flex',flexDirection:'column',background:C.bg.primary,padding:'24px 24px 24px',animation:'fadeUp .5s ease-out'}}>
      {/* Progress dots */}
      <div style={{display:'flex',gap:6,justifyContent:'center',marginTop:8,marginBottom:24}}>
        {slides.map((_,i)=>(
          <div key={i} style={{width:i===step?24:6,height:6,borderRadius:3,background:i===step?s.accent:C.border.strong,transition:'all .4s'}}/>
        ))}
      </div>
      {/* Icon halo */}
      <div style={{flex:1,display:'flex',flexDirection:'column',alignItems:'center',justifyContent:'center',gap:28}}>
        <div style={{position:'relative',width:140,height:140}}>
          <div style={{position:'absolute',inset:0,borderRadius:70,background:`radial-gradient(circle, ${s.accent}35 0%, transparent 70%)`,animation:'pulseGlow 3s ease-in-out infinite'}}/>
          <div style={{position:'absolute',inset:20,borderRadius:50,background:`${s.accent}15`,border:`1.5px solid ${s.accent}55`,display:'flex',alignItems:'center',justifyContent:'center'}}>
            <Icon name={s.icon} size={48} color={s.accent}/>
          </div>
        </div>
        <div style={{textAlign:'center'}}>
          <div style={{fontSize:11,fontWeight:700,color:s.accent,letterSpacing:2.5,marginBottom:12}}>{s.kicker}</div>
          <div style={{fontFamily:"'Barlow Condensed',sans-serif",fontSize:38,fontWeight:900,color:C.text.primary,lineHeight:1.05,letterSpacing:-.5,whiteSpace:'pre-line'}}>{s.title}</div>
          <div style={{fontSize:15,color:C.text.secondary,marginTop:14,lineHeight:1.55,maxWidth:280,marginLeft:'auto',marginRight:'auto'}}>{s.body}</div>
        </div>
      </div>
      <div style={{display:'flex',gap:10}}>
        <button onClick={onDone} style={{flex:1,height:50,background:'transparent',border:'none',fontFamily:"'DM Sans',sans-serif",fontSize:13,fontWeight:600,color:C.text.secondary,cursor:'pointer',letterSpacing:1,textTransform:'uppercase'}}>Skip</button>
        <button onClick={()=>step<slides.length-1?setStep(step+1):onDone()}
          style={{flex:2,height:52,background:s.accent,border:'none',borderRadius:14,fontFamily:"'DM Sans',sans-serif",fontSize:13,fontWeight:700,color:s.accent===C.brand.cyan?C.bg.primary:C.text.primary,cursor:'pointer',letterSpacing:2,textTransform:'uppercase',boxShadow:`0 8px 24px ${s.accent}60`,transition:'transform .1s'}}
          onMouseDown={e=>e.currentTarget.style.transform='scale(.97)'} onMouseUp={e=>e.currentTarget.style.transform='scale(1)'}>
          {step<slides.length-1?'Next':'Let\'s Go'}
        </button>
      </div>
    </div>
  )
}

// ─── ResultsScreen — MVP wow moment ──────────────────────
const ResultsScreen = ({ onBack, onAskCoach }) => {
  const score = 82
  const animScore = useCountUp(score, 1600, 400)
  const [showRest, setShowRest] = React.useState(false)
  React.useEffect(()=>{ const t=setTimeout(()=>setShowRest(true), 1400); return ()=>clearTimeout(t) },[])
  const col = getScoreColor(score)
  const metrics = [
    { label:'Release Angle', value:89, unit:'°', ideal:'52° optimal', trend:'+4', good:true },
    { label:'Arc Height', value:76, unit:'%', ideal:'consistent', trend:'+2', good:true },
    { label:'Knee Bend', value:74, unit:'%', ideal:'deeper flex', trend:'-3', good:false },
    { label:'Follow-Through', value:91, unit:'%', ideal:'excellent', trend:'+7', good:true },
    { label:'Balance', value:83, unit:'%', ideal:'steady', trend:'0', good:true },
  ]
  const sz = 180, r = (sz-14)/2, cx=sz/2, cy=sz/2, circ=2*Math.PI*r
  const pct = animScore/100
  return (
    <div style={{flex:1,overflowY:'auto',background:C.bg.primary}}>
      <div style={{display:'flex',alignItems:'center',padding:'8px 16px 4px'}}>
        <div onClick={onBack} style={{cursor:'pointer',padding:6,marginLeft:-6}}>
          <Icon name="chevron" size={20} color={C.text.primary} style={{transform:'rotate(180deg)'}}/>
        </div>
        <div style={{fontSize:10,fontWeight:700,color:C.text.tertiary,letterSpacing:2,marginLeft:4}}>SESSION · 6 SHOTS</div>
      </div>
      {/* Hero score */}
      <div style={{display:'flex',flexDirection:'column',alignItems:'center',padding:'20px 16px 28px',position:'relative'}}>
        <div style={{position:'absolute',top:20,width:260,height:260,borderRadius:130,background:`radial-gradient(circle, ${col}30 0%, transparent 65%)`,filter:'blur(10px)',animation:'pulseGlow 4s ease-in-out infinite'}}/>
        <div style={{fontSize:11,fontWeight:700,color:C.text.secondary,letterSpacing:2.5,marginBottom:10}}>YOUR SCORE</div>
        <div style={{position:'relative',width:sz,height:sz}}>
          <svg width={sz} height={sz} style={{transform:'rotate(-90deg)'}}>
            <circle cx={cx} cy={cy} r={r} fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="10"/>
            <circle cx={cx} cy={cy} r={r} fill="none" stroke={col} strokeWidth="10" strokeLinecap="round"
              strokeDasharray={`${circ*pct} ${circ*(1-pct)}`}
              style={{filter:`drop-shadow(0 0 16px ${col}90)`,transition:'stroke-dasharray .1s linear'}}/>
          </svg>
          <div style={{position:'absolute',inset:0,display:'flex',flexDirection:'column',alignItems:'center',justifyContent:'center'}}>
            <div style={{fontFamily:"'Barlow Condensed',sans-serif",fontSize:88,fontWeight:900,color:col,lineHeight:.9,letterSpacing:-2,textShadow:`0 0 30px ${col}60`}}>{animScore}</div>
            <div style={{fontSize:10,fontWeight:700,color:C.text.tertiary,letterSpacing:2,marginTop:2}}>OF 100</div>
          </div>
        </div>
        <div style={{marginTop:16,opacity:showRest?1:0,transform:showRest?'translateY(0)':'translateY(8px)',transition:'all .5s ease-out'}}>
          <span style={{display:'inline-flex',alignItems:'center',gap:8,background:`${col}20`,border:`1px solid ${col}50`,borderRadius:9999,padding:'8px 16px',fontSize:12,fontWeight:700,color:col,letterSpacing:1.5}}>
            <span>{getScoreTier(score).toUpperCase()} SHOOTER</span>
            <span style={{color:C.text.tertiary}}>·</span>
            <span style={{color:C.success}}>+6 from avg</span>
          </span>
        </div>
      </div>
      {/* Coach insight */}
      <div style={{margin:'0 16px 16px',background:C.brand.cyanDim,border:`1px solid rgba(0,212,255,0.22)`,borderRadius:18,padding:16,opacity:showRest?1:0,transform:showRest?'translateY(0)':'translateY(12px)',transition:'all .5s ease-out .1s'}}>
        <div style={{display:'flex',alignItems:'center',gap:10,marginBottom:8}}>
          <div style={{width:28,height:28,borderRadius:14,background:C.brand.cyan,display:'flex',alignItems:'center',justifyContent:'center',fontSize:12,fontWeight:700,color:C.bg.primary}}>J</div>
          <div style={{fontSize:13,fontWeight:700,color:C.text.primary}}>Coach J says</div>
        </div>
        <div style={{fontSize:14,color:C.text.primary,lineHeight:1.55}}>Your follow-through is elite (91%) — keep snapping that wrist. Biggest unlock: bend your knees deeper on catch-and-shoot. That alone could push you past 90.</div>
        <div onClick={onAskCoach} style={{marginTop:10,fontSize:12,fontWeight:700,color:C.brand.cyan,letterSpacing:1.5,cursor:'pointer',textTransform:'uppercase',display:'inline-flex',alignItems:'center',gap:6}}>Ask a follow-up <Icon name="chevron" size={12} color={C.brand.cyan}/></div>
      </div>
      {/* Metrics */}
      <div style={{padding:'0 16px 16px'}}>
        <div style={{fontSize:11,fontWeight:700,color:C.text.secondary,letterSpacing:2,marginBottom:12}}>BIOMECHANICS</div>
        <div style={{display:'flex',flexDirection:'column',gap:8}}>
          {metrics.map((m,i)=>(
            <div key={m.label} style={{background:C.bg.secondary,border:`1px solid ${C.border.default}`,borderRadius:14,padding:'12px 14px',opacity:showRest?1:0,transform:showRest?'translateY(0)':'translateY(12px)',transition:`all .4s ease-out ${.15+i*.06}s`}}>
              <div style={{display:'flex',alignItems:'baseline',justifyContent:'space-between',marginBottom:6}}>
                <span style={{fontSize:13,fontWeight:600,color:C.text.primary}}>{m.label}</span>
                <div style={{display:'flex',alignItems:'baseline',gap:8}}>
                  <span style={{fontFamily:"'Barlow Condensed',sans-serif",fontSize:22,fontWeight:900,color:m.good?C.success:C.warning,lineHeight:1}}>{m.value}<span style={{fontSize:12,marginLeft:2}}>{m.unit}</span></span>
                  <span style={{fontSize:10,fontWeight:700,color:m.trend.startsWith('+')?C.success:m.trend.startsWith('-')?C.error:C.text.tertiary,letterSpacing:.5}}>{m.trend}</span>
                </div>
              </div>
              <div style={{height:4,background:C.bg.elevated,borderRadius:2,overflow:'hidden'}}>
                <div style={{height:'100%',width:`${m.value}%`,background:m.good?`linear-gradient(90deg,${C.success},#4ade80)`:`linear-gradient(90deg,${C.warning},#fcd34d)`,borderRadius:2,transition:'width 1.2s cubic-bezier(.2,1,.3,1) .3s',transformOrigin:'left'}}/>
              </div>
              <div style={{fontSize:11,color:C.text.tertiary,marginTop:5}}>{m.ideal}</div>
            </div>
          ))}
        </div>
      </div>
      {/* Actions */}
      <div style={{padding:'0 16px 20px',display:'flex',gap:10,flexDirection:'column'}}>
        <PrimaryButton label="Drill This Weakness" icon="barbell" size="lg" fullWidth/>
        <PrimaryButton label="Share Result" variant="ghost" size="md" fullWidth/>
      </div>
    </div>
  )
}

// ─── AnalyzeScreen v2 — camera framing + CTA ─────────────
const AnalyzeScreenV2 = ({ onAnalyze }) => {
  const [recording, setRecording] = React.useState(false)
  const [countdown, setCountdown] = React.useState(0)
  const [analyzing, setAnalyzing] = React.useState(false)
  const start = () => {
    setCountdown(3)
    const iv = setInterval(()=>{
      setCountdown(c=>{
        if (c<=1) { clearInterval(iv); setRecording(true); setTimeout(()=>{setRecording(false); setAnalyzing(true); setTimeout(onAnalyze, 1800)}, 2200); return 0 }
        return c-1
      })
    }, 800)
  }
  return (
    <div style={{flex:1,display:'flex',flexDirection:'column',background:'#000',position:'relative',overflow:'hidden'}}>
      {/* Fake camera view */}
      <div style={{flex:1,background:`radial-gradient(ellipse at 50% 35%, #1a2030 0%, #0a0f18 60%, #000 100%)`,position:'relative'}}>
        {/* Court lines */}
        <svg style={{position:'absolute',inset:0,width:'100%',height:'100%',opacity:.12}} preserveAspectRatio="none" viewBox="0 0 100 100">
          <path d="M 20 80 L 80 80 M 30 60 Q 50 40 70 60 M 45 80 L 55 80 L 55 72 L 45 72 Z" fill="none" stroke="#E8521A" strokeWidth=".4"/>
        </svg>
        {/* Pose overlay dots */}
        {!analyzing && !countdown && (
          <svg style={{position:'absolute',inset:0,width:'100%',height:'100%'}} viewBox="0 0 100 140">
            {[[50,42],[46,52],[54,52],[42,64],[58,64],[46,78],[54,78],[44,92],[56,92]].map(([x,y],i)=>(
              <circle key={i} cx={x} cy={y} r="1.4" fill={C.brand.cyan} style={{filter:`drop-shadow(0 0 3px ${C.brand.cyan})`}}/>
            ))}
            <g stroke={C.brand.cyan} strokeWidth=".6" fill="none" opacity=".7">
              <line x1="50" y1="42" x2="46" y2="52"/><line x1="50" y1="42" x2="54" y2="52"/>
              <line x1="46" y1="52" x2="42" y2="64"/><line x1="54" y1="52" x2="58" y2="64"/>
              <line x1="46" y1="52" x2="46" y2="78"/><line x1="54" y1="52" x2="54" y2="78"/>
              <line x1="46" y1="78" x2="44" y2="92"/><line x1="54" y1="78" x2="56" y2="92"/>
            </g>
          </svg>
        )}
        {/* Framing guide */}
        {!recording && !analyzing && !countdown && (
          <div style={{position:'absolute',inset:40,border:`1.5px dashed ${C.brand.orange}60`,borderRadius:18,pointerEvents:'none'}}>
            <div style={{position:'absolute',bottom:-30,left:0,right:0,textAlign:'center',fontSize:11,fontWeight:700,color:C.brand.orange,letterSpacing:2}}>FRAME YOUR FULL BODY</div>
          </div>
        )}
        {/* Countdown */}
        {countdown>0 && (
          <div key={countdown} style={{position:'absolute',inset:0,display:'flex',alignItems:'center',justifyContent:'center',animation:'popIn .4s ease-out'}}>
            <div style={{fontFamily:"'Barlow Condensed',sans-serif",fontSize:160,fontWeight:900,color:C.brand.orange,textShadow:`0 0 40px ${C.brand.orange}`,lineHeight:1}}>{countdown}</div>
          </div>
        )}
        {/* Recording REC */}
        {recording && (
          <div style={{position:'absolute',top:16,left:16,display:'flex',alignItems:'center',gap:8,background:'rgba(0,0,0,.5)',borderRadius:9999,padding:'6px 12px'}}>
            <div style={{width:10,height:10,borderRadius:5,background:C.error,animation:'pulseGlow 1s ease-in-out infinite'}}/>
            <span style={{fontSize:12,fontWeight:700,color:'#fff',letterSpacing:1}}>REC</span>
          </div>
        )}
        {/* Analyzing overlay */}
        {analyzing && (
          <div style={{position:'absolute',inset:0,background:'rgba(0,0,0,.6)',backdropFilter:'blur(20px)',display:'flex',flexDirection:'column',alignItems:'center',justifyContent:'center',gap:16}}>
            <div style={{position:'relative',width:60,height:60}}>
              <svg width="60" height="60" viewBox="0 0 60 60" style={{animation:'spin 1.2s linear infinite'}}>
                <circle cx="30" cy="30" r="26" fill="none" stroke={C.brand.orange} strokeWidth="3" strokeLinecap="round" strokeDasharray="120 40" opacity=".9"/>
              </svg>
            </div>
            <div style={{fontSize:14,fontWeight:600,color:C.text.primary,letterSpacing:.5}}>Analyzing your form…</div>
            <div style={{fontSize:12,color:C.text.secondary}}>Running pose estimation</div>
          </div>
        )}
        {/* Corner brackets */}
        {[['0,0','tl'],['auto,0','tr'],['0,auto','bl'],['auto,auto','br']].map(([p,k])=>(
          <div key={k} style={{position:'absolute',top:k[0]==='t'?12:'auto',bottom:k[0]==='b'?12:'auto',left:k[1]==='l'?12:'auto',right:k[1]==='r'?12:'auto',width:24,height:24,borderTop:k[0]==='t'?`2px solid ${C.brand.orange}`:'none',borderBottom:k[0]==='b'?`2px solid ${C.brand.orange}`:'none',borderLeft:k[1]==='l'?`2px solid ${C.brand.orange}`:'none',borderRight:k[1]==='r'?`2px solid ${C.brand.orange}`:'none'}}/>
        ))}
      </div>
      {/* Bottom controls */}
      {!analyzing && (
        <div style={{background:'#000',padding:'16px 16px 16px',display:'flex',alignItems:'center',gap:16,flexShrink:0}}>
          <div style={{flex:1,fontSize:12,color:C.text.secondary,lineHeight:1.4}}>
            {recording?<span style={{color:C.error,fontWeight:600}}>Take your shot now…</span>:countdown>0?'Get ready…':'Tap to record. 6–10 sec works best.'}
          </div>
          <button disabled={recording||countdown>0} onClick={start}
            style={{width:66,height:66,borderRadius:33,background:recording?C.error:'transparent',border:`3px solid ${recording?C.error:'#fff'}`,cursor:recording?'default':'pointer',position:'relative',display:'flex',alignItems:'center',justifyContent:'center',transition:'all .2s'}}>
            <div style={{width:recording?22:52,height:recording?22:52,borderRadius:recording?4:26,background:recording?'#fff':C.brand.orange,transition:'all .25s cubic-bezier(.2,1,.3,1)'}}/>
          </button>
          <div style={{flex:1,textAlign:'right'}}>
            <div style={{display:'inline-block',padding:'8px 12px',background:'rgba(255,255,255,.06)',borderRadius:10,fontSize:11,fontWeight:600,color:C.text.secondary,letterSpacing:1}}>UPLOAD</div>
          </div>
        </div>
      )}
    </div>
  )
}

// ─── WorkoutsScreen ──────────────────────────────────────
const WorkoutsScreen = () => {
  const [tab, setTab] = React.useState('for-you')
  const [active, setActive] = React.useState(null)
  const workouts = {
    'for-you': [
      { id:1, title:'Fix Your Knee Bend', duration:'12 min', drills:4, difficulty:'Medium', tag:'FROM LAST SHOT', color:C.brand.orange },
      { id:2, title:'Form Shooting Ladder', duration:'15 min', drills:5, difficulty:'Easy', tag:'BUILD THE BASE', color:C.brand.cyan },
      { id:3, title:'Catch & Shoot Circuit', duration:'20 min', drills:6, difficulty:'Hard', tag:'GAME SPEED', color:C.score.elite },
    ],
    'library': [
      { id:4, title:'Free Throw Routine', duration:'8 min', drills:3, difficulty:'Easy' },
      { id:5, title:'Mid-Range Pull-Ups', duration:'18 min', drills:5, difficulty:'Medium' },
      { id:6, title:'Deep Threes', duration:'25 min', drills:7, difficulty:'Hard' },
    ]
  }
  const list = workouts[tab]
  return (
    <div style={{flex:1,overflowY:'auto',background:C.bg.primary}}>
      <div style={{padding:'12px 16px 8px'}}>
        <div style={{display:'flex',gap:8,background:C.bg.secondary,borderRadius:12,padding:4}}>
          {[['for-you','For You'],['library','Library']].map(([k,l])=>(
            <div key={k} onClick={()=>setTab(k)} style={{flex:1,textAlign:'center',padding:'9px 0',borderRadius:9,background:tab===k?C.bg.elevated:'transparent',fontSize:12,fontWeight:700,letterSpacing:1,color:tab===k?C.text.primary:C.text.secondary,cursor:'pointer',transition:'all .2s'}}>{l}</div>
          ))}
        </div>
      </div>
      {/* Streak calendar */}
      {tab==='for-you' && (
        <div style={{margin:'8px 16px 16px',background:C.bg.secondary,border:`1px solid ${C.border.default}`,borderRadius:16,padding:14}}>
          <div style={{display:'flex',alignItems:'center',justifyContent:'space-between',marginBottom:10}}>
            <div>
              <div style={{fontSize:11,fontWeight:700,color:C.text.secondary,letterSpacing:1.5}}>THIS WEEK</div>
              <div style={{fontSize:18,fontWeight:700,color:C.text.primary,marginTop:2}}>5 of 7 days trained</div>
            </div>
            <div style={{display:'flex',alignItems:'center',gap:5,background:'rgba(232,82,26,0.15)',border:`1px solid rgba(232,82,26,0.3)`,borderRadius:9999,padding:'5px 10px'}}>
              <Icon name="flame" size={13} color={C.brand.orange}/>
              <span style={{fontSize:13,fontWeight:700,color:C.brand.orange}}>7</span>
            </div>
          </div>
          <div style={{display:'flex',gap:6}}>
            {['M','T','W','T','F','S','S'].map((d,i)=>{
              const done = i<5, today = i===4
              return (
                <div key={i} style={{flex:1,display:'flex',flexDirection:'column',alignItems:'center',gap:4}}>
                  <div style={{fontSize:10,fontWeight:600,color:C.text.tertiary}}>{d}</div>
                  <div style={{width:'100%',height:34,borderRadius:8,background:done?C.brand.orange:C.bg.elevated,border:today?`2px solid ${C.brand.cyan}`:`1px solid ${C.border.default}`,display:'flex',alignItems:'center',justifyContent:'center',boxShadow:done?`0 0 12px ${C.brand.orange}50`:'none'}}>
                    {done && <Icon name="check" size={15} color="#fff"/>}
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}
      {/* Workout cards */}
      <div style={{padding:'0 16px',display:'flex',flexDirection:'column',gap:10}}>
        {list.map(w=>(
          <div key={w.id} onClick={()=>setActive(w)} style={{background:C.bg.secondary,border:`1px solid ${w.color?`${w.color}30`:C.border.default}`,borderRadius:16,padding:14,cursor:'pointer',transition:'transform .2s,border-color .2s',display:'flex',alignItems:'center',gap:14}}
            onMouseOver={e=>e.currentTarget.style.borderColor=w.color||C.border.strong} onMouseOut={e=>e.currentTarget.style.borderColor=w.color?`${w.color}30`:C.border.default}>
            <div style={{width:52,height:52,borderRadius:14,background:w.color?`${w.color}20`:C.bg.elevated,border:`1px solid ${w.color?w.color+'40':C.border.default}`,display:'flex',alignItems:'center',justifyContent:'center',flexShrink:0}}>
              <Icon name="barbell" size={22} color={w.color||C.text.secondary}/>
            </div>
            <div style={{flex:1,minWidth:0}}>
              {w.tag && <div style={{fontSize:9,fontWeight:700,color:w.color,letterSpacing:1.5,marginBottom:3}}>{w.tag}</div>}
              <div style={{fontSize:15,fontWeight:700,color:C.text.primary,marginBottom:3}}>{w.title}</div>
              <div style={{fontSize:12,color:C.text.secondary,display:'flex',gap:10}}>
                <span>{w.duration}</span><span style={{color:C.text.tertiary}}>·</span>
                <span>{w.drills} drills</span><span style={{color:C.text.tertiary}}>·</span>
                <span>{w.difficulty}</span>
              </div>
            </div>
            <Icon name="chevron" size={16} color={C.text.tertiary}/>
          </div>
        ))}
      </div>
      {/* Active workout bottom sheet */}
      {active && (
        <div onClick={()=>setActive(null)} style={{position:'absolute',inset:0,background:'rgba(0,0,0,.6)',backdropFilter:'blur(8px)',zIndex:10,display:'flex',alignItems:'flex-end',animation:'fadeIn .2s'}}>
          <div onClick={e=>e.stopPropagation()} style={{width:'100%',background:C.bg.secondary,borderRadius:'28px 28px 0 0',padding:'12px 16px 20px',animation:'slideUp .3s cubic-bezier(.2,1,.3,1)',borderTop:`1px solid ${C.border.default}`}}>
            <div style={{width:40,height:4,background:C.border.strong,borderRadius:2,margin:'0 auto 16px'}}/>
            <div style={{fontSize:11,fontWeight:700,color:active.color,letterSpacing:1.5,marginBottom:4}}>{active.tag||'DRILL PLAN'}</div>
            <div style={{fontSize:22,fontWeight:700,color:C.text.primary,marginBottom:6}}>{active.title}</div>
            <div style={{fontSize:13,color:C.text.secondary,marginBottom:16}}>{active.duration} · {active.drills} drills · {active.difficulty}</div>
            <div style={{display:'flex',flexDirection:'column',gap:8,marginBottom:16}}>
              {['Form shooting · 5 ft','Mid-range pull-ups','Deep knee bend sets','Free throw routine'].slice(0,active.drills||4).map((d,i)=>(
                <div key={i} style={{display:'flex',alignItems:'center',gap:12,padding:'10px 12px',background:C.bg.elevated,borderRadius:10}}>
                  <div style={{width:24,height:24,borderRadius:12,background:active.color+'25',color:active.color,display:'flex',alignItems:'center',justifyContent:'center',fontSize:12,fontWeight:700}}>{i+1}</div>
                  <span style={{flex:1,fontSize:13,color:C.text.primary}}>{d}</span>
                  <span style={{fontSize:11,color:C.text.tertiary}}>3 min</span>
                </div>
              ))}
            </div>
            <PrimaryButton label="Start Workout" icon="basketball" size="lg" fullWidth/>
          </div>
        </div>
      )}
      <div style={{height:20}}/>
    </div>
  )
}

Object.assign(window, { OnboardingScreen, ResultsScreen, AnalyzeScreenV2, WorkoutsScreen, useCountUp })
