from django.contrib import admin, auth
from import_export.admin import ImportExportModelAdmin
from . import models


# --- Authentication and Authorization ---

admin.site.unregister(auth.models.Group)
admin.site.unregister(auth.get_user_model())

@admin.register(auth.get_user_model())
class UserDetailAdmin(ImportExportModelAdmin):
	list_display = ['username']


# --- Provenance Names and Provenance Records ---

class ProvenanceOwnershipInline(admin.TabularInline):
	model = models.ProvenanceOwnership
	search_fields = ('owner',)
	autocomplete_fields = ('owner',)
	extra = 1
	
@admin.register(models.ProvenanceName)
class ProvenanceNameAdmin(ImportExportModelAdmin):
	ordering = ('name',)
	search_fields = ('name',)
	inlines = (ProvenanceOwnershipInline,)

@admin.register(models.ProvenanceOwnership)
class ProvenanceOwnershipAdmin(ImportExportModelAdmin):
	search_fields = ('owner',)
	autocomplete_fields = ('owner',)
	

# --- Locations ---

@admin.register(models.Location)
class LocationAdmin(ImportExportModelAdmin):
	ordering = ('name',)


# --- Core Census Data ---

@admin.register(models.Title)
class TitleAdmin(ImportExportModelAdmin):
	ordering = ('title',)

@admin.register(models.Edition)
class EditionAdmin(ImportExportModelAdmin):
	ordering = ('title__title', 'edition_number')

@admin.register(models.Issue)
class IssueAdmin(ImportExportModelAdmin):
	ordering = ('edition__title__title', 'edition__edition_number', 'estc')

@admin.register(models.Copy)
class CopyAdmin(ImportExportModelAdmin):
	search_fields = ('census_id', 'issue__edition__title__title')
	list_filter=['verification']
	inlines = (ProvenanceOwnershipInline,)


# --- Static Page Text ---

@admin.register(models.StaticPageText)
class StaticPageTextAdmin(ImportExportModelAdmin):
	pass
