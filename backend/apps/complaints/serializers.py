from rest_framework import serializers
from django.db import transaction
from .models import Complaint, ComplaintStatusHistory, ComplaintAttachment
from apps.institutions.models import Institution, ComplaintCategory, InstitutionDepartment
from apps.accounts.models import User

class ComplaintAttachmentSerializer(serializers.ModelSerializer):
    uploaded_by_name = serializers.CharField(source='uploaded_by.full_name', read_only=True)

    class Meta:
        model = ComplaintAttachment
        fields = [
            'id',
            'file',
            'file_name',
            'file_size',
            'mime_type',
            'uploaded_by',
            'uploaded_by_name',
            'created_at'
        ]
        read_only_fields = ['id', 'uploaded_by', 'created_at']


class ComplaintStatusHistorySerializer(serializers.ModelSerializer):
    changed_by_name = serializers.CharField(source='changed_by.full_name', read_only=True)

    class Meta:
        model = ComplaintStatusHistory
        fields = [
            'id',
            'previous_status',
            'new_status',
            'changed_by',
            'changed_by_name',
            'public_remark',
            'internal_note',
            'assignment_change',
            'timestamp'
        ]

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        # Strip internal notes for student users to maintain confidentiality
        request = self.context.get('request')
        if request and request.user.role == User.Role.STUDENT:
            ret.pop('internal_note', None)
        return ret


class ComplaintListSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    institution_name = serializers.CharField(source='institution.name', read_only=True)
    department_name = serializers.CharField(source='assigned_department.name', read_only=True)

    class Meta:
        model = Complaint
        fields = [
            'id',
            'complaint_id',
            'title',
            'institution',
            'institution_name',
            'category',
            'category_name',
            'department_name',
            'priority',
            'status',
            'source_type',
            'full_issue_location',
            'created_at',
            'submission_timestamp',
            'last_updated_at'
        ]


class ComplaintDetailSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.full_name', read_only=True)
    student_email = serializers.CharField(source='student.email', read_only=True)
    institution_name = serializers.CharField(source='institution.name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    assigned_department_name = serializers.CharField(source='assigned_department.name', read_only=True)
    assigned_admin_name = serializers.CharField(source='assigned_admin.full_name', read_only=True)
    status_history = ComplaintStatusHistorySerializer(many=True, read_only=True)
    attachments = ComplaintAttachmentSerializer(many=True, read_only=True)

    class Meta:
        model = Complaint
        fields = [
            'id',
            'complaint_id',
            'title',
            'institution',
            'institution_name',
            'student',
            'student_name',
            'student_email',
            'category',
            'category_name',
            'priority',
            'source_type',
            'campus',
            'building',
            'floor',
            'room_number',
            'full_issue_location',
            'original_description',
            'original_transcription',
            'final_submitted_application',
            'assigned_department',
            'assigned_department_name',
            'assigned_admin',
            'assigned_admin_name',
            'status',
            'submission_timestamp',
            'resolution_timestamp',
            'resolution_details',
            'due_date',
            'created_at',
            'last_updated_at',
            'status_history',
            'attachments'
        ]
        read_only_fields = [
            'id',
            'complaint_id',
            'institution',
            'student',
            'submission_timestamp',
            'resolution_timestamp',
            'created_at',
            'last_updated_at'
        ]


class ComplaintCreateSerializer(serializers.ModelSerializer):
    category_id = serializers.IntegerField(required=False, allow_null=True)
    category = serializers.CharField(required=False, allow_blank=True, write_only=True)
    submit_now = serializers.BooleanField(required=False, default=False)

    class Meta:
        model = Complaint
        fields = [
            'title',
            'original_description',
            'original_transcription',
            'final_submitted_application',
            'category_id',
            'category',
            'priority',
            'source_type',
            'campus',
            'building',
            'floor',
            'room_number',
            'full_issue_location',
            'submit_now'
        ]
        extra_kwargs = {
            'category': {'required': False}
        }

    @transaction.atomic
    def create(self, validated_data):
        submit_now = validated_data.pop('submit_now', False)
        category_id = validated_data.pop('category_id', None)
        category_name = validated_data.pop('category', None)

        request = self.context.get('request')
        student = request.user
        institution = getattr(student.student_profile, 'institution', None)

        category = None
        if category_id:
            category = ComplaintCategory.objects.filter(id=category_id, institution=institution).first()
        elif category_name:
            category = ComplaintCategory.objects.filter(
                institution=institution,
                name__iexact=category_name.strip()
            ).first()
            if not category:
                category = ComplaintCategory.objects.filter(
                    institution=institution,
                    name__icontains=category_name.strip()
                ).first()
            if not category and category_name.strip() and institution:
                category, _ = ComplaintCategory.objects.get_or_create(
                    institution=institution,
                    name=category_name.strip()
                )

        complaint = Complaint.objects.create(
            student=student,
            institution=institution,
            category=category,
            **validated_data
        )

        # If category has default department, pre-assign
        if category and category.default_department:
            complaint.assigned_department = category.default_department
            complaint.save(update_fields=['assigned_department'])

        if submit_now:
            from django.utils import timezone
            from apps.accounts.models import User
            complaint.status = Complaint.Status.SUBMITTED
            complaint.submission_timestamp = timezone.now()
            complaint.save()

            admins = User.objects.filter(
                role=User.Role.INSTITUTION_ADMIN,
                admin_profile__institution=complaint.institution,
                admin_profile__approval_status='APPROVED'
            )
            has_verified_admin = admins.exists()

            public_remark = (
                'Formal complaint submitted to institutional administration.'
                if has_verified_admin
                else 'Formal complaint lodged. Awaiting institutional administrator onboarding for review and resolution.'
            )

            ComplaintStatusHistory.objects.create(
                complaint=complaint,
                previous_status=Complaint.Status.DRAFT,
                new_status=Complaint.Status.SUBMITTED,
                changed_by=student,
                public_remark=public_remark
            )
        else:
            ComplaintStatusHistory.objects.create(
                complaint=complaint,
                previous_status='',
                new_status=Complaint.Status.DRAFT,
                changed_by=student,
                public_remark='Complaint draft created.'
            )

        return complaint
