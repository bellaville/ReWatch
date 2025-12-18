import os

required_env_vars = [
    'REDIS_URL'
]

missing_vars = [var for var in required_env_vars if var not in os.environ]
if missing_vars:
    raise EnvironmentError(f"Missing required environment variables: {', '.join(missing_vars)}")