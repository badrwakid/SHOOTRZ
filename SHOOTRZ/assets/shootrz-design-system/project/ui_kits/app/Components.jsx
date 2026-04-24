// SHOOTRZ App UI Kit — Core Components
// Shared to window for use in Screens.jsx

const C = {
  bg: { void:'#080A0E', primary:'#0D1117', secondary:'#13181F', elevated:'#1A2030', overlay:'#1F2737' },
  brand: { orange:'#E8521A', orangeLight:'#FF6B2B', orangeDim:'rgba(232,82,26,0.13)', orangeGlow:'rgba(232,82,26,0.25)', cyan:'#00D4FF', cyanLight:'#33DFFF', cyanDim:'rgba(0,212,255,0.09)', chrome:'#C8D0DC', chromeMid:'#8B95A3' },
  text: { primary:'#F0F4F8', secondary:'#8B95A3', tertiary:'#4A5568' },
  border: { subtle:'rgba(255,255,255,0.031)', default:'rgba(255,255,255,0.071)', strong:'rgba(255,255,255,0.125)' },
  score: { elite:'#FFD700', great:'#22C55E', good:'#3B82F6', fair:'#F59E0B', poor:'#EF4444' },
  success:'#22C55E', error:'#EF4444', warning:'#F59E0B'
}

function getScoreTier(s){ return s>=90?'elite':s>=75?'great':s>=60?'good':s>=40?'fair':'poor' }
function getScoreColor(s){ return C.score[getScoreTier(s)] }

// ─── SVG Icons ──────────────────────────────────────────
const Icon = ({ name, size=18, color=C.text.secondary, style={} }) => {
  const icons = {
    home:       <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>,
    camera:     <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"><path d="M23 19a2 2 0 01-2 2H3a2 2 0 01-2-2V8a2 2 0 012-2h4l2-3h6l2 3h4a2 2 0 012 2z"/><circle cx="12" cy="13" r="4"/></svg>,
    chart:      <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>,
    chat:       <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"/></svg>,
    person:     <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"><path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>,
    basketball: <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round"><circle cx="12" cy="12" r="10"/><path d="M4.9 4.9c3.9 3.9 3.9 10.3 0 14.1M19.1 4.9c-3.9 3.9-3.9 10.3 0 14.1M2 12h20M12 2c2 3 2 7 0 10s-2 7 0 10"/></svg>,
    trophy:     <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"><polyline points="8 21 12 21 16 21"/><line x1="12" y1="17" x2="12" y2="21"/><path d="M7 4H4a2 2 0 000 4c0 3.31 2.69 5 6 6 3.31-1 6-2.69 6-6a2 2 0 000-4h-3"/><path d="M5 4h14"/></svg>,
    flame:      <svg width={size} height={size} viewBox="0 0 24 24" fill={color}><path d="M12 2C8 7 6 10 6 14a6 6 0 0012 0c0-4-2-7-6-12z"/></svg>,
    send:       <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z"/></svg>,
    chevron:    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2.5" strokeLinecap="round"><path d="M9 18l6-6-6-6"/></svg>,
    refresh:    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"><polyline points="1 4 1 10 7 10"/><path d="M3.51 15a9 9 0 102.13-9.36L1 10"/></svg>,
    check:      <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2.5" strokeLinecap="round"><polyline points="20 6 9 17 4 12"/></svg>,
    settings:   <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2" strokeLinecap="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83-2.83l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 010-4h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 012.83-2.83l.06.06A1.65 1.65 0 009 4.68a1.65 1.65 0 001-1.51V3a2 2 0 014 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 2.83l-.06.06A1.65 1.65 0 0019.4 9a1.65 1.65 0 001.51 1H21a2 2 0 010 4h-.09a1.65 1.65 0 00-1.51 1z"/></svg>,
    logout:     <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"><path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>,
    barbell:    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2.2" strokeLinecap="round"><line x1="6" y1="12" x2="18" y2="12"/><rect x="2" y="9" width="4" height="6" rx="1"/><rect x="18" y="9" width="4" height="6" rx="1"/><rect x="5" y="10" width="2" height="4" rx=".5"/><rect x="17" y="10" width="2" height="4" rx=".5"/></svg>,
  }
  return <span style={{display:'inline-flex',alignItems:'center',justifyContent:'center',...style}}>{icons[name]||icons.check}</span>
}

