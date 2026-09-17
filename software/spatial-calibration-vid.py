import os
import time
from pathlib import Path
from threading import Thread

import cv2
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from app import picam2, stage, leds


# Output and camera settings
OUTPUT_ROOT = Path("/home/pi/robocam_scale_calibration")
VIDEO_DURATION = 5
EXPOSURE = 20_000
FPS = 30
ANALOGUE_GAIN = 1
SENSOR_MODE = 0

# The first camera startup is slower than later startups. This delay starts at
# the same time as video_capture() and keeps the first Z move inside the video.
Z_START_DELAY = 3.0
Z_SCAN_DISTANCE = 2.0
FOCUS_SMOOTHING_FRAMES = 3
# Camera setup and the stationary pre-sweep frames are not candidates. With the
# current 3 s movement delay, the Z sweep begins near 2.5-3 s in the MKV.
FOCUS_SEARCH_START_SECONDS = 2.5
MAX_SCALE_DIFFERENCE_PERCENT = 5.0


# Camera.video_capture() always creates a Tk preview. Replace it with a no-op
# viewer when running over SSH without a graphical display.
if not os.environ.get("DISPLAY"):
    import camera_backend_picamera2

    class HeadlessViewer:
        def show_frame(self, image):
            pass

        def close(self):
            pass

    camera_backend_picamera2.TkImageViewer = HeadlessViewer


calibration_positions = [
    {"name": "1.5MM-DOT", "x": 23.1, "y": 47, "analyse": True, "diameter_mm": 1.5},
    {"name": "0.6MM-DOT", "x": 35.8, "y": 47, "analyse": True, "diameter_mm": 0.60},
    {"name": "CROSS-HAIRS", "x": 48.0, "y": 47, "analyse": False, "diameter_mm": None},
    {"name": "0.15MM-DOT", "x": 61.5, "y": 47, "analyse": True, "diameter_mm": 0.15},
    {"name": "0.07MM-DOT", "x": 74.1, "y": 47, "analyse": True, "diameter_mm": 0.07},
]


def focus_score(frame):
    """Measure strong, denoised edges in the complete frame."""
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Suppress sensor and MJPEG noise before measuring edge sharpness.
    gray = cv2.GaussianBlur(gray, (3, 3), 0)
    gradient_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    gradient_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
    gradient_squared = gradient_x * gradient_x + gradient_y * gradient_y

    # The dot boundary occupies only a small part of the crop. Measure the
    # strongest 1% of gradients rather than averaging mostly flat background.
    cutoff = np.percentile(gradient_squared, 99)
    strong_edges = gradient_squared[gradient_squared >= cutoff]
    return float(strong_edges.mean()) if strong_edges.size else 0.0


def find_best_video_frame(video_path):
    """Score the video, smooth the curve, then extract the selected frame."""
    video = cv2.VideoCapture(str(video_path))
    if not video.isOpened():
        raise RuntimeError(f"Could not open video: {video_path}")

    video_fps = video.get(cv2.CAP_PROP_FPS)
    if video_fps <= 0:
        video_fps = FPS

    raw_scores = []

    while True:
        ok, frame = video.read()
        if not ok:
            break

        raw_scores.append(focus_score(frame))

    video.release()

    if not raw_scores:
        raise RuntimeError(f"No frames found in video: {video_path}")

    # Smooth only for plotting. Selection remains frame-by-frame because a fast
    # Z move may pass through perfect focus for only one or two video frames.
    smoothed_scores = (
        pd.Series(raw_scores)
        .rolling(
            window=FOCUS_SMOOTHING_FRAMES,
            center=True,
            min_periods=1,
        )
        .mean()
        .to_numpy()
    )
    video_times = np.arange(len(raw_scores)) / video_fps
    eligible_indices = np.flatnonzero(video_times >= FOCUS_SEARCH_START_SECONDS)
    if not len(eligible_indices):
        raise RuntimeError(
            "Video contains no frames in the configured focus-search period."
        )
    best_index = int(
        eligible_indices[np.argmax(np.asarray(raw_scores)[eligible_indices])]
    )
    best_score = float(raw_scores[best_index])

    # Reopen and read sequentially to the selected frame. This avoids occasional
    # frame-seek inaccuracies in MKV containers.
    video = cv2.VideoCapture(str(video_path))
    best_frame = None
    for frame_index in range(best_index + 1):
        ok, frame = video.read()
        if not ok:
            break
        if frame_index == best_index:
            best_frame = frame.copy()
    video.release()
    if best_frame is None:
        raise RuntimeError(
            f"Could not extract selected frame {best_index} from {video_path}"
        )

    extracted_score = focus_score(best_frame)
    if not np.isclose(extracted_score, best_score, rtol=1e-6, atol=1e-6):
        raise RuntimeError(
            "Extracted frame does not match the frame selected during scoring."
        )

    focus_table = pd.DataFrame({
        "frame": np.arange(len(raw_scores)),
        "time_s": video_times,
        "focus_score": raw_scores,
        "smoothed_focus_score": smoothed_scores,
    })
    focus_table["is_best"] = focus_table["frame"] == best_index
    return best_frame, best_index, best_score, focus_table


