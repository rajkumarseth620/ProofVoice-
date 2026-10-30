"""
Formal Application Generator Service.
Transforms student grievance data into formal academic applications
addressed to The Dean or configured authorities, adhering strictly to institutional standards.
"""

from django.utils import timezone
from apps.institutions.models import ComplaintRecipientConfiguration

class FormalApplicationGenerator:
    """
    Constructs formal complaint letters using verified student credentials
    and institution-configured recipient authorities.
    """

    @classmethod
    def resolve_recipient(cls, institution, category=None):
        """
        Determines the designated authority for the formal letter.
        Priority:
        1. Category-specific recipient configuration
        2. Institution-wide default recipient configuration
        3. Fallback to 'The Dean'
        """
        config = None
        if category:
            config = ComplaintRecipientConfiguration.objects.filter(
                institution=institution,
                category=category
            ).first()

        if not config:
            config = ComplaintRecipientConfiguration.objects.filter(
                institution=institution,
                category__isnull=True
            ).first()

        if config:
            designation = config.recipient_designation
            name = config.recipient_name
            address = config.recipient_address or f"{institution.name}\n{institution.official_address}"
        else:
            designation = "The Dean"
            name = ""
            address = f"Office of the Dean\n{institution.name}\n{institution.official_address}"

        return {
            'designation': designation,
            'name': name,
            'address': address
        }

    @classmethod
    def generate_letter(cls, student, institution, title, description, category=None, location_details=None):
        """
        Generates the formal letter text.
        Uses verified server-side profile data to prevent spoofing.
        """
        profile = getattr(student, 'student_profile', None)

        student_name = student.full_name or "Student"
        student_id = profile.student_id if profile and profile.student_id else "[Enrollment No. Pending]"
        department = profile.department if profile and profile.department else "[Department Pending]"
        course = profile.course if profile and profile.course else "[Course Pending]"
        semester = profile.semester if profile and profile.semester else "[Semester Pending]"
        phone = profile.phone if profile and profile.phone else "[Contact Number]"

        inst_name = institution.name if institution else "[Institution Name]"
        inst_address = institution.official_address if institution else ""

        recipient = cls.resolve_recipient(institution, category)

        # Date in Indian formal format
        current_date = timezone.now().strftime("%d %B %Y")

        # Location context block
        loc_str = ""
        if location_details:
            if isinstance(location_details, dict):
                loc_parts = [v for k, v in location_details.items() if v]
                loc_str = ", ".join(loc_parts)
            elif isinstance(location_details, str):
                loc_str = location_details.strip()

        location_clause = f" at {loc_str}" if loc_str else ""

        # Recipient address lines
        rec_lines = [recipient['designation']]
        if recipient['name']:
            rec_lines.append(recipient['name'])
        if recipient['address']:
            rec_lines.append(recipient['address'])
        else:
            rec_lines.append(inst_name)
            if inst_address:
                rec_lines.append(inst_address)
        recipient_block = "\n".join(rec_lines)

        letter = f"""Date: {current_date}

To,
{recipient_block}

Subject: Formal Grievance Regarding {title.strip()}

Respected Sir/Madam,

I, {student_name}, a bonafide student of {inst_name}, Department of {department}, enrolled in {course} (Roll/Enrollment No: {student_id}, Semester: {semester}), would like to formally bring the following matter to your esteemed attention.

{description.strip()}

This grievance occurred/is situated{location_clause}. The prevailing situation is causing disruption to daily campus activities and student well-being. Despite informal notifications, the problem remains unresolved and necessitates institutional intervention.

Therefore, I earnestly request your office to inspect the matter and instruct the concerned department to initiate corrective measures at the earliest convenience.

Thanking you.

Yours faithfully,
{student_name}
Enrollment No: {student_id}
Department of {department}
{course}, {semester}
Contact: {phone}
{inst_name}"""

        return {
            'application_text': letter,
            'recipient': recipient,
            'date': current_date,
            'student_details': {
                'name': student_name,
                'student_id': student_id,
                'department': department,
                'course': course,
                'semester': semester,
                'phone': phone
            }
        }
