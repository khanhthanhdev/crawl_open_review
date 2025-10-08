# Install: pip install openreview-py pandas

import openreview
import pandas as pd
import json
import time
from typing import List, Dict
import os
import dotenv
dotenv.load_dotenv()


def get_openreview_client():
    """
    Attempts to create an OpenReview client using API v2, falling back to API v1 if v2 fails.

    This function tries to initialize an OpenReview client with the v2 API endpoint. If that raises an exception,
    it falls back to the v1 API. It uses environment variables OPENREVIEW_USERNAME and OPENREVIEW_PASSWORD for authentication.

    Returns:
        tuple: A tuple containing the OpenReview client object and a string indicating the API version ('v2' or 'v1').
    """
    # Try API v2 first, fall back to v1
    try:
        client = openreview.api.OpenReviewClient(baseurl='https://api2.openreview.net',
                                                 username=os.getenv("OPENREVIEW_USERNAME"),
    password=os.getenv("OPENREVIEW_PASSWORD"))
        print("Using OpenReview API v2")
        return client, 'v2'
    except:
        client = openreview.Client(
    baseurl='https://api.openreview.net',
    username=os.getenv("OPENREVIEW_USERNAME"),
    password=os.getenv("OPENREVIEW_PASSWORD")
)
        print("Using OpenReview API v1")
        return client, 'v1'


def is_accepted_paper(decision):
    """
    Determine if a paper is accepted based on its decision
    
    Args:
        decision: The decision string from the meta review
        
    Returns:
        bool: True if the paper is accepted
    """
    if not decision:
        return False
    
    decision_lower = str(decision).lower()
    
    # Common acceptance indicators for ICLR
    accepted_keywords = [
        'accept', 'oral', 'poster', 'spotlight', 'notable', 'top', 'best'
    ]
    
    # Reject indicators to be sure
    rejected_keywords = [
        'reject', 'desk reject', 'withdraw'
    ]
    
    # Check for rejection first
    for reject_word in rejected_keywords:
        if reject_word in decision_lower:
            return False
    
    # Check for acceptance
    for accept_word in accepted_keywords:
        if accept_word in decision_lower:
            return True
    
    return False


