import os

REQUIRED_ENV_VARS = {
    "AUTH0_DOMAIN": str,
    "AUTH0_CLIENT_ID": str,
    "AUTH0_CLIENT_SECRET": str,
    "DATABASE_URL": str,
    "APP_SECRET_KEY": str,
    "WTF_CSRF_SECRET_KEY": str,
    "SECURITY_PASSWORD_SALT": str,
}

def validate_env_vars():
    """Validate required environment variables."""
    missing_vars = []
    invalid_vars = []

    for var, var_type in REQUIRED_ENV_VARS.items():
        value = os.getenv(var)
        if value is None:
            missing_vars.append(var)
        else:
            # Validate type if specified
            try:
                if var_type == int:
                    int(value)  # Attempt to cast to int
                elif var_type == float:
                    float(value)  # Attempt to cast to float
                elif var_type == bool:
                    if value.lower() not in ["true", "false"]:
                        raise ValueError(f"{var} must be a boolean (true/false).")
            except ValueError:
                invalid_vars.append(var)

    # Raise errors for missing or invalid variables
    if missing_vars:
        raise EnvironmentError(f"Missing required environment variables: {', '.join(missing_vars)}")
    if invalid_vars:
        raise EnvironmentError(f"Invalid values for environment variables: {', '.join(invalid_vars)}")