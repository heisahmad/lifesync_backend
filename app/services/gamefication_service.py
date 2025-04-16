
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.models.gamification import UserProfile, Badge, UserBadge

class GamificationService:
    XP_REWARDS = {
        "progress_logged": 10,
        "goal_completed": 100,
        "streak_maintained": 50
    }
    
    async def process_progress(self, db: Session, user_id: int, goal):
        profile = await self._get_or_create_profile(db, user_id)
        
        # Award XP for logging progress
        profile.xp += self.XP_REWARDS["progress_logged"]
        
        # Check streak
        if profile.last_activity:
            streak_maintained = (datetime.now() - profile.last_activity) <= timedelta(days=1)
            if streak_maintained:
                profile.streak_count += 1
                profile.xp += self.XP_REWARDS["streak_maintained"]
            else:
                profile.streak_count = 1
        
        profile.last_activity = datetime.now()
        
        # Check level up
        await self._check_level_up(profile)
        
        # Check badges
        if goal.completed:
            profile.xp += self.XP_REWARDS["goal_completed"]
            await self._check_badges(db, profile, goal)
        
        db.commit()
        return profile

    async def _get_or_create_profile(self, db: Session, user_id: int):
        profile = db.query(UserProfile).filter(
            UserProfile.user_id == user_id
        ).first()
        
        if not profile:
            profile = UserProfile(user_id=user_id)
            db.add(profile)
            db.commit()
        
        return profile

    async def _check_level_up(self, profile):
        xp_for_next_level = profile.level * 1000
        while profile.xp >= xp_for_next_level:
            profile.level += 1
            xp_for_next_level = profile.level * 1000

    async def _check_badges(self, db: Session, profile, goal):
        badges = db.query(Badge).all()
        for badge in badges:
            if self._meets_criteria(profile, goal, badge.criteria):
                user_badge = UserBadge(
                    user_profile_id=profile.id,
                    badge_id=badge.id
                )
                db.add(user_badge)

    def _meets_criteria(self, profile, goal, criteria):
        if criteria.get("min_level") and profile.level < criteria["min_level"]:
            return False
        if criteria.get("min_streak") and profile.streak_count < criteria["min_streak"]:
            return False
        if criteria.get("goals_completed") and goal.completed:
            return True
        return False
