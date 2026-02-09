"""Integration test for battle gen9vgc2025regi-2390379047.

This test validates our parser against a real Pokemon Showdown VGC battle:
- vernon1059 (p1) vs K1ngzzz (p2)
- Format: Gen 9 VGC 2025 Reg I
- Winner: K1ngzzz (p2)

Key mechanics in this battle:
- Snow Warning sets Snowscape
- Psychic Surge sets Psychic Terrain
- Aurora Veil under snow
- Moongeist Beam OHKO on Froslass (super effective)
- Leech Seed chip damage
- Intimidate stat drop
- Tera Shift (Terapagos)
- Tera Shell ability (reduces damage at full HP)
- Terastallize to Stellar
- Teraform Zero clears weather/terrain
- Tera Starstorm spread move
- Poison Touch inflicts poison
- Protect blocks Fake Out
- Multiple faints
"""

import pytest
from pathlib import Path

from parsers import (
    parse_battle_log_file,
    get_damage_events,
    get_move_events,
)


LOG_FILE = "doc/logs/gen9vgc2025regi-2390379047.log"


@pytest.fixture
def battle():
    """Parse the battle log."""
    return parse_battle_log_file(LOG_FILE)


class TestBattleMetadata:
    """Test battle metadata extraction."""

    def test_players(self, battle):
        """Verify players are correctly identified."""
        assert battle.players["p1"] == "vernon1059"
        assert battle.players["p2"] == "K1ngzzz"

    def test_winner(self, battle):
        """Verify winner is K1ngzzz."""
        assert battle.winner == "K1ngzzz"

    def test_total_turns(self, battle):
        """Verify battle lasted 7+ turns."""
        # Log shows turns 1-7, plus setup turn
        assert len(battle.turns) >= 7


class TestTeamComposition:
    """Test team parsing."""

    def test_p1_team_size(self, battle):
        """P1 has 6 Pokemon."""
        assert len(battle.teams["p1"]) == 6

    def test_p2_team_size(self, battle):
        """P2 has 6 Pokemon."""
        assert len(battle.teams["p2"]) == 6

    def test_p1_team_species(self, battle):
        """Verify P1's team species."""
        species = [p["species"] for p in battle.teams["p1"]]
        assert "Abomasnow" in species
        assert "Froslass" in species
        assert "Hippowdon" in species
        assert "Garchomp" in species
        assert "Muk-Alola" in species
        assert "Tsareena" in species

    def test_p2_team_species(self, battle):
        """Verify P2's team species."""
        species = [p["species"] for p in battle.teams["p2"]]
        assert "Lunala" in species
        assert "Terapagos" in species
        assert "Indeedee-F" in species
        assert "Comfey" in species
        assert "Incineroar" in species
        assert "Meowscarada" in species

    def test_pokemon_levels(self, battle):
        """All Pokemon are level 50."""
        for team in battle.teams.values():
            for pokemon in team:
                assert pokemon["level"] == 50


class TestTurn1Events:
    """Test Turn 1 events."""

    def test_froslass_ohko(self, battle):
        """Froslass is OHKO'd by Moongeist Beam (super effective Ghost vs Ghost)."""
        damage_events = get_damage_events(battle)
        turn1_damage = [e for e in damage_events if e["turn"] == 1]

        # Froslass goes from 100 to 0
        froslass_ko = [e for e in turn1_damage if e["slot"] == "p1b"]
        assert len(froslass_ko) == 1
        assert froslass_ko[0]["hp_before"] == 100
        assert froslass_ko[0]["hp_after"] == 0
        assert froslass_ko[0]["damage"] == 100

    def test_turn1_move_order(self, battle):
        """Verify turn 1 move order: Helping Hand -> Moongeist Beam -> Aurora Veil."""
        move_events = get_move_events(battle)
        turn1_moves = [e for e in move_events if e["turn"] == 1]

        assert len(turn1_moves) == 3
        assert turn1_moves[0]["move"] == "Helping Hand"
        assert turn1_moves[1]["move"] == "Moongeist Beam"
        assert turn1_moves[2]["move"] == "Aurora Veil"


class TestTurn2Events:
    """Test Turn 2 events - Leech Seed, Minimize."""

    def test_muk_takes_resisted_damage(self, battle):
        """Muk takes resisted damage from Moongeist Beam."""
        damage_events = get_damage_events(battle)
        turn2_damage = [e for e in damage_events if e["turn"] == 2 and e["slot"] == "p1b"]

        # Muk goes from 100 to 76 (resisted)
        muk_damage = [e for e in turn2_damage if e["source"] == ""]
        assert len(muk_damage) == 1
        assert muk_damage[0]["damage"] == 24

    def test_leech_seed_damage(self, battle):
        """Leech Seed deals chip damage to Lunala."""
        damage_events = get_damage_events(battle)
        turn2_damage = [e for e in damage_events if e["turn"] == 2]

        leech_seed = [e for e in turn2_damage if e["source"] == "Leech Seed"]
        assert len(leech_seed) == 1
        assert leech_seed[0]["slot"] == "p2b"
        assert leech_seed[0]["damage"] == 12  # 1/8 of max HP

    def test_minimize_used(self, battle):
        """Muk uses Minimize."""
        move_events = get_move_events(battle)
        turn2_moves = [e for e in move_events if e["turn"] == 2]

        minimize = [e for e in turn2_moves if e["move"] == "Minimize"]
        assert len(minimize) == 1
        assert minimize[0]["user"] == "Muk"


