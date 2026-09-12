---
name: line-chat-advisor
compat: [codex]
description: |
  Use whenever the user asks to read LINE messages, inspect a named LINE chat,
  decide whether to reply, continue a conversation, understand relationship
  context, or draft one reply in the user's style. This skill is read-only with
  respect to LINE and must never send or enter a message.
---

# LINE Chat Advisor

Read one exact LINE chat through the `line-readonly` MCP, refreshing the local
DB snapshot even when the Mac is locked or LINE cannot be activated. Export
the requested messages or provide reply advice according to the user's request.
All visible output is in Traditional Chinese (Taiwan).

## Non-negotiable safety

- Never use Computer Use, Chronicle, OCR, screenshots, browser automation, or
  coordinates for LINE.
- Never call or invent `send_message`, `select_chat`, generic input, clipboard,
  keyboard, Shell, AppleScript, or arbitrary app-control tools.
- Never type, paste, focus a composer, press Return/Enter, or send anything.
- Never call `sync_older_messages` for an ordinary latest-message request.
- Never upload or quote private chat history outside the current answer. Do not
  put chat text, chat IDs, snapshots, or relationship context in a repository.
- Suggestions appear only in Codex.

## Capability gate

Before reading any chat, confirm that the callable tool list contains all five
operations from the `line-readonly` MCP, regardless of namespace prefix:

1. `line_status`
2. `refresh_latest`
3. `get_relationship_context`
4. `read_history`
5. `save_relationship_context`

If any operation is absent, stop. Return one line telling the user the
`line-readonly` catalog is stale and Codex must be reloaded. Do not substitute
another tool or an older snapshot.

## Required workflow

1. Resolve the requested contact from the exact display name or a previously
   successful `chatId`. Never guess between duplicate names.
2. Call `line_status`. Continue only when `dbFound`, `keyAvailable`, `decryptOk`,
   `databaseSnapshot.readOnly`, and `databaseSnapshot.queryOnly` are all true.
3. Call `refresh_latest` for the exact chat with `timeoutSeconds: 30`.
   If `ok: true` and `localSnapshotRefreshed: true`, continue reading even when
   `freshnessVerified: false`. The locked-session path now polls passively up
   to the requested timeout (or until the target advances) and returns a
   successful local snapshot instead of a lock error.
   `targetAdvanced` only means a newer local target message appeared; it may
   be outgoing and does not prove incoming delivery or complete server sync.
   Otherwise, if lock state, missing Peekaboo, or focus/launch failure prevents
   verification, or an older result lacks `localSnapshotRefreshed` and reports
   `freshnessVerified: false` without a DB/identity error,
   continue in local-snapshot mode: call `line_status` again and require all
   checks in step 2 to pass before proceeding. This fallback is already
   authorized; do not ask the user to unlock or approve reading local data.
   Stop for missing/inaccessible DB or key, decryption/snapshot failure,
   unresolved contact identity, or unavailable MCP. Never bypass these failures.
4. Call `get_relationship_context` for the same exact chat.
5. If `initialized` is false, call `read_history` with `order: "oldest"` and
   `limit: 200`; follow every `pagination.nextCursor` until `hasMore` is false.
   Only after all pages succeed, synthesize and save the relationship context.
6. If `initialized` is true, call `read_history` with `order: "oldest"`,
   `limit: 200`, and `cursor: summaryThrough`; paginate until `hasMore` is false.
   Merge only the newly read messages into the saved context.
7. Set `summaryThrough` to the timestamp/message ID of the newest message that
   was actually read. Save these four concise, evidence-based fields:
   `relationship`, `stableBackground`, `toneNotes`, and `avoidReasking`.
   Never turn an inference into a fact.
8. Call `save_relationship_context` with the context version returned by the
   preceding get. On `context_version_conflict`, get the current context, rebase
   once, and retry once. If it conflicts again, stop.

Do not save context when pagination is incomplete, no message was read, or the
new cursor was not verified by `read_history`.

## Local snapshot and synchronization

`line_status` and `read_history` each create a new stable read-only snapshot of
the current LINE source DB, WAL and SHM. A failed app activation does not make
this read unavailable. Use the new `read_history` result, not an old export or
the `before`/`after` metadata as message content. Check its `ok`,
`databaseSnapshot.readOnly` and `databaseSnapshot.queryOnly` before using it.

