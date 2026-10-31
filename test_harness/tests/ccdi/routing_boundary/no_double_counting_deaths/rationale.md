# Intended Behavior

The agent filters on `vital_status=Dead`, reports per-source counts (CCDI-DCC ~7,939, ccdi-ecDNA ~581, KidsFirst ~335, ccdi-iusccc-pst ~54), and explains that it cannot give a unique count because subjects may overlap between sources. PCDC rejects this filter but answers through its count endpoint (~4,952).

# Incorrect Behavior

The agent gives a bare sum such as 13,861 as the number of unique children.