def crawl_iclr_papers_and_reviews(year: int, accepted_only: bool = False):
    """
    Crawl papers and reviews from ICLR conference
    
    Args:
        year: Conference year (e.g., 2024, 2023, 2022)
        accepted_only: If True, only return accepted papers
    """
    client, api_version = get_openreview_client()
    
    # Try different invitation patterns
    patterns = [
        f'ICLR.cc/{year}/Conference/-/Submission',
        f'ICLR.cc/{year}/Conference/-/Blind_Submission',
    ]
    
    submissions = []
    used_pattern = None
    
    for pattern in patterns:
        print(f"\nTrying pattern: {pattern}")
        try:
            if api_version == 'v2':
                submissions = list(client.get_all_notes(invitation=pattern))
            else:
                submissions = client.get_all_notes(invitation=pattern)
            
            if submissions and len(submissions) > 0:
                used_pattern = pattern
                print(f"✓ Found {len(submissions)} papers with pattern: {pattern}")
                break
            else:
                print(f"  No papers found with this pattern")
        except Exception as e:
            print(f"  Error: {e}")
    
    if not submissions or len(submissions) == 0:
        print("\nCould not find papers. Possible reasons:")
        print(f"  1. ICLR {year} papers may not be published yet on OpenReview")
        print(f"  2. The venue uses a different invitation format")
        print(f"\nTry visiting: https://openreview.net/group?id=ICLR.cc/{year}/Conference")
        print(f"Or try a different year like {year-1} or {year-2}")
        return []
    
    print(f"\nProcessing {len(submissions)} papers from {used_pattern}\n")
    
    all_data = []
    
    for i, paper in enumerate(submissions, 1):
        title = paper.content.get('title', {})
        if isinstance(title, dict):
            title = title.get('value', 'No title')
        
        print(f"[{i}/{len(submissions)}] {str(title)[:60]}...")
        
        # Extract paper information (handle both v1 and v2 formats)
        def get_value(content_dict, key):
            val = content_dict.get(key, '')
            if isinstance(val, dict):
                return val.get('value', '')
            return val
        
        paper_data = {
            'paper_id': paper.id,
            'forum_id': paper.forum if hasattr(paper, 'forum') else paper.id,
            'title': str(title),
            'abstract': get_value(paper.content, 'abstract'),
            'authors': get_value(paper.content, 'authors'),
            'keywords': get_value(paper.content, 'keywords'),
            'pdf_url': f"https://openreview.net/pdf?id={paper.forum if hasattr(paper, 'forum') else paper.id}",
            'forum_url': f"https://openreview.net/forum?id={paper.forum if hasattr(paper, 'forum') else paper.id}",
        }
        
        # Get all notes for this paper (reviews, comments, etc.)
        forum_id = paper.forum if hasattr(paper, 'forum') else paper.id
        
        try:
            if api_version == 'v2':
                notes = list(client.get_all_notes(forum=forum_id))
            else:
                notes = client.get_all_notes(forum=forum_id)
            
            reviews = []
            comments = []
            meta_reviews = []
            decision = None
            
            for note in notes:
                # Skip the submission itself
                if note.id == paper.id:
                    continue
                
                invitation = note.invitation if hasattr(note, 'invitation') else ''
                invitation_lower = str(invitation).lower()
                
                # DEBUG: Print invitation patterns we're seeing
                if i <= 3:  # Only for first few papers to avoid spam
                    print(f"    DEBUG: Note content keys: {list(note.content.keys())[:5]}")  # First 5 keys
                
                # Extract content
                def extract_content(note):
                    content = {}
                    for key, val in note.content.items():
                        if isinstance(val, dict) and 'value' in val:
                            content[key] = val['value']
                        else:
                            content[key] = val
                    return content
                
                note_content = extract_content(note)
                
                # Categorize the note based on content rather than invitation
                # Check if this looks like a review
                if any(key in note_content for key in ['rating', 'confidence', 'review', 'recommendation']):
                    review_data = {
                        'review_id': note.id,
                        'invitation': invitation,
                        'rating': note_content.get('rating', note_content.get('recommendation', '')),
                        'confidence': note_content.get('confidence', ''),
                        'summary': note_content.get('summary', ''),
                        'soundness': note_content.get('soundness', ''),
                        'presentation': note_content.get('presentation', ''),
                        'contribution': note_content.get('contribution', ''),
                        'strengths': note_content.get('strengths', ''),
                        'weaknesses': note_content.get('weaknesses', ''),
                        'questions': note_content.get('questions', ''),
                        'limitations': note_content.get('limitations', ''),
                        'review_text': note_content.get('review', ''),
                    }
                    reviews.append(review_data)
                    
                # Check if this looks like a decision/meta-review
                elif any(key in note_content for key in ['decision', 'recommendation']) and 'rating' not in note_content:
                    decision = note_content.get('decision', note_content.get('recommendation', ''))
                    meta_reviews.append({
                        'id': note.id,
                        'decision': decision,
                        'content': note_content
                    })
                    
                # Check if this looks like a comment
                elif any(key in note_content for key in ['comment', 'rebuttal']):
                    comments.append({
                        'note_id': note.id,
                        'invitation': invitation,
                        'comment': note_content.get('comment', note_content.get('rebuttal', '')),
                        'content': note_content
                    })
            
            paper_data['reviews'] = reviews
            paper_data['num_reviews'] = len(reviews)
            paper_data['meta_reviews'] = meta_reviews
            paper_data['decision'] = decision
            paper_data['comments'] = comments
            
            print(f"  → {len(reviews)} reviews, {len(comments)} comments, decision: {decision}")
            
        except Exception as e:
            print(f"  ⚠ Error fetching notes: {e}")
            paper_data['reviews'] = []
            paper_data['num_reviews'] = 0
            paper_data['meta_reviews'] = []
            paper_data['decision'] = None
            paper_data['comments'] = []
        
        # Filter for accepted papers if requested
        if accepted_only:
            if is_accepted_paper(paper_data.get('decision')):
                all_data.append(paper_data)
                print(f"  ✓ Accepted paper included")
            else:
                print(f"  ✗ Rejected/withdrawn paper skipped")
        else:
            all_data.append(paper_data)
        
        # Rate limiting
        time.sleep(0.3)
        
        # Optional: Limit for testing (remove this for full crawl)
        # if i >= 5:
        #     print("\n⚠ Stopping at 5 papers for testing. Remove limit for full crawl.")
        #     break
    
    return all_data


