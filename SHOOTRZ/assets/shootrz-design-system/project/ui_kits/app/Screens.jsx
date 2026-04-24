// SHOOTRZ App UI Kit — Screens

// ─── LoginScreen ────────────────────────────────────────
const LoginScreen = ({ onLogin }) => {
  const [isSignUp, setIsSignUp] = React.useState(false)
  const [email, setEmail] = React.useState('')
  const [password, setPassword] = React.useState('')
  const inp = {
    width:'100%', background:C.bg.elevated, border:`1px solid ${C.border.default}`,
    borderRadius:12, padding:'14px 16px', fontSize:15, color:C.text.primary,
    fontFamily:"'DM Sans',sans-serif", outline:'none', boxSizing:'border-box',
    transition:'border-color .2s'
  }
  return (
    <div style={{flex:1,display:'flex',flexDirection:'column',alignItems:'center',justifyContent:'center',
      padding:'32px 24px',background:C.bg.primary,overflowY:'auto'}}>
      {/* Logo */}
      <div style={{marginBottom:36,textAlign:'center'}}>
        <img src="../../assets/shootrz-logo.png" alt="SHOOTRZ" style={{height:44,objectFit:'contain'}}/>
        <div style={{fontSize:11,fontWeight:600,color:C.brand.cyan,letterSpacing:2,marginTop:10,textTransform:'uppercase'}}>
          Perfect the Game
        </div>
      </div>
      {/* Form Card */}
      <div style={{width:'100%',background:'rgba(13,17,23,0.75)',border:`1px solid rgba(255,255,255,0.05)`,
        borderRadius:24,padding:24}}>
        <div style={{fontSize:22,fontWeight:700,color:C.text.primary,textAlign:'center',marginBottom:4}}>
          {isSignUp?'Create Account':'Welcome Back'}
        </div>
        <div style={{fontSize:13,color:C.text.secondary,textAlign:'center',marginBottom:24}}>
          {isSignUp?'Start your basketball journey':'Sign in to continue training'}
        </div>
        {isSignUp&&(
          <>
            <div style={{marginBottom:16}}>
              <div style={{fontSize:13,fontWeight:600,color:C.text.secondary,marginBottom:6}}>Full Name</div>
              <input style={inp} placeholder="Your name"/>
            </div>
            <div style={{marginBottom:16}}>
              <div style={{fontSize:13,fontWeight:600,color:C.text.secondary,marginBottom:6}}>Username</div>
              <input style={inp} placeholder="Choose a username"/>
            </div>
          </>
        )}
        <div style={{marginBottom:16}}>
          <div style={{fontSize:13,fontWeight:600,color:C.text.secondary,marginBottom:6}}>Email</div>
          <input style={{...inp,borderColor:email?C.border.strong:C.border.default}}
            placeholder="you@example.com" type="email" value={email} onChange={e=>setEmail(e.target.value)}/>
        </div>
        <div style={{marginBottom:!isSignUp?8:20}}>
          <div style={{fontSize:13,fontWeight:600,color:C.text.secondary,marginBottom:6}}>Password</div>
          <input style={{...inp,borderColor:password?C.border.strong:C.border.default}}
            placeholder="Min 6 characters" type="password" value={password} onChange={e=>setPassword(e.target.value)}/>
        </div>
        {!isSignUp&&(
          <div style={{textAlign:'right',marginBottom:20}}>
            <span style={{fontSize:13,color:C.brand.cyan,cursor:'pointer'}}>Forgot Password?</span>
          </div>
        )}
        <button onClick={onLogin}
          style={{width:'100%',height:52,background:C.brand.orange,border:'none',borderRadius:12,
            fontFamily:"'DM Sans',sans-serif",fontSize:13,fontWeight:700,letterSpacing:2,
            color:C.text.primary,cursor:'pointer',textTransform:'uppercase',
            boxShadow:'0 4px 20px rgba(232,82,26,0.45)',transition:'transform .1s'}}
          onMouseDown={e=>e.currentTarget.style.transform='scale(0.97)'}
          onMouseUp={e=>e.currentTarget.style.transform='scale(1)'}>
          {isSignUp?'CREATE ACCOUNT':'SIGN IN'}
        </button>
        <div onClick={()=>setIsSignUp(!isSignUp)}
          style={{textAlign:'center',marginTop:16,cursor:'pointer',fontSize:13,color:C.text.secondary}}>
          {isSignUp?'Already have an account? ':'Don\'t have an account? '}
          <span style={{color:C.brand.cyan,fontWeight:600}}>{isSignUp?'Sign In':'Sign Up'}</span>
        </div>
      </div>
      {/* Social */}
      {!isSignUp&&(
        <div style={{width:'100%',marginTop:24}}>
          <div style={{display:'flex',alignItems:'center',marginBottom:20}}>
            <div style={{flex:1,height:1,background:C.border.default}}/>
            <span style={{fontSize:11,color:C.text.tertiary,margin:'0 14px'}}>OR</span>
            <div style={{flex:1,height:1,background:C.border.default}}/>
          </div>
          <button style={{width:'100%',height:52,background:'#fff',border:'none',borderRadius:12,
            fontFamily:"'DM Sans',sans-serif",fontSize:15,fontWeight:600,color:'#1F1F1F',cursor:'pointer',
            display:'flex',alignItems:'center',justifyContent:'center',gap:10,marginBottom:12}}>
            <svg width="20" height="20" viewBox="0 0 24 24"><path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/><path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/><path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/><path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/></svg>
            Sign in with Google
          </button>
          <button style={{width:'100%',height:52,background:'#000',border:`1px solid ${C.border.default}`,borderRadius:12,
            fontFamily:"'DM Sans',sans-serif",fontSize:15,fontWeight:600,color:'#fff',cursor:'pointer',
            display:'flex',alignItems:'center',justifyContent:'center',gap:10}}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="white"><path d="M18.71 19.5c-.83 1.24-1.71 2.45-3.05 2.47-1.34.03-1.77-.79-3.29-.79-1.53 0-2 .77-3.27.82-1.31.05-2.3-1.32-3.14-2.53C4.25 17 2.94 12.45 4.7 9.39c.87-1.52 2.43-2.48 4.12-2.51 1.28-.02 2.5.87 3.29.87.78 0 2.26-1.07 3.8-.91.65.03 2.47.26 3.64 1.98-.09.06-2.17 1.28-2.15 3.81.03 3.02 2.65 4.03 2.68 4.04-.03.07-.42 1.44-1.38 2.83M13 3.5c.73-.83 1.94-1.46 2.94-1.5.13 1.17-.34 2.35-1.04 3.19-.69.85-1.83 1.51-2.95 1.42-.15-1.15.41-2.35 1.05-3.11z"/></svg>
            Sign in with Apple
          </button>
        </div>
      )}
    </div>
  )
}

