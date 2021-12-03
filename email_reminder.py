# %%
import openreview
import datetime
from  openreview.journal import Journal

# %%
dev_client = openreview.api.OpenReviewClient(baseurl = 'https://devapi2.openreview.net', username = 'fabian@mail.com', password = '1234')

submissions = dev_client.get_notes(invitation='.TMLR/-/Author_Submission')

# %%
## Now we can check for each submission and each assigned reviewer if there is a review submitted by that reviewer or not

# ## We can get all the reviews and build a dictionary where the key is the signature(anonid)
# reviewers = dev_client.get_groups(regex='.TMLR/Paper.*/Reviewers')

# reviews_by_signature = { r.signatures[0]:r for r in dev_client.get_notes(invitation='.TMLR/Paper.*/-/Review')}
# ## Get the anon ids for all the submissions
# anon_reviewers = dev_client.get_groups(regex='.TMLR/Paper.*/Reviewer_')

# ## Get the paper reviewers group by id
# reviewers_groups = { g.id: g for g in dev_client.get_groups(regex='.TMLR/Paper.*/Reviewers')}

# ## for all the submssion, check all the assignment reviewer and try to find if they signed a review or not
# for s in submissions:
#     try:
#         assigned_reviewers = reviewers_groups[f'.TMLR/Paper{s.number}/Reviewers']
#     except KeyError:
#         continue
#     for m in assigned_reviewers.members:
#         for anon in anon_reviewers:
#             if anon.id.startswith(f'.TMLR/Paper{s.number}/Reviewer_') and anon.members[0] == m:
#                 review = reviews_by_signature.get(anon.id)
#                 print(s.id, m, anon.id, 'Yes' if review else 'No')
    
# # %%
# print(reviewers_groups.keys())
# # %%
# print([s.number for s in submissions])
# %%
invitations = dev_client.get_invitations(regex='.TMLR/Paper.*/-/Review$')
# %%
print(invitations[0].duedate)

# %%
type(invitations)
# %%
# %%
for i, inv in enumerate(invitations):
    if inv.duedate is not None:
        duedate = datetime.datetime.fromtimestamp(inv.duedate / 1000)
        
        if duedate < datetime.datetime.now():
            print(duedate, datetime.datetime.now())
            print("{} Late!".format(i), inv.id)
            print()
        else:
            print("Not late")
# %%
reviews = dev_client.get_notes(invitation='.TMLR/Paper19/-/Review')
# %%
# %%
invitations = dev_client.get_invitations(regex='.TMLR/Paper19/-/Review$')
# %%