def save_focus_curve(name, focus_table, output_dir):
    """Save the numerical focus curve and a plot."""
    focus_table.to_csv(output_dir / f"{name}_focus.csv", index=False)
    best = focus_table.loc[focus_table["is_best"]].iloc[0]

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(
        focus_table["time_s"],
        focus_table["focus_score"],
        color="gray",
        alpha=0.35,
        label="Raw frame score",
    )
    ax.plot(
        focus_table["time_s"],
        focus_table["smoothed_focus_score"],
        color="blue",
        label="Smoothed focus curve",
    )
    ax.scatter(best["time_s"], best["focus_score"], color="red", zorder=3)
    ax.axvline(
        best["time_s"],
        color="red",
        linestyle="--",
        label=f"Best frame at {best['time_s']:.3f} s",
    )
    ax.axvspan(
        0,
        FOCUS_SEARCH_START_SECONDS,
        color="orange",
        alpha=0.12,
        label="Excluded pre-sweep frames",
    )
    ax.set_title(f"Focus curve: {name}")
    ax.set_xlabel("Time in video (s)")
    ax.set_ylabel("Focus score (denoised edge strength)")
    ax.grid(alpha=0.25)
    ax.legend()
    fig.tight_layout()
    fig.savefig(output_dir / f"{name}_focus_curve.png", dpi=200)
    plt.close(fig)


def measure_dot(frame):
    """Measure the largest circular dark dot in the complete frame."""
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    _, mask = cv2.threshold(
        gray,
        0,
        255,
        cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU,
    )
    contours, _ = cv2.findContours(
        mask,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE,
    )

    circular_contours = []
    for contour in contours:
        area = cv2.contourArea(contour)
        perimeter = cv2.arcLength(contour, True)
        if area < 5 or perimeter == 0:
            continue
        circularity = 4 * np.pi * area / (perimeter * perimeter)
        if circularity >= 0.65:
            circular_contours.append(contour)

    if not circular_contours:
        raise RuntimeError("No suitable circular dot detected")

    dot = max(circular_contours, key=cv2.contourArea)
    contour_x, contour_y, contour_w, contour_h = cv2.boundingRect(dot)
    touches_crop_edge = (
        contour_x <= 1
        or contour_y <= 1
        or contour_x + contour_w >= gray.shape[1] - 1
        or contour_y + contour_h >= gray.shape[0] - 1
    )
    if touches_crop_edge:
        raise RuntimeError("Detected dot touches the image boundary.")

    overlay = frame.copy()

    if len(dot) >= 5:
        (local_x, local_y), (axis_1, axis_2), angle = cv2.fitEllipse(dot)
        diameter_px = (axis_1 + axis_2) / 2
        full_ellipse = (
            (local_x, local_y),
            (axis_1, axis_2),
            angle,
        )
        cv2.ellipse(overlay, full_ellipse, (0, 255, 0), 2)
    else:
        (local_x, local_y), radius = cv2.minEnclosingCircle(dot)
        diameter_px = 2 * radius
        centre = (round(local_x), round(local_y))
        cv2.circle(overlay, centre, round(radius), (0, 255, 0), 2)
    return diameter_px, overlay, mask


def save_image(path, image):
    """Save an image and fail clearly if OpenCV cannot write it."""
    if not cv2.imwrite(str(path), image):
        raise RuntimeError(f"Could not save image: {path}")


def capture_focus_video(
    output_dir,
    name,
    x,
    y,
    z_start,
    z_end,
    still_name=None,
):
    """Record one video while the stage moves from z_start to z_end."""
    still_name = still_name or name
    video_path = output_dir / f"{name}_z_sweep.mkv"
    still_path = output_dir / f"{still_name}.png"
    best_frame_path = output_dir / f"{still_name}_best_frame.png"
    overlay_path = output_dir / f"{name}_overlay.png"
    mask_path = output_dir / f"{name}_mask.png"
    focus_csv_path = output_dir / f"{name}_focus.csv"
    focus_curve_path = output_dir / f"{name}_focus_curve.png"

    # Remove previous outputs so a failed run cannot leave a stale still image.
    for old_path in (
        video_path,
        still_path,
        best_frame_path,
        overlay_path,
        mask_path,
        focus_csv_path,
        focus_curve_path,
    ):
        if old_path.exists():
            old_path.unlink()

    stage.moveXY(x, y, z_start)

    def move_z():
        time.sleep(Z_START_DELAY)
        stage.moveXY(x, y, z_end, f=5)

    movement = Thread(target=move_z)
    movement.start()

    # Direct call to the supplied Camera function.
    try:
        picam2.video_capture(
            str(video_path),
            VIDEO_DURATION,
            EXPOSURE,
            FPS,
            ANALOGUE_GAIN,
            SENSOR_MODE,
        )
    finally:
        movement.join()

    best_frame, best_index, best_score, focus_table = find_best_video_frame(video_path)
    best_time = float(focus_table.loc[best_index, "time_s"])

    # These two files now contain exactly the same selected video frame.
    save_image(still_path, best_frame)
    save_image(best_frame_path, best_frame)
    save_focus_curve(name, focus_table, output_dir)
    print(
        f"{name}: best focus at frame {best_index}, "
        f"time {best_time:.3f} s, score {best_score:.2f}"
    )
    return best_frame, best_index, best_time, best_score


