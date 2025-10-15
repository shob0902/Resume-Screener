import React from 'react'
import RadarChart from '../components/RadarChart'
import { useNavigate } from 'react-router-dom'

function ScoreBox({title, score, desc}){
  return (
    <div style={{padding:12, borderRadius:10, background:'rgba(3,157,154,0.04)'}}>
      <div style={{fontWeight:700}}>{title}</div>
      <div style={{fontSize:18, fontWeight:800, color:'var(--accent)'}}>{(score||0).toFixed(1)}/10</div>
      <div className="muted" style={{marginTop:6}}>{desc}</div>
    </div>
  )
}

function Tags({items}){
  return <div style={{display:'flex', flexWrap:'wrap', gap:8}}>{items.map((t,i)=>(<div key={i} style={{background:'#eef2ff', padding:'6px 10px', borderRadius:8, fontSize:13}}>{t}</div>))}</div>
}

function ResumeCard({r}){
  const impact = r.overall_score || 0
  const skills = r.skills_score || 0
  const projectQuality = ((r.experience_score||0) + (r.education_score||0)) / 2
  const experience = r.experience_score || 0
  // radar order matches RadarChart labels (Technical Skills, Experience, Education, Overall)
  const radarPoints = [skills, experience, r.education_score||0, impact]
  return (
    <div className="card" style={{marginBottom:18}}>
      <div style={{display:'flex', justifyContent:'space-between', alignItems:'flex-start', gap:16}}>
        <div style={{flex:1}}>
          <div style={{display:'flex', justifyContent:'space-between', alignItems:'baseline'}}>
            <div>
              <div style={{fontSize:20, fontWeight:800}}>{r.candidate_name || r.filename}</div>
              <div className="muted">{r.email || ''} • {r.phone || ''}</div>
            </div>
            <div style={{textAlign:'right'}}>
              <div style={{fontSize:20, fontWeight:800}}>{(impact||0).toFixed(1)}/10</div>
              <div className="muted">Overall Match</div>
            </div>
          </div>

          <div style={{display:'flex', gap:12, marginTop:12}}>
            <ScoreBox title="Skill Match" score={skills} desc="Technical & role alignment" />
            <ScoreBox title="Experience Fit" score={experience} desc="Relevant work history" />
            <ScoreBox title="Education" score={r.education_score||0} desc="Academic background & certifications" />
          </div>

          <div style={{marginTop:12}}>
            <h4>Extracted Skills</h4>
            <Tags items={(r.skills||['Java','Python','C++','JavaScript','HTML','CSS']).slice(0,30)} />
          </div>

          <div style={{display:'grid', gridTemplateColumns:'1fr 1fr', gap:12, marginTop:12}}>
            <div>
              <h4>Key Strengths</h4>
              <ul className="muted">{(r.strengths||[]).map((s,i)=>(<li key={i}>{s}</li>))}</ul>
            </div>
            <div>
              <h4>Areas for Growth</h4>
              <ul className="muted">{(r.gaps||[]).map((g,i)=>(<li key={i}>{g}</li>))}</ul>
            </div>
          </div>

          <div style={{marginTop:12}}>
            <h4>AI-Generated Justification</h4>
            <div className="muted">{r.justification || 'No justification provided.'}</div>
          </div>
        </div>

        <aside style={{width:300}}>
          <div style={{marginBottom:12}}>
            <div style={{background:'#fff', padding:12, borderRadius:10}}>
              <h4 style={{marginTop:0}}>Candidate Fit Analysis</h4>
              <div style={{display:'flex', alignItems:'center', gap:12}}>
                <div style={{width:160}}>
                  <RadarChart dataPoints={radarPoints} size={160} />
                </div>
                <div>
                  <div className="muted">Technical Skills: {(skills||0).toFixed(1)}</div>
                  <div className="muted">Experience: {(experience||0).toFixed(1)}</div>
                  <div className="muted">Education: {(r.education_score||0).toFixed(1)}</div>
                </div>
              </div>
            </div>
          </div>

          <div style={{background:'#fff', padding:12, borderRadius:10}}>
            <h4 style={{marginTop:0}}>Score Breakdown</h4>
            <div style={{display:'grid', gap:8}}>
              <ScoreBox title="Skill Match" score={skills} desc="How well skills align with the JD" />
              <ScoreBox title="Experience Fit" score={experience} desc="Relevant project history" />
              <ScoreBox title="Education" score={r.education_score||0} desc="Academic background & certifications" />
            </div>
          </div>
        </aside>
      </div>
    </div>
  )
}

