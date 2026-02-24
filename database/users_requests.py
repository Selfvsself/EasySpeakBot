from sqlalchemy import select, update
from sqlalchemy.orm.attributes import flag_modified

from database.engine import async_session
from database.models import UserProfile


async def get_user_profile(user_id: int) -> UserProfile:
    async with async_session() as session:
        query = select(UserProfile).filter(UserProfile.user_id == user_id)
        result = await session.execute(query)
        profile = result.scalar_one_or_none()

        if not profile:
            profile = UserProfile(user_id=user_id, bio_data={}, summary="")
            session.add(profile)
            await session.commit()
            await session.refresh(profile)

        return profile


async def update_user_profile(user_id: int, summary: str = None, bio_updates: dict = None):
    async with async_session() as session:
        update_data = {}
        if summary is not None:
            update_data['summary'] = summary

        if bio_updates is not None:
            profile = await get_user_profile(user_id)
            current_bio = profile.bio_data or {}
            current_bio.update(bio_updates)
            update_data['bio_data'] = current_bio
            flag_modified(profile, "bio_data")

        if update_data:
            query = update(UserProfile).where(UserProfile.user_id == user_id).values(**update_data)
            await session.execute(query)
            await session.commit()
