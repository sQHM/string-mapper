"""
Report Generator - Generate matching reports in various formats.
"""

from datetime import datetime
from io import BytesIO
from typing import Dict, List, Optional

import pandas as pd


class ReportGenerator:
    """Generate comprehensive matching reports."""

    def __init__(self, results_df: pd.DataFrame):
        """
        Initialize with matching results DataFrame.

        Args:
            results_df: DataFrame from StringMatcher.match_dataframes()
        """
        self.results_df = results_df
        self.generated_at = datetime.now()

    def get_summary_stats(self) -> Dict:
        """Generate summary statistics for the matching results."""
        total = len(self.results_df)
        if total == 0:
            return {
                "total_records": 0,
                "exact_matches": 0,
                "direct_matches": 0,
                "fuzzy_matches": 0,
                "no_matches": 0,
                "match_rate": 0.0,
                "exact_rate": 0.0,
                "fuzzy_rate": 0.0,
                "avg_fuzzy_score": 0.0,
            }

        match_types = self.results_df["match_type"].value_counts()

        exact = match_types.get("exact", 0)
        direct = match_types.get("direct", 0)
        fuzzy = match_types.get("fuzzy", 0)
        no_match = match_types.get("no_match", 0)

        fuzzy_df = self.results_df[self.results_df["match_type"] == "fuzzy"]
        avg_fuzzy = fuzzy_df["match_score"].mean() if len(fuzzy_df) > 0 else 0.0

        return {
            "total_records": total,
            "exact_matches": int(exact),
            "direct_matches": int(direct),
            "fuzzy_matches": int(fuzzy),
            "no_matches": int(no_match),
            "match_rate": ((exact + direct + fuzzy) / total) * 100,
            "exact_rate": ((exact + direct) / total) * 100,
            "fuzzy_rate": (fuzzy / total) * 100 if fuzzy > 0 else 0.0,
            "avg_fuzzy_score": float(avg_fuzzy),
        }

    def get_match_distribution(self) -> pd.DataFrame:
        """Get distribution of matches by source DataFrame."""
        if "matched_from" not in self.results_df.columns:
            return pd.DataFrame()

        distribution = self.results_df.groupby("matched_from").agg({
            "match_type": "count",
            "match_score": "mean"
        }).reset_index()

        distribution.columns = ["Source", "Count", "Avg Score"]
        return distribution

    def get_unmatched_records(self) -> pd.DataFrame:
        """Get all records that couldn't be matched."""
        return self.results_df[
            self.results_df["match_type"] == "no_match"
        ].copy()

    def get_low_confidence_matches(self, threshold: float = 85.0) -> pd.DataFrame:
        """Get fuzzy matches below a confidence threshold."""
        return self.results_df[
            (self.results_df["match_type"] == "fuzzy") &
            (self.results_df["match_score"] < threshold)
        ].copy()

    def get_high_confidence_matches(self, threshold: float = 95.0) -> pd.DataFrame:
        """Get matches above a confidence threshold."""
        return self.results_df[
            (self.results_df["match_score"] >= threshold)
        ].copy()

    def generate_excel_report(
        self,
        include_stats: bool = True,
        include_unmatched: bool = True,
        include_low_confidence: bool = True,
    ) -> BytesIO:
        """
        Generate a comprehensive Excel report.

        Returns:
            BytesIO buffer containing the Excel file
        """
        output = BytesIO()

        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            workbook = writer.book

            header_format = workbook.add_format({
                "bold": True,
                "bg_color": "#4F81BD",
                "font_color": "white",
                "border": 1,
            })

            success_format = workbook.add_format({"bg_color": "#C6EFCE"})
            warning_format = workbook.add_format({"bg_color": "#FFEB9C"})
            error_format = workbook.add_format({"bg_color": "#FFC7CE"})

            self.results_df.to_excel(writer, sheet_name="All Results", index=False)
            worksheet = writer.sheets["All Results"]

            for col_num, col in enumerate(self.results_df.columns):
                max_len = max(
                    self.results_df[col].astype(str).str.len().max(),
                    len(col)
                ) + 2
                worksheet.set_column(col_num, col_num, min(max_len, 50))

            if include_stats:
                stats = self.get_summary_stats()
                stats_df = pd.DataFrame([
                    ["Total Records", stats["total_records"]],
                    ["Exact Matches", stats["exact_matches"]],
                    ["Direct Matches", stats["direct_matches"]],
                    ["Fuzzy Matches", stats["fuzzy_matches"]],
                    ["No Matches", stats["no_matches"]],
                    ["Overall Match Rate", f"{stats['match_rate']:.1f}%"],
                    ["Exact/Direct Rate", f"{stats['exact_rate']:.1f}%"],
                    ["Avg Fuzzy Score", f"{stats['avg_fuzzy_score']:.1f}"],
                    ["Generated At", self.generated_at.strftime("%Y-%m-%d %H:%M:%S")],
                ], columns=["Metric", "Value"])

                stats_df.to_excel(writer, sheet_name="Summary", index=False)
                ws = writer.sheets["Summary"]
                ws.set_column(0, 0, 25)
                ws.set_column(1, 1, 25)

            if include_unmatched:
                unmatched = self.get_unmatched_records()
                if len(unmatched) > 0:
                    unmatched.to_excel(writer, sheet_name="Unmatched", index=False)
                    ws = writer.sheets["Unmatched"]
                    for col_num in range(len(unmatched.columns)):
                        ws.set_column(col_num, col_num, 20)

            if include_low_confidence:
                low_conf = self.get_low_confidence_matches()
                if len(low_conf) > 0:
                    low_conf.to_excel(writer, sheet_name="Low Confidence", index=False)
                    ws = writer.sheets["Low Confidence"]
                    for col_num in range(len(low_conf.columns)):
                        ws.set_column(col_num, col_num, 20)

            distribution = self.get_match_distribution()
            if len(distribution) > 0:
                distribution.to_excel(writer, sheet_name="Distribution", index=False)

        output.seek(0)
        return output

    def generate_text_report(self) -> str:
        """Generate a plain text summary report."""
        stats = self.get_summary_stats()

        report = f"""
╔══════════════════════════════════════════════════════════════╗
║                    STRING MATCHING REPORT                     ║
║              Generated: {self.generated_at.strftime("%Y-%m-%d %H:%M:%S")}                ║
╚══════════════════════════════════════════════════════════════╝

┌─────────────────────────────────────────────────────────────┐
│                       SUMMARY STATISTICS                     │
├─────────────────────────────────────────────────────────────┤
│  Total Records:        {stats['total_records']:>10}                         │
│  ─────────────────────────────────────────────────────────  │
│  Exact Matches:        {stats['exact_matches']:>10}                         │
│  Direct Matches:       {stats['direct_matches']:>10}                         │
│  Fuzzy Matches:        {stats['fuzzy_matches']:>10}                         │
│  No Matches:           {stats['no_matches']:>10}                         │
│  ─────────────────────────────────────────────────────────  │
│  Overall Match Rate:   {stats['match_rate']:>9.1f}%                         │
│  Exact/Direct Rate:    {stats['exact_rate']:>9.1f}%                         │
│  Average Fuzzy Score:  {stats['avg_fuzzy_score']:>9.1f}                          │
└─────────────────────────────────────────────────────────────┘
"""

        distribution = self.get_match_distribution()
        if len(distribution) > 0:
            report += """
┌─────────────────────────────────────────────────────────────┐
│                    MATCH DISTRIBUTION                        │
├─────────────────────────────────────────────────────────────┤
"""
            for _, row in distribution.iterrows():
                source = str(row["Source"])[:20].ljust(20)
                count = int(row["Count"])
                avg_score = float(row["Avg Score"])
                report += f"│  {source}  Count: {count:>5}  Avg Score: {avg_score:>5.1f}   │\n"
            report += "└─────────────────────────────────────────────────────────────┘\n"

        unmatched = self.get_unmatched_records()
        if len(unmatched) > 0:
            report += f"""
┌─────────────────────────────────────────────────────────────┐
│                    UNMATCHED RECORDS                         │
│              Total: {len(unmatched)} records need attention               │
└─────────────────────────────────────────────────────────────┘
"""

        low_conf = self.get_low_confidence_matches()
        if len(low_conf) > 0:
            report += f"""
┌─────────────────────────────────────────────────────────────┐
│                 LOW CONFIDENCE MATCHES                       │
│         {len(low_conf)} matches below 85% confidence                   │
└─────────────────────────────────────────────────────────────┘
"""

        return report
