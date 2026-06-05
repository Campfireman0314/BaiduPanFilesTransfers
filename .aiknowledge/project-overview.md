# Project Overview

Last reviewed: 2026-06-04

## Purpose

This project is a Python Baidu Netdisk batch transfer tool. The upstream app is a Tkinter desktop utility for:

- Batch saving Baidu share links into the user's Baidu Netdisk.
- Batch sharing files from a target folder.
- Checking whether share links are valid.
- Saving runtime inputs to `config.ini`.

The current working tree also adapts the app into a service-style fetch workflow: a Waitress/Flask endpoint receives a message containing Baidu links, transfers them into a fixed Baidu remote folder, downloads that folder locally with ByPy, then clears the remote folder.

## File Map

- `BaiduPanFilesTransfers.py`: Current entrypoint. In this working tree it runs a Flask app with Waitress on port `1001` instead of launching the original GUI. It also owns the external fetch workflow, POP/O alert calls, ByPy download/remove steps, and the single global worker thread.
- `src/operations.py`: Main orchestration layer. It prepares input, validates cookie/folder/link count, fetches `bdstoken`, creates directories, verifies share links, transfers files, shares files, and writes logs.
- `src/network.py`: Baidu Netdisk HTTP API wrapper using `requests.Session` and `retrying`. It handles token lookup, dir listing/creation, pass-code verification, transfer, and share creation.
- `src/utils.py`: Shared helpers for threading, config read/write, icon generation, link normalization, URL/code parsing, response parsing, and cookie update.
- `src/ui.py`: Tk/ttkbootstrap UI classes. In this working tree the `MainWindow.__init__` setup calls are commented out, so the original GUI path is effectively dormant unless re-enabled.
- `src/constants.py`: Static app metadata, UI strings, request headers, Baidu API base URL, error-code map, limits, timing, and config path.
- `src/test.py`: Unit tests for parsing and cookie helpers. The name is not picked up by pytest default discovery.
- `requirements.txt`: Runtime and packaging dependencies. Includes desktop deps plus Flask/Waitress/ByPy for the service adaptation.
- `Capture/`, `BaiduPanFilesTransfers.ico`, `BaiduPanFilesTransfers.png`: README/UI assets.
- `config.ini`: Local ignored runtime config. Not inspected because it may contain secrets.

## Runtime Flow

Desktop/upstream flow:

1. User enters cookie, destination/source folder, and links in the Tk UI.
2. `Operations.save()` or `Operations.share()` reads UI state and writes `config.ini`.
3. The network layer gets `bdstoken`.
4. Save mode normalizes links, optionally verifies extraction codes, parses transfer params from the share page, and posts `/share/transfer`.
5. Share mode lists a folder and posts `/share/set` for each item.

Current service flow:

1. `POST /` expects JSON with `message` and `group`.
2. If a worker thread is already running, the special message `做掉` attempts to terminate it via `PyThreadState_SetAsyncExc`; otherwise a busy reply is sent.
3. If idle, a global thread calls `main(group, message)`.
4. `main()` creates a `MainWindow(None)` placeholder plus `Operations`, runs the external transfer path with `prepare_run_ext()` and `setup_save_ext()`, then downloads the remote `/fetch` folder via ByPy to a timestamped local directory.
5. Success/failure notifications are sent through the hard-coded alert endpoint.

## Current Git State

- Existing uncommitted change before this note: `BaiduPanFilesTransfers.py`.
- New knowledge-base addition from this review: `.aiknowledge/project-overview.md`.
- I did not revert or rewrite the existing local modification.

## Test Reality

- `python -m pytest -q` reports `no tests ran` because `src/test.py` is not matched by default pytest discovery.
- `python -m pytest src/test.py -q` runs 30 tests: 29 pass, 1 fails.
- The failing case is `test_update_cookie` for malformed cookie input. `src.utils.update_cookie()` raises `ValueError`, while the test currently expects the literal string `"ValueError"`.

## Notable Risks And Optimization Watchpoints

