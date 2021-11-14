# uni-ahp-ranking

data.xml represents data necessary to calculate the AHP ranking.

No additional python requirements atm

Usage:
```
root = ET.parse('data.xml').getroot()
# AHP creates a tree of criteria, loads up the decision matrices and set's up waights based on them
ahp = AHP(root)
# returns a list of scores for alternatives at the specified indices (ordering identical to the one in the xml file)
print(ahp.get_scores_for([0, 1, 2]))
```

Returns:
```
{'Tom': 0.35813676942236533, 'Dick': 0.49278818823437454, 'Harry': 0.14907504234326027}
```

Example data taken from Wikipedia: https://en.wikipedia.org/wiki/Analytic_hierarchy_process_%E2%80%93_leader_example
