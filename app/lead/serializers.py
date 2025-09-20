from lead.models import (Lead, LeadEvent, LeadFollowup, LeadFollowupRule,
                         LeadStatus)
from rest_framework import serializers, status


def validate_lead(value):
    try:
        Lead.objects.get(id=value)
    except Lead.DoesNotExist:
        raise serializers.ValidationError('Lead not found', code=status.HTTP_400_BAD_REQUEST)
    return value


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


class NewLeadStatusValidator(serializers.Serializer):
    '''
    Validation of arguments for Lead's status updating
    '''
    lead_id = serializers.IntegerField(validators=[validate_lead])
    status = serializers.ChoiceField(choices=LeadStatus.choices)
