# Generic Nexus + Vortex Workflow

## 1. Source Discovery

Collect exact source records before queueing downloads:

- Nexus game slug and mod ID.
- File ID when available.
- Required vs optional status.
- Known dependencies and warnings.
- Expected archive or payload type.

Prefer primary Nexus pages and author-provided links. Use search only to discover candidates, not as final proof.

## 2. Queue Downloads

Use Chrome automation with the user's browser session:

1. Open the Nexus files page with `file_id` when known.
2. Click `Mod manager download`.
3. If the requirements popup appears, click `Download`.
4. Click `Slow download`.
5. Record queued label, URL, mod ID, file ID, and any blocker.

Never bypass login, adult-content, Cloudflare, paid, or rate-limit gates.

## 3. Monitor Downloads

Run `scripts/scan-vortex-downloads.ps1` against the Vortex game download folder. Treat results as:

- `Ready`: file is readable and size is stable.
- `Pending`: file size changed during the sample window.
- `Locked`: another process still holds the file.
- `MissingFolder`: Vortex game folder does not exist.

Only inspect `Ready` files unless the user asks for a live progress report.

## 4. Verify Candidates

Run `scripts/inspect-mod-archives.ps1` on ready files. Use its output to separate:

- Direct manager payloads such as `.pak`, `.esp`, `.esm`, `.esl`.
- Loose-file archives requiring game-specific instructions.
- Suspicious binaries or scripts requiring explicit user approval.
- Unknown archives needing manual inspection.

The generic skill must not claim a file is compatible just because it is present. Compatibility comes from the game adapter.

## 5. Install, Quarantine, Report

Install only after the game adapter has identified the correct payload and the user requested installation. Quarantine extras by moving them to a timestamped folder outside the manager/game directory.

Report:

- Queued downloads.
- Ready downloads.
- Pending or locked files.
- Verified candidates.
- Blocked files and reasons.
- Installed or quarantined files.
- Next game-specific load-order step.
