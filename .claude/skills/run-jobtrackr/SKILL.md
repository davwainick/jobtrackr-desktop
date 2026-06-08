---
name: run-jobtrackr
description: Launch and drive the JobTrackr Tkinter/ttkbootstrap desktop app on an X display, then screenshot and click it to verify a change.
---

# Running JobTrackr

JobTrackr is a Tkinter (ttkbootstrap) desktop GUI. It needs an X display, runs
`mainloop()` (blocks), and stores data in a local SQLite file in the per-OS user
data dir (created idempotently on first launch). Launch it, screenshot the
window, and click nav buttons to drive it — a static window that never changes
under interaction is a failure.

## Prerequisites (verified present on this machine)

- **venv**: `.venv/bin/python` is Python 3.12 with `tkinter` + `ttkbootstrap`
  importable. Always use the venv interpreter, not system `python`.
- **Display**: a real X server is available at `DISPLAY=:0`. Launching pops a
  real window on the user's desktop — that's expected and fine for a quick run.
- **Tools used**: `xdotool` (window search + clicking) and ImageMagick
  `import` / `identify` (screenshots). Both already installed.
- **NOT installed**: `Xvfb` / `xvfb-run`, `tmux`, `scrot`. Don't reach for them.
  For a headless/CI run you'd need `apt-get install xvfb` and wrap the launch in
  `xvfb-run -a` + set `DISPLAY` — not required when `:0` exists.

## Launch + drive (the recipe that worked)

```bash
cd <repo root>

# 1. Launch in background; logs to a file. main.py chdir's to its own dir.
.venv/bin/python main.py >/tmp/jobtrackr.log 2>&1 &

# 2. Wait for the window (title contains "JobTrackr"). No foreground sleep —
#    poll with a sub-second perl select.
for i in $(seq 1 20); do
  wid=$(xdotool search --name "JobTrackr" 2>/dev/null | head -1)
  [ -n "$wid" ] && break
  perl -e 'select(undef,undef,undef,0.5)'
done
echo "wid=$wid"          # empty wid => check /tmp/jobtrackr.log for a traceback

# 3. Screenshot the window by id (window is gridded at +0+0, ~1200x620).
xdotool windowactivate "$wid"; perl -e 'select(undef,undef,undef,0.7)'
import -window "$wid" /tmp/jobtrackr.png
identify /tmp/jobtrackr.png   # sanity-check it isn't 0 bytes / wrong size
```

Then **Read `/tmp/jobtrackr.png`** — a rendered sidebar + content pane means it
launched. A blank/black frame means it didn't; read `/tmp/jobtrackr.log`.

### Click a nav button (prove it's interactive)

Coordinates are window-relative; the window sits at `+0+0`. Sidebar nav buttons
(top to bottom): Dashboard, Companies, Job Postings, Contacts, Outreach Log,
Gap Analysis. Approximate y for each row, x≈110:

```bash
# e.g. "Companies" row
xdotool mousemove --window "$wid" 110 132 click 1
perl -e 'select(undef,undef,undef,0.6)'
import -window "$wid" /tmp/jobtrackr_after.png
```

Re-Read the screenshot: clicking Companies should switch the content pane to the
DataTableView (Search box, status filter, table columns Company/Tier/Status/…,
"N records" footer). Each `_show_*` destroys the previous view, so the content
pane fully changes on every nav click.

### Cleanup

```bash
pkill -f "main.py"   # or: kill <the launched PID>
```

## Gotchas

- App opens on the **Gap Analysis** screen by default (Job Seeker Profile form +
  Strengths / Gaps & Objections panels).
- `main.py` `os.chdir`s to its own directory on startup — don't rely on the cwd
  you launched from for relative paths.
- ttkbootstrap theme is `cosmo`; the sidebar uses `secondary.TFrame` (gray). The
  brand accent `#4f46e5` is hard-coded in a few places.
- Window title-match string is just "JobTrackr"; `xdotool search --name` finds it.
