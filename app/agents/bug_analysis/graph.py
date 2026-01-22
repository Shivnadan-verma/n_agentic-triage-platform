def analyze(severity):
    return 80 if severity in ["High", "Critical"] else 40
