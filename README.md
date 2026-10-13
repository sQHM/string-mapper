# String Mapper

A local Python application for intelligent string matching across Excel files. Supports Chinese characters, numbers, and provides both direct and fuzzy matching capabilities.

## Features

- **Direct Matching**: Exact and case-insensitive matching
- **Fuzzy Matching**: Uses multiple algorithms (ratio, partial ratio, token sort, token set) for best results
- **Chinese Text Support**: Full support for Chinese characters using jieba tokenization
- **Number Handling**: Extracts and matches numbers, including Chinese numerals
- **Multi-file Lookup**: Match against multiple Excel files simultaneously
- **Comprehensive Reports**: Export results to Excel with statistics and analysis
- **Elegant UI**: Clean, modern Streamlit interface

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/string-mapper.git
cd string-mapper
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Start the application:
```bash
streamlit run app.py
```

2. Open your browser to `http://localhost:8501`

3. Follow the steps in the UI:
   - Upload your source Excel file
   - Select the target column (values to match)
   - Select info columns (additional data to include)
   - Upload one or more lookup Excel files
   - Select the match column for each lookup file
   - Click "Run Matching"
   - Download your report

## How It Works

### Source File
Your main Excel file containing:
- **Target Column**: The column with values you want to match
- **Info Columns**: Additional columns to include in the results

### Lookup Files
One or more Excel files to match against:
- **Match Column**: The column in each file to compare with the target

### Matching Process

1. **Normalization**: Text is normalized (Unicode NFKC, lowercase, full-width to half-width)
2. **Direct Match**: Checks for exact matches first
3. **Fuzzy Match**: If no direct match, uses multiple fuzzy algorithms:
   - Standard ratio
   - Partial ratio
   - Token sort ratio
   - Token set ratio
   - Chinese token overlap
   - Number matching

### Match Types

| Type | Description | Score |
|------|-------------|-------|
| Exact | Perfect string match | 100% |
| Direct | Match after normalization | 100% |
| Fuzzy | Similarity-based match | Variable |
| No Match | No suitable match found | 0% |

## Configuration

### Fuzzy Threshold
Adjust the minimum score required for fuzzy matches (default: 70%):
- Higher values = stricter matching, fewer false positives
- Lower values = more matches, potentially more false positives

## Output

### Excel Report
Contains multiple sheets:
- **All Results**: Complete matching results
- **Summary**: Statistics and metrics
- **Unmatched**: Records that couldn't be matched
- **Low Confidence**: Fuzzy matches below 85%
- **Distribution**: Match counts by source file

### Text Report
A formatted text summary with key statistics.

## Examples

### Matching Product Names
```
Source: "苹果手机 iPhone 15 Pro"
Lookup: "Apple iPhone 15 Pro Max"
Result: Fuzzy match with 85% confidence
```

### Matching with Numbers
```
Source: "订单号：20231015001"
Lookup: "Order 20231015001"
Result: Direct match (numbers extracted and matched)
```

## Requirements

- Python 3.8+
- See `requirements.txt` for package dependencies

## Project Structure

```
string-mapper/
├── app.py                 # Main Streamlit application
├── requirements.txt       # Python dependencies
├── README.md             # This file
└── src/
    ├── __init__.py
    ├── chinese_handler.py # Chinese text processing
    ├── matcher.py         # Matching logic
    └── report_generator.py # Report generation
```

## License

MIT License
