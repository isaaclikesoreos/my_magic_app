from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Cube, Card, Draft, DeckList, CustomUser, CubeCard, CardImage, CubeImage, DraftPlayer
from django.utils.html import format_html

# Custom UserAdmin for the CustomUser model
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('display_name', 'display_img')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'display_name', 'password1', 'password2'),
        }),
    )

class CardAdmin(admin.ModelAdmin):
    list_display = ('name', 'mana_cost', 'color', 'type_line', 'image')
    search_fields = ('name',)
    list_filter = ('color', 'type_line')


    def display_image(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="100" />', obj.image)
        return "No Image"
    display_image.short_description = "Card Image"

# Register models with admin
admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Cube)
admin.site.register(Card)
admin.site.register(Draft)
admin.site.register(DeckList)
admin.site.register(CubeCard)
admin.site.register(CardImage)
admin.site.register(CubeImage)
admin.site.register(DraftPlayer)
