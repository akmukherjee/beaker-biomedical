# Intended Behavior

The agent uses `disease_phase=Relapse` and reports CCDI-DCC ~308, KidsFirst ~52 and Treehouse ~25, says StJude, ccdi-ecDNA and ccdi-iusccc-pst have no matches, and says PCDC could not answer.

# Incorrect Behavior

The agent reports PCDC as zero, or omits it, or treats the 200 status as meaning every source answered.
