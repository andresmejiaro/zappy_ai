#!/usr/bin/env python3
import argparse, socket, sys, time, threading, json

def parse_args():
    ap = argparse.ArgumentParser(description="Zappy gfx: players & levels over time")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, required=True)
    ap.add_argument("--out", default="-", help="CSV path or '-' for stdout")
    ap.add_argument("--sample", type=float, default=0.0,
                    help="seconds between samples; 0 = log only on changes")
    ap.add_argument("--quit-on-seg", action="store_true",
                    help="exit on 'seg' (game end)")
    return ap.parse_args()

def line_reader(sock, on_line):
    buf = b""
    sock.settimeout(0.5)
    while True:
        try:
            chunk = sock.recv(4096)
            if not chunk:
                break
            buf += chunk
            while b"\n" in buf:
                line, buf = buf.split(b"\n", 1)
                on_line(line.decode("utf-8", "replace").strip())
        except socket.timeout:
            continue

def main():
    args = parse_args()
    t0 = time.time()
    players = set()          # {pid}
    levels  = {}             # {pid: level}
    lock = threading.Lock()
    last_written = {"t": None, "count": None, "levels_sig": None}
    seg_seen = False
    levels_dirty = False

    def now_s(): return time.time() - t0

    out = sys.stdout if args.out == "-" else open(args.out, "w", buffering=1)
    print("seconds,count,levels", file=out, flush=True)

    # connect & handshake
    s = socket.create_connection((args.host, args.port))
    s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    wel = b""
    s.settimeout(5.0)
    while True:
        chunk = s.recv(4096)
        if not chunk:
            raise RuntimeError("Disconnected before BIENVENUE")
        wel += chunk
        if b"\n" in wel:
            for l in wel.split(b"\n"):
                if l.strip().upper() == b"BIENVENUE":
                    s.sendall(b"GRAPHIC\n")
                    break
            else:
                continue
            break
    s.settimeout(None)

    def snapshot():
        with lock:
            c = len(players)
            # Only include levels for players currently alive
            lvl_list = [levels[p] for p in players if p in levels]
        return c, lvl_list

    def levels_signature(lst):
        # order-independent signature for change detection
        return tuple(sorted(lst))

    def maybe_emit(force=False):
        c, lvl_list = snapshot()
        if lvl_list is not None:
            lvl_list.sort()
        t = now_s()
        sig = levels_signature(lvl_list)
        changed = (last_written["count"] != c) or (last_written["levels_sig"] != sig)
        if force or args.sample > 0.0 or changed:
            print(f"{t:.3f},{c},{json.dumps(lvl_list)}", file=out, flush=True)
            last_written.update(t=t, count=c, levels_sig=sig)

    def on_line(line: str):
        nonlocal seg_seen, levels_dirty
        if not line:
            return
        parts = line.split()
        cmd = parts[0]
        if cmd == "pnw" and len(parts) >= 6:
            # pnw #n X Y O L N
            pid = parts[1].lstrip("#")
            try:
                lvl = int(parts[5])
            except Exception:
                lvl = None
            with lock:
                players.add(pid)
                if lvl is not None:
                    levels[pid] = lvl
                    levels_dirty = True
        elif cmd == "plv" and len(parts) >= 3:
            # plv #n L
            pid = parts[1].lstrip("#")
            try:
                lvl = int(parts[2])
            except Exception:
                lvl = None
            if lvl is not None:
                with lock:
                    levels[pid] = lvl
                    levels_dirty = True
        elif cmd == "pdi" and len(parts) >= 2:
            # pdi #n
            pid = parts[1].lstrip("#")
            with lock:
                players.discard(pid)
                levels.pop(pid, None)
                levels_dirty = True
        elif cmd == "seg" and args.quit_on_seg:
            seg_seen = True

        # on-change mode: emit if count or levels changed
        if args.sample <= 0.0:
            if (last_written["count"] != len(players)) or levels_dirty:
                levels_dirty = False
                maybe_emit()

    # reader thread
    reader = threading.Thread(target=line_reader, args=(s, on_line), daemon=True)
    reader.start()

    # sampler (optional)
    try:
        if args.sample > 0.0:
            nxt = 0.0
            while reader.is_alive():
                t = now_s()
                if t >= nxt:
                    maybe_emit(force=True)
                    nxt = t + args.sample
                if seg_seen:
                    break
                time.sleep(0.05)
        else:
            while reader.is_alive() and not seg_seen:
                time.sleep(0.1)
    finally:
        try:
            s.shutdown(socket.SHUT_RDWR)
        except Exception:
            pass
        s.close()
        if out is not sys.stdout:
            out.close()

if __name__ == "__main__":
    main()
