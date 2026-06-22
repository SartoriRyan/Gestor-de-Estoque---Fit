import React, { useState } from 'react'

export default function Home() {
  const [file, setFile] = useState(null)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)

  const handleFileChange = (e) => {
    setFile(e.target.files[0])
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!file) return
    setLoading(true)
    setResult(null)
    const formData = new FormData()
    formData.append('file', file)

    const res = await fetch('/api/process', {
      method: 'POST',
      body: formData
    })

    if (!res.ok) {
      const text = await res.text()
      alert('Erro: ' + text)
      setLoading(false)
      return
    }

    const data = await res.json()
    setResult(data)
    setLoading(false)
  }

  const downloadXlsx = () => {
    if (!result || !result.xlsx_base64) return
    const byteCharacters = atob(result.xlsx_base64)
    const byteNumbers = new Array(byteCharacters.length)
    for (let i = 0; i < byteCharacters.length; i++) {
      byteNumbers[i] = byteCharacters.charCodeAt(i)
    }
    const byteArray = new Uint8Array(byteNumbers)
    const blob = new Blob([byteArray], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `estoque_atualizado_${new Date().toISOString().slice(0,10)}.xlsx`
    a.click()
    window.URL.revokeObjectURL(url)
  }

  return (
    <main style={{ fontFamily: 'Inter, Arial, sans-serif', padding: 24 }}>
      <h1>🏋️‍♂️ FitStock - Upload & Análise</h1>
      <p>Faça o upload de um arquivo .xlsx com as colunas mínimas: <b>Produto</b>, <b>Estoque atual (sistema)</b>, <b>Estoque Quartinho</b>, <b>Recepção</b>. As colunas de data representam baixas.</p>

      <form onSubmit={handleSubmit} style={{ marginBottom: 16 }}>
        <input type="file" accept=".xlsx, .xls" onChange={handleFileChange} />
        <button type="submit" style={{ marginLeft: 8 }} disabled={loading}>{loading ? 'Processando...' : 'Enviar e Analisar'}</button>
      </form>

      {result && (
        <section>
          <h2>Resumo</h2>
          <div style={{ display: 'flex', gap: 16, marginBottom: 12 }}>
            <div style={{ padding: 12, border: '1px solid #eee', borderRadius: 8 }}>
              <div style={{ fontSize: 12, color: '#666' }}>Itens</div>
              <div style={{ fontSize: 20 }}>{result.metrics.items_count}</div>
            </div>
            <div style={{ padding: 12, border: '1px solid #eee', borderRadius: 8 }}>
              <div style={{ fontSize: 12, color: '#666' }}>Saldo Quartinho (reconciliado)</div>
              <div style={{ fontSize: 20 }}>{result.metrics.total_quartinho}</div>
            </div>
            <div style={{ padding: 12, border: '1px solid #eee', borderRadius: 8 }}>
              <div style={{ fontSize: 12, color: '#666' }}>Saldo Recepção (reconciliado)</div>
              <div style={{ fontSize: 20 }}>{result.metrics.total_recepcao}</div>
            </div>
            <div style={{ padding: 12, border: '1px solid #eee', borderRadius: 8 }}>
              <div style={{ fontSize: 12, color: '#666' }}>Total Movimentado</div>
              <div style={{ fontSize: 20 }}>{result.metrics.total_movimentado}</div>
            </div>
          </div>

          <div style={{ marginTop: 12 }}>
            <h3>Top produtos movimentados</h3>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr>
                  <th style={{ textAlign: 'left', borderBottom: '1px solid #ddd' }}>Produto</th>
                  <th style={{ textAlign: 'right', borderBottom: '1px solid #ddd' }}>Total Saídas</th>
                </tr>
              </thead>
              <tbody>
                {result.top.map((r, i) => (
                  <tr key={i}>
                    <td style={{ padding: '6px 0' }}>{r.Produto}</td>
                    <td style={{ padding: '6px 0', textAlign: 'right' }}>{r['Total Saídas (Datas)']}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div style={{ marginTop: 16 }}>
            <h3>Gaps detectados</h3>
            {result.gaps.length === 0 ? (
              <div style={{ padding: 12, background: '#ECFDF5', borderRadius: 8 }}>Nenhum gap detectado</div>
            ) : (
              <div>
                {result.gaps.map((g,idx) => (
                  <div key={idx} style={{ padding: 12, background: '#FFF1F2', borderRadius: 8, marginBottom: 8 }}>
                    <b>{g.Produto}</b>
                    <div>Quartinho derivado: {g['Quartinho (Derivado do Sistema)']} | Total baixado: {g['Total Saídas (Datas)']} </div>
                    <div style={{ color: '#b91c1c' }}><b>Faltam {Math.abs(g['Quartinho Atual (Calculado)'])} itens no Quartinho.</b></div>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div style={{ marginTop: 18 }}>
            <button onClick={downloadXlsx}>Baixar planilha atualizada</button>
          </div>

        </section>
      )}

    </main>
  )
}
