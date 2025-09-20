from lead.models import Lead, LeadEvent, LeadFollowup, LeadFollowupRule
from rest_framework import serializers


class LeadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lead
        fields = ('id', 'phone', 'status', 'updated_at')


class LeadFollowupRuleSerializer(serializers.ModelSerializer):

    class Meta:
        model = LeadFollowupRule
        fields = ('text', 'status', 'delay', 'is_enabled')


class LeadFollowupSerializer(serializers.ModelSerializer):
    rule = LeadFollowupRuleSerializer(read_only=True)

    class Meta:
        model = LeadFollowup
        fields = ('lead', 'rule', 'created_at')


class LeadEventSerializer(serializers.ModelSerializer):
    lead = LeadSerializer(read_only=True)

    class Meta:
        model = LeadEvent
        fields = ('lead', 'status', 'created_at')
