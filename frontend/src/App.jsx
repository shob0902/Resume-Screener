import React from 'react'
import { Routes, Route, Link } from 'react-router-dom'
import Landing from './pages/Landing'
import Screening from './pages/Screening'
import Results from './pages/Results'
import PageWrapper from './components/PageWrapper'
import { useEffect, useState } from 'react'

export default function App(){
  const [showSplash, setShowSplash] = useState(true)

  useEffect(()=>{
    const t = setTimeout(()=> setShowSplash(false), 4000)
    return ()=> clearTimeout(t)
  },[])
  if (showSplash) {
    return (
      <div className="splash-overlay">
        <dotlottie-wc src="https://lottie.host/f4c13f9d-8c34-4b17-bd30-4d639abd4a7c/m7RBhG8C2c.lottie" style={{width:300,height:300}} autoplay loop></dotlottie-wc>
      </div>
    )
  }

  return (
    <div className="app">
      <header className="topbar">
        <div style={{display:'flex', alignItems:'center', gap:12}}>
          <img src="/loader.png" alt="loader" className="loader-icon" />
          <div className="brand"><Link to="/">Smart Resume Screener</Link></div>
        </div>
      </header>

      <main>
        <Routes>
          <Route path="/" element={<PageWrapper><Landing/></PageWrapper>} />
          <Route path="/screen" element={<PageWrapper><Screening/></PageWrapper>} />
          <Route path="/results" element={<PageWrapper><Results/></PageWrapper>} />
        </Routes>
      </main>
    </div>
  )
}
