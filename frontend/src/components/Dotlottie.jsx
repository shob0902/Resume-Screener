import React, { useEffect, useRef, useState } from 'react'

export default function Dotlottie({ src, width = 300, height = 300, className = '', debug = false }){
  const containerRef = useRef(null)
  const [ready, setReady] = useState(!!(typeof customElements !== 'undefined' && customElements.get && customElements.get('dotlottie-wc')))

  useEffect(()=>{
    function mount(){
      if (!containerRef.current) return
      containerRef.current.innerHTML = ''
        // ensure the container has space so the webcomponent can render
        try{
          containerRef.current.style.minWidth = typeof width === 'number' ? width + 'px' : width
          containerRef.current.style.minHeight = typeof height === 'number' ? height + 'px' : height
        }catch(e){}
      const el = document.createElement('dotlottie-wc')
      el.setAttribute('src', src)
      // ensure attributes are passed as attributes (boolean attributes)
      el.setAttribute('autoplay', '')
      el.setAttribute('loop', '')
      el.style.width = typeof width === 'number' ? width + 'px' : width
      el.style.height = typeof height === 'number' ? height + 'px' : height
      // make sure the mounted element takes layout space
      el.style.display = 'block'
      el.style.width = typeof width === 'number' ? width + 'px' : width
      el.style.height = typeof height === 'number' ? height + 'px' : height
      containerRef.current.appendChild(el)
      // mark container as loaded
      containerRef.current.classList.add('dotlottie-loaded')
    }

    if (typeof customElements !== 'undefined' && customElements.get && customElements.get('dotlottie-wc')){
      setReady(true)
      mount()
      return
    }

    // dynamically load the webcomponent script (module)
    const script = document.createElement('script')
    script.type = 'module'
    script.src = 'https://unpkg.com/@lottiefiles/dotlottie-wc@0.8.1/dist/dotlottie-wc.js'
    script.onload = ()=>{
      setReady(true)
      // small timeout to allow customElements to register
      setTimeout(()=>{ mount() }, 50)
    }
    script.onerror = ()=>{
      // mark ready so fallback stays visible
      setReady(false)
    }
    document.head.appendChild(script)

    return ()=>{
      // don't remove the script on unmount to avoid reloading repeatedly
    }
  }, [src, width, height])

  return (
    <div ref={containerRef} className={`${className} ${debug ? 'debug' : ''}`} style={{display:'flex',alignItems:'center',justifyContent:'center'}}>
      {!ready && (
        // fallback visual in case the component is not yet loaded or fails
        <div style={{display:'flex',flexDirection:'column',alignItems:'center',gap:8}}>
          <img src="/loader.png" alt="animation" style={{width: width, height: height, objectFit: 'contain'}} />
          <div style={{color:'#0f172a', opacity:0.7, fontSize:12}}>Animation loading or blocked — showing fallback</div>
        </div>
      )}
    </div>
  )
}
