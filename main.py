# Backward compatibility wrapper - imports from the new src structure
from src.engine.bot import ArbitrageBot, main

# Make main function available at module level for backward compatibility
if __name__ == "__main__":
    main()