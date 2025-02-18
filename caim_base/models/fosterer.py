from typing import List, Optional, Union

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import ArrayField
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField
from caim_base.notifications import notify_new_fosterer_application
from ..utils import full_url

from caim_base.models.animals import Animal

from ..states import states

User = get_user_model()


class ChoiceArrayField(ArrayField):
    """
    A field that allows us to store an array of choices.
    Uses Django's Postgres ArrayField
    and a MultipleChoiceField with checkboxes for its formfield.
    """

    def formfield(self, **kwargs):
        defaults = {
            "widget": forms.CheckboxSelectMultiple,
            "form_class": forms.MultipleChoiceField,
            "choices": self.base_field.choices,
        }
        defaults.update(kwargs)
        # Skip our parent's formfield implementation completely as we don't
        # care for it.
        # pylint:disable=bad-super-call
        return super(ArrayField, self).formfield(**defaults)


class TypeOfAnimals(models.TextChoices):
    DOGS = "DOGS", "Dogs"
    CATS = "CATS", "Cats"


class YesNo(models.TextChoices):
    YES = "YES", "Yes"
    NO = "NO", "No"


class FostererExistingPetDetail(models.Model):
    name = models.CharField(max_length=64, blank=True, null=True)
    type_of_animal = models.CharField(max_length=64, blank=True, null=True)
    breed = models.CharField(max_length=64, blank=True, null=True)
    sex = models.CharField(
        max_length=6,
        choices=(("Male", "Male"), ("Female", "Female")),
        blank=True,
        null=True,
    )
    age = models.PositiveIntegerField(blank=True, null=True)
    weight_lbs = models.PositiveIntegerField(blank=True, null=True)
    spayed_neutered = models.CharField(
        choices=YesNo.choices,
        max_length=32,
        blank=True,
        null=True,
        verbose_name="Spayed or Neutered?",
    )
    up_to_date_shots = models.CharField(
        choices=YesNo.choices,
        max_length=32,
        blank=True,
        null=True,
        verbose_name="Up to date on their shots?",
    )
    quirks = models.TextField(
        max_length=1024, blank=True, null=True, verbose_name="Any quirks?"
    )

    fosterer_profile = models.ForeignKey(
        "FostererProfile", on_delete=models.CASCADE, related_name="existing_pets"
    )

    def __str__(self) -> str:
        return f"{self.fosterer_profile} - {self.name}"


class FostererReferenceDetail(models.Model):
    fosterer_profile = models.ForeignKey(
        "FostererProfile", on_delete=models.CASCADE, related_name="references"
    )
    first_name = models.CharField(max_length=64)
    last_name = models.CharField(max_length=64)
    email = models.EmailField(max_length=255)
    phone = PhoneNumberField(null=True, default=None)
    relation = models.CharField(max_length=128)

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name}"


class FostererPersonInHomeDetail(models.Model):
    fosterer_profile = models.ForeignKey(
        "FostererProfile", on_delete=models.CASCADE, related_name="people_in_home"
    )
    name = models.CharField(max_length=128, blank=True, null=True, default=None)
    relation = models.CharField(max_length=128, blank=True, null=True, default=None)
    age = models.IntegerField(blank=True, null=True, default=None)
    email = models.EmailField(max_length=255, blank=True, null=True, default=None)

    def __str__(self) -> str:
        return f"{self.name}"


# NOTE model not currently in use.
class FostererLandlordContact(models.Model):
    fosterer_profile = models.OneToOneField(
        "FostererProfile", on_delete=models.CASCADE, related_name="landlord_contact"
    )
    first_name = models.CharField(max_length=64)
    last_name = models.CharField(max_length=128)
    email = models.EmailField(max_length=255, blank=True, null=True)
    phone = PhoneNumberField(blank=True, null=True, default=None)

    def __str__(self) -> str:
        return f"{self.firstname} {self.lastname}"


