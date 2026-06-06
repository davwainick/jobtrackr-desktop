# JobTrackr — Desktop Edition

A standalone, cross-platform job-search CRM that runs as a native desktop application. No accounts, no subscriptions, no cloud — your data stays on your machine in a local SQLite database.

## Features

- **Companies** — Track target companies with tier rankings, status pipeline, funding stage, and remote posture
- **Job Postings** — Capture job details, skills analysis, qualification gaps, and application status
- **Contacts** — Professional network CRM with connection degrees, warm intro flags, and touchpoint history
- **Outreach Log** — Message tracking with response monitoring and follow-up management
- **Gap Analysis** — Two-panel interview prep with editable strengths and objection cards
- **Dashboard** — Summary cards, due-today items, and recent activity feed
- **CSV Export** — Per-table CSV downloads or bulk export all tables
- **Markdown Export** — Full Gap Analysis as a `.md` file
- **All data local** — SQLite database stored in your OS's standard app data folder

## Why Python over Rust?

This application is a form-heavy CRUD tool that spends 99% of its time waiting for user input. Rust's strengths — memory safety, zero-cost abstractions, sub-millisecond performance — provide no user-visible benefit for a CRM. Python with ttkbootstrap delivers the same UX with dramatically less code (this entire app is ~2,500 lines vs an estimated 8,000+ in Rust). The trade-off is a larger executable (~50-80MB vs ~5-10MB), which is acceptable for a desktop CRM.

## Tech Stack

| Technology | Purpose |
|---|---|
| **Python 3.12+** | Application language |
| **ttkbootstrap** | Modern themed Tkinter GUI (Bootstrap-style widgets) |
| **SQLite** | Local embedded database (no server needed) |
| **PyInstaller** | Cross-platform executable packaging |

## Running from Source

### Prerequisites

- Python 3.10 or higher
- pip

### Install and run

```bash
# Clone the project
cd jobtrackr-desktop

# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

## Building Executables

Build on each target platform natively (cross-compilation isn't supported by PyInstaller):

```bash
# Install build dependencies
pip install -r requirements.txt

# Build the executable
python build.py
```

This produces:

| Platform | Output |
|---|---|
| **Windows** | `dist/JobTrackr.exe` |
| **macOS** | `dist/JobTrackr.app` |
| **Linux** | `dist/JobTrackr` |

### Platform-specific notes

**Windows:** The build uses `--noconsole` so no terminal window appears. Windows Defender may flag the first run — this is a known PyInstaller false positive.

**macOS:** The build uses `--windowed` to create a proper `.app` bundle. You may need to right-click → Open on first launch to bypass Gatekeeper.

**Linux:** The output is a standard ELF binary. Make it executable with `chmod +x dist/JobTrackr` if needed.

## Data Storage

Your data is stored in a SQLite database at:

| OS | Location |
|---|---|
| **Windows** | `%APPDATA%/JobTrackr/jobtrackr.db` |
| **macOS** | `~/Library/Application Support/JobTrackr/jobtrackr.db` |
| **Linux** | `~/.local/share/JobTrackr/jobtrackr.db` |

The database is created automatically on first launch. To reset all data, delete this file or use Settings → Delete All Data.

## Project Structure

```
jobtrackr-desktop/
├── main.py              # Entry point
├── database.py          # SQLite schema + all CRUD operations
├── build.py             # PyInstaller build script
├── requirements.txt     # Python dependencies
├── ui/
│   ├── app.py           # Main window, sidebar, all views
│   └── widgets.py       # Reusable form/table/detail widgets
└── export/
    ├── csv_export.py    # CSV generation
    └── markdown_export.py   # Gap Analysis markdown export
```

## Architecture

The application follows a simple MVC-like pattern:

- **`database.py`** — The model layer. All SQL queries, schema management, and CRUD operations live here. Every view calls `Database` methods directly — no ORM, no abstraction layers.
- **`ui/widgets.py`** — Reusable UI components: `DataTableView` (sortable, filterable Treeview table), `FormDialog` (scrollable modal with labeled fields), `DetailView` (read-only record viewer), and `FormField` (labeled input wrapper).
- **`ui/app.py`** — The controller+view layer. Contains the main window, sidebar navigation, and all six views (Dashboard, Companies, Job Postings, Contacts, Outreach, Gap Analysis, Settings). Each view is built as a method that creates/destroys frames.

Data flows directly: user interaction → `Database` method → refresh view. No state management, no event bus, no reactive framework — just function calls and widget updates.
