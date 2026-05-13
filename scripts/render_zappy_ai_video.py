#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import shlex
import subprocess
import sys
import textwrap
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
REPLAY_DIR = ROOT_DIR / ".local" / "demo" / "replay"
VIDEO_DIR = ROOT_DIR / ".local" / "demo" / "video"
MONTAGE_DIR = ROOT_DIR / ".local" / "demo" / "montage"

VIDEO_WIDTH = 1920
VIDEO_HEIGHT = 1080
VIDEO_FPS = 30
MIN_REPLAY_SECONDS = 120
CAPTION_SECONDS = 6.2
DEFAULT_AUDIO_TRACKS = [
    Path.home() / "Downloads" / "Ancient Civilisations - Alex Jones _ Xander Jones.mp3",
    Path.home() / "Downloads" / "Majestic-12 - Alex Jones _ Xander Jones.mp3",
]


@dataclass
class ReplayEvent:
    t_ms: int
    line: str


@dataclass
class CardEntry:
    text: str
    size: int
    y: int
    color: str = "white"


@dataclass
class CardSegment:
    key: str
    duration_s: int
    entries: list[CardEntry]
    background_start_s: int | None = None
    background_preset: str = "overview"
    background_focus: tuple[int, int] | None = None


@dataclass
class ClipSegment:
    key: str
    start_s: int
    duration_s: int
    preset: str
    caption: str
    focus: tuple[int, int] | None = None


def log(message: str) -> None:
    print(message, flush=True)


def require_command(name: str) -> None:
    if shutil_which(name) is None:
        raise SystemExit(f"Missing required command: {name}")


def shutil_which(name: str) -> str | None:
    for directory in os.environ.get("PATH", "").split(os.pathsep):
        candidate = Path(directory) / name
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return str(candidate)
    return None


def run(
    command: list[str],
    *,
    env: dict[str, str] | None = None,
    cwd: Path = ROOT_DIR,
    allowed_codes: tuple[int, ...] = (0,),
) -> None:
    log("+ " + shlex.join(command))
    completed = subprocess.run(command, cwd=cwd, env=env, check=False)
    if completed.returncode not in allowed_codes:
        raise SystemExit(
            f"Command failed with exit code {completed.returncode}: {shlex.join(command)}"
        )


