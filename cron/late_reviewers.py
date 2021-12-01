import openreview
import datetime
from  openreview.journal import Journal


dev_client = openreview.api.OpenReviewClient(baseurl = 'https://devapi2.openreview.net', username = 'fabian@mail.com', password = '1234')


reviews = dev_client.get_notes(invitation='.TMLR/Paper.*/-/Review')
## Send reminders to late reviewers

## Find all the submission that are under review
submissions = dev_client.get_notes(invitation='.TMLR/-/Author_Submission', content={'venueid': '.TMLR/Under_Review'})

for submission in submissions:
    
    ## get the review invitation and check if the duedate is in the past
    review_invitation = dev_client.get_invitation(id=f'.TMLR/Paper{submission.number}/-/Review')
    
    print(review_invitation.duedate, datetime.datetime.fromtimestamp(review_invitation.duedate/1000))
    if review_invitation.duedate < openreview.tools.datetime_millis(datetime.datetime.utcnow()):
        print(f'due date reached for {review_invitation.id}')
        
        ## get the reviewers assigned to this submission
        reviewers_group = dev_client.get_group(id=f'.TMLR/Paper{submission.number}/Reviewers')
        print(f'Found reviewers: {reviewers_group.members}')

        
        ## get the submitted reviews
        reviews = dev_client.get_notes(invitation=review_invitation.id)
        print(f'Found reviews: {len(reviews)}')
        
        review_by_signature = { r.signatures[0]:r for r in reviews }
        
        ## find unsubmitted reviews
        for reviewer in reviewers_group.members:
            
            ## get anon id
            anon_reviewer_groups = dev_client.get_groups(regex=f'.TMLR/Paper{submission.number}/Reviewer_', member=reviewer)
            
            assert len(anon_reviewer_groups) == 1
            
            if anon_reviewer_groups:
                anon_reviewer_group = anon_reviewer_groups[0]
                
                ## find review
                review = review_by_signature.get(anon_reviewer_group.id)
                
                if not review:
                    print(f'Remind reviewer {reviewer} to submit the review for paper {submission.number}')
                    # message=dev_client.post_message(recipients=[reviewer],
                    #    subject='[TMLR] Please submit your review',
                    #    message=f'Hi {{fullname}}, please submit your review for submission {submission.number}, thanks TMLR.',
                    #    replyTo='tmlr@jmlr.org')