// ─── ScoreRing ──────────────────────────────────────────
const ScoreRing = ({ score, size='md' }) => {
  const sz = size==='lg'?72:size==='sm'?44:56
  const r = (sz-8)/2, cx=sz/2, cy=sz/2
  const circ = 2*Math.PI*r
  const pct = score/100
  const col = getScoreColor(score)
  return (
    <div style={{position:'relative',width:sz,height:sz,flexShrink:0}}>
      <svg width={sz} height={sz} style={{transform:'rotate(-90deg)'}}>
        <circle cx={cx} cy={cy} r={r} fill="none" stroke="rgba(255,255,255,0.07)" strokeWidth="4"/>
        <circle cx={cx} cy={cy} r={r} fill="none" stroke={col} strokeWidth="4"
          strokeDasharray={`${circ*pct} ${circ*(1-pct)}`} strokeLinecap="round"
          style={{filter:`drop-shadow(0 0 6px ${col}60)`}}/>
      </svg>
      <div style={{position:'absolute',inset:0,display:'flex',alignItems:'center',justifyContent:'center',
        fontFamily:"'Barlow Condensed',sans-serif",fontSize:sz*0.34,fontWeight:900,color:col,lineHeight:1}}>
        {score}
      </div>
    </div>
  )
}

// ─── TierBadge ─────────────────────────────────────────
const TierBadge = ({ score }) => {
  const tier = getScoreTier(score)
  const col = C.score[tier]
  return (
    <span style={{display:'inline-flex',alignItems:'center',background:`${col}22`,border:`1px solid ${col}44`,
      borderRadius:9999,padding:'3px 10px',fontSize:10,fontWeight:700,letterSpacing:1.5,color:col}}>
      {tier.toUpperCase()}
    </span>
  )
}

// ─── StreakBadge ────────────────────────────────────────
const StreakBadge = ({ count }) => (
  <div style={{display:'flex',alignItems:'center',gap:5,background:'rgba(232,82,26,0.15)',
    border:'1px solid rgba(232,82,26,0.35)',borderRadius:9999,padding:'6px 12px'}}>
    <Icon name="flame" size={13} color={C.brand.orange}/>
    <span style={{fontSize:13,fontWeight:700,color:C.brand.orange}}>{count}</span>
  </div>
)

// ─── StatCard ──────────────────────────────────────────
const StatCard = ({ icon, label, value, color='default' }) => {
  const tint = color==='orange'?C.brand.orange:color==='cyan'?C.brand.cyan:C.brand.chrome
  const bg = color==='orange'?C.brand.orangeDim:color==='cyan'?C.brand.cyanDim:'rgba(255,255,255,0.04)'
  return (
    <div style={{flex:1,background:C.bg.secondary,border:`1px solid ${C.border.default}`,borderRadius:16,
      padding:12,display:'flex',flexDirection:'column',alignItems:'center',gap:4}}>
      <div style={{width:34,height:34,borderRadius:17,background:bg,display:'flex',alignItems:'center',justifyContent:'center'}}>
        <Icon name={icon} size={17} color={tint}/>
      </div>
      <div style={{fontFamily:"'Barlow Condensed',sans-serif",fontSize:22,fontWeight:900,color:C.text.primary,lineHeight:1}}>{value}</div>
      <div style={{fontSize:10,fontWeight:600,color:C.text.secondary,letterSpacing:1,textTransform:'uppercase'}}>{label}</div>
    </div>
  )
}

// ─── PrimaryButton ─────────────────────────────────────
const PrimaryButton = ({ label, icon, variant='orange', size='md', fullWidth=false, onClick }) => {
  const [pressed, setPressed] = React.useState(false)
  const h = size==='lg'?56:size==='sm'?40:48
  const bg = variant==='cyan'?C.brand.cyan:variant==='ghost'?'transparent':variant==='danger'?C.error:C.brand.orange
  const textColor = variant==='ghost'?C.brand.orange:variant==='cyan'?C.bg.primary:C.text.primary
  const shadow = variant==='orange'?`0 4px 16px rgba(232,82,26,0.4)`:variant==='cyan'?`0 4px 16px rgba(0,212,255,0.3)`:'none'
  const border = variant==='ghost'?`1.5px solid rgba(232,82,26,0.5)`:'none'
  return (
    <button onClick={onClick} onMouseDown={()=>setPressed(true)} onMouseUp={()=>setPressed(false)} onMouseLeave={()=>setPressed(false)}
      style={{height:h,width:fullWidth?'100%':'auto',background:bg,border,borderRadius:12,padding:'0 24px',
        display:'flex',alignItems:'center',justifyContent:'center',gap:8,cursor:'pointer',outline:'none',
        boxShadow:shadow,transition:'transform .1s,opacity .1s',transform:pressed?'scale(0.97)':'scale(1)',
        fontFamily:"'DM Sans',sans-serif",fontSize:size==='sm'?11:13,fontWeight:700,letterSpacing:2,
        textTransform:'uppercase',color:textColor}}>
      {icon&&<Icon name={icon} size={size==='sm'?14:17} color={textColor}/>}
      {label}
    </button>
  )
}