class FostererProfile(models.Model):
    class CategoryOfAnimals(models.TextChoices):
        ADULT_FEMALE = "ADULT_FEMALE", "Adult female"
        ADULT_MALE = "ADULT_MALE", "Adult male"
        PREGNANT_MOTHER = "PREGNANT_MOTHER", "Pregnant mom"
        MOTHER_WITH_BABIES = "MOTHER_WITH_BABIES", "Mom with nursing babies"
        BABIES = "BABIES", "Puppies / kittens"
        PIT_BULLY_BREEDS = "PIT_BULLY_BREEDS", "Pit and/or Bully breeds"
        SHEPARD_OR_MALINOIS = (
            "SHEPARD_OR_MALINOIS",
            "German Shepherd and/or Malinois breeds",
        )

    class DogSize(models.TextChoices):
        SMALL = "SMALL", "Small (5 – 20 lbs)"
        MEDIUM = "MEDIUM", "Medium (21 – 50 lbs)"
        LARGE = "LARGE", "Large (50+ lbs)"

    class BehaviouralAttributes(models.TextChoices):
        GOOD_WITH_DOGS = "GOOD_WITH_DOGS", "Good with dogs"
        GOOD_WITH_CATS = "GOOD_WITH_CATS", "Good with cats"
        GOOD_WITH_KIDS = "GOOD_WITH_KIDS", "Good with children"

    class BehaviouralIssueChoices(models.TextChoices):
        YES = "YES", "Yes"
        MINOR = (
            "MINOR",
            "Not severe behavioral issues, but open to minor behavioral challenges.",
        )
        NO = "NO", "No"

    class Timeframe(models.TextChoices):
        MAX_2_WEEKS = "MAX_2_WEEKS", "Up to 2 weeks"
        MAX_3_MONTHS = "MAX_3_MONTHS", "Up to 3 months"
        ANY_DURATION = "ANY_DURATION", "Any duration"
        # OTHER = "OTHER", "Other (please specify)"

    class ExperienceCategories(models.TextChoices):
        HOUSE_POTTY = "HOUSE_POTTY", "House / potty training"
        CRATE = "CRATE", "Crate training"
        LEASH_WALKING = "LEASH_WALKING", "Challenges with leash / walking"
        JUMPING = "JUMPING", "Jumping"
        HIGH_ENERGY = "HIGH_ENERGY", "High energy"
        OBEDIENCE = "OBEDIENCE", "Basic obedience"
        PUPPIES = "PUPPIES", "Training puppies"
        SEPARATION_ANXIETY = "SEPARATION_ANXIETY", "Separation anxiety"
        FEARS = "FEARS", "Fears / phobias"
        REACTIVITY = "REACTIVITY", "Reactivity"
        FOOD_GUARDING = "FOOD_GUARDING", "Food guarding"
        MEDICAL_ISSUES = "MEDICAL_ISSUES", "Medical issues"
        GERIATRIC = "GERIATRIC", "Geriatric concerns"
        NONE_OF_ABOVE = "NONE_OF_ABOVE", "None of the above"

    class YardTypes(models.TextChoices):
        NO_YARD = "NO_YARD", "No yard"
        UNFENCED = "UNFENCED", "Unfenced yard"
        PARTIALLY_FENCED = "PARTIALLY_FENCED", "Partially fenced yard"
        FULLY_FENCED = "FULLY_FENCED", "Fully fenced yard"

    class RentOwn(models.TextChoices):
        RENT = "RENT", "Rent"
        OWN = "OWN", "Own"

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    firstname = models.CharField(blank=True, null=True, max_length=64, default=None)
    lastname = models.CharField(blank=True, null=True, max_length=64, default=None)
    age = models.IntegerField(blank=True, null=True, default=None)
    email = models.EmailField(blank=True, null=True, max_length=255, default=None)
    phone = PhoneNumberField(blank=True, null=True, default=None)
    street_address = models.CharField(
        blank=True, null=True, max_length=244, default=None
    )
    city = models.CharField(max_length=32, blank=True, null=True, default=None)
    state = models.CharField(
        max_length=2, blank=True, null=True, choices=states.items(), default=None
    )
    zip_code = models.CharField(max_length=16, blank=True, null=True, default=None)
    type_of_animals = ChoiceArrayField(
        models.CharField(max_length=32, choices=TypeOfAnimals.choices),
        blank=True,
        null=True,
        default=None,
        verbose_name="Which type of animal(s) are you wanting to foster?",
    )
    category_of_animals = ChoiceArrayField(
        models.CharField(max_length=32, choices=CategoryOfAnimals.choices),
        blank=True,
        null=True,
        default=None,
        verbose_name="Please check any / all that you're interested in fostering.",
    )
    dog_size = ChoiceArrayField(
        models.CharField(max_length=32, choices=DogSize.choices),
        blank=True,
        null=True,
        default=None,
        verbose_name=(
            "If you’re interested in fostering dogs,"
            " do you have a preference about size?"
        ),
    )
    behavioural_attributes = ChoiceArrayField(
        models.CharField(max_length=32, choices=BehaviouralAttributes.choices),
        blank=True,
        null=True,
        default=None,
        verbose_name=(
            "Please check any of the requirements you have for a foster animal."
        ),
    )
    medical_issues = models.CharField(
        choices=YesNo.choices,
        max_length=32,
        blank=False,
        null=True,
        default=None,
        verbose_name="Would you be willing to foster an animal with medical issues?",
    )
    special_needs = models.CharField(
        choices=YesNo.choices,
        max_length=32,
        blank=False,
        null=True,
        default=None,
        verbose_name="Would you be willing to foster an animal with special needs?",
    )
    behavioral_issues = models.CharField(
        choices=BehaviouralIssueChoices.choices,
        max_length=32,
        blank=False,
        null=True,
        default=None,
        verbose_name="Would you be willing to foster an animal with behavioral issues?",
    )
    timeframe = models.CharField(
        choices=Timeframe.choices,
        max_length=32,
        blank=False,
        null=True,
        default=None,
        verbose_name="How long are you able to foster an animal for?",
    )
    num_existing_pets = models.IntegerField(
        blank=True,
        null=True,
        default=None,
        verbose_name="How many pets do you currently have in your home?",
    )
    experience_given_up_pet = models.TextField(
        blank=True,
        null=True,
        default=None,
        verbose_name=(
            "Have you ever given a pet up? If so, please describe the situation."
        ),
    )
    experience_description = models.TextField(
        blank=True,
        null=True,
        default=None,
        verbose_name=(
            "Please describe your experience with animals"
            " (personal pets, training, interactions, etc.)"
        ),
    )
    experience_categories = ChoiceArrayField(
        models.CharField(max_length=32, choices=ExperienceCategories.choices),
        blank=True,
        null=True,
        default=None,
        verbose_name=(
            "Have you had experience with any of the following"
            " in animals you’ve owned or fostered?"
        ),
    )
    # These references are not used and simply to preserve existing data.
    # going forward associated `ReferenceDetail` holds this information.
    reference_1 = models.TextField(
        blank=True, null=True, default=None, verbose_name="Reference #1"
    )
    reference_2 = models.TextField(
        blank=True, null=True, default=None, verbose_name="Reference #2"
    )
    reference_3 = models.TextField(
        blank=True, null=True, default=None, verbose_name="Reference #3"
    )
    # This is old "people at home" and is simply to preserve existing data.
    # Unused in the future this info should come from associated `PersonInHomeDetail`.
    people_at_home = models.TextField(
        blank=True,
        null=True,
        default=None,
        verbose_name=(
            "Please list how many people live in your home and their ages (legacy)"
        ),
    )
    num_people_in_home = models.IntegerField(
        blank=True,
        null=True,
        default=None,
        verbose_name="How many people live in your home, including yourself?",
    )
    # TODO use Personinhomedetail
    people_in_home_detail = models.TextField(
        blank=True,
        null=True,
        default=None,
        verbose_name=(
            "Please list the following details for each person in your home,"
            " excluding yourself: Name, Relation, Age, Email address."
        ),
    )
    all_in_agreement = models.CharField(
        choices=YesNo.choices,
        max_length=32,
        blank=False,
        null=True,
        default=None,
        verbose_name="Are all members of your household in agreement about fostering?",
    )
    pet_allergies = models.CharField(
        choices=YesNo.choices,
        max_length=32,
        blank=False,
        null=True,
        default=None,
        verbose_name="Does anyone in your home have pet allergies?",
    )
    stairs = models.CharField(
        choices=YesNo.choices,
        max_length=32,
        blank=False,
        null=True,
        default=None,
        verbose_name="Do you have stairs that a dog would have to walk daily?",
    )
    yard_type = models.CharField(
        choices=YardTypes.choices,
        max_length=32,
        blank=False,
        null=True,
        default=None,
        verbose_name="Describe your yard",
    )
    yard_fence_over_5ft = models.CharField(
        choices=YesNo.choices,
        max_length=32,
        blank=False,
        null=True,
        default=None,
        verbose_name="If your yard is fully fenced, is it all over 5 feet tall?",
    )
    rent_own = models.CharField(
        choices=RentOwn.choices,
        max_length=32,
        blank=False,
        null=True,
        default=None,
        verbose_name="Do you rent or own?",
    )
    rent_restrictions = models.TextField(
        blank=True,
        null=True,
        default=None,
        verbose_name=(
            "If you rent, please describe any pet restrictions that are in place."
        ),
    )
    landlord_contact_text = models.CharField(
        blank=True,
        null=True,
        max_length=128,
        default=None,
        verbose_name=(
            "If you rent, please provide your landlord’s"
            " contact information (email and/or phone)."
            " We will contact them to confirm that you have approval to foster."
        ),
    )
    hours_alone_description = models.TextField(
        blank=True,
        null=True,
        default=None,
        verbose_name="How many hours per day will your foster animal be left alone?",
    )
    hours_alone_location = models.TextField(
        blank=True,
        null=True,
        default=None,
        verbose_name="Where will your foster animal be kept when you're not home?",
    )
    sleep_location = models.TextField(
        blank=True,
        null=True,
        default=None,
        verbose_name="Where will your foster animal sleep?",
    )
    other_info = models.TextField(
        blank=True,
        null=True,
        default=None,
        verbose_name="Is there anything else you want us / rescues to know?",
    )
    ever_been_convicted_abuse = models.CharField(
        choices=YesNo.choices,
        max_length=32,
        blank=False,
        null=True,
        default=None,
        verbose_name=(
            "Have you or a family / household member ever been convicted"
            " of an animal related crime (animal abuse, neglect, abandonment, etc.)?"
        ),
    )
    agree_share_details = models.CharField(
        choices=YesNo.choices,
        max_length=32,
        blank=False,
        null=True,
        default=None,
        verbose_name=(
            "Do you agree that we can share the details you've provided with rescues?"
        ),
    )
    agree_social_media = models.CharField(
        choices=YesNo.choices,
        max_length=32,
        blank=False,
        null=True,
        default=None,
        verbose_name=(
            "Do you agree to help promote your foster animal on social media"
            " and/or by attending adoption events and public outings?"
        ),
    )
    is_complete = models.BooleanField(default=False)

    def __str__(self) -> str:
        return f"{self.firstname} {self.lastname}"