In local-snapshot mode, preface the result with one concise note containing
the actual snapshot time and newest target-chat message time, for example:
「已刷新本機紀錄（讀取時間：…；此對話最新訊息：…）；LINE 同步狀態未確認。」
The current bridge returns `freshnessVerified: false`, `syncComplete: null`
and `serverWatermark: null` because it has no server completion acknowledgement.
These remain unknown even after app activation or target advancement. Treat
legacy `freshnessVerified: true` as local evidence only, not server completion.
Include the synchronization note whenever `syncComplete` is not explicitly
true with authoritative server evidence, including an unlocked successful read.
Do not interpret snapshot time as cloud sync time or claim that no remote
messages exist. Say「本機紀錄未見新訊息」
when appropriate. This mode works while the DB/key remain accessible; a skill
cannot guarantee new server messages while the Mac is asleep/offline or LINE
is logged out. Do not change lock, sleep, login, or security settings.

Local reads may advance `summaryThrough` after complete pagination; that cursor
tracks messages actually read, not verified cloud synchronization. Keep transient
sync failures in the current response, not as relationship facts.

## Transcript requests

For latest-message or date-range requests, output timestamp, sender and content
without unsolicited analysis or reply suggestions. Interpret「最近 N 天」as
today plus the preceding N-1 calendar days in the user's timezone, through now.
After the incremental context workflow, read the requested range separately;
`summaryThrough` must not exclude previously read messages from the export.
Use `order: "latest"` with a sufficient limit, increasing it up to 200 until the
range boundary is covered. If more history is needed, use oldest-first cursor
pagination. If coverage cannot be completed, label it as partial.

Preserve original message text. Show available sticker text, and label images
or other media without inventing their contents. Identify dates with no local
records, and distinguish an empty result from a failed read.

### Default transcript format

Use the user's approved format below for transcript requests unless they ask
for another format. This does not change reply-advice output.

- Open with `聯絡人｜YYYY/M/D–M/D，共 N 則本機訊息。` Count only the
  deduplicated messages actually displayed within the requested range, not the
  tool's total chat count or an unfiltered page count. Label partial coverage.
- Follow with `讀取時間：M/D HH:mm；此對話最新訊息：M/D HH:mm:ss。`
  and the synchronization note required above. State the timezone, e.g.
  `以下時間皆為台灣時間。`; omit the repeated date only when unambiguous.
- Group dates chronologically under `### M/D` headings, with a blank line
  after each heading. For date-range requests, consecutive days with no local
  records may share a heading such as `### M/D–M/D` and the plain-text line
  `本機無對話紀錄。` Do not infer an empty day from incomplete coverage.
- Put each day's messages in a fenced `text` block, oldest first, using
  `HH:mm:ss 你：原文` for outgoing messages and
  `HH:mm:ss 聯絡人稱呼：原文` for incoming messages. Use the confirmed name
  or an established unambiguous short name; do not guess sender identity.
- Keep short exchanges compact; separate longer or multiline messages with
  a blank line. Preserve original line breaks, typos, correction messages,
  emojis and raw URLs; do not silently edit or merge messages.
- Represent media inline as `[圖片]`, `[影片]`, or `[貼圖] 原始可用文字`.
  Do not invent attachment contents. If original text contains a code fence,
  use a longer outer fence so the transcript remains intact.
- Deliver the transcript directly in the answer, without a table, relationship
  analysis, reply suggestions, or a separate file unless the user requests it.

## Relationship and reply judgment

Use the complete saved context plus newly read messages. Give more weight to
recent conversational state than old tone patterns.

Reply when the newest inbound message contains a direct question, actionable
request, emotional bid, meaningful new information needing acknowledgment, or
a natural opening the user would normally continue.

Do not reply when the newest message is outgoing, the exchange has naturally
closed, it is only a reaction/attachment with no reliable meaning, or a reply
would reopen the conversation without benefit. Never invent the content of a
sticker, image, video, call, file, or deleted message.

Infer the user's style from their real outgoing messages. Prefer one short,
natural sentence; at most one question; no customer-service tone, invented
experience, fake emotion, schedule, promise, or sudden over-intimacy.

## Reply-advice output

- Apply this section only when the user requests reply advice.
- Reply needed: output the proposed LINE sentence. No header, quotation
  marks, analysis, alternatives, or explanation.
- No reply needed: output exactly `現在不用回。`
- Local-snapshot mode: include the synchronization note before any advice.
- DB/key/tool failure: output one concise sentence naming the blocker.

Never transmit the proposed sentence to LINE.
