# Mortis Trials Buff Manager — Three Play Modes

Mortis Buff Manager requires SoloPlay and also supports Realms. Prepare native Mortis Buffs before a mission, earn random choices through mission progress, or compete for personal kill rewards. The host selects one mode and one shared Buff limit (progress: 0–10; other modes: 0–64) for the whole party. Talent Point Manager is optional.

## Three global modes

- Preselection: open the talent tree before the mission and choose your Buffs. Everyone uses the same point limit, including a limit of zero. Each selected Buff costs one point. The list offers category filters, a selected-only view, native icons and a detail panel. Family, class, ability and talent requirements follow native data.
- Progress mode: first choose one of three shared Mortis routes and immediately receive its foundation Buff. Route rewards are automatic, with native legendary choices at reward slots 4, 7 and 10. Including the opening Buff, at most 10 are granted. Path milestones are 8%, 16%, 24%, 32%, 40%, 50%, 60%, 70% and 80%, bringing the final reward forward. Without a linear path, main objective starts supply bounded stage rewards; path and objectives do not double-count. Mortis Trials uses wave events. Time never earns a reward.
- Competition: first choose a route. Each player earns personal kill progress; at 100%, receive an automatic random Buff from the chosen route, with foundation Buffs first. When that route is exhausted, automatically receive compatible public / class Buffs. There are no wave-based legendary choices, no rewards from other routes, and no duplicate Buffs. Overflow is retained. Regular enemies / hordes default to 0.25%, specials 5%, elites 2.5%; ordinary bosses, weakened bosses and captains / twins have separate settings, initially 50% each. Bot kills do not award human-player progress.

## Route and legendary choices

Three compact cards appear above the centre of the screen. Press Ctrl+1, Ctrl+2 or Ctrl+3 to choose. Slide-in, selection highlighting and fade-out show the result. The mod does not stop movement, capture the mouse or open the native modal picker; other menus and text entry take priority over these shortcuts.

Opening route choices and progress-mode legendary choices allow 60 seconds, then the host randomly selects an option. New opportunities queue behind the active choice. Every next choice receives a fresh 60 seconds, even when several opportunities arrive together. Choices are unique and exclude Buffs already acquired. If the eligible pool has fewer than three remaining entries, only those entries are offered; an exhausted pool stops further picks.

Press Tab to see the native Mortis category containing Buffs actually applied to your character. Candidates and queued rewards are not listed as acquired Buffs. In progress and competition modes, the talent-tree Mortis entry is disabled and shows synchronized reward counts. Preselection editing is locked after the mission begins.

Competition also shows a small personal progress indicator at the lower centre of the combat HUD, including while a choice is open. In DMF, choose one of four styles: Small bar, Small bar + percentage (default), Percentage only, or Hidden. Hiding this indicator does not hide reward choices or stop earning progress. This is a local display preference and does not change the host's mode, weights or limits.

## Realms host controls and deployment status

DMF kill-progress numbers support two decimal places and a visible input box: type or paste, press Enter or click elsewhere to confirm, and Esc to cancel. Weakened bosses use the native boss flag; captains and twins always use their own category.

The preparation list has one global Mortis control row: enable the feature, set the shared limit, and select the mode. It appears as soon as the host creates a room, including an empty room. Click the limit to type or paste; Enter or clicking elsewhere confirms, Esc cancels. Minus/plus repeat after a 400 ms hold. Mortis does not provide per-player mode or point overrides.

Each player also has a Mortis deployment status: connecting, ready, loading resources, disabled, missing/incompatible, no response or connection lost. A reported version appears when available. Persistent problems notify the host without repeating every update. A missing/incompatible indication cannot distinguish an absent mod from an unsupported version with certainty; check the guest's installation.

Talent Point Manager 2.2.2 can add its own per-player talent controls and deployment status to the same list. Both integrations preserve the other's rows and text input. A four-player list uses Realms' native scrollbar. Guests do not see host management rows. Without Realms, use DMF Mod options; the integration stays inactive.

## Join, disconnect and rule changes

The host owns candidates, queues and accepted rewards. Guests must confirm their mod and native resources are ready before they receive these Buffs. An unready, disabled or disconnected guest does not hold up other players. A resource or communication interruption pauses that player's active choice and remaining time. Rejoining the same room and character during the same mission retains acquired choices; another character or mission has independent state.

Old-session choices, duplicates and stale replies are rejected. Reconnect handshakes and periodic snapshots recover missed messages. A client stops using stale host rules when the host lease expires. This does not provide host migration or preserve a run after the host closes the room.

Reducing the shared limit limits active Buffs while retaining the saved selection or run history. Raising it can restore the retained choices. Changing reward mode during a mission starts a new run for that mode; configure the intended mode before starting.

## Installation requirements

Required: Darktide Mod Loader, Darktide Mod Framework and SoloPlay. Realms is optional for player-hosted co-op. Use MortisBuffManager 3.1.0 on the host and participating guests. For both management interfaces, also update TalentPointManager to 2.2.2; neither mod requires the other.

## Vortex installation

- Exit the game and install the requirements.
- Download the installation ZIP from Files. Use Install From File in Vortex, enable it, then Deploy Mods.
- Enable MortisBuffManager in Load Order after SoloPlay; keep Realms enabled for co-op.
- Restart. Enable custom Mortis Buffs in Mod options → Mortis Trials Buff Manager, then choose a mode and limit.

## Manual installation

- Exit the game and install the requirements.
- Extract the ZIP's MortisBuffManager folder into Darktide/mods, producing mods/MortisBuffManager.
- Add MortisBuffManager on its own line after SoloPlay in mods/mod_load_order.txt.
- Restart and enable the feature in Mod options. Install one version of this mod at a time.

## Defaults and compatibility

The DMF switch and the feature's own master switch must both be enabled. The feature defaults off, the mode defaults to preselection, and the shared limit defaults to 32. Existing character selections are retained. Disabling DMF removes this mod's UI, input state and applied effects while keeping saved choices.

Buffs use the game's original templates, identifiers and mission-Buff manager. Native stacking and eligibility rules still apply; this is not a promise that every native effect stacks with every other effect. When this feature manages a Mortis Trials mission, it replaces native reward selection to avoid the native picker taking control of the player. Other mods replacing that reward flow can conflict. This mod does not change permanent progression in official matchmaking.

## 3.1.0 validation

Native-source checks compare 128 character / Blitz / combat configurations, seven routes, priority rewards and legendary weights. Local checks cover the real Lua queue/transport logic, native Buff application boundaries, native Tab collection, DMF enable/disable, Realms loading, both control integrations together, three languages and common screen ratios including 16:9, 16:10, 21:9 and 4:3. The cards occupy about 41% less area than the initial preview. Long text shrinks to fit; excessive text uses the native ellipsis fallback.

Images are offline UI layout renders with sample Buff text and players, not gameplay screenshots. Game materials remain in the game; no extracted artwork is included. This release still needs live-game and multiplayer testing.

## Credits

SoloPlay and Realms: deluxghost. Native Mortis systems, Buff definitions and referenced game materials: Fatshark. Existing source and copyright notices are retained in the installation.
