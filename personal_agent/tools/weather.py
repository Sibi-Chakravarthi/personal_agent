"""Weather lookup via wttr.in — no API key needed."""

import requests


def get_weather(location: str) -> str:
    """Get weather for a location. Pass city name or 'auto' for IP-based."""
    if not location or location.lower() == "auto":
        location = ""

    try:
        url = f"https://wttr.in/{location}?format=j1"
        resp = requests.get(url, timeout=10, headers={"User-Agent": "curl/7.68.0"})
        resp.raise_for_status()
        data = resp.json()

        current = data.get("current_condition", [{}])[0]
        area = data.get("nearest_area", [{}])[0]

        city = area.get("areaName", [{}])[0].get("value", location or "Unknown")
        country = area.get("country", [{}])[0].get("value", "")

        temp_c = current.get("temp_C", "?")
        temp_f = current.get("temp_F", "?")
        feels_c = current.get("FeelsLikeC", "?")
        desc = current.get("weatherDesc", [{}])[0].get("value", "?")
        humidity = current.get("humidity", "?")
        wind_kmh = current.get("windspeedKmph", "?")
        wind_dir = current.get("winddir16Point", "")
        uv = current.get("uvIndex", "?")
        visibility = current.get("visibility", "?")

        lines = [
            f"🌤️  WEATHER — {city}, {country}",
            "─" * 40,
            f"  Condition  : {desc}",
            f"  Temp       : {temp_c}°C / {temp_f}°F (feels like {feels_c}°C)",
            f"  Humidity   : {humidity}%",
            f"  Wind       : {wind_kmh} km/h {wind_dir}",
            f"  UV Index   : {uv}",
            f"  Visibility : {visibility} km",
        ]

        # 3-day forecast
        forecasts = data.get("weather", [])
        if forecasts:
            lines.append(f"\n📅 FORECAST")
            lines.append("─" * 40)
            for day in forecasts[:3]:
                date = day.get("date", "?")
                max_c = day.get("maxtempC", "?")
                min_c = day.get("mintempC", "?")
                desc_d = day.get("hourly", [{}])[4].get("weatherDesc", [{}])[0].get("value", "?") if len(day.get("hourly", [])) > 4 else "?"
                lines.append(f"  {date} : {min_c}°C – {max_c}°C | {desc_d}")

        return "\n".join(lines)

    except requests.exceptions.Timeout:
        return "[ERROR] Weather service timed out."
    except Exception as e:
        return f"[WEATHER ERROR] {e}"
