# Intended Behavior

The agent filters `/file` on `type=BAM` and reports CCDI-DCC ~42,101, StJude ~38,112, KidsFirst ~23,674 and ccdi-iusccc-pst ~131. Treehouse and ccdi-ecDNA have none, and PCDC could not answer.

# Incorrect Behavior

The agent reports total file counts as BAM counts, or leaves out the sources with no matches or failures without saying so.
