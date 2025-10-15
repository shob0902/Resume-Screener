import React, {useState, useEffect} from 'react'
import axios from 'axios'
import { useNavigate } from 'react-router-dom'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

export default function Screening(){
  const [files, setFiles] = useState([])
  const [role, setRole] = useState('')
  const [busy, setBusy] = useState(false)
  const [showFullLoader, setShowFullLoader] = useState(false)
  const nav = useNavigate()

  useEffect(()=>{
    // Ensure the dotlottie webcomponent is loaded on client when this page is visited
    if (typeof document !== 'undefined' && !document.querySelector('script[data-dotlottie-loader]')){
      const s = document.createElement('script')
      s.type = 'module'
      s.src = 'https://unpkg.com/@lottiefiles/dotlottie-wc@0.8.1/dist/dotlottie-wc.js'
      s.setAttribute('data-dotlottie-loader','true')
      document.head.appendChild(s)
    }
  }, [])

  useEffect(()=>{
    // prevent background scrolling when overlay is visible
    if(typeof document !== 'undefined'){
      if(showFullLoader) document.body.style.overflow = 'hidden'
      else document.body.style.overflow = ''
    }
    return ()=>{ if(typeof document !== 'undefined') document.body.style.overflow = '' }
  }, [showFullLoader])

  function onFileChange(e){
    setFiles(Array.from(e.target.files))
  }

  async function uploadAndMatch(){
    if(!files.length){ alert('Please select at least one PDF resume'); return }
    setBusy(true)
    // show the full-screen animation until backend responds
    setShowFullLoader(true)
    try{
      const form = new FormData()
      files.forEach(f=>form.append('files', f))

      await axios.post(`${API_BASE}/batch-upload`, form, { headers: {'Content-Type':'multipart/form-data'} })

      // After upload, trigger match with job description
      const jdForm = new FormData()
      jdForm.append('job_description', role || '')
      const matchResp = await axios.post(`${API_BASE}/match`, jdForm)

      // Save results to localStorage and navigate to results
      localStorage.setItem('screen_results', JSON.stringify(matchResp.data))
      nav('/results')
    }catch(err){
      console.error(err)
      alert('Error during upload or matching: '+(err.response?.data?.detail||err.message||'Network Error'))
      // hide the full-screen loader so user can retry
      setShowFullLoader(false)
    }finally{
      setBusy(false)
    }
  }

  return (
    <div className="container page-enter">
      {showFullLoader && (
        <div className="screen-overlay" role="status" aria-live="polite" aria-hidden="false">
          <dotlottie-wc src="https://lottie.host/fad050a0-e2d2-4d0d-8f18-aa45f9567066/BLoCNQf3b9.lottie" style={{width:300, height:300}} autoplay loop aria-label="processing" />
        </div>
      )}
  <div aria-hidden={showFullLoader} style={ showFullLoader ? {pointerEvents:'none'} : undefined }>
      <div className="grid">
        <div>
          <div className="card">
            <h2>Screen Resumes</h2>
            <div>
              <label htmlFor="resume-upload" className="btn-label">Upload Resumes (PDF only)</label>
              <input id="resume-upload" className="input-hidden" type="file" multiple accept="application/pdf" onChange={onFileChange} />
              <div className="file-list">
                {files.map((f,idx)=>(<div key={idx} className="muted">{f.name}</div>))}
              </div>
            </div>

            <div style={{marginTop:12}}>
              <label>Job role / description</label>
              <input type="text" value={role} onChange={e=>setRole(e.target.value)} style={{width:'100%', marginTop:6, padding:10, borderRadius:8, border:'1px solid rgba(15,23,42,0.06)'}} placeholder="Enter job title or short role (e.g. Software Engineer)" />
            </div>

            <div style={{marginTop:12}}>
              <button className="btn" onClick={uploadAndMatch} disabled={busy}>{busy? 'Processing...':'Upload & Match'}</button>
            </div>
          </div>
        </div>

        <aside>
          <div className="card">
            <h3>Tips</h3>
            <ul className="muted">
              <li>Upload PDF resumes for best parsing accuracy.</li>
              <li>Paste a clear job description for better semantic matching.</li>
              <li>Results will include a score (out of 10) and suggested improvements.</li>
            </ul>
          </div>

          
        </aside>
  </div>
  </div>
  {/* wrapper end */}
    </div>
  )
}
