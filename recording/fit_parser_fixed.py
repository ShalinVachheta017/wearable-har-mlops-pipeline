"""
Garmin FIT parser for accelerometer + gyroscope data.

Purpose:
- Extract record, accelerometer_data, and gyroscope_data messages from a Garmin FIT file.
- Preserve / reconstruct sample-level timestamps so long recordings do not collapse to a short duration.
- Write CSV files compatible with the HAR MLOps pipeline ingestion stage.

Why this parser is needed:
Some FIT sensor messages contain arrays of 25 samples per message. The message timestamp is shared by
the packet, while sample timing must be reconstructed inside the packet. If every sample is written with
only the same whole-second timestamp, a 30+ minute recording can be incorrectly compressed during
resampling and produce too few windows.

Output columns:
- record CSV: all available record message fields.
- accelerometer CSV:
    timestamp, timestamp_original, timestamp_ms, sample_index, packet_sample_index,
    sample_time_offset, accel_x, accel_y, accel_z
- gyroscope CSV:
    timestamp, timestamp_original, timestamp_ms, sample_index, packet_sample_index,
    sample_time_offset, gyro_x, gyro_y, gyro_z

Usage:
    python fit_parser_fixed.py --fit "recording/4th and 5th may/2026-05-05-15-11-15.fit" --out-dir "recording"

Optional:
    python fit_parser_fixed.py --fit "...fit" --out-dir "recording" --session-id "2026-05-05-15-11-15"
"""

from __future__ import annotations

import argparse
import csv
import os
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence

import fitparse


ACCEL_KEYS = ("calibrated_accel_x", "calibrated_accel_y", "calibrated_accel_z")
GYRO_KEYS = ("calibrated_gyro_x", "calibrated_gyro_y", "calibrated_gyro_z")


def _to_list(value: Any) -> Optional[List[Any]]:
    """Return value as list if it is a FIT vector field; otherwise None."""
    if isinstance(value, (list, tuple)):
        return list(value)
    return None


