def closest_rapid_speed(speed_mm_per_minute):
    # Convert speed from mm/min to mm/s
    speed_mm_per_second = speed_mm_per_minute / 60

    # List of predefined RAPID speeds in mm/s
    rapid_speeds = {
        5: 'v5', 10: 'v10', 20: 'v20', 30: 'v30', 40: 'v40',
        50: 'v50', 60: 'v60', 80: 'v80', 100: 'v100', 150: 'v150',
        200: 'v200', 300: 'v300', 400: 'v400', 500: 'v500',
        600: 'v600', 800: 'v800', 1000: 'v1000', 1500: 'v1500',
        2000: 'v2000', 3000: 'v3000', 4000: 'v4000', 5000: 'v5000'
    }
    # Find the closest predefined speed
    closest_speed = min(rapid_speeds.keys(), key=lambda x: abs(x - speed_mm_per_second))
    return rapid_speeds[closest_speed]

print(closest_rapid_speed(850))