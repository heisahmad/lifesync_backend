from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from app.models.gamification import UserProfile, Badge, UserBadge
from app.models.goal import Goal, ProgressLog
from app.utils.redis_utils import redis_cache

class GamificationService:
    XP_REWARDS = {
        "progress_logged": 10,
        "goal_completed": 100,
        "streak_maintained": 50,
        "social_interaction": 15,
        "health_milestone": 75,
        "financial_milestone": 75
    }
    
    LEVEL_MULTIPLIER = 1000  # XP needed per level = level * multiplier
    
    ACHIEVEMENT_CRITERIA = {
        "early_bird": {
            "description": "Complete 5 tasks before 9 AM",
            "xp_reward": 200,
            "icon": "sunrise"
        },
        "night_owl": {
            "description": "Maintain productivity after 9 PM",
            "xp_reward": 200,
            "icon": "moon"
        },
        "consistency_king": {
            "description": "Maintain a 7-day streak",
            "xp_reward": 300,
            "icon": "crown"
        },
        "health_master": {
            "description": "Meet all health goals for a week",
            "xp_reward": 400,
            "icon": "heart"
        },
        "savings_expert": {
            "description": "Stay under budget for 3 months",
            "xp_reward": 500,
            "icon": "piggy-bank"
        }
    }
    
    async def process_progress(self, db: Session, user_id: int, goal: Goal) -> Dict:
        profile = await self._get_or_create_profile(db, user_id)
        rewards = []
        
        # Award XP for logging progress
        base_xp = self.XP_REWARDS["progress_logged"]
        multiplier = self._calculate_multiplier(profile)
        xp_earned = int(base_xp * multiplier)
        
        profile.xp += xp_earned
        rewards.append({"type": "xp", "amount": xp_earned, "reason": "Progress logged"})
        
        # Check streak
        streak_reward = await self._process_streak(profile)
        if streak_reward:
            rewards.extend(streak_reward)
        
        # Process goal completion
        if goal.completed:
            completion_rewards = await self._process_goal_completion(db, profile, goal)
            rewards.extend(completion_rewards)
        
        # Check level up
        level_rewards = await self._check_level_up(profile)
        if level_rewards:
            rewards.extend(level_rewards)
        
        # Check achievements
        achievement_rewards = await self._check_achievements(db, profile, goal)
        if achievement_rewards:
            rewards.extend(achievement_rewards)
        
        # Update profile
        profile.last_activity = datetime.now()
        db.commit()
        
        # Cache rewards for real-time notifications
        await redis_cache.set_json(
            f"rewards:{user_id}:{datetime.now().timestamp()}", 
            rewards,
            expiry=timedelta(hours=24)
        )
        
        return {
            "profile": {
                "level": profile.level,
                "xp": profile.xp,
                "streak": profile.streak_count
            },
            "rewards": rewards
        }

    async def _get_or_create_profile(self, db: Session, user_id: int) -> UserProfile:
        profile = db.query(UserProfile).filter(
            UserProfile.user_id == user_id
        ).first()
        
        if not profile:
            profile = UserProfile(
                user_id=user_id,
                level=1,
                xp=0,
                streak_count=0
            )
            db.add(profile)
            db.commit()
        
        return profile

    def _calculate_multiplier(self, profile: UserProfile) -> float:
        """Calculate XP multiplier based on various factors"""
        base_multiplier = 1.0
        
        # Level bonus (small bonus for higher levels)
        level_bonus = 0.05 * (profile.level - 1)
        
        # Streak bonus
        streak_bonus = min(profile.streak_count * 0.1, 1.0)  # Cap at 100% bonus
        
        return base_multiplier + level_bonus + streak_bonus

    async def _process_streak(self, profile: UserProfile) -> Optional[List[Dict]]:
        rewards = []
        
        if profile.last_activity:
            time_diff = datetime.now() - profile.last_activity
            
            if time_diff <= timedelta(days=1):
                profile.streak_count += 1
                streak_xp = self.XP_REWARDS["streak_maintained"]
                profile.xp += streak_xp
                rewards.append({
                    "type": "streak",
                    "count": profile.streak_count,
                    "xp": streak_xp
                })
            else:
                profile.streak_count = 1
        
        return rewards if rewards else None

    async def _process_goal_completion(self, db: Session, profile: UserProfile, goal: Goal) -> List[Dict]:
        rewards = []
        
        # Base completion reward
        completion_xp = self.XP_REWARDS["goal_completed"]
        profile.xp += completion_xp
        rewards.append({
            "type": "completion",
            "xp": completion_xp,
            "goal_title": goal.title
        })
        
        # Category-specific rewards
        if goal.category == "health":
            health_xp = self.XP_REWARDS["health_milestone"]
            profile.xp += health_xp
            rewards.append({
                "type": "health_milestone",
                "xp": health_xp
            })
        elif goal.category == "finance":
            finance_xp = self.XP_REWARDS["financial_milestone"]
            profile.xp += finance_xp
            rewards.append({
                "type": "finance_milestone",
                "xp": finance_xp
            })
        
        return rewards

    async def _check_level_up(self, profile: UserProfile) -> Optional[List[Dict]]:
        rewards = []
        xp_for_next_level = profile.level * self.LEVEL_MULTIPLIER
        
        while profile.xp >= xp_for_next_level:
            profile.level += 1
            rewards.append({
                "type": "level_up",
                "new_level": profile.level,
                "perks": self._get_level_perks(profile.level)
            })
            xp_for_next_level = profile.level * self.LEVEL_MULTIPLIER
        
        return rewards if rewards else None

    def _get_level_perks(self, level: int) -> List[str]:
        """Return perks unlocked at specific levels"""
        perks = []
        
        if level >= 5:
            perks.append("Custom theme unlocked")
        if level >= 10:
            perks.append("Advanced analytics unlocked")
        if level >= 15:
            perks.append("Priority notifications")
        if level >= 20:
            perks.append("Extended history access")
        
        return perks

    async def _check_achievements(self, db: Session, profile: UserProfile, goal: Goal) -> Optional[List[Dict]]:
        rewards = []
        
        # Check each achievement criteria
        for achievement_id, criteria in self.ACHIEVEMENT_CRITERIA.items():
            if not await self._has_achievement(db, profile.id, achievement_id):
                if await self._meets_achievement_criteria(db, profile, goal, achievement_id):
                    # Award achievement
                    badge = await self._award_achievement(db, profile, achievement_id)
                    rewards.append({
                        "type": "achievement",
                        "name": badge.name,
                        "description": badge.description,
                        "xp": criteria["xp_reward"],
                        "icon": criteria["icon"]
                    })
        
        return rewards if rewards else None

    async def _has_achievement(self, db: Session, profile_id: int, achievement_id: str) -> bool:
        return db.query(UserBadge).join(Badge).filter(
            UserBadge.user_profile_id == profile_id,
            Badge.name == achievement_id
        ).first() is not None

    async def _meets_achievement_criteria(self, db: Session, profile: UserProfile, goal: Goal, achievement_id: str) -> bool:
        if achievement_id == "consistency_king":
            return profile.streak_count >= 7
        elif achievement_id == "health_master":
            return await self._check_health_mastery(db, profile.user_id)
        elif achievement_id == "savings_expert":
            return await self._check_savings_expertise(db, profile.user_id)
        # Add more achievement checks as needed
        return False

    async def _award_achievement(self, db: Session, profile: UserProfile, achievement_id: str) -> Badge:
        badge = db.query(Badge).filter(Badge.name == achievement_id).first()
        if not badge:
            badge = Badge(
                name=achievement_id,
                description=self.ACHIEVEMENT_CRITERIA[achievement_id]["description"],
                criteria=self.ACHIEVEMENT_CRITERIA[achievement_id],
                icon_url=f"/icons/{self.ACHIEVEMENT_CRITERIA[achievement_id]['icon']}.svg"
            )
            db.add(badge)
            db.flush()
        
        user_badge = UserBadge(
            user_profile_id=profile.id,
            badge_id=badge.id
        )
        db.add(user_badge)
        
        # Award XP for achievement
        profile.xp += self.ACHIEVEMENT_CRITERIA[achievement_id]["xp_reward"]
        
        db.commit()
        return badge

    async def _check_health_mastery(self, db: Session, user_id: int) -> bool:
        week_ago = datetime.now() - timedelta(days=7)
        health_goals = db.query(Goal).filter(
            Goal.user_id == user_id,
            Goal.category == "health",
            Goal.created_at >= week_ago
        ).all()
        
        return all(goal.completed for goal in health_goals) if health_goals else False

    async def _check_savings_expertise(self, db: Session, user_id: int) -> bool:
        three_months_ago = datetime.now() - timedelta(days=90)
        finance_goals = db.query(Goal).filter(
            Goal.user_id == user_id,
            Goal.category == "finance",
            Goal.created_at >= three_months_ago
        ).all()
        
        return all(goal.completed for goal in finance_goals) if finance_goals else False
