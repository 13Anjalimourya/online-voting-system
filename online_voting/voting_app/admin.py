from django.contrib import admin
from .models import Voter, Party, Vote, Election
from django.db.models import Count

# -------------------------
# Voter Admin
# -------------------------
@admin.register(Voter)
class VoterAdmin(admin.ModelAdmin):
    list_display = ('voter_id', 'full_name', 'email', 'has_voted')
    search_fields = ('voter_id', 'full_name')
    list_filter = ('has_voted',)
    change_list_template = "admin/vote_chart.html"

    # 🔒 Hide system-managed fields
    exclude = ('otp', 'otp_time', 'device_id')


# -------------------------
# Party Admin
# -------------------------
@admin.register(Party)
class PartyAdmin(admin.ModelAdmin):
    list_display = ('name',)
    


# -------------------------
# Election Admin
# -------------------------
@admin.register(Election)
class ElectionAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_time', 'end_time', 'is_active')
    list_filter = ('is_active',)


# -------------------------
# Vote Admin
# -------------------------
@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = ('voter', 'party', 'time')
    readonly_fields = ('voter', 'party', 'time')
   
    # ❌ Prevent admin from adding votes manually
    def has_add_permission(self, request):
        return False
