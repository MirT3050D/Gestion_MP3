from django.db import models

class FichierMP3(models.Model):
    fichier = models.FileField(upload_to='mp3/')
    duree_secondes = models.IntegerField(null=True, blank=True)
    metadonnees = models.JSONField(default=dict, blank=True)
    date_upload = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.fichier.name

class Playlist(models.Model):
    nom = models.CharField(max_length=255)
    utilisateur = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    date_creation = models.DateTimeField(auto_now_add=True)
    musiques = models.ManyToManyField(FichierMP3, through='PlaylistTrack')

    def __str__(self):
        return self.nom

class PlaylistTrack(models.Model):
    playlist = models.ForeignKey(Playlist, on_delete=models.CASCADE)
    fichier_mp3 = models.ForeignKey(FichierMP3, on_delete=models.CASCADE)
    ordre = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['ordre']