// ─── HomeScreen ─────────────────────────────────────────
const HomeScreen = ({ onNavigate }) => {
  const sessions = [
    { id:1, date:'Today', score:82, shots:6 },
    { id:2, date:'Yesterday', score:74, shots:4 },
    { id:3, date:'3 days ago', score:91, shots:8 },
  ]
  return (
    <div style={{flex:1,overflowY:'auto',background:C.bg.primary}}>
      {/* Header */}
      <div style={{display:'flex',alignItems:'center',justifyContent:'space-between',padding:'16px 16px 12px'}}>
        <div>
          <div style={{fontSize:22,fontWeight:700,color:C.text.primary}}>Good afternoon, Marcus</div>
          <div style={{fontSize:11,fontWeight:600,color:C.brand.cyan,letterSpacing:2,marginTop:3,textTransform:'uppercase'}}>
            Perfect the Game
          </div>
        </div>
        <StreakBadge count={7}/>
      </div>

      {/* Hero Card */}
      <div style={{margin:'0 16px 0',background:C.brand.orangeDim,border:`1px solid rgba(232,82,26,0.25)`,
        borderRadius:16,padding:16,display:'flex',alignItems:'center',gap:20}}>
        <ScoreRing score={82} size="lg"/>
        <div style={{flex:1}}>
          <div style={{fontSize:10,fontWeight:600,color:C.text.secondary,letterSpacing:2,textTransform:'uppercase',marginBottom:4}}>Last Session</div>
          <div style={{fontFamily:"'Barlow Condensed',sans-serif",fontSize:42,fontWeight:900,color:C.brand.chrome,lineHeight:1}}>82</div>
          <div style={{marginTop:6}}><TierBadge score={82}/></div>
          <div style={{fontSize:11,color:C.text.tertiary,marginTop:6}}>Today</div>
        </div>
      </div>

      {/* Stats Row */}
      <div style={{display:'flex',gap:10,padding:'16px 16px 0'}}>
        <StatCard icon="basketball" label="Sessions" value={24} color="orange"/>
        <StatCard icon="chart" label="Avg Score" value={78} color="cyan"/>
        <StatCard icon="trophy" label="Best" value={97}/>
      </div>

      {/* CTA */}
      <div style={{padding:'16px 16px 0'}}>
        <PrimaryButton label="Analyze Shot" icon="camera" size="lg" fullWidth onClick={()=>onNavigate('analyze')}/>
      </div>

      {/* Coach J */}
      <div onClick={()=>onNavigate('chat')}
        style={{margin:'12px 16px 0',background:C.brand.cyanDim,border:`1px solid rgba(0,212,255,0.2)`,
          borderRadius:16,padding:'14px 16px',display:'flex',alignItems:'center',gap:12,cursor:'pointer'}}
        onMouseOver={e=>e.currentTarget.style.opacity='.85'} onMouseOut={e=>e.currentTarget.style.opacity='1'}>
        <div style={{width:40,height:40,borderRadius:20,background:C.brand.cyan,display:'flex',alignItems:'center',
          justifyContent:'center',fontSize:17,fontWeight:700,color:C.bg.primary,flexShrink:0}}>J</div>
        <div style={{flex:1}}>
          <div style={{fontSize:15,fontWeight:600,color:C.text.primary}}>Coach J</div>
          <div style={{fontSize:13,color:C.text.secondary,marginTop:2}}>Ask me anything about your game...</div>
        </div>
        <Icon name="chevron" size={16} color={C.brand.cyan}/>
      </div>

      {/* Recent Sessions */}
      <div style={{padding:'20px 16px 0'}}>
        <SectionHeader title="Recent Sessions" action="See all" onAction={()=>onNavigate('progress')}/>
        <div style={{display:'flex',flexDirection:'column',gap:10}}>
          {sessions.map(s=>(
            <AnalysisCard key={s.id} date={s.date} score={s.score} shotCount={s.shots}
              onClick={()=>onNavigate('progress')}/>
          ))}
        </div>
      </div>
      <div style={{height:20}}/>
    </div>
  )
}

