from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.models import Group
from django.db.models.expressions import RawSQL
from import_export.admin import ImportExportModelAdmin
from . import models


# --- Authentication and Authorization ---

try:
    admin.site.unregister(Group)
except admin.sites.NotRegistered:
    pass

User = get_user_model()
try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass

@admin.register(User)
class UserAdmin(ImportExportModelAdmin, DjangoUserAdmin):
    list_display = ("username", "email", "is_staff", "is_active")
    search_fields = ("username", "email")
    ordering = ("username",)


# --- Provenance Names and Provenance Records ---

class ProvenanceOwnershipInline(admin.TabularInline):
	model = models.ProvenanceOwnership
	autocomplete_fields = ('owner',)
	extra = 1
	
@admin.register(models.ProvenanceName)
class ProvenanceNameAdmin(ImportExportModelAdmin):
	ordering = ('name',)
	search_fields = ('name',)
	inlines = (ProvenanceOwnershipInline,)

@admin.register(models.ProvenanceOwnership)
class ProvenanceOwnershipAdmin(ImportExportModelAdmin):
    ordering = ("owner__name", "id")
    search_fields = ("owner__name",)
    autocomplete_fields = ("owner",)
	

# --- Locations ---

@admin.register(models.Location)
class LocationAdmin(ImportExportModelAdmin):
	ordering = ('name',)
	search_fields = ("name",)


# --- Core Census Data ---

@admin.register(models.Title)
class TitleAdmin(ImportExportModelAdmin):
	ordering = ('title',)
	search_fields = ("title",)

@admin.register(models.Edition)
class EditionAdmin(ImportExportModelAdmin):
	ordering = ('title__title', 'edition_number')
	search_fields = ("title__title",)
	autocomplete_fields = ("title",)
	list_select_related = ("title",)

@admin.register(models.Issue)
class IssueAdmin(ImportExportModelAdmin):
	ordering = ('edition__title__title', 'edition__edition_number', 'estc')
	search_fields = ("estc", "edition__title__title")
	autocomplete_fields = ("edition",)
	list_select_related = ("edition", "edition__title")

@admin.register(models.Copy)
class CopyAdmin(ImportExportModelAdmin):
    search_fields = ("census_id", "issue__edition__title__title")
    list_filter = ["verification"]
    autocomplete_fields = ("issue",)
    list_select_related = ("issue", "issue__edition", "issue__edition__title")

    def get_ordering(self, request):
        return ()

    def get_queryset(self, request):
        qs = super().get_queryset(request)

        is_numeric_sql = (
            "(census_id GLOB '[0-9]*' OR census_id GLOB '[0-9]*.[0-9]*') AND census_id != ''"
        )
        
        return qs.order_by(
            "issue__edition__title__title",
            "issue__edition__edition_number",
            "issue__estc",
            RawSQL(f"CASE WHEN {is_numeric_sql} THEN 0 ELSE 1 END", []),  # numerics first
            RawSQL("CASE WHEN " + is_numeric_sql + " THEN CAST(census_id AS REAL) END", []),
            "census_id",
        )


# --- Static Page Text ---

@admin.register(models.StaticPageText)
class StaticPageTextAdmin(ImportExportModelAdmin):
	pass