- Secret handling: `BaiduPanFilesTransfers.py` currently contains a hard-coded Baidu cookie. Treat it as sensitive, avoid committing it, and prefer environment/config loading before broader cleanup.
- More secret handling: `prepare_run_ext()` writes cookie data to `config.ini`; the file is ignored, but still lives on disk.
- Unsafe cancellation: `PyThreadState_SetAsyncExc` can interrupt code at arbitrary points. It may leave network sessions, local folders, or remote `/fetch` state inconsistent.
- Shared mutable headers: `Network.__init__` assigns `self.headers = HEADERS`, so cookie updates mutate the module-level header dict across `Network` instances.
- UI/service coupling: `Operations` still depends on a `root` object and has separate `change_status` / `change_status_ext` paths. This is workable but brittle for headless operation.
- `check_condition()` calls `sys.exit()`, which is awkward inside worker threads and library-style code. Raising a domain exception would be easier to handle.
- Link parsing uses fixed URL slicing and "last four characters" extraction-code logic. It matches existing tests, but can misread extra trailing text.
- `setup_save_ext()` uses custom POP/O tag and link transformation logic; this is likely the main area to understand before optimizing fetch input handling.
- `Network` disables TLS verification warnings and passes `verify=False` on Baidu requests. This may be intentional for compatibility, but it is a security tradeoff.
- Logging in headless mode uses Python logging without visible configuration in the repo, so service logs may be sparse depending on the host environment.

## Good Starting Points For The Next Change

- If optimizing fetch input parsing: start in `src/operations.py` at `transform_text_between_tags()`, `transform_link()`, and `setup_save_ext()`.
- If optimizing transfer throughput/reliability: start in `Operations.handle_process_save()`, `Operations.pause_detection()`, and `src/network.py` retry/timeouts.
- If optimizing service reliability: start in `BaiduPanFilesTransfers.py` worker lifecycle, hard-coded paths/secrets, and ByPy cleanup.
- If restoring/maintaining desktop behavior: first revisit `src/ui.py` `MainWindow.__init__`, because the setup calls are currently commented out.

## 2026-06-04 Queue And Download Staging Update

- Incoming Flask requests are no longer refused while a job is active. `BaiduPanFilesTransfers.py` now keeps an in-memory `deque` guarded by `queue_lock`, starts one worker thread, and processes queued fetch jobs sequentially.
- A request is accepted into the queue only when the message contains `pan.baidu.com`. Invalid messages get an immediate POP/O warning and are not queued.
- The worker sends a "now processing" POP/O message containing a shortened preview of the link/message before calling the existing `main()` workflow.
- The special `做掉` command still attempts to stop the current worker thread, clears pending queued jobs, removes remote `/fetch`, and cleans the current local temp download directory.
- Local download behavior changed after `bp.downdir('/fetch', current_working_local_dir)`: downloads now go into `_fetch_tmp/YYYYMMDD_HHMMSS_microseconds`, then contents are moved into a day-level final folder `YYYYMMDD`, and the temp folder is deleted.
- The Baidu transfer and ByPy calls themselves were left in the same order and location as much as possible; the new behavior wraps local filesystem staging around the existing download call.
- If a moved file or directory name already exists in the day folder, `unique_destination_path()` appends `_1`, `_2`, etc. to avoid overwriting.

## 2026-06-04 Transfer Debug Note

- A runtime log showed `转存失败，目标目录不存在` for `/apps/bypy/fetch` while ByPy could still list and delete `/fetch`.
- `src.operations.transform_link()` had a parser flaw for common message formats like `url code` and `url 提取码：code`; those could be converted into strings with extra spaces and accidentally trigger the service's custom-subdirectory branch.
- `transform_link()` now canonicalizes supported incoming forms through `normalize_link()` and `parse_url_and_code()`, returning `url?pwd=code` when a code exists. This keeps `link_list_org` as one token and prevents accidental `/fetch/1` target paths.
- A brief errno `2` transfer retry was added and then removed because duplicate transfer attempts are unsafe for this workflow.
- The queue now tracks queued, active, and very recently completed job keys. Exact duplicate messages are ignored while active/pending and for 30 seconds after completion.
- `src.network.normalize_remote_path()` now gives list/create/transfer paths one consistent leading-slash shape such as `/apps/bypy/fetch`.
- `Operations` tracks failed transfer tasks; the headless `main()` path now stops before the ByPy download/delete phase if transfer failed.

## 2026-06-05 Noisy Share Text Parsing

- `src.operations.transform_link()` now scans the whole incoming message for actual Baidu share URLs instead of treating each text line as a link candidate.
- It extracts `pwd=xxxx` directly from the URL when present, or the nearest following `提取码` / `提取` / `密码` / `pwd` marker, or a bare 4-character code immediately after the link.
- This supports Baidu share blurbs such as `通过网盘分享的文件... 链接: https://pan.baidu.com/s/...?...pwd=rbiy 提取码: rbiy --来自...` and whitespace-collapsed versions where `pwd=rbiy提取码:rbiy--来自...` appears as one run.
- Parser regression tests live in `src/test.py` under `test_transform_link_extracts_baidu_share_from_noisy_text`.
