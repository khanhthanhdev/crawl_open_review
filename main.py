import openreview
import dotenv
import os
import pandas as pd
dotenv.load_dotenv()
# API V2
client = openreview.Client(
    baseurl='https://api.openreview.net',
    username=os.getenv("OPENREVIEW_USERNAME"),
    password=os.getenv("OPENREVIEW_PASSWORD")
)

invitation_id = 'ICLR.cc/2025/Conference/-/Submission'

# Fetch the first 10 submissions
submissions = client.get_notes(invitation=invitation_id, limit=10)

# Prepare a list to store paper and review data
papers_data = []

# Iterate over each submission
for submission in submissions:
    paper_info = {
        'Paper ID': submission.number,
        'Title': submission.content.get('title', {}).get('value', 'N/A'),
        'Authors': ', '.join(submission.content.get('authorids', {}).get('value', [])),
        'Abstract': submission.content.get('abstract', {}).get('value', 'N/A'),
    }
    
    # Fetch reviews for the current paper
    reviews = client.get_notes(invitation=f'ICLR.cc/2025/Conference/-/Paper{submission.number}/Official_Review')
    for review in reviews:
        paper_info.update({
            'Reviewer': review.signatures[0],
            'Rating': review.content.get('rating', 'N/A'),
            'Review': review.content.get('review', 'N/A'),
        })
        papers_data.append(paper_info.copy())  # Append a copy of the paper info with review

# Convert the list of dictionaries into a DataFrame
df = pd.DataFrame(papers_data)

# Export the DataFrame to a CSV file
df.to_csv('iclr2025_papers_reviews.csv', index=False)

print("Data extraction complete. CSV file saved as 'iclr2025_papers_reviews.csv'.")