def __str__(self) -> str:
    return f"{self.firstname} {self.lastname}"


def query_fostererprofiles(
    behavioural_attributes: Optional[List[str]] = None,
    is_complete=True,
    sort: Optional[Union[str, List[str]]] = None,
) -> models.QuerySet:
    """
    Query fosterer profiles with preferred defaults
    """

    if sort is None:
        sort = ["firstname", "lastname"]
    query = FostererProfile.objects.all()

    if behavioural_attributes:
        query = query.filter(behavioural_attributes__contains=behavioural_attributes)

    if is_complete:
        query = query.filter(is_complete=True)

    if sort is not None:
        if isinstance(sort, list):
            for s in sort:
                query = query.order_by(s)
        else:
            query = query.order_by(sort)

    return query


class FosterApplication(models.Model):
    class Statuses(models.TextChoices):
        ACCEPTED = "ACCEPTED", "Accepted"
        REJECTED = "REJECTED", "Rejected"
        PENDING = "PENDING", "Pending"

    class RejectionReasons(models.TextChoices):
        UNSUITABLE = (
            "UNSUITABLE",
            (
                "Not suitable for the animal requested,"
                " and not willing to consider alternative"
            ),
        )
        UNRELIABLE = "UNRELIABLE", "Concerns about fosterer reliability/commitment"
        PROPERTY = "PROPERTY", "Concerns with home and/or yard situation"
        HUMAN_ROOMMATES = "HUMAN_ROOMMATES", "Concerns with the people in the home"
        PET_ROOMMATES = "PET_ROOMMATES", "Concerns with the other pets in the home"
        NO_LANDLORD_APPROVAL = (
            "NO_LANDLORD_APPROVAL",
            "Landlord has not approved fostering",
        )
        LIED = "LIED", "Lied on Application"
        OTHER = "OTHER", "Other"

    fosterer = models.ForeignKey(
        FostererProfile, on_delete=models.CASCADE, related_name="applications"
    )
    animal = models.ForeignKey(
        Animal, on_delete=models.CASCADE, related_name="applications"
    )
    status = models.CharField(max_length=32, choices=Statuses.choices)
    reject_reason = models.CharField(
        max_length=32, choices=RejectionReasons.choices, null=True
    )
    reject_reason_detail = models.TextField(max_length=65516, null=True, blank=True)
    submitted_on = models.DateField(auto_now_add=True)
    updated_on = models.DateField(auto_now=True)

    def __str__(self) -> str:
        return f"Application for {self.animal} by {self.fosterer}"

    def save(self, *args, **kwargs):
        if not self.id:  # the first save
            notify_new_fosterer_application(self)
        super().save()

    def get_absolute_url(self):
        return full_url(f"/foster/application?animal_id={self.animal.id}")


class FosterApplicationAnimalSuggestion(models.Model):
    application = models.ForeignKey(
        FosterApplication,
        on_delete=models.CASCADE,
        related_name="alternative_suggested_animals",
    )
    animal = models.ForeignKey(Animal, on_delete=models.CASCADE)
    submitted_on = models.DateField(auto_now_add=True)
    updated_on = models.DateField(auto_now=True)

    def __str__(self) -> str:
        return f"Suggestion of {self.animal} for {self.fosterer}"
