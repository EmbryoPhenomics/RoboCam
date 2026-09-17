import os
import time
from pathlib import Path

import cv2
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from tqdm import tqdm
from picamera2 import Picamera2
from app import picam2, stage, leds, experimental_log, coord_data, email
from acquisition import Acquisition
import time  
from picamera2 import Picamera2
import cv2
from tqdm import tqdm
import cv2
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import glob
import json
import os
from itertools import combinations

#from picamera2 import Picamera2

def measure_dot(frame, expected_center=None, crop_size=1000):
    gray = frame[:, :, 0]
    height, width = gray.shape

    if expected_center is None:
        expected_center = (
            width // 2,
            height // 2,
        )

    centre_x, centre_y = map(int, expected_center)
    half = crop_size // 2

    x0 = max(0, centre_x - half)
    x1 = min(width, centre_x + half)
    y0 = max(0, centre_y - half)
    y1 = min(height, centre_y + half)

    crop = gray[y0:y1, x0:x1]

    # No blur: preserve the smallest dot's boundary.
    threshold_value, mask = cv2.threshold(
        crop,
        0,
        255,
        cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU,
    )

    contours, _ = cv2.findContours(
        mask,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE,
    )

    candidates = []

    for contour in contours:
        area = cv2.contourArea(contour)
        perimeter = cv2.arcLength(contour, True)

        if area < 5 or perimeter == 0:
            continue

        circularity = (
            4 * np.pi * area
            / (perimeter * perimeter)
        )

        # Slightly relaxed for small pixelated circles.
        if circularity >= 0.65:
            candidates.append(contour)

    if not candidates:
        raise RuntimeError(
            "No suitable circular dot detected"
        )

    # Within the restricted crop, the dot should be the
    # largest circular object.
    dot = max(candidates, key=cv2.contourArea)

    (local_x, local_y), radius = cv2.minEnclosingCircle(dot)
    diameter_px = 2 * radius

    x = local_x + x0
    y = local_y + y0

    overlay = frame.copy()

    # Convert contour coordinates back to the full image.
    full_dot = dot.copy()
    full_dot[:, 0, 0] += x0
    full_dot[:, 0, 1] += y0

    cv2.drawContours(
        overlay,
        [full_dot],
        -1,
        (255, 0, 0),
        1,
    )

    cv2.circle(
        overlay,
        (round(x), round(y)),
        round(radius),
        (0, 255, 0),
        2,
    )

    cv2.rectangle(
        overlay,
        (x0, y0),
        (x1, y1),
        (0, 255, 255),
        1,
    )

    return diameter_px, overlay, mask

ROOT_DIR = Path("/home/pi/robocam_scale_calibration")
ROOT_DIR.mkdir(parents=True, exist_ok=True)
results=[]

stage.setOrigin()

leds.set(100)

calibration_positions = [
    { "name": "cal_1",
        "x": 23.1,
        "y": 47,
        "analyse": True,
        "expected_diameter_mm": 1.5,
    },
    {
        "name": "cal_2",
        "x": 35.8,
        "y": 47,
        "analyse": True,
        "expected_diameter_mm": 0.60,
    },
    {
        "name": "cal_3",
        "x": 48,
        "y": 47,
        "analyse": False,      # Save image only
        "expected_diameter_mm": None,
    },
    {
        "name": "cal_4",
        "x": 61.5,
        "y": 47,
        "analyse": True,
        "expected_diameter_mm": 0.15,
    },
        {
        "name": "cal_5",
        "x": 74.1,
        "y": 47,
        "analyse": True,
        "expected_diameter_mm": 0.07,
    },
]

import numpy as np
import cv2

import time
import cv2
import numpy as np


def autofocus_scan(
    stage,
    picam2,
    x,
    y,
    z_min,
    z_max,
    z_step=0.1,
    settle_time=0.2,
    output_dir=None,
    scan_name="autofocus",
):
    z_min = max(0.0, float(z_min))
    z_max = max(0.0, float(z_max))
    z_step = float(z_step)

    if z_step <= 0:
        raise ValueError("z_step must be greater than zero")

    if z_max < z_min:
        raise ValueError("z_max must be greater than or equal to z_min")

    focus_results = []
    z_positions = np.arange(
        z_min,
        z_max + z_step / 2,
        z_step,
    )

    for z in z_positions:
        z = max(0.0, float(z))

        stage.moveXY(x, y, z)

        time.sleep(settle_time)

        # A new image is captured at every Z position.
        image = picam2.still_capture(50000, 1, 1)

        if image.ndim == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image

        focus_score = cv2.Laplacian(
            gray,
            cv2.CV_64F,
        ).var()

        focus_results.append({
            "z": z,
            "focus_score": float(focus_score),
        })

        print(f"{scan_name}: z={z:.3f}, focus={focus_score:.2f}")

    best = max(focus_results, key=lambda result: result["focus_score"])
    best_z = best["z"]

    # Finish at the best-focus position.
    stage.moveXY(x, y, best_z)

    if output_dir is not None:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        focus_df = pd.DataFrame(focus_results)
        focus_df.insert(0, "scan_name", scan_name)
        focus_df.insert(1, "x", float(x))
        focus_df.insert(2, "y", float(y))
        focus_df["is_best"] = np.isclose(focus_df["z"], best_z)
        focus_df.to_csv(output_dir / f"{scan_name}_focus.csv", index=False)

        fig, ax = plt.subplots(figsize=(8, 5))
        ax.plot(
            focus_df["z"],
            focus_df["focus_score"],
            marker="o",
            linewidth=2,
            color="#167D8D",
        )
        ax.scatter(
            [best_z],
            [best["focus_score"]],
            color="#D95F02",
            s=80,
            zorder=3,
        )
        ax.axvline(
            best_z,
            color="#D95F02",
            linestyle="--",
            label=f"Best Z = {best_z:.3f}",
        )
        ax.set_title(f"Focus scan: {scan_name} (X={x:.2f}, Y={y:.2f})")
        ax.set_xlabel("Z height")
        ax.set_ylabel("Focus score (variance of Laplacian)")
        ax.grid(alpha=0.25)
        ax.legend()
        fig.tight_layout()
        fig.savefig(output_dir / f"{scan_name}_focus.png", dpi=200)
        plt.close(fig)

    return focus_results, best_z

