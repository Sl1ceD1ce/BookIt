# TODO: Use environment variables or more secure method in production

# Status codes
OK = 200
BAD_REQUEST = 400
UNAUTHORIZED = 401

# User validation
MAX_NAME_LEN = 30
MAX_EMAIL_LEN = 50
PASSWORD_REGEX = r"^[A-Za-z0-9_]+$"

# JWT token
JWT_SECRET = "your-secret-key-change-this-in-production"
JWT_ALGORITHM = "HS256"
JWT_EXP_HOURS = 24
