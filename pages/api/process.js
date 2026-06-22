import formidable from 'formidable'
import fs from 'fs'
import XLSX from 'xlsx'

export const config = {
  api: {
    bodyParser: false,
  }
}

const BASE_COLS = ['Produto', 'Estoque atual (sistema)', 'Estoque Quartinho', 'Recepção']

function detectDateCols(headers) {
  return headers.filter(h => !BASE_COLS.includes(h))
}

function toNumber(v) {
  const n = Number(v)
  return isNaN(n) ? 0 : n
}

export default async function handler(req, res) {
  if (req.method !== 'POST') {
    res.status(405).send('Method Not Allowed')
    return
  }

  const form = new formidable.IncomingForm()
  form.parse(req, async (err, fields, files) => {
    if (err) {
      res.status(500).send('Error parsing form')
      return
    }

    const file = files.file
    if (!file) {
      res.status(400).send('No file uploaded')
      return
    }

    const buffer = fs.readFileSync(file.filepath)
    const workbook = XLSX.read(buffer, { type: 'buffer' })
    const sheetName = workbook.SheetNames[0]
    const sheet = workbook.Sheets[sheetName]
    const raw = XLSX.utils.sheet_to_json(sheet, { defval: '' }) // array of objects

    if (raw.length === 0) {
      res.status(400).send('Empty sheet')
      return
    }

    const headers = Object.keys(raw[0])
    const dateCols = detectDateCols(headers)

    // Process each row
    const processed = raw.map(row => {
      const rowCopy = { ...row }
      // ensure numeric for base cols
      rowCopy['Estoque atual (sistema)'] = toNumber(rowCopy['Estoque atual (sistema)'])
      rowCopy['Estoque Quartinho'] = toNumber(rowCopy['Estoque Quartinho'])
      rowCopy['Recepção'] = toNumber(rowCopy['Recepção'])

      // ensure date cols numeric
      let totalSaidas = 0
      for (const dc of dateCols) {
        rowCopy[dc] = toNumber(rowCopy[dc])
        totalSaidas += rowCopy[dc]
      }
      rowCopy['Total Saídas (Datas)'] = totalSaidas

      rowCopy['Quartinho (Derivado do Sistema)'] = rowCopy['Estoque atual (sistema)'] - rowCopy['Recepção']
      rowCopy['Quartinho Diferença'] = rowCopy['Estoque Quartinho'] - rowCopy['Quartinho (Derivado do Sistema)']
      rowCopy['Quartinho Atual (Calculado)'] = rowCopy['Quartinho (Derivado do Sistema)'] - rowCopy['Total Saídas (Datas)']
      rowCopy['Recepção Atual (Calculada)'] = rowCopy['Recepção'] + rowCopy['Total Saídas (Datas)']
      rowCopy['Soma Pós Movimentação'] = rowCopy['Quartinho Atual (Calculado)'] + rowCopy['Recepção Atual (Calculada)']
      rowCopy['Inconsistência com Sistema'] = rowCopy['Estoque atual (sistema)'] - rowCopy['Soma Pós Movimentação']

      return rowCopy
    })

    // Metrics
    const metrics = {
      items_count: processed.length,
      total_quartinho: processed.reduce((s, r) => s + Math.max(0, toNumber(r['Quartinho Atual (Calculado)'])), 0),
      total_recepcao: processed.reduce((s, r) => s + Math.max(0, toNumber(r['Recepção Atual (Calculada)'])), 0),
      total_movimentado: processed.reduce((s, r) => s + toNumber(r['Total Saídas (Datas)']), 0)
    }

    // Top products by movimentado
    const top = [...processed].sort((a,b) => toNumber(b['Total Saídas (Datas)']) - toNumber(a['Total Saídas (Datas)'])).slice(0,10)

    // Gaps
    const gaps = processed.filter(r => toNumber(r['Quartinho Atual (Calculado)']) < 0)

    // Build new workbook with processed data
    const newSheet = XLSX.utils.json_to_sheet(processed)
    const newWb = XLSX.utils.book_new()
    XLSX.utils.book_append_sheet(newWb, newSheet, 'Estoque')
    const xlsxBuffer = XLSX.write(newWb, { bookType: 'xlsx', type: 'buffer' })
    const xlsxBase64 = xlsxBuffer.toString('base64')

    res.status(200).json({ metrics, top, gaps, xlsx_base64: xlsxBase64 })
  })
}
