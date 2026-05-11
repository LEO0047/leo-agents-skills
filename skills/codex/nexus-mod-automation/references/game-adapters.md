# Game Adapters

The Nexus/Vortex workflow is generic. A game adapter decides what a valid mod looks like and how load order should be written.

## Adapter Responsibilities

- Define install roots and manager-owned folders.
- Define metadata sources: manifest, plugin headers, hashes, UUIDs, file names, folder names, or manager metadata.
- Decide whether loose files are allowed and where they go.
- Decide duplicate handling rules.
- Write or export load order through the correct game-specific tool.
- Validate the game can see the intended files.

## BG3 Example

BG3 is an adapter example, not the generic workflow:

- Payloads are usually `.pak`.
- Identity is usually in `meta.lsx` inside the pak.
- Save recovery can compare save UUIDs to installed pak UUIDs.
- Load order is written to `PlayerProfiles\Public\modsettings.lsx`.
- Unique Tav and similar mods may require loose files under the game `Data` folder if the mod instructions say so.

Keep BG3 scripts in a BG3-focused skill such as `game-mod-management`; do not bake BG3 assumptions into this generic skill.

## Bethesda Example

For Skyrim/Fallout-style games:

- Payloads may include `.esp`, `.esm`, `.esl`, BSA/BA2 archives, DLL plugins, and loose files.
- Load order should be handled by a game-specific manager or LOOT-aware workflow.
- The generic archive inspector can flag payload types, but it cannot decide plugin order.

## Other Games

Use the strongest available proof:

- Author or manager manifest.
- Hashes from a trusted local manifest.
- Game-specific metadata files.
- Exact expected file names only when no stronger metadata exists.

When proof is weak, report a candidate rather than installing automatically.