export default function Results(){
  const nav = useNavigate()
  const raw = localStorage.getItem('screen_results')
  const data = raw ? JSON.parse(raw) : null

  if(!data){
    return (
      <div className="container">
        <div className="card">No results found. Please run a screening first. <button className="btn" onClick={()=>nav('/screen')}>Go to screening</button></div>
      </div>
    )
  }

  // Deduplicate candidates (by filename, email, or candidate_name) and pick the highest-scoring entry for duplicates
  const rawCandidates = data.shortlisted_candidates || []
  const candidateMap = new Map()
  rawCandidates.forEach((r, idx) => {
    // Prefer email as a stable identifier, then candidate_name, then filename. Normalize to lowercase trim.
    const rawKey = (r.email || r.candidate_name || r.filename || `idx-${idx}`)
    const key = String(rawKey).toLowerCase().trim()
    const existing = candidateMap.get(key)
    if (!existing) candidateMap.set(key, r)
    else {
      // Keep the entry with higher overall_score
      const exScore = Number(existing.overall_score || 0)
      const curScore = Number(r.overall_score || 0)
      if (curScore > exScore) candidateMap.set(key, r)
    }
  })

  // Convert to array and sort by overall_score descending (best first)
  const uniqueCandidates = Array.from(candidateMap.values()).sort((a,b)=> (Number(b.overall_score||0) - Number(a.overall_score||0)))

  const sample = uniqueCandidates[0] || {}

  return (
    <div className="container page-enter">
      <div className="card" style={{marginBottom:18}}>
        <div style={{display:'flex', justifyContent:'space-between', alignItems:'center'}}>
          <div>
            <h2>Candidate Report</h2>
            <div className="muted">{sample.candidate_name || 'Candidate Name'} • {sample.email || 'email@example.com'}</div>
          </div>
          <div style={{textAlign:'right'}}>
            <div style={{fontSize:22, fontWeight:800}}>{(sample.overall_score||0).toFixed(1)}/10</div>
            <div className="muted">Overall Match</div>
          </div>
        </div>
      </div>

      <div className="grid">
        <div>
          <div className="card">
            <h3>Scores Overview</h3>
            <div style={{display:'flex', gap:12}}>
              <ScoreBox title="Skill Match" score={sample.skills_score||0} desc="Technical & role alignment" />
              <ScoreBox title="Experience Fit" score={sample.experience_score||0} desc="Relevant work history" />
              <ScoreBox title="Education" score={sample.education_score||0} desc="Academic background & certifications" />
            </div>
          </div>

          <div className="card" style={{marginTop:12}}>
            <h3>Candidate Fit Analysis</h3>
            <div style={{display:'flex', gap:12, alignItems:'center'}}>
              <div style={{flex:1}}>
                <div className="muted">Radar metrics: Technical Skills, Experience, Education, Overall</div>
                <div style={{display:'flex', gap:8, marginTop:8}}>
                  <div className="muted">Technical Skills: {(sample.skills_score||0).toFixed(1)}</div>
                  <div className="muted">Experience: {(sample.experience_score||0).toFixed(1)}</div>
                  <div className="muted">Education: {(sample.education_score||0).toFixed(1)}</div>
                </div>
              </div>
              <div style={{width:320}}>
                <RadarChart dataPoints={[(sample.skills_score||0),(sample.experience_score||0),(sample.education_score||0),(sample.overall_score||0)]} size={300} />
              </div>
            </div>
          </div>

          <div className="card" style={{marginTop:12}}>
            <h3>Extracted Skills</h3>
            <Tags items={(sample.skills||['C/C++','Java','Python','JavaScript','HTML','CSS','SQL','React','REST APIs']).slice(0,20)} />
          </div>
        </div>

        <aside>
          <div className="card">
            <h3>Score Breakdown</h3>
            <div style={{display:'grid', gap:8}}>
              <ScoreBox title="Skill Match" score={sample.skills_score||0} desc="How well skills align with the JD" />
              <ScoreBox title="Experience Fit" score={sample.experience_score||0} desc="Relevant project history" />
              <ScoreBox title="Education" score={sample.education_score||0} desc="Academic background & certifications" />
            </div>
          </div>

          <div className="card" style={{marginTop:12}}>
            <h3>AI-Generated Justification</h3>
            <div className="muted">{sample.justification || 'No AI justification available.'}</div>
          </div>
        </aside>
      </div>

      <div style={{marginTop:18}}>
  {uniqueCandidates.map((r,idx)=>(<ResumeCard key={r.filename || r.email || r.candidate_name || idx} r={r} />))}
      </div>
    </div>
  )
}
