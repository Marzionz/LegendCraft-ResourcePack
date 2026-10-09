"""The client pack formats this pack is tested on, and how a pack.mcmeta declares a range of them.

The merge that builds the served pack and the gates over it read every bound from here, so the
tested ceiling moves in one place.
"""

# The newest client pack format this pack and the plugin packs merged into it have been
# exercised on. A client above it is served the pack without any overlay claiming its format.
TESTED_MAX_FORMAT = 88
