import json
import random
from datetime import datetime, timedelta


def _hourly_profile(total, peak_hour, width):
    """Distribute a daily total across 24 hours with a bell-curve around peak_hour."""
    raw = [
        max(0.0, 1.0 - ((h - peak_hour) / width) ** 2)
        for h in range(24)
    ]
    s = sum(raw) or 1.0
    return [round(total * v / s, 1) for v in raw]


def generate_fake_stats(days=180):
    stats = {}
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    current = start_date
    while current <= end_date:
        date_str = current.strftime("%Y-%m-%d")

        # Seasonality: peaks in June (month 6), troughs in December
        month = current.month
        season_mult = 0.3 + 0.7 * (1.0 - abs(month - 6) / 6.0)

        # Random daily weather variation
        weather_mult = random.uniform(0.2, 1.2)
        solar_factor = season_mult * weather_mult

        # Daily totals (Wh)
        # Solar redirected to equipment (water heater)
        redirected = round(4500 * solar_factor, 1)
        # Grid import: higher when solar is weak
        grid_import = round(2000 * (1.5 - season_mult) * random.uniform(0.8, 1.2), 1)
        # Grid export: surplus solar that exceeds equipment capacity
        grid_export = round(max(0.0, redirected * random.uniform(0.1, 0.4) * solar_factor), 1)
        # Active heating time (seconds): roughly proportional to redirected energy
        # Assume ~2000W equipment: Wh / W * 3600 s/h, with some variation
        active_time = int((redirected / 2000.0) * 3600 * random.uniform(0.85, 1.15))

        # Hourly breakdown:
        # - Solar (redirect + export) peaks at solar noon (~13h)
        # - Import peaks in morning (~8h) and evening (~20h)
        h_redirect = _hourly_profile(redirected, peak_hour=13, width=4.5)
        h_export   = _hourly_profile(grid_export,  peak_hour=13, width=3.5)

        # Import: bimodal (morning + evening), modelled as sum of two peaks
        morning = _hourly_profile(grid_import * 0.4, peak_hour=8,  width=2.5)
        evening = _hourly_profile(grid_import * 0.6, peak_hour=20, width=2.5)
        h_import = [round(morning[h] + evening[h], 1) for h in range(24)]

        stats[date_str] = {
            "import":      grid_import,
            "redirect":    redirected,
            "export":      grid_export,
            "active_time": active_time,
            "h_import":    h_import,
            "h_redirect":  h_redirect,
            "h_export":    h_export,
        }

        current += timedelta(days=1)

    with open("stats.json", "w") as f:
        json.dump(stats, f, indent=2)

    print(f"Generated fake stats for {days} days in stats.json")


if __name__ == "__main__":
    generate_fake_stats(180)  # 6 months
