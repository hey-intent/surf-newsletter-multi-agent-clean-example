"""Tests for core personas."""

import pytest

from src.core.personas import ALL_PERSONAS, ANNIE, JOHNNY, JOANA, Persona


class TestPersona:
    """Tests for the Persona dataclass."""

    def test_persona_creation(self, sample_persona: Persona):
        """Test basic persona creation."""
        assert sample_persona.name == "TestPersona"
        assert sample_persona.description == "A test persona for unit testing."
        assert sample_persona.system_prompt == "You are a test persona."
        assert "Test criterion" in sample_persona.criteria_text

    def test_persona_is_frozen(self, sample_persona: Persona):
        """Test persona is immutable (frozen dataclass)."""
        with pytest.raises(AttributeError):
            sample_persona.name = "NewName"

    def test_persona_equality(self):
        """Test persona equality based on all fields."""
        persona1 = Persona(
            name="Test",
            description="Desc",
            system_prompt="Prompt",
            criteria_text="Criteria",
        )
        persona2 = Persona(
            name="Test",
            description="Desc",
            system_prompt="Prompt",
            criteria_text="Criteria",
        )
        assert persona1 == persona2


class TestPredefinedPersonas:
    """Tests for the predefined personas (Johnny, Annie, Joana)."""

    def test_johnny_exists(self):
        """Test Johnny persona is defined."""
        assert JOHNNY is not None
        assert JOHNNY.name == "Johnny"
        assert len(JOHNNY.description) > 0
        assert len(JOHNNY.system_prompt) > 0
        assert len(JOHNNY.criteria_text) > 0

    def test_annie_exists(self):
        """Test Annie persona is defined."""
        assert ANNIE is not None
        assert ANNIE.name == "Annie"
        assert len(ANNIE.description) > 0
        assert len(ANNIE.system_prompt) > 0
        assert len(ANNIE.criteria_text) > 0

    def test_joana_exists(self):
        """Test Joana persona is defined."""
        assert JOANA is not None
        assert JOANA.name == "Joana"
        assert len(JOANA.description) > 0
        assert len(JOANA.system_prompt) > 0
        assert len(JOANA.criteria_text) > 0

    def test_all_personas_list(self):
        """Test ALL_PERSONAS contains all three personas."""
        assert len(ALL_PERSONAS) == 3
        assert JOHNNY in ALL_PERSONAS
        assert ANNIE in ALL_PERSONAS
        assert JOANA in ALL_PERSONAS

    def test_persona_names_unique(self):
        """Test all persona names are unique."""
        names = [p.name for p in ALL_PERSONAS]
        assert len(names) == len(set(names))

    def test_johnny_criteria_has_weights(self):
        """Test Johnny's criteria include percentage weights."""
        assert "30%" in JOHNNY.criteria_text or "%" in JOHNNY.criteria_text

    def test_annie_criteria_has_weights(self):
        """Test Annie's criteria include percentage weights."""
        assert "35%" in ANNIE.criteria_text or "%" in ANNIE.criteria_text

    def test_joana_criteria_has_weights(self):
        """Test Joana's criteria include percentage weights."""
        assert "35%" in JOANA.criteria_text or "%" in JOANA.criteria_text

    def test_personas_have_distinct_focus(self):
        """Test each persona has a distinct focus area."""
        # Johnny focuses on performance/competition
        assert "performance" in JOHNNY.system_prompt.lower() or "competition" in JOHNNY.system_prompt.lower()

        # Annie focuses on travel/lifestyle
        assert "travel" in ANNIE.system_prompt.lower() or "destination" in ANNIE.system_prompt.lower()

        # Joana focuses on environment/community
        assert "environment" in JOANA.system_prompt.lower() or "community" in JOANA.system_prompt.lower()
