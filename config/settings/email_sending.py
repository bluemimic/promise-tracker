from config.env import env

SMTP_HOST = env.str("SMTP_HOST", default="smtp.example.com")
SMTP_PORT = env.int("SMTP_PORT", default=465)

SMTP_LOGIN = env.str("SMTP_LOGIN", default="")
SMTP_PASSWORD = env.str("SMTP_PASSWORD", default="")

SMTP_SENDER = env.str("SMTP_SENDER", default=SMTP_LOGIN)
