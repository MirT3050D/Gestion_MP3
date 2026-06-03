from django.contrib import admin
from .models import FichierMP3

@admin.register(FichierMP3)
class FichierMP3Admin(admin.ModelAdmin):
    list_display = ('id', 'nom_fichier', 'duree_secondes', 'date_upload')
    list_filter = ('date_upload',)
    search_fields = ('fichier',)
    readonly_fields = ('date_upload',)

    def nom_fichier(self, obj):
        return obj.fichier.name.split('/')[-1] if obj.fichier else "Aucun fichier"
    nom_fichier.short_description = "Nom du fichier"
