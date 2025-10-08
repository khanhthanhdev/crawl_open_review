"""
Example usage of Pydantic schemas for OpenReview data validation.

This script demonstrates how to use the Pydantic models to validate
and work with crawled OpenReview data.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.schemas import (
    Paper, Review, Comment, MetaReview, CrawlResult,
    create_paper_from_dict, create_crawl_result
)
from datetime import datetime


def example_paper_creation():
    """Example of creating and validating a Paper object."""
    print("=== Paper Creation Example ===")

    # Example paper data (similar to what the crawler produces)
    paper_data = {
        "paper_id": "ICLR.cc/2024/Conference/1234",
        "forum_id": "ICLR.cc/2024/Conference/1234",
        "title": "Deep Learning with Transformers",
        "abstract": "This paper introduces transformer architectures...",
        "authors": ["Alice Smith", "Bob Johnson", "Carol Williams"],
        "keywords": ["deep learning", "transformers", "NLP"],
        "pdf_url": "https://openreview.net/pdf?id=1234",
        "forum_url": "https://openreview.net/forum?id=1234",
        "reviews": [
            {
                "review_id": "review_1",
                "rating": "8: Accept",
                "confidence": "4: High",
                "summary": "Excellent work on transformer architectures",
                "strengths": "Novel architecture, strong empirical results",
                "weaknesses": "Limited comparison to baselines",
                "review_text": "This paper presents an innovative approach..."
            },
            {
                "review_id": "review_2",
                "rating": 7.5,
                "confidence": "3",
                "summary": "Good contribution but needs more analysis",
                "review_text": "The authors present a solid method..."
            }
        ],
        "comments": [
            {
                "note_id": "comment_1",
                "comment": "Thank you for the reviews. We have addressed the concerns..."
            }
        ],
        "meta_reviews": [
            {
                "id": "meta_1",
                "decision": "Accept (Poster)",
                "content": {"justification": "Strong technical contribution"}
            }
        ],
        "decision": "Accept (Poster)"
    }

    # Create validated Paper object
    try:
        paper = create_paper_from_dict(paper_data)
        print(f"✅ Created paper: {paper.title}")
        print(f"   Authors: {', '.join(paper.authors) if paper.authors else 'None'}")
        print(f"   Reviews: {len(paper.reviews)}")
        print(f"   Average rating: {paper.average_rating}")
        print(f"   Decision: {paper.decision}")
        print()

        # Show review summary
        review_stats = paper.get_reviews_summary()
        print(f"   Review statistics: {review_stats}")
        print()

    except Exception as e:
        print(f"❌ Validation error: {e}")
        return None

    return paper


def example_crawl_result():
    """Example of creating a complete CrawlResult."""
    print("=== Crawl Result Example ===")

    # Create some sample papers
    papers_data = [
        {
            "paper_id": "ICLR.cc/2024/Conference/1234",
            "forum_id": "ICLR.cc/2024/Conference/1234",
            "title": "Paper One",
            "authors": ["Author A", "Author B"],
            "reviews": [{"review_id": "r1", "rating": 8}],
            "decision": "Accept (Poster)"
        },
        {
            "paper_id": "ICLR.cc/2024/Conference/5678",
            "forum_id": "ICLR.cc/2024/Conference/5678",
            "title": "Paper Two",
            "authors": ["Author C"],
            "reviews": [{"review_id": "r2", "rating": 6}],
            "decision": "Reject"
        }
    ]

    # Create validated CrawlResult
    try:
        result = create_crawl_result(
            venue="ICLR",
            year=2024,
            papers=papers_data,
            accepted_only=False,
            api_version="v2"
        )

        print(f"✅ Created crawl result for {result.venue} {result.year}")
        print(f"   Total papers: {result.total_papers}")
        print(f"   Papers with reviews: {result.papers_with_reviews}")
        print(f"   Total reviews: {result.total_reviews}")
        print()

        # Show statistics
        stats = result.get_statistics()
        print("   Statistics:")
        for key, value in stats.items():
            if key != "decision_breakdown":
                print(f"     {key}: {value}")
        print(f"     decision_breakdown: {stats.get('decision_breakdown', {})}")
        print()

    except Exception as e:
        print(f"❌ Validation error: {e}")


def example_validation_errors():
    """Example of validation errors and how they're handled."""
    print("=== Validation Error Examples ===")

    # Example 1: Invalid rating
    print("1. Invalid rating handling:")
    try:
        review = Review(
            review_id="test_review",
            rating="invalid_rating_text",
            confidence="not_a_number"
        )
        print(f"   Rating processed as: {review.rating}")
        print(f"   Confidence processed as: {review.confidence}")
    except Exception as e:
        print(f"   Error: {e}")

    # Example 2: Missing required fields
    print("\n2. Missing required fields:")
    try:
        paper = Paper(
            paper_id="",  # Empty required field - this should fail
            forum_id="test_forum",
            title="Test Paper"
        )
        print("   Unexpected success - validation should have failed")
    except Exception as e:
        print(f"   Expected validation error: {str(e)[:100]}...")

    # Example 3: Authors normalization
    print("\n3. Authors normalization:")
    try:
        paper = Paper(
            paper_id="test_123",
            forum_id="test_forum",
            title="Test Paper",
            authors="Author One, Author Two, Author Three"  # String with commas
        )
        print(f"   Authors parsed as: {paper.authors}")
    except Exception as e:
        print(f"   Error: {e}")


def example_json_schema():
    """Example of generating JSON schema from Pydantic models."""
    print("=== JSON Schema Generation ===")

    # Generate schema for Paper model
    schema = Paper.model_json_schema()

    print("Paper model JSON schema (first 200 chars):")
    import json
    schema_str = json.dumps(schema, indent=2)[:500] + "..."
    print(schema_str)
    print()

    # Show some key properties
    print("Key schema properties:")
    print(f"  Required fields: {schema.get('required', [])}")
    print(f"  Total properties: {len(schema.get('properties', {}))}")


if __name__ == "__main__":
    print("OpenReview Pydantic Schemas Examples")
    print("=" * 50)
    print()

    # Run examples
    paper = example_paper_creation()
    example_crawl_result()
    example_validation_errors()
    example_json_schema()

    print("\n🎉 All examples completed!")