// ─── ProgressScreen ──────────────────────────────────────
const ProgressScreen = () => {
  const [period, setPeriod] = React.useState('month')
  const sessions = [
    { id:1, date:'Apr 23, 2026', score:82, shots:6 },
    { id:2, date:'Apr 22, 2026', score:74, shots:4 },
    { id:3, date:'Apr 20, 2026', score:91, shots:8 },
    { id:4, date:'Apr 18, 2026', score:67, shots:5 },
    { id:5, date:'Apr 15, 2026', score:58, shots:3 },
  ]
  // Simple line chart
  const scores = [58, 67, 74, 82, 91]
  const labels = ['Apr 15','Apr 18','Apr 20','Apr 22','Apr 23']
  const max = 100, min = 0, W = 270, H = 90
  const pts = scores.map((s,i)=>`${(i/(scores.length-1))*W},${H-(s/max)*H}`)
  const pathD = `M ${pts.join(' L ')}`
  return (
    <div style={{flex:1,overflowY:'auto',background:C.bg.primary,paddingTop:4}}>
      {/* Period Pills */}
      <div style={{display:'flex',gap:8,padding:'12px 16px'}}>
        {['week','month','all'].map(p=>(
          <div key={p} onClick={()=>setPeriod(p)}
            style={{flex:1,textAlign:'center',padding:'8px 0',borderRadius:9999,border:`1px solid ${p===period?C.brand.orange:C.border.default}`,
              background:p===period?C.brand.orange:'transparent',cursor:'pointer',
              fontSize:13,fontWeight:600,color:p===period?C.text.primary:C.text.secondary}}>
            {p==='all'?'All Time':p.charAt(0).toUpperCase()+p.slice(1)}
          </div>
        ))}
      </div>
      {/* Overall Score */}
      <div style={{margin:'0 16px',background:C.brand.orangeDim,border:`1px solid rgba(232,82,26,0.25)`,
        borderRadius:16,padding:'16px',display:'flex',alignItems:'center',gap:20}}>
        <ScoreRing score={78} size="lg"/>
        <div>
          <div style={{fontSize:10,fontWeight:600,color:C.text.secondary,letterSpacing:2,textTransform:'uppercase'}}>Average Score</div>
          <div style={{fontFamily:"'Barlow Condensed',sans-serif",fontSize:38,fontWeight:900,color:C.brand.chrome,lineHeight:1}}>78</div>
          <div style={{fontSize:13,color:C.text.tertiary,marginTop:4}}>5 sessions</div>
        </div>
      </div>
      {/* Chart */}
      <div style={{margin:'16px 16px 0',background:C.bg.secondary,border:`1px solid ${C.border.default}`,borderRadius:16,padding:16}}>
        <div style={{fontSize:13,fontWeight:700,color:C.text.primary,marginBottom:12}}>Score Trend</div>
        <svg width="100%" viewBox={`0 0 ${W} ${H+20}`} style={{overflow:'visible'}}>
          <defs>
            <linearGradient id="chartGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#E8521A" stopOpacity=".25"/>
              <stop offset="100%" stopColor="#E8521A" stopOpacity="0"/>
            </linearGradient>
          </defs>
          <path d={`${pathD} L ${W},${H} L 0,${H} Z`} fill="url(#chartGrad)"/>
          <path d={pathD} fill="none" stroke={C.brand.orange} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"/>
          {scores.map((s,i)=>(
            <circle key={i} cx={(i/(scores.length-1))*W} cy={H-(s/max)*H} r="4"
              fill={C.brand.orangeLight} stroke={C.brand.orange} strokeWidth="2"/>
          ))}
          {labels.map((l,i)=>(
            <text key={i} x={(i/(labels.length-1))*W} y={H+16} textAnchor="middle"
              fontSize="9" fill={C.text.tertiary}>{l}</text>
          ))}
        </svg>
      </div>
      {/* Session History */}
      <div style={{padding:'16px 16px 0'}}>
        <SectionHeader title="Session History"/>
        <div style={{display:'flex',flexDirection:'column',gap:10}}>
          {sessions.map(s=><AnalysisCard key={s.id} date={s.date} score={s.score} shotCount={s.shots} onClick={()=>{}}/>)}
        </div>
      </div>
      <div style={{height:20}}/>
    </div>
  )
}