class TestTurn3Events:
    """Test Turn 3 events - Terapagos switch, Tera Shell."""

    def test_blizzard_spread(self, battle):
        """Blizzard is a spread move hitting both targets."""
        move_events = get_move_events(battle)
        turn3_moves = [e for e in move_events if e["turn"] == 3]

        blizzard = [e for e in turn3_moves if e["move"] == "Blizzard"]
        assert len(blizzard) == 1
        assert blizzard[0]["spread"] is True

    def test_tera_shell_reduces_damage(self, battle):
        """Tera Shell reduces damage to Terapagos at full HP."""
        damage_events = get_damage_events(battle)
        turn3_damage = [e for e in damage_events if e["turn"] == 3 and e["slot"] == "p2a"]

        # Terapagos takes only 11 damage from Blizzard (Tera Shell resistance)
        assert len(turn3_damage) == 1
        assert turn3_damage[0]["damage"] == 11


class TestTurn4Events:
    """Test Turn 4 events - Intimidate, Terastallize, Poison Touch."""

    def test_tera_starstorm_spread(self, battle):
        """Tera Starstorm is a spread move when Terastallized."""
        move_events = get_move_events(battle)
        turn4_moves = [e for e in move_events if e["turn"] == 4]

        starstorm = [e for e in turn4_moves if e["move"] == "Tera Starstorm"]
        assert len(starstorm) == 1
        assert starstorm[0]["spread"] is True

    def test_drain_punch_super_effective(self, battle):
        """Drain Punch is super effective on Terapagos-Stellar (Fighting vs Normal)."""
        damage_events = get_damage_events(battle)
        turn4_damage = [e for e in damage_events if e["turn"] == 4 and e["slot"] == "p2a"]

        # First damage to Terapagos this turn is from Drain Punch (21 damage)
        terapagos_damage = [e for e in turn4_damage if e["source"] == ""]
        assert len(terapagos_damage) >= 1
        assert terapagos_damage[0]["damage"] == 21

    def test_poison_touch_inflicts_poison(self, battle):
        """Poison Touch inflicts poison on Terapagos."""
        damage_events = get_damage_events(battle)
        turn4_damage = [e for e in damage_events if e["turn"] == 4]

        # Poison damage at end of turn
        poison_damage = [e for e in turn4_damage if e["source"] == "psn"]
        assert len(poison_damage) == 1
        assert poison_damage[0]["slot"] == "p2a"
        assert poison_damage[0]["damage"] == 13


class TestTurn5Events:
    """Test Turn 5 events - Protect, Fake Out blocked."""

    def test_protect_used(self, battle):
        """Abomasnow uses Protect."""
        move_events = get_move_events(battle)
        turn5_moves = [e for e in move_events if e["turn"] == 5]

        protect = [e for e in turn5_moves if e["move"] == "Protect"]
        assert len(protect) == 1
        assert protect[0]["user"] == "Abomasnow"

    def test_fake_out_after_protect(self, battle):
        """Fake Out is used but blocked by Protect (no damage to Abomasnow)."""
        move_events = get_move_events(battle)
        turn5_moves = [e for e in move_events if e["turn"] == 5]

        fake_out = [e for e in turn5_moves if e["move"] == "Fake Out"]
        assert len(fake_out) == 1
        assert fake_out[0]["user"] == "Incineroar"

        # No direct damage to Abomasnow this turn (protected)
        damage_events = get_damage_events(battle)
        turn5_damage = [e for e in damage_events if e["turn"] == 5 and e["slot"] == "p1a"]
        assert len(turn5_damage) == 0

    def test_poison_continues(self, battle):
        """Poison continues to damage Terapagos."""
        damage_events = get_damage_events(battle)
        turn5_damage = [e for e in damage_events if e["turn"] == 5]

        poison_damage = [e for e in turn5_damage if e["source"] == "psn"]
        assert len(poison_damage) == 1
        assert poison_damage[0]["damage"] == 12


class TestTurn6Events:
    """Test Turn 6 events - Double KO."""

    def test_abomasnow_faints(self, battle):
        """Abomasnow faints from Tera Starstorm."""
        damage_events = get_damage_events(battle)
        turn6_damage = [e for e in damage_events if e["turn"] == 6 and e["slot"] == "p1a"]

        assert len(turn6_damage) == 1
        assert turn6_damage[0]["hp_after"] == 0

    def test_muk_faints(self, battle):
        """Muk faints from Tera Starstorm."""
        damage_events = get_damage_events(battle)
        turn6_damage = [e for e in damage_events if e["turn"] == 6 and e["slot"] == "p1b"]

        assert len(turn6_damage) == 1
        assert turn6_damage[0]["hp_after"] == 0


