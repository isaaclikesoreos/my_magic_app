from django.contrib import admin
from .models import Cube, Card, Draft, DeckList, CubeCard, CardImage, CubeImage, DraftPlayer, DraftPack
from django.utils.html import format_html

# Custom Admin for Card
class CardAdmin(admin.ModelAdmin):
    list_display = ('name', 'mana_cost', 'color', 'type_line', 'display_image')
    search_fields = ('name',)
    list_filter = ('color', 'type_line')

    def display_image(self, obj):
        images = CardImage.objects.filter(card=obj, is_primary=True)
        if images.exists():
            return format_html('<img src="{}" width="100" />', images.first().image_url)
        return "No Image"

    display_image.short_description = "Primary Card Image"

# Custom Admin for Cube
class CubeAdmin(admin.ModelAdmin):
    list_display = ('name', 'creator', 'card_count', 'draft_count', 'power_level', 'tags')
    search_fields = ('name', 'tags', 'creator__username')
    list_filter = ('power_level',)

# Custom Admin for Draft
class DraftAdmin(admin.ModelAdmin):
    list_display = ('id','cube', 'pack_count', 'cards_per_pack', 'player_count', 'active')
    search_fields = ('cube__name',)
    list_filter = ('active',)

# Registering Models
admin.site.register(Cube, CubeAdmin)
admin.site.register(Card, CardAdmin)
admin.site.register(Draft, DraftAdmin)
admin.site.register(DeckList)
admin.site.register(CubeCard)
admin.site.register(CardImage)
admin.site.register(CubeImage)
admin.site.register(DraftPlayer)
admin.site.register(DraftPack)
