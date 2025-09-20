from django.urls import path
from lead.views import (LeadEventListView, LeadFollowupListView,
                        LeadFollowupRuleListView, LeadListView)

app_name = 'lead'

urlpatterns = [
    path('leads_events/', LeadEventListView.as_view(), name='lead-event-list'),
    path('leads_followups/', LeadFollowupListView.as_view(), name='lead-followup-list'),
    path('leads_followup_rules/', LeadFollowupRuleListView.as_view(), name='lead-followup-rule-list'),
    path('leads/', LeadListView.as_view(), name='lead-list')
]
