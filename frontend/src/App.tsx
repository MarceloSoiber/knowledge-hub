const layers = [
  {
    title: "Frontend simples",
    description: "Interface de acompanhamento para ingestão, busca e estado do sistema.",
  },
  {
    title: "Backend FastAPI",
    description: "API principal para documentos, busca semântica e integração com LLM.",
  },
  {
    title: "PostgreSQL + pgvector",
    description: "Base para armazenar fontes, chunks e embeddings vetoriais.",
  },
  {
    title: "MCP Server",
    description: "Ferramentas para clientes MCP acessarem o hub de conhecimento.",
  },
  {
    title: "LLM local ou API",
    description: "Camada configurável para Ollama, OpenAI ou outro provedor compatível.",
  },
];

function App() {
  return (
    <main className="shell">
      <section className="hero">
        <div className="hero__badge">Knowledge Hub</div>
        <h1>Uma base inicial para um hub de conhecimento com busca vetorial e MCP.</h1>
        <p>
          Estrutura pronta para evoluir ingestão de conteúdo, consulta semântica, ferramentas MCP e
          integração com modelos locais ou via API.
        </p>
        <div className="hero__actions">
          <a href="http://localhost:8000/health" target="_blank" rel="noreferrer">
            API health
          </a>
          <a href="http://localhost:5173" target="_blank" rel="noreferrer">
            Frontend
          </a>
        </div>
      </section>

      <section className="grid">
        {layers.map((layer) => (
          <article className="card" key={layer.title}>
            <h2>{layer.title}</h2>
            <p>{layer.description}</p>
          </article>
        ))}
      </section>

      <section className="footer-panel">
        <h2>Próximo passo</h2>
        <p>
          Conectar um pipeline de ingestão, criar migrations, expor ferramentas reais no MCP e ligar
          a UI ao backend.
        </p>
      </section>
    </main>
  );
}

export default App;