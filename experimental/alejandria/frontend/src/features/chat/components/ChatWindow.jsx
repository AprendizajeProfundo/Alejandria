import React, { useState, useRef } from 'react';
import ReactMarkdown from 'react-markdown';

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
    // Agrega el mensaje del usuario al historial local
    setHistory(h => [...h, { from: 'user', text: message }]);
    setAgentResponses({}); // Reset respuestas
    if (wsRef.current) wsRef.current.close();
    wsRef.current = new window.WebSocket('ws://localhost:8000/v1/ws/chat');
    agentBuffers.current = {}; // reset buffers
    wsRef.current.onopen = () => {
      // Enviar historial junto con el mensaje
      const payload = {
        user_id: 'demo',
        message,
        history: [
          ...history,
          { from: 'user', text: message }
        ]
      };
      wsRef.current.send(JSON.stringify(payload));
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
        // Guarda en historial la respuesta del agente (acumulativo)
        setHistory(h => [...h, { from: 'agent', agent, text: agentBuffers.current[agent] }]);
      } else {
        setFinalResponse(agentBuffers.current[agent]);
        // Guarda en historial la respuesta del manager (acumulativo)
        setHistory(h => [...h, { from: 'agent', agent: 'manager', text: agentBuffers.current[agent] }]);
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

  // Mostrar historial conversacional (usuario y agentes)
  const renderConversationHistory = () => (
    <div style={{
      width: '100%',
      maxHeight: 200,
      overflowY: 'auto',
      background: '#fafdff',
      borderRadius: 12,
      marginBottom: 18,
      padding: '16px 24px',
      boxShadow: '0 2px 8px #b3e0ff22',
      fontSize: 16,
      color: '#1a3a5e',
      border: '1px solid #b3e0ff',
    }}>
      {history.map((item, idx) => (
        <div key={idx} style={{marginBottom:8}}>
          {item.from === 'user' ? (
            <span style={{fontWeight:700, color:'#0072ff'}}>Tú: </span>
          ) : (
            <span style={{fontWeight:700, color:'#00b894'}}>{item.agent || 'Agente'}: </span>
          )}
          <span>{item.text}</span>
        </div>
      ))}
    </div>
  );

  return (
    <div style={{
      minHeight: '100vh',
      minWidth: '100vw',
      width: '100vw',
      height: '100vh',
      position: 'fixed',
      top: 0,
      left: 0,
      zIndex: 0,
      display: 'flex',
      flexDirection: 'row', // Cambia a row para sidebar
      alignItems: 'stretch',
      justifyContent: 'flex-start',
      fontFamily: 'Inter, Arial, sans-serif',
      color: '#fff',
      background: 'linear-gradient(120deg, #eaf6ff 0%, #fafdff 100%)',
      overflow: 'hidden',
    }}>
      {/* Sidebar para historial */}
      <div style={{
        width: 320,
        minWidth: 220,
        maxWidth: 400,
        background: 'rgba(30,40,60,0.97)',
        borderRight: '2px solid #b3e0ff',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        padding: '48px 0 0 0',
        gap: 24,
        boxShadow: '2px 0 16px #b3e0ff22',
      }}>
        <div style={{fontWeight:900, fontSize:28, color:'#b3e0ff', marginBottom:16, letterSpacing:1}}>Historial</div>
        <div style={{color:'#fff', opacity:0.7, fontSize:16, textAlign:'center', padding:'0 18px'}}>
          Aquí aparecerán tus conversaciones previas.
        </div>
        {/* Aquí se listarán las conversaciones en el futuro */}
      </div>
      {/* Main chat area */}
      <div style={{
        flex: 1,
        background: 'rgba(30,40,60,0.95)',
        borderRadius: 0,
        boxShadow: '0 8px 32px 0 rgba(31,38,135,0.37)',
        padding: 48,
        minHeight: '100vh',
        display: 'flex',
        flexDirection: 'column',
        gap: 32,
        alignItems: 'center',
        justifyContent: 'flex-start',
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
          maxHeight: '70vh',
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
          width: 900,
          maxWidth: '90vw',
          margin: '0 auto 32px',
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
                  <div style={{fontSize:16}}>
                    <ReactMarkdown>{text}</ReactMarkdown>
                  </div>
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
            }}>
              <span style={{fontSize: 38, marginRight: 12, color:'#1a3a5e', fontWeight:900}}>🔗</span>
              <ReactMarkdown>{finalResponse}</ReactMarkdown>
              <span style={{fontSize: 38, marginLeft: 12, color: '#1a3a5e', fontWeight:900}}>★</span>
            </div>
          )}
          {history.length === 0 && !loading && (
            <div style={{ color: '#1a3a5e', textAlign: 'center', fontFamily: 'Poppins, Arial, sans-serif', letterSpacing: '0.06em', textTransform: 'uppercase', fontWeight: 700, fontSize: 24 }}>
              ¡Comienza la conversación con la comunidad de agentes!
            </div>
          )}
        </div>
        <div style={{display:'flex',gap:24,marginTop:8,marginBottom:8,justifyContent:'center', width:'100%', flexWrap:'wrap'}}>
          <textarea
            value={message}
            onChange={e => setMessage(e.target.value)}
            rows={3}
            style={{
              width: 700,
              maxWidth: '95vw',
              borderRadius: 12,
              border: 'none',
              padding: 16,
              fontSize: 20,
              background: '#1a2639',
              color: '#fff',
              resize: 'none',
              boxShadow:'0 2px 8px #0072ff22',
              marginRight: 12,
              transition: 'width 0.2s',
            }}
            placeholder="Escribe tu mensaje..."
            disabled={loading}
            onKeyDown={e => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
                setMessage("");
              }
            }}
          />
          <button
            onClick={() => { sendMessage(); setMessage(""); }}
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
              maxWidth: 220,
              width: '100%',
              flex: '1 1 180px',
            }}
          >
            {loading ? 'Enviando...' : 'Enviar'}
          </button>
        </div>
        {error && <div style={{ color: '#ff6b6b', marginTop: 18, textAlign: 'center', fontSize:18 }}>{error}</div>}
      </div>
      {/* <div style={{ color: '#aaa', fontSize: 15, marginTop: 18, opacity: 0.7 }}>
        Alejandría Multiagente Experimental · {new Date().getFullYear()}
      </div> */}
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
