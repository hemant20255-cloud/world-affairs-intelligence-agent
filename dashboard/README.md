# Intel Dashboard

Streamlit dashboard with 7 tabs (Defence, Geopolitics & World, National, International,
Markets & Gold, CSR & ESG, Sustainable India) plus a live market strip
(Gold $/oz and ₹/10g, Silver, USD/INR, Nifty, Sensex, Brent).

- Sources: Google News RSS (India edition) + direct feeds (The Hindu, ET Defence, Mint,
  The Diplomat, BBC, Al Jazeera, India CSR). Edit `feeds.yaml` to add/remove.
- Prices: Yahoo Finance via `yfinance`. Cached 15 minutes.
- Optional: `DASHBOARD_PASSWORD` to lock the page, `OPENAI_API_KEY` for a "Brief me" AI summary per tab.

## Run locally
```bash
cd dashboard && python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt && streamlit run app.py
```

## Deploy on AWS EC2 (console, ~15 min)
1. EC2 → Launch instance → Ubuntu Server 24.04, **t3.micro** (free tier), region ap-south-1.
2. Key pair: create/download one (or skip and use EC2 Instance Connect).
3. Security group: SSH 22 from **My IP**, HTTP 80 from **My IP** (or Anywhere if you set a password).
4. Launch → select the instance → **Connect** → EC2 Instance Connect.
5. In the terminal:
```bash
export DASHBOARD_PASSWORD='choose-a-strong-one'
# export OPENAI_API_KEY='sk-...'   # optional
curl -fsSL https://raw.githubusercontent.com/hemant20255-cloud/world-affairs-intelligence-agent/main/dashboard/deploy/setup.sh | sudo -E bash
```
6. Open `http://<Public IPv4>/`.

Update later: `sudo git -C /opt/intel pull && sudo systemctl restart intel-dashboard`
Logs: `sudo journalctl -u intel-dashboard -f`

Tip: allocate an **Elastic IP** so the address survives restarts (free while attached to a running instance).
