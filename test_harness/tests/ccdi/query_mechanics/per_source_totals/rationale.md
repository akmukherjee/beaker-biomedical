# Intended Behavior

The agent calls `/sample/summary` through `source_totals`, lists each answering source (KidsFirst ~201,614, CCDI-DCC ~79,285, StJude ~38,926, Treehouse ~13,046, ccdi-ecDNA ~3,868, ccdi-iusccc-pst ~131), and states that PCDC could not answer (`InvalidRoute`).

# Incorrect Behavior

The agent invents a field to count on, leaves PCDC out silently, treats PCDC as zero, or presents a single sum as the number of unique samples.
