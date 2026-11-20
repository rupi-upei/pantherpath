
import itertools
import time
import urllib.parse

import folium
import requests
import streamlit as st
from streamlit_folium import st_folium

# UPEI main campus, as (longitude, latitude)
UPEI = (-63.1381, 46.2594)
# Free OpenStreetMap services - no API key needed
NOMINATIM = "https://nominatim.openstreetmap.org/search"
OSRM = "https://router.project-osrm.org"
# Nominatim asks every app to identify itself
HEADERS = {"User-Agent": "PantherPath student project (UPEI)"}

st.set_page_config(page_title="PantherPath", page_icon="🐾")


@st.cache_data(show_spinner=False)
def geocode(address):
    """Turn an address into (lon, lat, label). Returns None if not found."""
    params = {
        "q": address,
        "format": "json",
        "limit": 1,
        "countrycodes": "ca",
        "viewbox": "-64.5,47.1,-61.9,45.9",  # box around PEI
        "bounded": 1,
    }
    res = requests.get(NOMINATIM, params=params, headers=HEADERS, timeout=10).json()
    time.sleep(1)  # Nominatim allows max 1 request per second
    if not res:
        return None
    return float(res[0]["lon"]), float(res[0]["lat"]), res[0]["display_name"]


def coord_str(points):
    return ";".join(f"{lon},{lat}" for lon, lat in points)


def get_durations(points):
    """Driving time in seconds between every pair of points."""
    url = f"{OSRM}/table/v1/driving/{coord_str(points)}?annotations=duration"
    return requests.get(url, timeout=15).json()["durations"]


def get_route_shape(points):
    """The actual road path, for drawing on the map."""
    url = f"{OSRM}/route/v1/driving/{coord_str(points)}?overview=full&geometries=geojson"
    geom = requests.get(url, timeout=15).json()["routes"][0]["geometry"]
    return {"type": "Feature", "geometry": geom, "properties": {}}


def best_order(d, n, mode):
    """Try every drop-off order and return the best one.
    Index 0 is UPEI, 1..n are the stops."""
    best, best_score = None, float("inf")
    for perm in itertools.permutations(range(1, n + 1)):
        route = (0,) + perm + (0,)
        legs = [d[a][b] for a, b in zip(route, route[1:])]
        if None in legs:
            continue
        if mode == "fastest":
            score = sum(legs)  # whole trip, including the drive back to UPEI
        else:
            arrivals = list(itertools.accumulate(legs[:-1]))  # when each student gets home
            score = sum(arrivals) / len(arrivals)
        if score < best_score:
            best, best_score = perm, score
    return best


def gmaps_link(points):
    fmt = lambda p: f"{p[1]},{p[0]}"
    params = {
        "api": "1",
        "origin": fmt(UPEI),
        "destination": fmt(UPEI),
        "waypoints": "|".join(fmt(p) for p in points),
        "travelmode": "driving",
    }
    return "https://www.google.com/maps/dir/?" + urllib.parse.urlencode(params)


st.title("🐾 PantherPath")
st.caption("Starts and ends at UPEI. Addresses are not saved anywhere.")

text = st.text_area(
    "Drop-off addresses (one per line)",
    height=150,
    placeholder="25 Kent St, Charlottetown\n100 Main St, Stratford",
)
mode_label = st.radio(
    "Optimize for", ["Fastest total trip", "Lowest average wait for students"]
)

if st.button("Plan route", type="primary"):
    addresses = [a.strip() for a in text.splitlines() if a.strip()]
    if not 1 <= len(addresses) <= 8:
        st.error("Enter between 1 and 8 addresses.")
        st.stop()

    with st.spinner("Finding addresses..."):
        stops = []
        for a in addresses:
            g = geocode(a)
            if g is None:
                st.error(f"Couldn't find: {a}. Try adding the town name.")
                st.stop()
            stops.append(g)

    with st.spinner("Working out the best order..."):
        points = [UPEI] + [(s[0], s[1]) for s in stops]
        d = get_durations(points)
        mode = "fastest" if mode_label.startswith("Fastest") else "fair"
        order = best_order(d, len(stops), mode)
        if order is None:
            st.error("Couldn't find a drivable route for these addresses.")
            st.stop()
        path = [UPEI] + [points[i] for i in order] + [UPEI]
        route_geo = get_route_shape(path)

    # Arrival time for each stop, in seconds from leaving UPEI
    full = (0,) + order + (0,)
    legs = [d[a][b] for a, b in zip(full, full[1:])]
    arrivals = list(itertools.accumulate(legs))

    st.session_state["result"] = {
        "order": order,
        "stops": stops,
        "arrivals": arrivals,
        "route_geo": route_geo,
        "link": gmaps_link([points[i] for i in order]),
    }

# Show the last result (kept in session so it doesn't vanish when you touch the map)
r = st.session_state.get("result")
if r:
    st.subheader("Drop-off order")
    for n, (i, t) in enumerate(zip(r["order"], r["arrivals"]), start=1):
        st.write(f"**{n}.** {r['stops'][i - 1][2]} — about {t / 60:.0f} min")
    st.write(f"Back at UPEI after about **{r['arrivals'][-1] / 60:.0f} min**")
    st.link_button("Open in Google Maps", r["link"])

    m = folium.Map(location=[UPEI[1], UPEI[0]], zoom_start=12)
    folium.GeoJson(r["route_geo"]).add_to(m)
    folium.Marker([UPEI[1], UPEI[0]], tooltip="UPEI", icon=folium.Icon(color="red")).add_to(m)
    for n, i in enumerate(r["order"], start=1):
        lon, lat, label = r["stops"][i - 1]
        folium.Marker([lat, lon], tooltip=f"{n}. {label}").add_to(m)
    st_folium(m, height=450, use_container_width=True)

