# Intended Behavior

The agent maps the wording to `tissue_type=Normal` and reports KidsFirst ~104,212, CCDI-DCC ~37,131, StJude ~22,743 and ccdi-iusccc-pst ~93. Treehouse and ccdi-ecDNA have no matches, and PCDC could not answer.

# Incorrect Behavior

The agent guesses a field such as `sample_type`, sends lowercase `normal`, or reports the rejected call as a failure of the sources.
