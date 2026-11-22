## Project architecture — Mandatory rules

### 1. Directory structure

- The `prototype/` directory is deprecated and will be removed.
- **Never create, use, or reference a `prototype/` directory.**
- All gameplay-related classes and logic must be placed in the existing `gameplay/` directory.
- Reuse the existing project structure instead of creating parallel directories.
- Before adding a new file, inspect the existing files to avoid duplication.
- Keep game logic separate from Pygame rendering and user input.
- The game is designed for multiplayer. Android is the primary platform, and the game also runs on PC, primarily for development and testing.

### 2. Card types

The game supports two card types:

- `character`: a character that can be deployed in an empty slot on its owner's battlefield. Each player has 3 character slots.
- `ref`: a reference card that performs an immediate action on a deployed character.

**Reference cards support exactly three effects:**

- `attack`: deal damage to a deployed enemy character. Shield points absorb damage before HP. A character at 0 HP is removed from its slot.
- `heal`: restore HP to a deployed allied character, up to its maximum HP.
- `shield`: add shield points to a deployed allied character's existing shield.

No other effects are allowed.

Do not implement special abilities, status effects, damage over time, passive abilities, complex triggers, or additional effect categories.

### 3. Reference card synergy

A reference card may be associated with the character responsible for that reference (the character who originally performed or created the reference).

When that character is deployed on the battlefield by the player using the reference card, the reference receives a numerical bonus.

Rules:

- The synergy activates only if the associated character is currently deployed on the player's battlefield.
- The bonus increases the amount of the reference's existing effect.
- The bonus can apply to `attack`, `heal`, or `shield`, depending on the reference card.
- The bonus is applied only when the reference is played.
- The synergy must not create any new effect or ability.
- Synergy configuration must be stored in the reference card's JSON data.
- If the associated character is not deployed, the reference uses its normal amount.

Formula:

`final_amount = base_amount + synergy_bonus`

If no synergy is active:

`final_amount = base_amount`

### 4. Reference JSON configuration

Reference cards must store their effect type, base amount, associated character, and synergy bonus in JSON.

Example:

```json
{
  "kind": "ref",
  "abilities": {
    "effect": {
      "type": "attack",
      "amount": 3
    }
  },
  "synergy": {
    "character_id": "character_jojo",
    "bonus": 2
  }
}
```

In this example:

- Base attack: 3 damage.
- If `character_jojo` is deployed: 5 damage.
- Otherwise: 3 damage.

For references without synergy, use `null` for the `synergy` field.

Keep the JSON schemas consistent with these rules. Do not introduce unnecessary effect fields or complex ability systems.

### 5. Turns, energy, and player HP

- A player must have enough energy to pay a card's `cost` when they play it.
- Players draw their opening hands for free. Drawing cards after that costs energy.
- Players recharge energy on each of their turns.
- The active player can end their turn with **Passer**, including at 0 energy or when they cannot afford any card.
- Track each player's HP separately from their characters' HP.
- In the battle UI, show both players' current HP next to their names and place **Passer** in the top-right corner. On character cards, the left badge shows the energy cost and the right badge shows the character's current HP.
- Preview values are sample data. Starting player HP, the draw cost, energy limits and the amount restored per turn, how players take damage, and victory conditions still need confirmation.

### 6. Multiplayer architecture

- Each player owns an independent deck, hand, and battlefield.
- The game rules must be independent of the rendering system.
- The server must validate turn ownership, pass actions, draws, energy costs, card actions, targets, damage, healing, shields, and synergies.
- Clients must not be authoritative over game state.
- An opponent's hidden cards must not be revealed to the other player.
- Pygame classes are responsible for rendering and interaction, not for deciding game outcomes.

### 7. Simplicity

This is a simple multiplayer card game, not a complex trading card game engine.

- Prefer small, readable Python classes.
- Avoid unnecessary abstractions and design patterns.
- Do not add mechanics that have not been explicitly requested.
- Do not overengineer the effect or synergy systems.
- Ask before introducing new gameplay mechanics.