def newest_replay_files() -> list[Path]:
    if not REPLAY_DIR.exists():
        return []
    return sorted(
        REPLAY_DIR.glob("protocol-*.jsonl"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )


def load_replay_events(path: Path) -> list[ReplayEvent]:
    events: list[ReplayEvent] = []
    for raw_line in path.read_text().splitlines():
        if not raw_line:
            continue
        payload = json.loads(raw_line)
        if payload.get("type") != "event":
            continue
        events.append(ReplayEvent(int(payload["t_ms"]), str(payload["line"])))
    if not events:
        raise SystemExit(f"Replay file contains no events: {path}")
    return events


def replay_duration_seconds(events: list[ReplayEvent]) -> int:
    return int(events[-1].t_ms / 1000)


def first_matching_time(
    events: list[ReplayEvent],
    predicate,
    *,
    after_s: int = 0,
    default_s: int,
) -> int:
    threshold = after_s * 1000
    for event in events:
        if event.t_ms < threshold:
            continue
        if predicate(event.line):
            return int(event.t_ms / 1000)
    return default_s


def parse_activity_coords(line: str) -> list[tuple[int, int, int]]:
    parts = line.split()
    if not parts:
        return []

    kind = parts[0]
    try:
        if kind in {"ppo", "pin"} and len(parts) >= 4:
            return [(int(parts[2]), int(parts[3]), 1)]
        if kind in {"pnw", "enw"} and len(parts) >= 4:
            return [(int(parts[2]), int(parts[3]), 2)]
        if kind in {"pic", "pie", "bct"} and len(parts) >= 3:
            return [(int(parts[1]), int(parts[2]), 4 if kind == "pic" else 2)]
    except ValueError:
        return []

    return []


def hotspot_for_window(
    events: list[ReplayEvent], start_s: int, duration_s: int
) -> tuple[int, int] | None:
    start_ms = start_s * 1000
    end_ms = (start_s + duration_s) * 1000
    counts: dict[tuple[int, int], int] = {}

    for event in events:
        if event.t_ms < start_ms:
            continue
        if event.t_ms > end_ms:
            break
        for x, y, weight in parse_activity_coords(event.line):
            counts[(x, y)] = counts.get((x, y), 0) + weight

    if not counts:
        return None

    return max(counts.items(), key=lambda item: item[1])[0]


def clamp_start(start_s: int, duration_s: int, replay_duration_s: int) -> int:
    latest = max(0, replay_duration_s - duration_s - 3)
    return max(0, min(start_s, latest))


def choose_replay_file(explicit: str | None, record_seconds: int) -> tuple[Path, list[ReplayEvent]]:
    if explicit:
        path = Path(explicit)
        if not path.is_file():
            raise SystemExit(f"Replay file not found: {path}")
        events = load_replay_events(path)
        if replay_duration_seconds(events) < MIN_REPLAY_SECONDS:
            raise SystemExit(
                f"Replay file is too short for the montage ({replay_duration_seconds(events)}s): {path}"
            )
        return path, events

    for replay in newest_replay_files():
        events = load_replay_events(replay)
        if replay_duration_seconds(events) >= MIN_REPLAY_SECONDS:
            return replay, events

    return record_replay(record_seconds)


def record_replay(record_seconds: int) -> tuple[Path, list[ReplayEvent]]:
    REPLAY_DIR.mkdir(parents=True, exist_ok=True)
    before = {path.name for path in newest_replay_files()}
    log_dir = ROOT_DIR / ".local" / "demo-montage-record"
    command = [
        "timeout",
        f"{record_seconds}s",
        "make",
        "demo-full",
        "GODOT_ARGS=--headless",
        "DEMO_RECORD_PROTOCOL=1",
        f"DEMO_LOG_DIR={log_dir}",
    ]
    run(command, allowed_codes=(0, 124))

    after = newest_replay_files()
    for replay in after:
        if replay.name not in before:
            events = load_replay_events(replay)
            if replay_duration_seconds(events) >= MIN_REPLAY_SECONDS:
                return replay, events

    raise SystemExit("Replay recording completed, but no usable replay file was produced.")


def resolve_audio_tracks() -> list[Path]:
    explicit = os.environ.get("DEMO_MONTAGE_AUDIO_FILES", "").strip()
    if explicit:
        tracks = [Path(item).expanduser() for item in explicit.split(os.pathsep) if item.strip()]
    else:
        tracks = [path for path in DEFAULT_AUDIO_TRACKS if path.is_file()]

    missing = [str(path) for path in tracks if not path.is_file()]
    if missing:
        raise SystemExit(
            "Montage audio tracks were requested, but these files were not found:\n"
            + "\n".join(missing)
        )

    return tracks


def build_segments(events: list[ReplayEvent]) -> list[CardSegment | ClipSegment]:
    duration_s = replay_duration_seconds(events)
    ready_anchor = first_matching_time(
        events,
        lambda line: line.startswith("pbc ") and '"kind": "ready"' in line,
        default_s=48,
    )
    pic_anchor = first_matching_time(
        events,
        lambda line: line.startswith("pic "),
        after_s=ready_anchor,
        default_s=ready_anchor + 26,
    )
    result_anchor = max(duration_s - 30, pic_anchor + 10)

    raw_segments: list[CardSegment | ClipSegment] = [
        CardSegment(
            key="intro-card",
            duration_s=6,
            entries=[
                CardEntry("Zappy | 42 Project", 72, 180),
                CardEntry("C++ server: @psegura- @sacorder", 44, 420),
                CardEntry("Godot GUI: @samusanc | Python AI: @amejia", 44, 500),
            ],
            background_start_s=0,
            background_preset="overview",
        ),
        ClipSegment(
            key="game-overview",
            start_s=0,
            duration_s=10,
            preset="overview",
            caption=(
                "Zappy is a multiplayer game where autonomous agents explore, "
                "gather resources, broadcast, fork, and cooperate to level up."
            ),
        ),
        CardSegment(
            key="architecture-card",
            duration_s=7,
            entries=[
                CardEntry("Project structure", 68, 180),
                CardEntry("C++ server handles rules and protocol", 46, 400),
                CardEntry("Godot renders the world in real time", 46, 480),
                CardEntry("Python controls the AI agents", 46, 560),
            ],
            background_start_s=82,
            background_preset="medium_alt",
            background_focus=(6, 6),
        ),
        ClipSegment(
            key="agent-state",
            start_s=100,
            duration_s=9,
            preset="medium_alt",
            focus=(5, 6),
            caption=(
                "Each Python agent tracks its own position, direction, inventory, "
                "visible resources, and nearby teammates."
            ),
        ),
        ClipSegment(
            key="behavior-tree",
            start_s=118,
            duration_s=9,
            preset="medium",
            focus=(6, 5),
            caption=(
                "The AI uses a behavior-tree system to switch between survival, "
                "exploration, gathering, regrouping, forking, and leveling up."
            ),
        ),
        ClipSegment(
            key="exploration",
            start_s=104,
            duration_s=9,
            preset="topdown",
            focus=(5, 5),
            caption=(
                "Agents do not move randomly: they search uncertain areas, look for "
                "missing stones, and adapt when food becomes critical."
            ),
        ),
        ClipSegment(
            key="queen-bee",
            start_s=ready_anchor,
            duration_s=9,
            preset="queen",
            focus=(7, 3),
            caption="The team organizes itself around a queen, similar to a bee colony.",
        ),
        ClipSegment(
            key="queen-reference",
            start_s=ready_anchor + 12,
            duration_s=10,
            preset="queen_alt",
            focus=(7, 3),
            caption=(
                "In a world with no shared map and no shared north, the queen "
                "becomes the reference point for the whole swarm."
            ),
        ),
        ClipSegment(
            key="broadcasts",
            start_s=118,
            duration_s=9,
            preset="dense_alt",
            focus=(6, 6),
            caption=(
                "Agents exchange structured broadcast messages to share inventory, "
                "readiness, food status, and team needs."
            ),
        ),
        ClipSegment(
            key="coordination",
            start_s=120,
            duration_s=9,
            preset="medium_alt",
            focus=(4, 5),
            caption=(
                "The queen coordinates regrouping, resource delivery, forking, "
                "and preparation for incantation."
            ),
        ),
        ClipSegment(
            key="result",
            start_s=max(result_anchor, 124),
            duration_s=9,
            preset="low_alt",
            focus=(5, 4),
            caption=(
                "The result is a cooperative swarm: multiple Python clients acting "
                "as one evolving team."
            ),
        ),
        CardSegment(
            key="end-card",
            duration_s=6,
            entries=[
                CardEntry("Python AI by @amejia", 64, 350),
                CardEntry(
                    "Zappy team: @samusanc | @psegura- | @sacorder | @amejia",
                    42,
                    500,
                ),
            ],
        ),
    ]

    for segment in raw_segments:
        if isinstance(segment, ClipSegment):
            segment.start_s = clamp_start(segment.start_s, segment.duration_s, duration_s)
            if segment.focus is None and segment.preset != "overview":
                segment.focus = hotspot_for_window(events, segment.start_s, segment.duration_s)

    return raw_segments


def ffmpeg_escape(text: str) -> str:
    return (
        text.replace("\\", r"\\")
        .replace(":", r"\:")
        .replace("'", r"\'")
        .replace(",", r"\,")
        .replace("%", r"\%")
        .replace("[", r"\[")
        .replace("]", r"\]")
        .replace("\n", r"\n")
    )


def ffmpeg_escape_path(path: Path) -> str:
    return str(path).replace("\\", r"\\").replace(":", r"\:")


def find_font_file() -> str:
    output = subprocess.check_output(
        ["fc-match", "-f", "%{file}\n", "Sans"], text=True
    ).strip()
    if not output:
        raise SystemExit("Unable to resolve a font file with fc-match.")
    return output.splitlines()[0]


def render_card(
    segment: CardSegment,
    output_path: Path,
    font_file: str,
    background_clip: Path | None = None,
) -> None:
    filters = []
    if background_clip is not None:
        filters.extend(
            [
                "scale=1920:1080:force_original_aspect_ratio=increase",
                "crop=1920:1080",
                "eq=saturation=0.72:contrast=0.88:brightness=-0.07",
                "gblur=sigma=2.4",
            ]
        )

    filters.extend(
        [
        f"fade=t=in:st=0:d=0.35",
        f"fade=t=out:st={segment.duration_s - 0.35}:d=0.35",
            "drawbox=x=90:y=110:w=1740:h=860:color=0x07111a@0.54:t=fill",
        ]
    )

    for entry in segment.entries:
        filters.append(
            "drawtext="
            f"fontfile={font_file}:"
            f"text='{ffmpeg_escape(entry.text)}':"
            f"fontcolor={entry.color}:"
            f"fontsize={entry.size}:"
            "x=(w-text_w)/2:"
            f"y={entry.y}:"
            "shadowcolor=black@0.8:shadowx=2:shadowy=2"
        )

    command = [
            "ffmpeg",
            "-y",
    ]
    if background_clip is None:
        command.extend(
            [
            "-f",
            "lavfi",
            "-i",
            f"color=c=0x07111a:s={VIDEO_WIDTH}x{VIDEO_HEIGHT}:d={segment.duration_s}",
            ]
        )
    else:
        command.extend(["-i", str(background_clip), "-t", str(segment.duration_s)])

    command.extend(
        [
            "-vf",
            ",".join(filters),
            "-r",
            str(VIDEO_FPS),
            "-c:v",
            "libx264",
            "-crf",
            "18",
            "-preset",
            "fast",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            str(output_path),
        ]
    )
    run(command)


def wrap_caption(text: str) -> str:
    return textwrap.fill(text, width=54)


def render_captioned_clip(
    segment: ClipSegment, raw_clip: Path, output_path: Path, font_file: str
) -> None:
    caption = wrap_caption(segment.caption)
    line_count = caption.count("\n") + 1
    caption_file = output_path.with_suffix(".txt")
    caption_file.write_text(caption + "\n")
    box_height = 64 + line_count * 54
    box_y = VIDEO_HEIGHT - box_height - 58
    text_y = box_y + 28
    enable_box = f"between(t,0.5,{CAPTION_SECONDS})"
    enable_text = f"between(t,0.8,{CAPTION_SECONDS - 0.2})"

    filters = [
        "eq=saturation=0.86:contrast=0.97:brightness=-0.02",
        (
            "drawbox="
            f"x=42:y={box_y}:w={VIDEO_WIDTH - 84}:h={box_height}:"
            f"color=black@0.46:t=fill:enable='{enable_box}'"
        ),
        (
            "drawtext="
            f"fontfile={font_file}:"
            f"textfile={ffmpeg_escape_path(caption_file)}:"
            "fontcolor=white:"
            "fontsize=38:"
            "line_spacing=12:"
            "x=(w-text_w)/2:"
            f"y={text_y}:"
            "shadowcolor=black@0.85:shadowx=2:shadowy=2:"
            f"enable='{enable_text}'"
        ),
    ]

    run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(raw_clip),
            "-vf",
            ",".join(filters),
            "-r",
            str(VIDEO_FPS),
            "-c:v",
            "libx264",
            "-crf",
            "18",
            "-preset",
            "fast",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            str(output_path),
        ]
    )


