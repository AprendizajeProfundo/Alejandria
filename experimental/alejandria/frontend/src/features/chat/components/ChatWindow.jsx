import React, { useState, useRef } from 'react';

export default function ChatWindow() {
  const [message, setMessage] = useState('');
  const [history, setHistory] = useState([]); // [{from, text}] o {type: 'agent', agent, content}
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [finalResponse, setFinalResponse] = useState(null); // Para la respuesta mágica
  const wsRef = useRef(null);
  const agentBuffers = useRef({}); // <--- buffer por agente

  const [agentResponses, setAgentResponses] = useState({}); // {agent: texto}

  const sendMessage = async () => {
    if (!message.trim()) return;
    setLoading(true);
    setError(null);
    setFinalResponse(null); // Reset final
    setHistory(h => [...h, { from: 'user', text: message }]);
    setAgentResponses({}); // Reset respuestas
    if (wsRef.current) wsRef.current.close();
    wsRef.current = new window.WebSocket('ws://localhost:8000/v1/ws/chat');
    agentBuffers.current = {}; // reset buffers
    wsRef.current.onopen = () => {
      wsRef.current.send(JSON.stringify({ user_id: 'demo', message }));
    };
    wsRef.current.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.done) {
        setLoading(false);
        wsRef.current.close();
        return;
      }
      const agent = data.agent_name;
      if (!agentBuffers.current[agent]) agentBuffers.current[agent] = '';
      agentBuffers.current[agent] += data.content;
      if (!data.is_manager) {
        setAgentResponses(prev => ({ ...prev, [agent]: agentBuffers.current[agent] }));
      } else {
        setFinalResponse(agentBuffers.current[agent]);
      }
    };
    wsRef.current.onerror = (e) => {
      setError('No se pudo obtener respuesta. Intenta de nuevo.');
      setLoading(false);
    };
    wsRef.current.onclose = () => {
      setLoading(false);
    };
  };

  // Cambia la fuente global y mayúsculas fijas
  React.useEffect(() => {
    document.body.style.fontFamily = 'Poppins, Arial, sans-serif';
    document.body.style.textTransform = '';
    document.body.style.background = 'linear-gradient(120deg, #eaf6ff 0%, #fafdff 100%)';
    document.body.style.letterSpacing = '0.01em';
    return () => {
      document.body.style.fontFamily = '';
      document.body.style.textTransform = '';
      document.body.style.background = '';
      document.body.style.letterSpacing = '';
    };
  }, []);

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      fontFamily: 'Inter, Arial, sans-serif',
      color: '#fff',
      background: 'linear-gradient(120deg, #eaf6ff 0%, #fafdff 100%)',
    }}>
      <div style={{
        background: 'rgba(30,40,60,0.95)',
        borderRadius: 32,
        boxShadow: '0 8px 32px 0 rgba(31,38,135,0.37)',
        padding: 48,
        width: 1200,
        maxWidth: '99vw',
        minHeight: 900,
        marginBottom: 48,
        display: 'flex',
        flexDirection: 'column',
        gap: 32,
      }}>
        <h1 style={{
          textAlign: 'center',
          letterSpacing: 2,
          fontWeight: 900,
          fontSize: 48,
          marginBottom: 8,
          background: 'linear-gradient(90deg,#00c6ff,#0072ff)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          textShadow: '0 2px 12px #b3e0ff99',
        }}>
          Alejandría Experimental
        </h1>
        <h2 style={{
          textAlign: 'center',
          fontWeight: 400,
          fontSize: 26,
          marginBottom: 24,
          color: '#b3e0ff',
          letterSpacing: 1,
        }}>
          Sistema Multiagente Educativo en Tiempo Real
        </h2>
        <div style={{
          minHeight: 350,
          maxHeight: 600,
          overflowY: 'auto',
          background: 'rgba(255,255,255,0.92)',
          borderRadius: 28,
          padding: 32,
          marginBottom: 32,
          boxShadow: '0 2px 24px 0 #b3e0ff44',
          border: '2px solid #b3e0ff',
          display: 'flex',
          flexDirection: 'column',
          gap: 32,
          transition: 'background 0.5s',
        }}>
          {loading && (
            <div style={{textAlign:'center',margin:'32px 0'}}>
              <div className="lds-ellipsis" style={{display:'inline-block',marginBottom:12}}>
                <div></div><div></div><div></div><div></div>
              </div>
              <div style={{color:'#0072ff',fontWeight:600,fontSize:20,letterSpacing:1}}>Procesando agentes...</div>
            </div>
          )}
          {/* Mostrar respuestas de agentes */}
          {Object.keys(agentResponses).length > 0 && (
            <div style={{marginBottom: 24}}>
              <h3 style={{color:'#0072ff', fontWeight:700, fontSize:22, marginBottom:12, letterSpacing:1}}>Respuestas de los agentes</h3>
              {Object.entries(agentResponses).map(([agent, text]) => (
                <div key={agent} style={{marginBottom:24, background:'#eaf6ff', borderRadius:16, padding:'18px 20px', color:'#1a3a5e', boxShadow:'0 2px 12px #b3e0ff33'}}>
                  <div style={{fontWeight:800, color:'#0072ff', fontSize:18, marginBottom:8, letterSpacing:1}}>{agent}</div>
                  <div style={{fontSize:16, whiteSpace:'pre-line'}}>{text}</div>
                </div>
              ))}
            </div>
          )}
          {/* Síntesis final */}
          {finalResponse && (
            <div id="final-sync" style={{
              background: 'linear-gradient(120deg, #eaf6ff 0%, #b3e0ff 100%)',
              borderRadius: 36,
              margin: '0 auto 32px',
              padding: '48px 54px',
              maxWidth: 800,
              color: '#1a3a5e',
              fontSize: 24,
              fontWeight: 600,
              boxShadow: '0 4px 32px 0 #b3e0ff66',
              textAlign: 'left',
              position: 'relative',
              animation: 'fadeIn 1.2s',
              border: '3px solid #b3e0ff',
              filter: 'drop-shadow(0 0 24px #b3e0ffcc)',
              letterSpacing: '0.01em',
              fontFamily: 'Poppins, Arial, sans-serif',
              textTransform: 'none',
              lineHeight: 1.6,
              whiteSpace: 'pre-line',
            }}>
              <span style={{fontSize: 38, marginRight: 12, color:'#1a3a5e', fontWeight:900}}>🔗</span>
              {finalResponse}
              <span style={{fontSize: 38, marginLeft: 12, color: '#1a3a5e', fontWeight:900}}>★</span>
            </div>
          )}
          {history.length === 0 && !loading && (
            <div style={{ color: '#1a3a5e', textAlign: 'center', fontFamily: 'Poppins, Arial, sans-serif', letterSpacing: '0.06em', textTransform: 'uppercase', fontWeight: 700, fontSize: 24 }}>
              ¡Comienza la conversación con la comunidad de agentes!
            </div>
          )}
        </div>
        <div style={{display:'flex',gap:24,marginTop:8,marginBottom:8,justifyContent:'center'}}>
          <textarea
            value={message}
            onChange={e => setMessage(e.target.value)}
            rows={3}
            style={{
              width: 600,
              borderRadius: 12,
              border: 'none',
              padding: 16,
              fontSize: 20,
              background: '#1a2639',
              color: '#fff',
              resize: 'none',
              boxShadow:'0 2px 8px #0072ff22',
              marginRight: 12,
            }}
            placeholder="Escribe tu mensaje..."
            disabled={loading}
          />
          <button
            onClick={sendMessage}
            disabled={loading || !message.trim()}
            style={{
              minWidth: 180,
              padding: '18px 0',
              borderRadius: 12,
              border: 'none',
              background: 'linear-gradient(90deg,#00c6ff,#0072ff)',
              color: '#fff',
              fontWeight: 800,
              fontSize: 22,
              letterSpacing: 1,
              cursor: loading ? 'not-allowed' : 'pointer',
              transition: 'background 0.2s',
              boxShadow: '0 2px 8px rgba(0,0,0,0.10)',
              marginLeft: 12,
            }}
          >
            {loading ? 'Enviando...' : 'Enviar'}
          </button>
        </div>
        {error && <div style={{ color: '#ff6b6b', marginTop: 18, textAlign: 'center', fontSize:18 }}>{error}</div>}
      </div>
      <div style={{ color: '#aaa', fontSize: 15, marginTop: 18, opacity: 0.7 }}>
        Alejandría Multiagente Experimental · {new Date().getFullYear()}
      </div>
      <style>{`
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;800;900&display=swap');
@keyframes fadeIn { from { opacity: 0; transform: translateY(30px);} to { opacity: 1; transform: none; } }
.lds-ellipsis { display: inline-block; position: relative; width: 80px; height: 24px; }
.lds-ellipsis div { position: absolute; top: 8px; width: 13px; height: 13px; border-radius: 50%; background: #0072ff; animation-timing-function: cubic-bezier(0, 1, 1, 0); }
.lds-ellipsis div:nth-child(1) { left: 8px; animation: lds-ellipsis1 0.6s infinite; }
.lds-ellipsis div:nth-child(2) { left: 8px; animation: lds-ellipsis2 0.6s infinite; }
.lds-ellipsis div:nth-child(3) { left: 32px; animation: lds-ellipsis2 0.6s infinite; }
.lds-ellipsis div:nth-child(4) { left: 56px; animation: lds-ellipsis3 0.6s infinite; }
@keyframes lds-ellipsis1 { 0% { transform: scale(0); } 100% { transform: scale(1); } }
@keyframes lds-ellipsis2 { 0% { transform: translateX(0); } 100% { transform: translateX(24px); } }
@keyframes lds-ellipsis3 { 0% { transform: scale(1); } 100% { transform: scale(0); } }
`}</style>
    </div>
  );
}
