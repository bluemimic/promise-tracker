from config.env import env

EMAIL_HOST = env.str("EMAIL_HOST", default="smtp.example.com")
EMAIL_PORT = env.int("EMAIL_PORT", default=465)

EMAIL_HOST_USER = env.str("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env.str("EMAIL_HOST_PASSWORD", default="")

EMAIL_SENDER = env.str("EMAIL_SENDER", default=EMAIL_HOST_USER)

EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=False)
EMAIL_USE_SSL = env.bool("EMAIL_USE_SSL", default=True)
EMAIL_SENDING_DELAY_MINUTES = env.int("EMAIL_SENDING_DELAY_MINUTES", default=2)
