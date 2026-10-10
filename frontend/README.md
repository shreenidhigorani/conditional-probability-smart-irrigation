# IrrigAI frontend (React + Tailwind CSS v4 + Vite)

The app is a presentation: five stages, arrow keys to move. No PPT needed.

## Run
```bash
cd frontend && npm install && npm run dev     # http://localhost:5173
```
Backend: `uvicorn app.main:app --reload --port 8000` (allow CORS origin http://localhost:5173).
Different address? Copy `.env.example` to `.env` and set VITE_API_URL.

## Structure
```
frontend/
├── index.html
├── package.json / vite.config.js / .env.example
├── docs/FRONTEND_PROMPT.md        # prompt to give an AI assistant
└── src/
    ├── main.jsx  App.jsx  index.css  api.js
    ├── lib/decision.js            # zone maths + mock decision (same rule as Python)
    ├── hooks/ useCountUp.js  useStages.js
    └── components/
        StageNav  Stage  Footer     # presentation shell
        SoilCrossSection           # animated field illustration
        InputPanel  ResultPanel    # live decision
        DotGrid  CostBalance  ZoneGauge  Heatmap
        TablesPanel  IndependencePanel
```

## Backend contract (ask Member 4)
- POST /predict -> p_dry_tomorrow, threshold, decision, reason (+ optional n, low_support)
- GET /tables   -> joint, marginal_soil, marginal_rain, conditional = P(dry tomorrow | soil, rain) as {soil:{rain:p}}
  Optional extras the UI uses if present: `counts` ({soil:{rain:n}}) and
  `independence` ({chi2, df, p_value, alpha, conclusion}).

## Before presenting
- `npm run build && npm run preview` for a stable copy; keep screenshots as a fallback.
- Switch Mock mode OFF. Mock numbers are placeholders.
- Text on the Data stage assumes GWETROOT for soil wetness; edit if your team used another variable.
