#!/bin/bash
echo ""
echo "╔══════════════════════════════════════════╗"
echo "║   Workday Agent (Groq) — Setup           ║"
echo "╚══════════════════════════════════════════╝"
echo ""

echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

echo ""
echo "🎭 Installing Playwright Chromium browser..."
playwright install chromium

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Place your resume PDF here and name it: resume.pdf"
echo "  2. Set your Groq API key:"
echo "     export GROQ_API_KEY='gsk_your-key-here'"
echo "  3. Run: streamlit run app.py"
echo ""
echo "Get a FREE Groq API key at: https://console.groq.com"
