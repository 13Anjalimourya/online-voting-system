from voting_app.models import Voter

def voter_context(request):
    voter_id = request.session.get('voter_id')
    voter = None

    if voter_id:
        try:
            voter = Voter.objects.get(voter_id=voter_id)
        except Voter.DoesNotExist:
            pass

    return {
        'logged_voter': voter
    }