_, _, z_pos = stage.grabXY()
all_focus_results = []
for cal in calibration_positions:
# Move to first calibration dot - 1.5mm
    #stage.moveXY(cal["x"], cal["y"], z_pos)
    stage.moveXY(cal["x"], cal["y"], z_pos)
    focus, opt_z = autofocus_scan(
        stage,
        picam2,
        cal["x"],
        cal["y"],
        z_pos - 0.5,
        z_pos + 0.5,
        z_step=0.1,
        settle_time=1,
        output_dir=ROOT_DIR,
        scan_name=cal["name"],
    )
    for focus_row in focus:
        all_focus_results.append({
            "calibration": cal["name"],
            "x": cal["x"],
            "y": cal["y"],
            "z": focus_row["z"],
            "focus_score": focus_row["focus_score"],
            "selected_z": opt_z,
        })
    stage.moveXY(cal["x"], cal["y"], opt_z)
    z_pos = opt_z
    frame = picam2.still_capture(50000,1,1)
    filename = ROOT_DIR / f"{cal['name']}.png"
    cv2.imwrite(str(filename), frame)
    # Analyse
    if cal["analyse"]:
        try:
            diameter, overlay, mask = measure_dot(frame, crop_size = 400)
            px_per_mm = diameter/cal['expected_diameter_mm']
            print(f"Diameter = {diameter}, px/mm = {px_per_mm}")
            results.append({
                "name": cal["name"],
                "diameter_px": diameter,
                "diameter_mm": cal["expected_diameter_mm"],
                "px_per_mm": px_per_mm,
                })
        except RuntimeError as e:
            print(f"{cal['name']}: detection failed - {e}")
            overlay = frame.copy()
        cv2.imwrite(str(ROOT_DIR/ f"{cal['name']}_overlay.png"), overlay)
        cv2.imwrite(str(ROOT_DIR/ f"{cal['name']}_mask.png"), overlay)

# Save a combined autofocus table and plot for all calibration positions.
focus_df = pd.DataFrame(all_focus_results)
if not focus_df.empty:
    focus_df.to_csv(ROOT_DIR / "autofocus_results.csv", index=False)

    fig, ax = plt.subplots(figsize=(9, 6))
    for calibration, group in focus_df.groupby("calibration", sort=False):
        group = group.sort_values("z")
        ax.plot(
            group["z"],
            group["focus_score"],
            marker="o",
            linewidth=1.8,
            label=calibration,
        )

    ax.set_title("Autofocus curves across calibration positions")
    ax.set_xlabel("Z height")
    ax.set_ylabel("Focus score (variance of Laplacian)")
    ax.grid(alpha=0.25)
    ax.legend(title="Calibration point")
    fig.tight_layout()
    fig.savefig(ROOT_DIR / "autofocus_curves.png", dpi=200)
    plt.close(fig)

# Save results
df = pd.DataFrame(results)
if df.empty:
    print("No valid calibration measurements.")
else:
    df["deviation_from_median_pct"] = (
        100 * (df["px_per_mm"] - df["px_per_mm"].median()).abs()
        / df["px_per_mm"].median()
    )
    print("\nCalibration results:")
    print(df)
    max_deviation = df["deviation_from_median_pct"].max()
    print(f"\nMedian scale: {df['px_per_mm'].median():.2f} px/mm")
    print(f"Maximum deviation from median: {max_deviation:.2f}%")
    if max_deviation > 5:
        print(
            "\nWARNING: Calibration points differ by more than 5%.\n"
            "No average scale returned. Check dot detection, focus, lighting, or expected dot diameters."
        )
        mean_px_per_mm = None
    else:
        mean_px_per_mm = df["px_per_mm"].mean()
        print(f"\nMean scale: {mean_px_per_mm:.2f} px/mm")
df.to_csv(ROOT_DIR / "calibration_results.csv", index=False)
print(df)
mean_px_per_mm = df["px_per_mm"].mean()
print(f"\nMean scale: {mean_px_per_mm:.2f} px/mm")