def next_output_directory():
    """Create run_001, run_002, ... without overwriting an earlier run."""
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    run_numbers = []
    for path in OUTPUT_ROOT.glob("run_*"):
        try:
            run_numbers.append(int(path.name.split("_")[-1]))
        except ValueError:
            pass

    output_dir = OUTPUT_ROOT / f"run_{max(run_numbers, default=0) + 1:03d}"
    output_dir.mkdir()
    return output_dir


def scan_position(output_dir, position, z_start, z_end, still_name=None):
    """Capture one position and measure it when it is a calibration dot."""
    name = position["name"]

    print('#####################')
    print(f'## Scanning {name} ##', position)

    best_frame, best_index, best_time, best_score = capture_focus_video(
        output_dir,
        name,
        position["x"],
        position["y"],
        z_start,
        z_end,
        still_name=still_name,
    )

    if not position["analyse"]:
        return None

    try:
        diameter_px, overlay, mask = measure_dot(best_frame)
    except RuntimeError as error:
        print(f"{name}: dot measurement failed: {error}")
        return None

    px_per_mm = diameter_px / position["diameter_mm"]
    save_image(output_dir / f"{name}_mask.png", mask)
    save_image(output_dir / f"{name}_overlay.png", overlay)
    return {
        "name": name,
        "diameter_px": diameter_px,
        "diameter_mm": position["diameter_mm"],
        "px_per_mm": px_per_mm,
        "best_frame": best_index,
        "best_time_s": best_time,
        "focus_score": best_score,
    }


def percentage_difference(value_1, value_2):
    """Return the symmetric percentage difference between two values."""
    mean_value = (value_1 + value_2) / 2
    if mean_value == 0:
        return 0.0 if value_1 == value_2 else float("inf")
    return 100 * abs(value_1 - value_2) / mean_value


def save_results(output_dir, calibration_results):
    pd.DataFrame(calibration_results).to_csv(
        output_dir / "calibration_results.csv",
        index=False,
    )


def main():
    output_dir = next_output_directory()
    print(f"Saving this run to: {output_dir}")
    stage.setOrigin()
    leds.set(100)

    _, _, centre_z = stage.grabXY()
    z_start = max(0.0, centre_z - Z_SCAN_DISTANCE / 2)
    z_end = centre_z + Z_SCAN_DISTANCE / 2

    calibration_results = []
    agreeing_pair = None
    previous_measurement = None

    # # Dot order excludes the save-only cross-hair position.
    # dot_positions = [
    #     calibration_positions[0],
    #     calibration_positions[1],

    #     calibration_positions[3],
    #     calibration_positions[4],
    # ]

    for dot_number, position in enumerate(calibration_positions):
        print('###########')
        print(dot_number, position)
        # Save the calibration slide after the first two dots, regardless of
        # whether those dots have already produced an accepted calibration.
        if dot_number == 2:
            scan_position(
                output_dir,
                position,
                z_start,
                z_end,
                still_name="Calibration Slide",
            )
            continue


        # if agreeing_pair is not None:
        #     break

        result = scan_position(output_dir, position, z_start, z_end)
        if result is None:
            continue

        calibration_results.append(result)
        if (
            previous_measurement is not None
            and percentage_difference(
                previous_measurement["px_per_mm"],
                result["px_per_mm"],
            ) < MAX_SCALE_DIFFERENCE_PERCENT
        ):
            agreeing_pair = (previous_measurement, result)
        previous_measurement = result

    # If fewer than three dot positions were reached, the loop did not encounter
    # the cross-hair insertion point, so save it now.
    calibration_slide_path = output_dir / "Calibration Slide.png"
    if not calibration_slide_path.exists():
        scan_position(
            output_dir,
            calibration_positions[2],
            z_start,
            z_end,
            still_name="Calibration Slide",
        )

    save_results(output_dir, calibration_results)
    if agreeing_pair is None:
        print("No consecutive dot measurements agreed within 5%.")
        return "n/a"

    average = float(np.mean([
        agreeing_pair[0]["px_per_mm"],
        agreeing_pair[1]["px_per_mm"],
    ]))
    print(
        f"Consecutive measurements {agreeing_pair[0]['name']} and "
        f"{agreeing_pair[1]['name']} agree. Mean scale: {average:.2f} px/mm"
    )
    return average


if __name__ == "__main__":
    calibration = main()
    print(f"Calibration returned by main(): {calibration}")
