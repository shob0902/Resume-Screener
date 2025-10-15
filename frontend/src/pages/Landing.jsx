import React, { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
// Using a direct image fallback to guarantee visibility while troubleshooting the webcomponent

export default function Landing(){
  const nav = useNavigate()
  const fullText = 'Resume Screener'
  // Two-line typing loop: first line is the main title, second line is a short tagline.
  // Types line1, pauses, appends line2, pauses, clears, repeats infinitely.
  const line1 = 'Resume Screener'
  const line2 = 'Intelligently parse resumes and surface top candidates'
  const [displayText, setDisplayText] = useState('')

  useEffect(()=>{
    let mounted = true
    let phase = 0 // 0: typing line1, 1: pause, 2: typing line2, 3: pause, 4: clearing
    let idx = 0
    let interval = null

    const startTyping = (text, onComplete)=>{
      idx = 0
      interval = setInterval(()=>{
        if(!mounted) return
        setDisplayText(prev => {
          // For typing second line, keep the first line + newline
          if(phase === 2) return line1 + '\n' + text.slice(0, idx+1)
          return text.slice(0, idx+1)
        })
        idx++
        if(idx >= text.length){
          clearInterval(interval)
          interval = null
          onComplete && onComplete()
        }
      }, 50)
    }

    const startCycle = ()=>{
      // Type line1
      phase = 0
      startTyping(line1, ()=>{
        // pause after line1
        phase = 1
        setTimeout(()=>{
          // type line2 appended on new line
          phase = 2
          startTyping(line2, ()=>{
            // pause after both lines visible
            phase = 3
            setTimeout(()=>{
              // clear and restart
              phase = 4
              const clearIntervalId = setInterval(()=>{
                if(!mounted) return
                setDisplayText(prev => {
                  if(prev.length === 0) return ''
                  // Remove characters from the end; when there's a newline, remove second line first
                  return prev.slice(0, -1)
                })
              }, 30)
              // stop clearing when fully cleared and restart cycle
              setTimeout(()=>{
                clearInterval(clearIntervalId)
                if(mounted) startCycle()
              }, 1000)
            }, 1800)
          })
        }, 800)
      })
    }

    startCycle()

    return ()=>{
      mounted = false
      if(interval) clearInterval(interval)
    }
  }, [])
  useEffect(()=>{
    // Inject the dotlottie webcomponent module script on the client only once
    if (typeof document !== 'undefined' && !document.querySelector('script[data-dotlottie-loader]')){
      const s = document.createElement('script')
      s.type = 'module'
      s.src = 'https://unpkg.com/@lottiefiles/dotlottie-wc@0.8.1/dist/dotlottie-wc.js'
      s.setAttribute('data-dotlottie-loader','true')
      document.head.appendChild(s)
    }
  }, [])
  return (
    <div className="container">
      <div className="landing-cards">
        <div className="card">
          <div className="landing-hero">
            <div className="hero-left">
              <h1 className="typing-title">{displayText}<span className="typing-cursor">|</span></h1>
              <div className="landing-animation" style={{display:'flex', alignItems:'center', justifyContent:'center'}}>
                {/* Dynamically load the dotlottie webcomponent script so the bundle doesn't need to include it */}
                <div id="dotlottie-placeholder" style={{width:100, height:100}}>
                  {/* Placeholder while the webcomponent loads */}
                  <img src="/l.png" alt="animation fallback" style={{width:200, height:200, objectFit:'contain', borderRadius:8}} />
                </div>

                {/* Render the dotlottie element. We place it here so React can render it once the module defines the custom element. */}
                <dotlottie-wc src="https://lottie.host/e1230c40-621c-4775-b4ec-3a32b45b14a0/bTmJ34x3RI.lottie" style={{width:100, height:100}} autoplay loop aria-label="animation" />
              </div>
              <p className="muted">Intelligently parse resumes, extract skills, and match them with job descriptions using an LLM-backed scoring engine.</p>
              <p>Upload candidate resumes (PDF) and provide a job description to compute a match score and get tailored improvement suggestions.</p>
              <div style={{marginTop:16}}>
                <button className="btn" onClick={()=>nav('/screen')}>Start Screening</button>
              </div>
            </div>
          </div>
        </div>

        <div className="card">
          <h1 style={{ textAlign: "center" }}>About</h1>
          <p className="muted">This demo UI connects seamlessly to a FastAPI backend, enabling intelligent and automated resume screening.
It allows users to batch-upload multiple PDF resumes and provide a job description for comparison. The backend leverages natural language processing (NLP) to extract key details such as skills, experience, and education from each resume, and computes a match score that quantifies how well each candidate fits the given job description.</p>
        </div>
      </div>
    </div>
  )
}