// ─── ChatScreen ──────────────────────────────────────────
const ChatScreen = () => {
  const [messages, setMessages] = React.useState([
    { id:'g', role:'assistant', content:"What's up! I'm Coach J, your AI basketball coach. I can review your shot form, suggest drills, and help you level up. What would you like to work on?" }
  ])
  const [input, setInput] = React.useState('')
  const [typing, setTyping] = React.useState(false)
  const listRef = React.useRef()
  const CHIPS = ['Review my last shot','Give me a drill plan','Fix my follow-through']
  const RESPONSES = {
    'Review my last shot': "Looking at your last session — you scored 82 overall. Your release angle was excellent at 89°, but your knee bend (74%) is slightly low. Try bending deeper before your shot for more power and consistency.",
    'Give me a drill plan': "Here's a 3-drill plan for today:\n1. 🏀 Form Shooting (10 min) — 5 feet from basket, focus on follow-through\n2. Mid-Range Pull-Ups (10 min) — elbow drive, 3 spots\n3. Free Throws (5 min) — lock in your routine",
    'Fix my follow-through': "For follow-through: snap your wrist fully on release so your fingers point down. Hold the pose until the ball hits the rim. Your data shows you're releasing too early — try holding the follow-through for a full second after each shot.",
  }
  const send = (text) => {
    const t = text.trim(); if(!t) return
    const uid = `u${Date.now()}`
    setMessages(prev=>[...prev,{id:uid,role:'user',content:t}])
    setInput('')
    setTyping(true)
    setTimeout(()=>{
      setTyping(false)
      const reply = RESPONSES[t]||"Great question! Let me analyze that for you. Keep working on your fundamentals — consistency is key. Try recording another session and I'll give you more specific feedback."
      setMessages(prev=>[...prev,{id:`a${Date.now()}`,role:'assistant',content:reply}])
    }, 1200)
  }
  React.useEffect(()=>{ if(listRef.current) listRef.current.scrollTop=listRef.current.scrollHeight },[messages,typing])
  const hasExtra = messages.length>1
  return (
    <div style={{flex:1,display:'flex',flexDirection:'column',background:C.bg.primary,minHeight:0}}>
      {/* Header */}
      <div style={{display:'flex',alignItems:'center',gap:12,padding:'12px 16px',borderBottom:`1px solid ${C.border.subtle}`,flexShrink:0}}>
        <div style={{width:36,height:36,borderRadius:18,background:C.brand.cyan,display:'flex',alignItems:'center',
          justifyContent:'center',fontSize:14,fontWeight:700,color:C.bg.primary}}>J</div>
        <div style={{flex:1}}>
          <div style={{fontSize:15,fontWeight:600,color:C.text.primary}}>Coach J</div>
          <div style={{fontSize:11,color:C.brand.cyan}}>AI Basketball Coach</div>
        </div>
        <div onClick={()=>setMessages([messages[0]])} style={{cursor:'pointer',padding:4}}>
          <Icon name="refresh" size={18} color={C.text.tertiary}/>
        </div>
      </div>
      {/* Messages */}
      <div ref={listRef} style={{flex:1,overflowY:'auto',padding:'12px 16px'}}>
        {messages.map(m=><ChatBubble key={m.id} message={m.content} role={m.role}/>)}
        {typing&&(
          <div style={{display:'flex',alignItems:'flex-end',gap:8,marginBottom:10}}>
            <div style={{width:30,height:30,borderRadius:15,background:C.brand.cyan,display:'flex',alignItems:'center',justifyContent:'center',fontSize:13,fontWeight:700,color:C.bg.primary}}>J</div>
            <div style={{background:C.bg.elevated,border:`1px solid ${C.border.default}`,borderRadius:'18px 18px 18px 4px',padding:'10px 16px',display:'flex',gap:4,alignItems:'center'}}>
              {[0,1,2].map(i=><div key={i} style={{width:6,height:6,borderRadius:3,background:C.text.tertiary,animation:`pulse 1.2s ease-in-out ${i*0.2}s infinite`}}/>)}
            </div>
          </div>
        )}
      </div>
      {/* Quick chips */}
      {!hasExtra&&(
        <div style={{display:'flex',gap:8,flexWrap:'wrap',padding:'0 16px 10px',flexShrink:0}}>
          {CHIPS.map(c=>(
            <div key={c} onClick={()=>send(c)} style={{background:C.brand.cyanDim,border:`1px solid rgba(0,212,255,0.2)`,
              borderRadius:9999,padding:'7px 14px',fontSize:12,fontWeight:600,color:C.brand.cyan,cursor:'pointer'}}>
              {c}
            </div>
          ))}
        </div>
      )}
      {/* Input */}
      <div style={{display:'flex',gap:8,alignItems:'flex-end',padding:'10px 16px 12px',borderTop:`1px solid ${C.border.subtle}`,flexShrink:0}}>
        <input value={input} onChange={e=>setInput(e.target.value)}
          onKeyDown={e=>e.key==='Enter'&&!e.shiftKey&&(e.preventDefault(),send(input))}
          placeholder="Ask Coach J..." style={{flex:1,background:C.bg.secondary,border:'none',borderRadius:24,
            padding:'11px 16px',fontSize:15,color:C.text.primary,fontFamily:"'DM Sans',sans-serif",outline:'none'}}/>
        <button onClick={()=>send(input)} style={{width:40,height:40,borderRadius:20,background:C.brand.orange,
          border:'none',cursor:'pointer',display:'flex',alignItems:'center',justifyContent:'center',flexShrink:0,
          boxShadow:'0 4px 12px rgba(232,82,26,0.35)',opacity:input.trim()?1:0.4}}>
          <Icon name="send" size={15} color={C.text.primary}/>
        </button>
      </div>
    </div>
  )
}

