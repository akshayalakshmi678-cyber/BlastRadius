import unittest
from analyzer import analyze_source

SAMPLE = """
def leaf():
    return 1

def middle():
    return leaf()

def top():
    return middle()
"""

class AnalyzerTests(unittest.TestCase):
    def test_finds_functions_and_calls(self):
        report = analyze_source(SAMPLE, "leaf")
        self.assertEqual(report["function_count"], 3)
        self.assertEqual(report["edge_count"], 2)
        self.assertEqual(report["direct_callers"], ["middle"])
        self.assertEqual([x["name"] for x in report["affected"]], ["middle", "top"])

    def test_missing_target(self):
        report = analyze_source(SAMPLE, "missing")
        self.assertFalse(report["target_exists"])
        self.assertEqual(report["affected"], [])

    def test_syntax_error_is_not_silently_ignored(self):
        with self.assertRaises(SyntaxError):
            analyze_source("def broken(:", "broken")

if __name__ == "__main__":
    unittest.main()
