cat > README.md <<'EOF'
# PantherPath

A route planner for evening student drop-offs. Enter (or say) up to 8 addresses, and it finds the best order to drop everyone off, starting and ending at UPEI.

> Student project. Not affiliated with UPEI or Panther Patrol.

## The problem

UPEI's Panther Patrol drives students home every hour, up to 5 at a time. The driver has to decide the drop-off order on the fly. A bad order wastes time for the driver and for every student still in the van.

## How it works

1. **Addresses to coordinates** using OpenStreetMap's Nominatim, limited to PEI.
2. **Drive times** between every pair of stops from OSRM, a free routing service.
3. **Best order** by checking every possible order (5 stops = 120 orders, 8 stops = 40,320), so the answer is guaranteed optimal.

Two goals to choose from:
- **Fastest total trip:** shortest round trip for the driver (the Traveling Salesman Problem).
- **Lowest average wait:** gets students home sooner on average (the minimum latency problem).

You can type addresses or speak them. Voice input uses faster-whisper, which runs on the server, so recordings aren't sent to a third party. Nothing is saved.

## Run it locally

Needs Python 3.12.

    python3.12 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    streamlit run app.py

## Built with

Python, Streamlit, Folium, OpenStreetMap (Nominatim, OSRM), faster-whisper

## Limits

- Drive times don't include live traffic.
- The free OpenStreetMap services are fine for a demo, not for heavy daily use.
- Speech can mishear street names, so check the box before planning.
EOF
head -3 README.md