// ─── AnalyzeScreen ───────────────────────────────────────
const AnalyzeScreen = () => (
  <div style={{flex:1,display:'flex',flexDirection:'column',alignItems:'center',justifyContent:'center',
    background:C.bg.primary,padding:24,gap:20}}>
    <div style={{width:100,height:100,borderRadius:50,background:C.brand.orangeDim,border:`2px solid rgba(232,82,26,0.35)`,
      display:'flex',alignItems:'center',justifyContent:'center',boxShadow:'0 0 40px rgba(232,82,26,0.2)'}}>
      <Icon name="camera" size={44} color={C.brand.orange}/>
    </div>
    <div style={{textAlign:'center'}}>
      <div style={{fontSize:22,fontWeight:700,color:C.text.primary,marginBottom:8}}>Analyze Your Shot</div>
      <div style={{fontSize:14,color:C.text.secondary,lineHeight:1.6,maxWidth:280}}>
        Record or upload a video of your shot. Our AI will analyze your form and give you a detailed breakdown.
      </div>
    </div>
    <div style={{display:'flex',flexDirection:'column',gap:10,width:'100%'}}>
      <PrimaryButton label="Record Shot" icon="camera" size="lg" fullWidth/>
      <PrimaryButton label="Upload Video" variant="ghost" size="lg" fullWidth/>
    </div>
  </div>
)

