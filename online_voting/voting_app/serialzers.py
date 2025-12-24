from rest_framework import serializers
from .models import Voter, Party, Vote


class VoterLookupSerializer(serializers.Serializer):
    voter_id = serializers.CharField()


class VoterDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Voter
        fields = ['voter_id', 'full_name', 'email', 'phone', 'has_voted']


class PartySerializer(serializers.ModelSerializer):
    class Meta:
        model = Party
        fields = ['id', 'name']


class VoteSerializer(serializers.Serializer):
    voter_id = serializers.CharField()
    party_id = serializers.IntegerField()

    def validate(self, data):
        from .models import Voter, Party
        
        # Validate voter
        try:
            voter = Voter.objects.get(voter_id=data['voter_id'])
        except Voter.DoesNotExist:
            raise serializers.ValidationError('Voter not found')

        # Check if voter has already voted
        if voter.has_voted:
            raise serializers.ValidationError('This voter has already cast a vote')

        # Validate party
        try:
            party = Party.objects.get(pk=data['party_id'])
        except Party.DoesNotExist:
            raise serializers.ValidationError('Party not found')

        # Attach objects for create()
        data['voter_obj'] = voter
        data['party_obj'] = party
        return data

    def create(self, validated_data):
        voter = validated_data['voter_obj']
        party = validated_data['party_obj']

        from django.db import transaction
        with transaction.atomic():
            # Update voter status
            voter.has_voted = True
            voter.save(update_fields=['has_voted'])

            # Create vote entry
            vote = Vote.objects.create(voter=voter, party=party)

        return vote


class ReceiptSerializer(serializers.ModelSerializer):
    voter = VoterDetailSerializer(read_only=True)
    party = PartySerializer(read_only=True)

    class Meta:
        model = Vote
        fields = ['receipt_id', 'voter', 'party', 'timestamp']
