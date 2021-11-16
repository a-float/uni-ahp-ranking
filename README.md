# uni-ahp-ranking

A simple cli program for managing an AHP process loaded from an xml file with a following structure:
```
<root>
    <criterion name="Goal" goal="Choose a leader">
        <criterion name="Experience"/>
        <criterion name="Education"> 
          <!-- criteria can be nested -->
          <criterion name="Practical knowledge/>
          <criterion name="Practical knowledge/>
        </criterion>
        <criterion name="Charisma"/>
        <criterion name="Age"/>
    </criterion>
    <alternatives>
        <!-- every alternatives is considered with respect to criteria with no subcriteria-->
        <alternative name="Tom"/>
        <alternative name="Dick"/>
        <alternative name="Harry"/>
    </alternatives>
    <data>
    <!-- optional matrices data -->
    </data>
</root>
```

### Usage
```
pip install -r requirements.txt
python ahp_cli.py
```

To view available commands use `help`

Example data taken from Wikipedia: 
- [Choosing a leader](https://en.wikipedia.org/wiki/Analytic_hierarchy_process_%E2%80%93_leader_example)
- [Choosing a car](https://en.wikipedia.org/wiki/Analytic_hierarchy_process_%E2%80%93_car_example)