// ─── ProfileScreen ───────────────────────────────────────
const ProfileScreen = ({ onLogout }) => {
  const rows = [
    { icon:'settings', label:'Account Settings' },
    { icon:'basketball', label:'My Drills' },
    { icon:'barbell', label:'Workout History' },
    { icon:'logout', label:'Sign Out', danger:true, action:onLogout },
  ]
  return (
    <div style={{flex:1,overflowY:'auto',background:C.bg.primary}}>
      {/* Avatar */}
      <div style={{display:'flex',flexDirection:'column',alignItems:'center',padding:'28px 16px 20px'}}>
        <div style={{width:76,height:76,borderRadius:38,background:C.brand.orangeDim,border:`2px solid rgba(232,82,26,0.4)`,
          display:'flex',alignItems:'center',justifyContent:'center',marginBottom:12,
          fontSize:30,fontFamily:"'Barlow Condensed',sans-serif",fontWeight:900,color:C.brand.orange}}>M</div>
        <div style={{fontSize:20,fontWeight:700,color:C.text.primary}}>Marcus Williams</div>
        <div style={{fontSize:13,color:C.text.secondary,marginTop:3}}>@marcus_w</div>
        <div style={{marginTop:8}}><StreakBadge count={7}/></div>
      </div>
      {/* Stats */}
      <div style={{display:'flex',gap:10,padding:'0 16px 20px'}}>
        <StatCard icon="basketball" label="Sessions" value={24} color="orange"/>
        <StatCard icon="chart" label="Avg Score" value={78} color="cyan"/>
        <StatCard icon="trophy" label="Best" value={97}/>
      </div>
      {/* Settings Rows */}
      <div style={{padding:'0 16px'}}>
        {rows.map((r,i)=>(
          <div key={i} onClick={r.action} style={{display:'flex',alignItems:'center',gap:14,padding:'14px 16px',
            background:C.bg.secondary,borderRadius:14,marginBottom:8,cursor:'pointer',border:`1px solid ${C.border.default}`}}
            onMouseOver={e=>e.currentTarget.style.opacity='.8'} onMouseOut={e=>e.currentTarget.style.opacity='1'}>
            <Icon name={r.icon} size={20} color={r.danger?C.error:C.text.secondary}/>
            <span style={{flex:1,fontSize:15,fontWeight:500,color:r.danger?C.error:C.text.primary}}>{r.label}</span>
            {!r.danger&&<Icon name="chevron" size={16} color={C.text.tertiary}/>}
          </div>
        ))}
      </div>
      <div style={{height:20}}/>
    </div>
  )
}

Object.assign(window, { LoginScreen, HomeScreen, ProgressScreen, ChatScreen, AnalyzeScreen, ProfileScreen })