// ─── AnalysisCard ──────────────────────────────────────
const AnalysisCard = ({ date, score, shotCount, onClick }) => {
  const col = getScoreColor(score)
  return (
    <div onClick={onClick} style={{background:C.bg.secondary,border:`1px solid ${C.border.default}`,borderRadius:14,
      padding:'12px 16px',display:'flex',alignItems:'center',gap:14,cursor:'pointer',transition:'opacity .15s'}}
      onMouseOver={e=>e.currentTarget.style.opacity='.85'} onMouseOut={e=>e.currentTarget.style.opacity='1'}>
      <ScoreRing score={score} size="sm"/>
      <div style={{flex:1}}>
        <div style={{fontSize:14,fontWeight:600,color:C.text.primary}}>{date}</div>
        {shotCount&&<div style={{fontSize:12,color:C.text.tertiary,marginTop:2}}>{shotCount} shot{shotCount!==1?'s':''}</div>}
      </div>
      <TierBadge score={score}/>
      <Icon name="chevron" size={16} color={C.text.tertiary}/>
    </div>
  )
}

// ─── ChatBubble ────────────────────────────────────────
const ChatBubble = ({ message, role }) => {
  const isUser = role==='user'
  return (
    <div style={{display:'flex',justifyContent:isUser?'flex-end':'flex-start',marginBottom:10}}>
      {!isUser&&(
        <div style={{width:30,height:30,borderRadius:15,background:C.brand.cyan,
          display:'flex',alignItems:'center',justifyContent:'center',
          fontSize:13,fontWeight:700,color:C.bg.primary,flexShrink:0,marginRight:8,alignSelf:'flex-end'}}>J</div>
      )}
      <div style={{maxWidth:'72%',background:isUser?C.brand.orange:C.bg.elevated,
        border:`1px solid ${isUser?C.brand.orangeGlow:C.border.default}`,
        borderRadius:isUser?'18px 18px 4px 18px':'18px 18px 18px 4px',
        padding:'10px 14px',fontSize:14,color:C.text.primary,lineHeight:1.5,
        boxShadow:isUser?`0 2px 10px rgba(232,82,26,0.25)`:'none'}}>
        {message}
      </div>
    </div>
  )
}

// ─── TabBar ────────────────────────────────────────────
const TabBar = ({ active, onNavigate }) => {
  const tabs = [
    { id:'home', label:'Home', icon:'home' },
    { id:'analyze', label:'Analyze', icon:'camera' },
    { id:'progress', label:'Progress', icon:'chart' },
    { id:'chat', label:'Coach J', icon:'chat' },
    { id:'profile', label:'Profile', icon:'person' },
  ]
  return (
    <div style={{display:'flex',background:C.bg.primary,borderTop:`1px solid ${C.border.subtle}`,paddingBottom:8}}>
      {tabs.map(t=>{
        const isActive = t.id===active
        return (
          <div key={t.id} onClick={()=>onNavigate(t.id)}
            style={{flex:1,display:'flex',flexDirection:'column',alignItems:'center',justifyContent:'center',
              padding:'10px 0 4px',cursor:'pointer',gap:3}}>
            <Icon name={t.icon} size={22} color={isActive?C.brand.orange:C.text.tertiary}/>
            <span style={{fontSize:10,fontWeight:600,color:isActive?C.brand.orange:C.text.tertiary,letterSpacing:.3}}>{t.label}</span>
          </div>
        )
      })}
    </div>
  )
}

// ─── SectionHeader ─────────────────────────────────────
const SectionHeader = ({ title, action, onAction }) => (
  <div style={{display:'flex',alignItems:'center',justifyContent:'space-between',marginBottom:10}}>
    <span style={{fontSize:16,fontWeight:700,color:C.text.primary}}>{title}</span>
    {action&&<span onClick={onAction} style={{fontSize:13,color:C.brand.cyan,cursor:'pointer',fontWeight:500}}>{action}</span>}
  </div>
)

// Export everything to window
Object.assign(window, {
  C, getScoreTier, getScoreColor,
  Icon, ScoreRing, TierBadge, StreakBadge, StatCard, PrimaryButton,
  AnalysisCard, ChatBubble, TabBar, SectionHeader
})
