import asyncio
from app.core.database import connect_to_mongo
from app.models.review import Review
from beanie import PydanticObjectId

async def inspect():
    await connect_to_mongo()
    
    # Get the latest completed review
    review = await Review.find_one(
        Review.status == "completed"
    )
    
    if review:
        print(f"Review ID: {review.id}")
        print(f"\nLogic Analysis Type: {type(review.logic_analysis)}")
        print(f"Logic Analysis:\n{review.logic_analysis[:500] if review.logic_analysis else 'None'}...")
        print(f"\nReadability Analysis Type: {type(review.readability_analysis)}")
        print(f"Readability Analysis:\n{review.readability_analysis[:500] if review.readability_analysis else 'None'}...")

if __name__ == "__main__":
    asyncio.run(inspect())