def capture_clip(
    segment: ClipSegment,
    replay_file: Path,
    output_path: Path,
    log_dir: Path,
) -> None:
    env = os.environ.copy()
    env.update(
        {
            "DEMO_MODE": "1",
            "DEMO_REPLAY_FILE": str(replay_file),
            "DEMO_RECORD_PROTOCOL": "",
            "DEMO_VIDEO_SECONDS": str(segment.duration_s),
            "DEMO_VIDEO_WARMUP": str(segment.start_s),
            "DEMO_VIDEO_FPS": str(VIDEO_FPS),
            "DEMO_VIDEO_OUT": str(output_path),
            "DEMO_LOG_DIR": str(log_dir),
            "DEMO_CAMERA_PRESET": segment.preset,
        }
    )
    if segment.focus is not None:
        env["DEMO_CAMERA_FOCUS_X"] = str(segment.focus[0])
        env["DEMO_CAMERA_FOCUS_Y"] = str(segment.focus[1])
    else:
        env.pop("DEMO_CAMERA_FOCUS_X", None)
        env.pop("DEMO_CAMERA_FOCUS_Y", None)

    run(["./scripts/demo_video.sh"], env=env)


def build_soundtrack(
    audio_tracks: list[Path],
    duration_s: int,
    work_dir: Path,
) -> Path:
    concat_audio = work_dir / "audio-tracks.txt"
    soundtrack = work_dir / "soundtrack.m4a"

    concat_audio.write_text(
        "".join(f"file '{path.resolve()}'\n" for path in audio_tracks)
    )

    fade_out_start = max(0.0, duration_s - 4.0)
    run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_audio),
            "-t",
            str(duration_s),
            "-vn",
            "-af",
            (
                "volume=0.18,"
                "afade=t=in:st=0:d=1.5,"
                f"afade=t=out:st={fade_out_start:.2f}:d=3.5"
            ),
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            str(soundtrack),
        ]
    )
    return soundtrack