class TestTurn7Events:
    """Test Turn 7 events - Final KO."""

    def test_tsareena_faints(self, battle):
        """Tsareena faints from Tera Starstorm, ending the battle."""
        damage_events = get_damage_events(battle)
        turn7_damage = [e for e in damage_events if e["turn"] == 7 and e["slot"] == "p1b"]

        assert len(turn7_damage) == 1
        assert turn7_damage[0]["hp_after"] == 0


class TestDamageProgression:
    """Test damage values match Showdown log exactly."""

    def test_all_damage_values(self, battle):
        """Verify all damage events match expected values from log."""
        damage_events = get_damage_events(battle)

        # Expected damage sequence from the log
        expected = [
            # Turn 1: Froslass OHKO
            {"turn": 1, "slot": "p1b", "damage": 100},
            # Turn 2: Muk resisted, Leech Seed
            {"turn": 2, "slot": "p1b", "damage": 24},
            {"turn": 2, "slot": "p2b", "damage": 12},  # Leech Seed
            # Turn 3: Moongeist to Abomasnow, Blizzard hits, Leech Seed
            {"turn": 3, "slot": "p1a", "damage": 31},
            {"turn": 3, "slot": "p2a", "damage": 11},  # Tera Shell
            {"turn": 3, "slot": "p2b", "damage": 20},  # Blizzard
            {"turn": 3, "slot": "p2b", "damage": 12},  # Leech Seed
            # Turn 4: Tera Starstorm spread, Drain Punch, Blizzard, poison
            {"turn": 4, "slot": "p1a", "damage": 37},
            {"turn": 4, "slot": "p1b", "damage": 34},
            {"turn": 4, "slot": "p2a", "damage": 21},  # Drain Punch
            {"turn": 4, "slot": "p2a", "damage": 15},  # Blizzard
            {"turn": 4, "slot": "p2b", "damage": 7},   # Blizzard resisted
            {"turn": 4, "slot": "p2a", "damage": 13},  # Poison
            # Turn 5: Tera Starstorm (protected Abomasnow), poison
            {"turn": 5, "slot": "p1b", "damage": 33},
            {"turn": 5, "slot": "p2a", "damage": 12},  # Poison
        ]

        for exp in expected:
            matching = [
                e for e in damage_events
                if e["turn"] == exp["turn"]
                and e["slot"] == exp["slot"]
                and e["damage"] == exp["damage"]
            ]
            assert len(matching) >= 1, f"Missing damage event: {exp}"


class TestMoveSequence:
    """Test complete move sequence."""

    def test_total_moves(self, battle):
        """Count total moves in the battle."""
        move_events = get_move_events(battle)
        # Approximately 20+ moves across 7 turns
        assert len(move_events) >= 18

    def test_helping_hand_count(self, battle):
        """Helping Hand is used twice (turns 1 and 2)."""
        move_events = get_move_events(battle)
        helping_hand = [e for e in move_events if e["move"] == "Helping Hand"]
        assert len(helping_hand) == 2

    def test_moongeist_beam_count(self, battle):
        """Moongeist Beam is used 3 times."""
        move_events = get_move_events(battle)
        moongeist = [e for e in move_events if e["move"] == "Moongeist Beam"]
        assert len(moongeist) == 3

    def test_tera_starstorm_count(self, battle):
        """Tera Starstorm is used 4 times (turns 4-7)."""
        move_events = get_move_events(battle)
        starstorm = [e for e in move_events if e["move"] == "Tera Starstorm"]
        assert len(starstorm) == 4

    def test_blizzard_count(self, battle):
        """Blizzard is used twice."""
        move_events = get_move_events(battle)
        blizzard = [e for e in move_events if e["move"] == "Blizzard"]
        assert len(blizzard) == 2


class TestBattleOutcome:
    """Verify final battle outcome."""

    def test_p2_wins(self, battle):
        """K1ngzzz (p2) wins the battle."""
        assert battle.winner == "K1ngzzz"

    def test_p1_loses_all_pokemon(self, battle):
        """P1 loses Froslass, Abomasnow, Muk, and Tsareena."""
        damage_events = get_damage_events(battle)

        # Count faints (hp_after == 0)
        p1_faints = [e for e in damage_events if e["slot"].startswith("p1") and e["hp_after"] == 0]
        assert len(p1_faints) >= 4  # Froslass, Abomasnow, Muk, Tsareena

    def test_battle_ends_turn_7(self, battle):
        """Battle ends on turn 7 with Tsareena's faint."""
        damage_events = get_damage_events(battle)

        # Final KO is on turn 7
        turn7_kos = [e for e in damage_events if e["turn"] == 7 and e["hp_after"] == 0]
        assert len(turn7_kos) >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
