from rest_framework import serializers


class ContactSubmissionSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    email = serializers.EmailField(max_length=255, required=False, allow_blank=True, default='')
    message = serializers.CharField()
    type = serializers.ChoiceField(choices=['contact', 'bug'], default='contact')
