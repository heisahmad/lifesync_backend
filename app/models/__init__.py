# Import all your models here to make them easily accessible
from app.models.user import User
from app.models.integration import Integration

# This makes these models available when importing from app.models
__all__ = ["User", "Integration"]