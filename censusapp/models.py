from django.db import models
from .utils import split_record


# --- TextChoices (employed by other models) --- 

class CenturyChoices(models.TextChoices):
	SEVENTEENTH = '17', 'Pre-1700'
	EIGHTEENTH = '18', '18th-Century'
	NINETEENTH = '19', '19th-Century'
	TWENTIETH = '20', 'Post-1900'

class GenderChoices(models.TextChoices):
	MALE = 'M', 'Male'
	FEMALE = 'F', 'Female'
	UNKNOWN = 'U', 'Unknown'
	NOT_APPLICABLE = 'X', 'N/A'

class VerificationChoices(models.TextChoices):
	VERIFIED = 'V', 'Verified'
	UNVERIFIED = 'U', 'Unverified'
	FALSE = 'F', 'False'


# --- Six core data tables ---

class Location(models.Model):
	name = models.CharField(max_length=500)
	city = models.CharField(max_length=128, blank=True, null=True)
	state = models.CharField('State/Province/County', max_length=128, blank=True, null=True)
	country = models.CharField(max_length=128, blank=True, null=True)
	continent = models.CharField(max_length=128, blank=True, null=True)    

	def __str__(self):
		return self.name

class ProvenanceName(models.Model):
	name = models.CharField(max_length=256, blank=False)
	bio = models.CharField(max_length=1024, blank=True, null=True)
	viaf = models.CharField('VIAF', max_length=256, blank=True, null=True)
	start_century = models.CharField(max_length=2, choices=CenturyChoices.choices, blank=True, null=True)
	end_century = models.CharField(max_length=2, choices=CenturyChoices.choices, blank=True, null=True)
	gender = models.CharField(max_length=1, choices=GenderChoices.choices, blank=True, null=True)

	def __str__(self):
		return self.name

	class Meta:
		verbose_name_plural = "Provenance Names"
		verbose_name = "Provenance Name"

class Title(models.Model):
	title = models.CharField(max_length=128, unique=True)
	apocryphal = models.BooleanField(default=False)
	notes = models.TextField(blank=True, null=True)
	image = models.ImageField(upload_to='titleicon', blank=True, null=True)

	def __str__(self):
		return self.title

class Edition(models.Model):
	title = models.ForeignKey(Title, on_delete=models.CASCADE)
	edition_number = models.CharField(max_length=20, unique=False, blank=False)
	edition_format = models.CharField(max_length=10, blank=True, null=True)
	notes = models.TextField(blank=True, null=True)

	def __str__(self):
		return f"{self.title} {self.edition_number}"

class Issue(models.Model):
	edition = models.ForeignKey(Edition, unique=False, on_delete=models.CASCADE)
	stc_wing = models.CharField('STC / Wing', max_length=20, blank=True, null=True)
	estc = models.CharField('ESTC', max_length=20, blank=True, null=True)
	year = models.CharField(max_length=20, blank=True, null=True)
	start_date = models.IntegerField(blank=True, default=0)
	end_date = models.IntegerField(blank=True, default=0)
	deep = models.CharField('DEEP', max_length=20, blank=True, null=True)
	notes = models.TextField(blank=True, null=True)

	def estc_as_list(self):
		return split_record(self.estc)

	def deep_as_list(self):
		return split_record(self.deep)

	def __str__(self):
		return f"{self.edition} {self.estc}"

class Copy(models.Model):
	issue = models.ForeignKey(Issue, unique=False, on_delete=models.CASCADE)
	location = models.ForeignKey(Location, unique=False, on_delete=models.CASCADE)
	shelfmark = models.CharField(max_length=500, blank=True, null=True)
	census_id = models.CharField('{{ COPY_ID_PREFIX }}#', max_length=40, blank=True, null=True)
	verification = models.CharField(max_length=1, choices=VerificationChoices.choices, blank=False, default='U')
	fragment = models.BooleanField(default=False)
	from_estc = models.BooleanField('From ESTC', default=False)
	digital_facsimile_url = models.URLField('Digital Facsimile URL', max_length=500, blank=True, null=True)
	binding = models.TextField(blank=True, null=True)
	in_early_sammelband = models.BooleanField(default=False)
	sammelband_notes = models.TextField(blank=True, null=True)
	marginalia = models.TextField(blank=True, null=True)
	local_notes = models.TextField(blank=True, null=True)
	provenance_names = models.ManyToManyField(
		ProvenanceName,
		through='ProvenanceOwnership',
		through_fields=('copy', 'owner')
		)
	provenance_notes = models.TextField(blank=True, null=True)
	height = models.FloatField('Height (cm)', blank=True, null=True)
	width = models.FloatField('Width (cm)', blank=True, null=True)
	bibliography = models.TextField(blank=True, null=True)
	nonpublic_notes = models.TextField(blank=True, null=True)
	created_by = models.CharField(max_length=500, blank=True, null=True)
	verified_by = models.CharField(max_length=500, blank=True, null=True)
	examined_by = models.CharField(max_length=500, blank=True, null=True)

	def __str__(self):
		return f"{self.issue} ({self.issue.year}), {{ COPY_ID_PREFIX }}# {self.census_id}"
 
	class Meta:
		verbose_name_plural = "Copies"


# --- Relationship model linking Provenance Names to Copies ---

class ProvenanceOwnership(models.Model):
	copy = models.ForeignKey(Copy, on_delete=models.CASCADE)
	owner = models.ForeignKey(ProvenanceName, on_delete=models.CASCADE)

	def __str__(self):
		return f'{self.owner.name} owned {self.copy}'
	class Meta:
		verbose_name_plural = "Provenance Records"
		verbose_name = "Provenance Record"


# --- Static Page model for text that gets edited through the Admin Interface ---

class StaticPageText(models.Model):
	content = models.TextField(blank=True, null=True)
	viewname = models.CharField(max_length=255, blank=True, null=True)

	def __str__(self):
		return self.viewname

	class Meta:
		verbose_name_plural = "Static Pages"
		verbose_name = "Static Page"
