# Full-history workflow

## Preflight: preserve unread state

1. Inspect `/direct/inbox/` without opening the conversation.
2. Confirm the row has no unread marker. A latest preview beginning with `你:` or otherwise showing the user's outgoing message is useful evidence, but still inspect the row for unread indicators.
3. If unread state is ambiguous, stop at the preview. Do not use the stored thread URL.
4. Resolve the URL from `known-threads.md`. For an unknown but clearly read thread, activate its semantic DOM locator once and record the resulting `/direct/t/.../` URL only for the current task.

## Background read

Create a new `iab` tab and navigate directly to the verified thread URL. Do not repurpose the user's visible inbox tab. Verify the profile heading and account before extraction.

Use DOM snapshots and read-only Playwright evaluation to identify the message pane. Instagram currently uses a reverse scroll container: the newest end is `scrollTop = 0` and older content has negative `scrollTop` values. The message pane can be distinguished from the thread list by its position, width, `overflow-y: scroll`, and scroll height.

Playwright evaluation is read-only. To scroll without GUI coordinates, use the tab's `cdp` capability and `Runtime.evaluate` only to assign the message container's `scrollTop`. Do not use CDP for network inspection, storage, cookies, tokens, or private APIs.

## Reach the oldest end

Move the message pane toward a very large negative `scrollTop`, wait for lazy loading, and re-read `scrollHeight`, `scrollTop`, the progress indicator, and visible top text. Continue until:

- `scrollHeight` does not increase for three consecutive load attempts;
- the progress indicator is absent; and
- the top contains the conversation profile introduction or another clear start marker.

If these conditions cannot be verified, export the result as partial.

## Handle virtualization

Instagram removes off-screen message rows from the DOM, so a single final snapshot is not complete.

After the oldest end is loaded:

1. Scan from `-(scrollHeight - clientHeight)` back to `0` in overlapping increments of roughly 250-300 pixels.
2. At each position, capture visible top-level `[role="group"]` rows, their stable `offsetTop`, and time labels outside message groups.
3. A group can contain a quoted bubble and the actual reply. Treat the last non-empty `[role="presentation"]` as the message body; earlier presentations are quoted context. Emoji outside that presentation are visible reactions/emoji, not replacement message text.
4. Determine sender from the actual presentation's nearest flex-row ancestor: `row-reverse` or `justify-content: flex-end` means the user; `row` with `justify-content: flex-start` means the other participant. Apply the same ancestor check to a text/image leaf when no presentation exists. Never classify sender from an absolute X coordinate or message length.
5. Restore reply direction from labels: `你回覆了<對話名稱>` is sent by the user; `<對話名稱>已回覆你` is received from the other participant.
6. Deduplicate repeated virtualized observations by stable offset, raw group content, and direction. Collapse identical adjacent render duplicates only when their offsets are within one row height; do not deduplicate by text alone because identical messages can be legitimate.
7. Validate that every visible actual presentation appears exactly once in the merged transcript and that quoted/reaction content was not substituted for it. Mark unresolved sender or body fields as uncertain instead of guessing.

Blank large message groups containing an `IMG` with an empty `alt` can be reported as `[圖片]` only after the image element is verified. Report other unidentifiable rows as `[無法辨識的媒體]`. Treat visible emoji near a message as `可見 emoji` because it may be inline content or a reaction.

## Export and cleanup

Use the private export directory explicitly supplied by the user or established for this task. Do not export messages into this public skill repository.

Write a Markdown file named `<對話名稱> - Instagram完整對話歷史 - <YYYY-MM-DD>.md` containing account, fetch time, source, message count, completeness evidence, original Instagram time labels, and chronological messages. Validate the numbered message count and file size.

Close the agent-created background tab when finished so no temporary scroll state remains. Leave the user's inbox tab untouched.