def _safe_timestamp(value: Any) -> Optional[datetime]:
    """Convert FIT timestamp to datetime where possible."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.replace(tzinfo=None)
    try:
        # Fallback for string timestamps.
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).replace(tzinfo=None)
    except Exception:
        return None


def _get_message_timestamp_ms(values: Dict[str, Any]) -> int:
    """
    Garmin sensor messages may include timestamp_ms.
    If present, use it as packet-level millisecond offset inside the second.
    If absent, use 0 and reconstruct timing from packet order.
    """
    raw = values.get("timestamp_ms", 0)
    try:
        return int(raw)
    except Exception:
        return 0


def _sample_offsets_ms(values: Dict[str, Any], n_samples: int) -> List[float]:
    """
    Return sample offsets in milliseconds within the packet.

    Preferred:
    - use FIT sample_time_offset if available and vector-like.

    Fallback:
    - distribute samples evenly inside the packet.
      For 25 samples at an assumed 100 Hz stream, one packet covers about 250 ms,
      so offsets are 0, 10, 20, ..., 240 ms.
    """
    offsets = _to_list(values.get("sample_time_offset"))
    if offsets and len(offsets) == n_samples:
        out: List[float] = []
        for v in offsets:
            try:
                out.append(float(v))
            except Exception:
                out.append(0.0)
        return out

    # Fallback for your current files: 25 samples per packet from a 100 Hz stream.
    # The packet itself occurs four times per second.
    if n_samples > 0:
        return [i * (1000.0 / 100.0) for i in range(n_samples)]
    return []


def _write_csv(filename: Path, rows: List[Dict[str, Any]], headers: Sequence[str]) -> None:
    filename.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        print(f"No data to write for {filename}")
        return

    with filename.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=headers, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    print(f"Created {filename} ({len(rows):,} rows)")


def _session_id_from_fit_path(fit_path: Path) -> str:
    return fit_path.stem


def parse_fit_file(fit_path: Path, out_dir: Path, session_id: Optional[str] = None) -> None:
    if not fit_path.exists():
        raise FileNotFoundError(f"FIT file not found: {fit_path}")

    session_id = session_id or _session_id_from_fit_path(fit_path)

    record_csv = out_dir / f"{session_id}_record_data.csv"
    accel_csv = out_dir / f"{session_id}_accelerometer_data.csv"
    gyro_csv = out_dir / f"{session_id}_gyroscope_data.csv"

    record_rows: List[Dict[str, Any]] = []
    accel_rows: List[Dict[str, Any]] = []
    gyro_rows: List[Dict[str, Any]] = []

    record_headers = set(["timestamp"])

    # Packet counters per whole-second timestamp. This is used when timestamp_ms is not available.
    # If there are 4 packets per second, fallback packet offsets become 0 ms, 250 ms, 500 ms, 750 ms.
    accel_packet_counter: Dict[datetime, int] = defaultdict(int)
    gyro_packet_counter: Dict[datetime, int] = defaultdict(int)

    fitfile = fitparse.FitFile(str(fit_path))

    print(f"Parsing FIT file: {fit_path}")
    print("Extracting record, accelerometer_data, and gyroscope_data messages...")

    for message in fitfile.get_messages(["record", "accelerometer_data", "gyroscope_data"]):
        values = message.get_values()

        if message.name == "record":
            record_rows.append(values)
            record_headers.update(values.keys())
            continue

        if message.name == "accelerometer_data":
            x_values = _to_list(values.get(ACCEL_KEYS[0]))
            y_values = _to_list(values.get(ACCEL_KEYS[1]))
            z_values = _to_list(values.get(ACCEL_KEYS[2]))

            if not x_values or y_values is None or z_values is None:
                continue

            n = min(len(x_values), len(y_values), len(z_values))
            packet_timestamp = _safe_timestamp(values.get("timestamp"))
            if packet_timestamp is None:
                continue

            timestamp_ms = _get_message_timestamp_ms(values)
            has_timestamp_ms = "timestamp_ms" in values

            if has_timestamp_ms:
                packet_offset_ms = timestamp_ms
            else:
                packet_index = accel_packet_counter[packet_timestamp]
                accel_packet_counter[packet_timestamp] += 1
                # 25 samples at 100 Hz => packet duration ≈250 ms.
                packet_offset_ms = packet_index * 250.0

            offsets_ms = _sample_offsets_ms(values, n)

            for i in range(n):
                total_offset_ms = packet_offset_ms + offsets_ms[i]
                sample_timestamp = packet_timestamp + timedelta(milliseconds=total_offset_ms)

                accel_rows.append(
                    {
                        "timestamp": sample_timestamp.isoformat(sep=" "),
                        "timestamp_original": packet_timestamp.isoformat(sep=" "),
                        "timestamp_ms": int(round(total_offset_ms)),
                        "sample_index": len(accel_rows),
                        "packet_sample_index": i,
                        "sample_time_offset": int(round(offsets_ms[i])),
                        "accel_x": x_values[i],
                        "accel_y": y_values[i],
                        "accel_z": z_values[i],
                    }
                )

        elif message.name == "gyroscope_data":
            x_values = _to_list(values.get(GYRO_KEYS[0]))
            y_values = _to_list(values.get(GYRO_KEYS[1]))
            z_values = _to_list(values.get(GYRO_KEYS[2]))

            if not x_values or y_values is None or z_values is None:
                continue

            n = min(len(x_values), len(y_values), len(z_values))
            packet_timestamp = _safe_timestamp(values.get("timestamp"))
            if packet_timestamp is None:
                continue

            timestamp_ms = _get_message_timestamp_ms(values)
            has_timestamp_ms = "timestamp_ms" in values

            if has_timestamp_ms:
                packet_offset_ms = timestamp_ms
            else:
                packet_index = gyro_packet_counter[packet_timestamp]
                gyro_packet_counter[packet_timestamp] += 1
                packet_offset_ms = packet_index * 250.0

            offsets_ms = _sample_offsets_ms(values, n)

            for i in range(n):
                total_offset_ms = packet_offset_ms + offsets_ms[i]
                sample_timestamp = packet_timestamp + timedelta(milliseconds=total_offset_ms)

                gyro_rows.append(
                    {
                        "timestamp": sample_timestamp.isoformat(sep=" "),
                        "timestamp_original": packet_timestamp.isoformat(sep=" "),
                        "timestamp_ms": int(round(total_offset_ms)),
                        "sample_index": len(gyro_rows),
                        "packet_sample_index": i,
                        "sample_time_offset": int(round(offsets_ms[i])),
                        "gyro_x": x_values[i],
                        "gyro_y": y_values[i],
                        "gyro_z": z_values[i],
                    }
                )

    accel_headers = [
        "timestamp",
        "timestamp_original",
        "timestamp_ms",
        "sample_index",
        "packet_sample_index",
        "sample_time_offset",
        "accel_x",
        "accel_y",
        "accel_z",
    ]
    gyro_headers = [
        "timestamp",
        "timestamp_original",
        "timestamp_ms",
        "sample_index",
        "packet_sample_index",
        "sample_time_offset",
        "gyro_x",
        "gyro_y",
        "gyro_z",
    ]

    _write_csv(record_csv, record_rows, sorted(record_headers))
    _write_csv(accel_csv, accel_rows, accel_headers)
    _write_csv(gyro_csv, gyro_rows, gyro_headers)

    _print_summary("ACC", accel_rows)
    _print_summary("GYRO", gyro_rows)


def _print_summary(name: str, rows: List[Dict[str, Any]]) -> None:
    if not rows:
        print(f"{name}: no rows")
        return

    first = datetime.fromisoformat(rows[0]["timestamp"])
    last = datetime.fromisoformat(rows[-1]["timestamp"])
    duration = (last - first).total_seconds()
    hz = len(rows) / duration if duration > 0 else float("nan")
    unique_timestamps = len({r["timestamp"] for r in rows})

    print()
    print(f"{name} summary")
    print(f"Rows: {len(rows):,}")
    print(f"Start: {first}")
    print(f"End:   {last}")
    print(f"Duration: {duration:.2f} sec = {duration / 60:.2f} min")
    print(f"Estimated Hz: {hz:.2f}")
    print(f"Unique timestamps: {unique_timestamps:,}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Parse Garmin FIT sensor data into pipeline-ready CSV files.")
    parser.add_argument("--fit", required=True, help="Path to Garmin FIT file")
    parser.add_argument("--out-dir", default="recording", help="Output directory for CSV files")
    parser.add_argument("--session-id", default=None, help="Optional session ID prefix for output files")
    args = parser.parse_args()

    parse_fit_file(Path(args.fit), Path(args.out_dir), args.session_id)


if __name__ == "__main__":
    main()
