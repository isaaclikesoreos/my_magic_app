from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Cube, Card, Draft, CubeCard, DraftPlayer, DeckList, CardImage, CubeImage


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']


class CardImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = CardImage
        fields = ["id", "image_url", "is_primary"]


class CubeImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = CubeImage
        fields = ["id", "image_url", "is_primary"]


class CubeSerializer(serializers.ModelSerializer):
    creator = UserSerializer(read_only=True)
    images = CubeImageSerializer(many=True, read_only=True)

    class Meta:
        model = Cube
        fields = ["id", "name", "creator", "card_count", "draft_count", "power_level", "tags", "description", "images"]


class CardSerializer(serializers.ModelSerializer):
    images = CardImageSerializer(many=True, read_only=True)

    class Meta:
        model = Card
        fields = ["id", "name", "mana_cost", "color", "type_line", "images"]


class DraftSerializer(serializers.ModelSerializer):
    cube = CubeSerializer(read_only=True)

    class Meta:
        model = Draft
        fields = ['id', 'cube', 'pack_count', 'cards_per_pack', 'player_count', 'active']


class DraftPlayerSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = DraftPlayer
        fields = ['id', 'draft', 'user', 'role']


class DeckListSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    draft = DraftSerializer()
    card = CardSerializer()

    class Meta:
        model = DeckList
        fields = ['id', 'user', 'draft', 'card']
