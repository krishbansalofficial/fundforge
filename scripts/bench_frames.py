"""B4: Godot client frame time on one chosen GPU (docs/BENCHMARKS.md "B4").

Wraps scripts/measure_frames.py: 1280x720, V-Sync off, uncapped, a 10 s settle reported separately ("settle")
and 60 s recorded while the player walks the office-and-street route twice. Forces the adapter with Godot's
--gpu-index (Forward+ only) and records the adapter Godot actually used (RenderingServer), so a forced index
that silently falls back is visible. Windows only for the machine checks (power, plan, load, GPU driver).

    py -3 scripts/bench_frames.py --server http://127.0.0.1:8044 --gpu-index 1 --tag igpu --run 1

Refuses to record on battery. Marks the result "machine_busy" when CPU load at start is above --busy-load or
a pytest / bench_* python process is running. Writes bench/results/<date>-B4-<commit>-<tag>-r<run>.json.
"""

import argparse
import json
import platform
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from measure_frames import ROUTE  # noqa: E402

TARGET_P99_MS = 16.7
MAX_STEADY_FRAME_MS = 100.0


def ps(command: str) -> str:
    return subprocess.run(["powershell", "-NoProfile", "-Command", command], capture_output=True, text=True,
                          timeout=120).stdout.strip()


def machine_state() -> dict:
    load = ps("(Get-Counter '\\Processor(_Total)\\% Processor Time' -SampleInterval 1 -MaxSamples 5)"
              ".CounterSamples.CookedValue | Measure-Object -Average | ForEach-Object { [math]::Round($_.Average, 1) }")
    busy = ps("Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | Where-Object { $_.CommandLine -match "
              "'pytest|bench_' -and $_.CommandLine -notmatch 'bench_frames' } | ForEach-Object { $_.ProcessId }")
    battery = ps("(Get-CimInstance Win32_Battery | Select-Object -First 1).BatteryStatus")
    gpus = json.loads(ps("Get-CimInstance Win32_VideoController | Select-Object Name, DriverVersion | ConvertTo-Json"))
    return {"cpu_load_pct_at_start": float(load or "nan"), "busy_python_pids": busy.split() if busy else [],
            "power_source": ("AC" if battery == "2"
                             else "no battery" if battery == "" else f"battery (status {battery})"),
            "power_plan": ps("powercfg /getactivescheme"),
            "gpus": gpus if isinstance(gpus, list) else [gpus]}


def git(*args: str) -> str:
    return subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, text=True).stdout.strip()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--server", default="http://127.0.0.1:8000")
    ap.add_argument("--godot", default="godot_console")
    ap.add_argument("--gpu-index", type=int, required=True)
    ap.add_argument("--rendering-driver", default="d3d12", help="d3d12 lists both GPUs here; vulkan sees only one")
    ap.add_argument("--tag", required=True, help="short GPU label for the file name, e.g. igpu or dgpu")
    ap.add_argument("--run", type=int, default=1)
    ap.add_argument("--resolution", default="1280x720")
    ap.add_argument("--warmup", type=float, default=10)
    ap.add_argument("--seconds", type=float, default=60)
    ap.add_argument("--busy-load", type=float, default=15.0, help="CPU %% above which the run is marked busy")
    ap.add_argument("--out", default=str(ROOT / "bench" / "results"))
    a = ap.parse_args()

    state = machine_state()
    if state["power_source"].startswith("battery"):
        print(f"on battery ({state['power_source']}); not recording", file=sys.stderr)
        return 2
    lap = [s.split("@") for s in ROUTE.split(",")]  # office and street, 0..34 s; walk it twice to cover 70 s
    route = ",".join(f"{loc}@{float(t) + off:g}" for off in (0, 36) for loc, t in lap)
    commit = git("rev-parse", "--short", "HEAD")
    raw = ROOT / "bench" / f".b4-{a.tag}-r{a.run}.json"
    cmd = [sys.executable, str(ROOT / "scripts" / "measure_frames.py"), "--server", a.server, "--godot", a.godot,
           "--resolution", a.resolution, "--warmup", str(a.warmup), "--seconds", str(a.seconds), "--route", route,
           "--output", str(raw), f"--engine-args=--rendering-driver {a.rendering_driver} --gpu-index {a.gpu_index}"]
    subprocess.run(cmd, stdout=subprocess.DEVNULL)  # exits 1 on its own p95 budget; the report is what counts
    if not raw.exists():
        print("measure_frames.py wrote no report", file=sys.stderr)
        return 1
    frames = json.loads(raw.read_text())
    raw.unlink()
    steady_ok = frames["p99_ms"] <= TARGET_P99_MS and frames["worst_ms"] <= MAX_STEADY_FRAME_MS
    adapter = frames["adapter"]
    driver = next((g["DriverVersion"] for g in state["gpus"] if g["Name"] in adapter or adapter in g["Name"]), None)
    result = {
        "benchmark": "B4-frame-time",
        "commit": commit,
        "dirty": bool(git("status", "--porcelain", "game", "scripts")),
        "measured_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "godot": frames["godot"],
        "machine": f"{platform.system()} {platform.release()} ({platform.version()}), {frames['cpu']}",
        "label": "one laptop, two GPUs (not two machines)",
        "requested_gpu_index": a.gpu_index,
        "requested_rendering_driver": a.rendering_driver,
        "adapter_used": adapter,  # from RenderingServer.get_video_adapter_name(), not inferred from the index
        "adapter_driver_version": driver,
        "renderer": f"{frames['driver']} / {frames['method']} (API {frames['api_version']})",
        "resolution": frames["window"],
        "vsync": frames["vsync"],
        "route": route,
        "settle_s": a.warmup,
        "steady_s": a.seconds,
        "machine_busy": state["cpu_load_pct_at_start"] > a.busy_load or bool(state["busy_python_pids"]),
        **state,
        "settle_first_10s": frames["settle"],
        "steady": {k: frames[k] for k in ("frames", "p50_ms", "p95_ms", "p99_ms", "worst_ms", "mean_ms", "mean_fps",
                                           "over_33_3ms", "over_100ms", "process_ms_p50", "process_ms_p99",
                                           "gpu_ms_mean", "gpu_ms_p95", "slowest")},
        "target": {"p99_ms_max": TARGET_P99_MS, "steady_frame_ms_max": MAX_STEADY_FRAME_MS,
                   "applies_to": "integrated GPU at 1280x720", "met": steady_ok},
        "raw": frames,
    }
    out = Path(a.out) / f"{datetime.now().date()}-B4-{commit}-{a.tag}-r{a.run}.json"
    out.write_text(json.dumps(result, indent=1) + "\n")
    print(json.dumps({k: result[k] for k in ("adapter_used", "renderer", "resolution", "machine_busy",
                                             "cpu_load_pct_at_start", "settle_first_10s", "steady",
                                             "target")}, indent=1))
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
