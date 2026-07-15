"""Application entry point.

This is the minimal entry point for Module 0 (Project Foundation). It
initializes centralized logging and confirms that the project
scaffold is wired together correctly. No agents, workflows, or API
routes exist yet — those are introduced in later modules.
"""

from app.core.logger import configure_logging, logger


def main() -> None:
    """Initialize application logging and confirm successful startup."""
    configure_logging()
    logger.info("Initializing AI Consulting Firm application.")
    print("AI Consulting Firm initialized successfully.")


if __name__ == "__main__":
    main()
