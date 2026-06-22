# FitStock - Next.js (API + Frontend) for Vercel

This version converts the Streamlit prototype into a Next.js app with an API endpoint that processes uploaded Excel files and returns an updated workbook plus analysis JSON. It's ready to deploy directly on Vercel.

How to run locally:

1. Install dependencies:
   npm install

2. Run development server:
   npm run dev

3. Open http://localhost:3000

How it works:
- Upload an Excel file (.xlsx) with the required columns:
  - Produto
  - Estoque atual (sistema)
  - Estoque Quartinho
  - Recepção
  - Additional columns are treated as date-columns with quantities (they are summed as "Total Saídas (Datas)")

- The API (/api/process) returns a JSON with computed metrics, top products, gaps, and a base64-encoded XLSX file ready to be downloaded.

Deploy to Vercel:
1. Push this branch to GitHub (already created in this repo under feat/nextjs-vercel).
2. On Vercel, import the repository and select the branch feat/nextjs-vercel.
3. Vercel detects Next.js automatically and will build & deploy.

Notes:
- If you want prettier UI/graphs, we can add chart components and better styling.
