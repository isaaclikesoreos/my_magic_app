from django.db import models
from django.contrib.auth.models import User


class Cube(models.Model):
    POWER_LEVEL_CHOICES = [
        ('vintage', 'Vintage'),
        ('legacy', 'Legacy'),
        ('modern', 'Modern'),
        ('pioneer', 'Pioneer'),
        ('pauper', 'Pauper'),
    ]

    name = models.CharField(max_length=255)
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_cubes')
    card_count = models.IntegerField(default=0)
    draft_count = models.IntegerField(default=0)
    power_level = models.CharField(max_length=20, choices=POWER_LEVEL_CHOICES, null=True, blank=True)
    tags = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.name


class Card(models.Model):
    name = models.CharField(max_length=255)
    mana_cost = models.CharField(max_length=50, null=True, blank=True)
    cmc = models.FloatField(null=True, blank=True)
    color = models.CharField(max_length=50, null=True, blank=True)
    type_line = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.name


class Draft(models.Model):
    cube = models.ForeignKey(Cube, on_delete=models.CASCADE, related_name='drafts')
    pack_count = models.IntegerField(default=3)
    cards_per_pack = models.IntegerField(default=5)
    player_count = models.IntegerField()
    max_players = models.IntegerField(default=8)  # Add this field
    active = models.BooleanField(default=True)
    players_with_active_packs = models.IntegerField(default=0)
    def __str__(self):
        return f"Draft for {self.cube.name}"


class CubeCard(models.Model):
    cube = models.ForeignKey(Cube, on_delete=models.CASCADE, related_name='cube_cards')
    card = models.ForeignKey(Card, on_delete=models.CASCADE, related_name='in_cubes')

    class Meta:
        unique_together = ('cube', 'card')

    def __str__(self):
        return f"{self.card.name} in {self.cube.name}"


class DraftPlayer(models.Model):
    draft = models.ForeignKey(Draft, on_delete=models.CASCADE, related_name='players')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='drafts_participated')
    role = models.CharField(
        max_length=50,
        choices=[("creator", "Creator"), ("player", "Player")],
        default="player"  # Add a default value for new entries
    )

    class Meta:
        unique_together = ('draft', 'user')

    def __str__(self):
        return f"{self.user.username} in {self.draft.cube.name} draft"


class DeckList(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='deck_lists')
    draft = models.ForeignKey(Draft, on_delete=models.CASCADE, related_name='deck_lists2')
    card = models.ForeignKey(Card, on_delete=models.CASCADE, related_name='selected_in_decks')

    class Meta:
        unique_together = ('user', 'draft', 'card')

    def __str__(self):
        return f"{self.card.name} selected by {self.user.username} in {self.draft.cube.name} draft"


class CardImage(models.Model):
    card = models.ForeignKey(Card, on_delete=models.CASCADE, related_name="images")
    image_url = models.URLField(max_length=500)
    is_primary = models.BooleanField(default=False)

    def __str__(self):
        return f"Image for {self.card.name} ({'Primary' if self.is_primary else 'Secondary'})"


class CubeImage(models.Model):
    cube = models.ForeignKey(Cube, on_delete=models.CASCADE, related_name="images")
    image_url = models.URLField(max_length=500)
    is_primary = models.BooleanField(default=False)

    def __str__(self):
        return f"Image for Cube: {self.cube.name} ({'Primary' if self.is_primary else 'Secondary'})"


class DraftPack(models.Model):
    draft = models.ForeignKey(Draft, on_delete=models.CASCADE, related_name="packs")
    player = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name="draft_packs")
    cards = models.ManyToManyField(Card, related_name="packs")
    is_draft_complete = models.BooleanField(default=False)

    def __str__(self):
        return f"Pack for Draft {self.draft.id} - Player: {self.player.username if self.player else 'None'}"


class DraftDeck(models.Model):
    draft = models.ForeignKey(Draft, on_delete=models.CASCADE, related_name="decks")
    player = models.ForeignKey(User, on_delete=models.CASCADE, related_name="decks")
    card = models.ForeignKey(Card, on_delete=models.CASCADE)
    mainboard = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.card.name} drafted by {self.player.username} in {self.draft.cube.name}"
