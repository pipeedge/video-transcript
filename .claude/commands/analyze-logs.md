Please act as a senior operations engineer and analyze the main server log file.

Follow these steps precisely:

1.  Locate the main server log file. It's usually found at `logs/server.log`.
2.  Filter the logs for entries from the last 24 hours. (Today's date is Monday, July 28, 2025).
3.  Within that 24-hour period, search for all lines containing the keywords "ERROR" or "CRITICAL".
4.  If `$ARGUMENTS` is provided, further filter the results to only include lines that also contain the specific text from `$ARGUMENTS`.
5.  Group the resulting errors by the type of error message.
6.  Provide a concise summary of your findings. Start with a high-level overview (e.g., "Found 15 critical errors across 3 types..."), and then list the unique error types and how many times each occurred.
7.  Present the results in a clean, readable format.