def ffprobe_summary(path: Path) -> None:
    run(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=width,height,r_frame_rate",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=0",
            str(path),
        ]
    )


def main() -> None:
    require_command("ffmpeg")
    require_command("ffprobe")
    require_command("fc-match")
    require_command("timeout")

    font_file = find_font_file()
    audio_tracks = resolve_audio_tracks()
    record_seconds = int(os.environ.get("DEMO_MONTAGE_RECORD_SECONDS", "150"))
    explicit_replay = os.environ.get("DEMO_REPLAY_FILE") or None
    replay_file, events = choose_replay_file(explicit_replay, record_seconds)

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    work_dir = MONTAGE_DIR / timestamp
    raw_dir = work_dir / "raw"
    rendered_dir = work_dir / "rendered"
    capture_logs = work_dir / "capture-logs"
    for directory in (VIDEO_DIR, work_dir, raw_dir, rendered_dir, capture_logs):
        directory.mkdir(parents=True, exist_ok=True)

    final_output_env = os.environ.get("DEMO_MONTAGE_OUT", "").strip()
    final_output = Path(final_output_env) if final_output_env else VIDEO_DIR / "zappy-ai-montage.mp4"
    final_output.parent.mkdir(parents=True, exist_ok=True)

    log(f"Using replay: {replay_file}")
    log(f"Replay duration: {replay_duration_seconds(events)}s")
    if audio_tracks:
        log("Using audio tracks:")
        for track in audio_tracks:
            log(f"  - {track}")
    else:
        log("No audio tracks found. Rendering silent montage.")
    log(f"Montage workspace: {work_dir}")
    log(f"Final output: {final_output}")

    segments = build_segments(events)
    ordered_outputs: list[Path] = []

    for segment in segments:
        rendered_path = rendered_dir / f"{segment.key}.mp4"

        if isinstance(segment, CardSegment):
            background_path = None
            if segment.background_start_s is not None:
                background_path = raw_dir / f"{segment.key}-background.mp4"
                background_segment = ClipSegment(
                    key=f"{segment.key}-background",
                    start_s=clamp_start(
                        segment.background_start_s,
                        segment.duration_s,
                        replay_duration_seconds(events),
                    ),
                    duration_s=segment.duration_s,
                    preset=segment.background_preset,
                    caption="",
                    focus=segment.background_focus,
                )
                capture_log_dir = capture_logs / background_segment.key
                capture_log_dir.mkdir(parents=True, exist_ok=True)
                capture_clip(background_segment, replay_file, background_path, capture_log_dir)
            render_card(segment, rendered_path, font_file, background_path)
            ordered_outputs.append(rendered_path)
            continue

        raw_path = raw_dir / f"{segment.key}.mp4"
        capture_log_dir = capture_logs / segment.key
        capture_log_dir.mkdir(parents=True, exist_ok=True)
        capture_clip(segment, replay_file, raw_path, capture_log_dir)
        render_captioned_clip(segment, raw_path, rendered_path, font_file)
        ordered_outputs.append(rendered_path)

    concat_file = work_dir / "segments.txt"
    concat_file.write_text(
        "".join(f"file '{path.resolve()}'\n" for path in ordered_outputs)
    )

    total_duration_s = sum(
        segment.duration_s if isinstance(segment, CardSegment) else segment.duration_s
        for segment in segments
    )
    video_only = work_dir / "video-only.mp4"

    run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(concat_file),
            "-c:v",
            "libx264",
            "-crf",
            "18",
            "-preset",
            "fast",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            str(video_only),
        ]
    )

    if audio_tracks:
        soundtrack = build_soundtrack(audio_tracks, total_duration_s, work_dir)
        run(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(video_only),
                "-i",
                str(soundtrack),
                "-c:v",
                "copy",
                "-c:a",
                "aac",
                "-b:a",
                "192k",
                "-shortest",
                "-movflags",
                "+faststart",
                str(final_output),
            ]
        )
    else:
        run(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(video_only),
                "-c:v",
                "copy",
                "-movflags",
                "+faststart",
                str(final_output),
            ]
        )

    ffprobe_summary(final_output)
    log(f"Montage complete: {final_output}")


if __name__ == "__main__":
    main()
