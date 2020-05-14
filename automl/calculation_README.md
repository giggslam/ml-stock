# Class CalcIntersection()

Calculate stock intersection (e.g. MA3 & MA10);

Calculate difference between intersection and the previous closing price;

Check cross signal.

## functions

### calculate_intersection()

Calculate the point where MA3 and MA10 intersect.

#### parameters

|parameters|type        |description                                   |
|----------|------------|----------------------------------------------|
|data      |pd.DataFrame| required                                     |
|date      |string      | intersection of specific date. default: None |

#### return

float value of intersection

---

### calculate_difference()

Calculate the difference from previous closing price to cross point.

#### parameters

|parameters|type        |description                                   |
|----------|------------|----------------------------------------------|
|data      |pd.DataFrame| required                                     |
|date      |string      | intersection of specific date. default: None |

#### return

float value of difference

---

### cross_signal()

Check if first MA and second MA crossed in the last 2 days.

#### parameters

|parameters|type        |description                                   |
|----------|------------|----------------------------------------------|
|data      |pd.DataFrame| required                                     |
|window1   |int         | window of first MA. default: 3               |
|window2   |int         | window of second MA. default: 10             |

#### return

> 1 if crossed
>
> 0 otherwise
