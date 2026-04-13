"""
Unit-тесты для get_random_notification_message.

Стратегия:
- Детерминированные тесты через random.seed — проверяют точную строку.
- Параметризованные тесты — покрывают все 5 шаблонов и граничные случаи склонения.
- Инвариантные свойства — независимо от seed: комментарий есть, пол согласован.
"""
import sys
import os
import random
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from bot_stars.commands import get_random_notification_message


# ---------------------------------------------------------------------------
# Детерминированные тесты (random.seed)
# ---------------------------------------------------------------------------

class TestDeterministicMessages:
    async def test_seed0_male(self):
        random.seed(0)
        msg = await get_random_notification_message(3, "помогал на служении", "Мужской")
        assert msg == "🌠 Ты только что поймал 3 звезды за то, что ты помогал на служении. Красавчик!"

    async def test_seed1_male(self):
        random.seed(1)
        msg = await get_random_notification_message(3, "помогал на служении", "Мужской")
        assert msg == "🌟 Бум! На твой счёт упали 3 звезды за то, что ты помогал на служении. Продолжай сиять!"

    async def test_seed42_male(self):
        random.seed(42)
        msg = await get_random_notification_message(3, "помогал на служении", "Мужской")
        assert msg == "🚀 Круто! Ты получил 3 звезды за то, что ты помогал на служении. Красавчик!"

    async def test_seed0_female(self):
        random.seed(0)
        msg = await get_random_notification_message(3, "помогла на служении", "Женский")
        assert msg == "🌠 Ты только что поймала 3 звезды за то, что ты помогла на служении. Молодец!"

    async def test_seed42_female(self):
        random.seed(42)
        msg = await get_random_notification_message(3, "помогла на служении", "Женский")
        assert msg == "🚀 Круто! Ты получила 3 звезды за то, что ты помогла на служении. Молодец!"


# ---------------------------------------------------------------------------
# Инвариантные свойства (независимо от seed)
# ---------------------------------------------------------------------------

MALE_VERB_FORMS = {"получил", "поймал"}
FEMALE_VERB_FORMS = {"получила", "поймала"}
# В варианте «Бум! На твой счёт упало/упала/упали» нет глагола «получил»
MALE_INDICATORS = MALE_VERB_FORMS | {"упал"}      # упала/упали — подходят обоим
FEMALE_INDICATORS = FEMALE_VERB_FORMS | {"упала", "упали", "упал"}

N_SAMPLES = 30  # достаточно, чтобы выпали все 5 шаблонов


class TestInvariantProperties:
    @pytest.mark.parametrize("comment", ["убирал зал", "пел на сцене", "вёл группу"])
    async def test_comment_always_present_male(self, comment):
        for seed in range(N_SAMPLES):
            random.seed(seed)
            msg = await get_random_notification_message(5, comment, "Мужской")
            assert comment in msg, f"seed={seed}: комментарий не найден"

    @pytest.mark.parametrize("comment", ["убирала зал", "пела на сцене"])
    async def test_comment_always_present_female(self, comment):
        for seed in range(N_SAMPLES):
            random.seed(seed)
            msg = await get_random_notification_message(5, comment, "Женский")
            assert comment in msg

    async def test_male_no_female_compliment(self):
        for seed in range(N_SAMPLES):
            random.seed(seed)
            msg = await get_random_notification_message(1, "тест", "Мужской")
            assert "Молодец" not in msg
            assert "Красавчик" in msg or "сиять" in msg or "держать" in msg

    async def test_female_no_male_compliment(self):
        for seed in range(N_SAMPLES):
            random.seed(seed)
            msg = await get_random_notification_message(1, "тест", "Женский")
            assert "Красавчик" not in msg

    async def test_female_no_hero_male_form(self):
        """«звёздный герой!» никогда не попадает в женский вариант."""
        for seed in range(N_SAMPLES):
            random.seed(seed)
            msg = await get_random_notification_message(2, "тест", "Женский")
            assert "звёздный герой!" not in msg


# ---------------------------------------------------------------------------
# Склонение числа звёзд (параметризовано)
# ---------------------------------------------------------------------------

class TestStarDeclension:
    @pytest.mark.parametrize("stars,form_in_accusative,form_in_nominative", [
        (1,  "звезду",  "звезда"),   # вин. / им. (шаблон «Бум»)
        (2,  "звезды",  "звезды"),
        (3,  "звезды",  "звезды"),
        (4,  "звезды",  "звезды"),
        (5,  "звёзд",   "звёзд"),
        (11, "звёзд",   "звёзд"),    # исключение 11
        (12, "звёзд",   "звёзд"),
        (21, "звезду",  "звезда"),
    ])
    async def test_star_word_in_message(self, stars, form_in_accusative, form_in_nominative):
        random.seed(42)
        msg = await get_random_notification_message(stars, "тест", "Мужской")
        assert form_in_accusative in msg or form_in_nominative in msg, (
            f"stars={stars}: ни '{form_in_accusative}', ни '{form_in_nominative}' не найдено в: {msg!r}"
        )

    async def test_stars_count_is_present(self):
        for stars in [1, 5, 11, 42, 100]:
            random.seed(0)
            msg = await get_random_notification_message(stars, "тест", "Мужской")
            assert str(stars) in msg


# ---------------------------------------------------------------------------
# Все 5 шаблонов достижимы за 30 итераций
# ---------------------------------------------------------------------------

TEMPLATE_MARKERS = ["🚀", "🌟", "💫", "🌠", "✨"]


class TestAllTemplatesReachable:
    async def test_all_five_templates_appear(self):
        seen_markers = set()
        for seed in range(50):
            random.seed(seed)
            msg = await get_random_notification_message(3, "тест", "Мужской")
            for marker in TEMPLATE_MARKERS:
                if msg.startswith(marker):
                    seen_markers.add(marker)
            if seen_markers == set(TEMPLATE_MARKERS):
                break
        assert seen_markers == set(TEMPLATE_MARKERS), (
            f"Не все шаблоны были выбраны. Найдены: {seen_markers}"
        )