def save_data(data: List[Dict], year: int, accepted_only: bool = False):
    """Save crawled data to JSON and CSV files"""
    
    if not data:
        print("No data to save!")
        return None
    
    # Determine filename suffix
    suffix = "_accepted" if accepted_only else ""
    
    # Save complete data as JSON
    json_filename = f'iclr_{year}_papers_reviews{suffix}.json'
    with open(json_filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"\n✓ Saved complete data to {json_filename}")
    
    # Create a flattened version for CSV
    csv_data = []
    for paper in data:
        # Calculate average rating if reviews exist
        ratings = []
        for review in paper.get('reviews', []):
            rating_str = str(review.get('rating', ''))
            if rating_str:
                # Extract number from rating (various formats)
                try:
                    # Handle formats like "6: Weak Accept", "6", "6.0", etc.
                    rating_clean = rating_str.split(':')[0].strip()
                    rating_num = float(rating_clean)
                    ratings.append(rating_num)
                except:
                    pass
        
        avg_rating = round(sum(ratings) / len(ratings), 2) if ratings else None
        
        authors = paper.get('authors', [])
        if isinstance(authors, list):
            authors_str = ', '.join([str(a) for a in authors])
        else:
            authors_str = str(authors)
        
        keywords = paper.get('keywords', [])
        if isinstance(keywords, list):
            keywords_str = ', '.join([str(k) for k in keywords])
        else:
            keywords_str = str(keywords)
        
        csv_data.append({
            'paper_id': paper['paper_id'],
            'title': paper['title'],
            'authors': authors_str,
            'num_reviews': paper['num_reviews'],
            'avg_rating': avg_rating,
            'decision': paper.get('decision', ''),
            'keywords': keywords_str,
            'forum_url': paper['forum_url']
        })
    
    # Save as CSV
    df = pd.DataFrame(csv_data)
    csv_filename = f'iclr_{year}_papers_summary{suffix}.csv'
    df.to_csv(csv_filename, index=False, encoding='utf-8')
    print(f"✓ Saved summary to {csv_filename}")
    
    return df


# Main execution
if __name__ == "__main__":
    # Choose the year you want to crawl
    YEAR = 2024  
    ACCEPTED_ONLY = True  # Set to True to only crawl accepted papers
    
    print(f"{'='*60}")
    print(f"ICLR {YEAR} Paper & Review Crawler")
    if ACCEPTED_ONLY:
        print("Mode: ACCEPTED PAPERS ONLY")
    else:
        print("Mode: ALL PAPERS")
    print(f"{'='*60}\n")
    
    # Crawl the data
    data = crawl_iclr_papers_and_reviews(YEAR, accepted_only=ACCEPTED_ONLY)
    
    if not data:
        print("\nNo data collected. Try a different year.")
        exit(1)
    
    # Save to files
    df = save_data(data, YEAR, accepted_only=ACCEPTED_ONLY)
    
    if df is not None and len(df) > 0:
        # Display summary statistics
        print(f"\n{'='*60}")
        print(f"Summary Statistics for ICLR {YEAR}")
        print(f"{'='*60}")
        print(f"Total papers: {len(data)}")
        print(f"Papers with reviews: {df['num_reviews'].gt(0).sum()}")
        print(f"Average reviews per paper: {df['num_reviews'].mean():.2f}")
        if df['avg_rating'].notna().any():
            print(f"Average rating: {df['avg_rating'].mean():.2f}")
        
        # Decision breakdown
        if 'decision' in df.columns and df['decision'].notna().any():
            print(f"\nDecision breakdown:")
            print(df['decision'].value_counts())
        
