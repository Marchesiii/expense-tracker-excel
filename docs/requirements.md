# Expense Tracker Application Requirements

## Table of Contents
- [System Requirements](#system-requirements)
- [Dependencies](#dependencies)
- [Installation](#installation)
- [Project Structure](#project-structure)
- [Scripts Overview](#scripts-overview)
- [Usage](#usage)
- [Data Format](#data-format)

## System Requirements

### Minimum Requirements
- **Python**: 3.8 or higher
- **RAM**: 512 MB (minimum), 2 GB recommended
- **Disk Space**: 500 MB available
- **Operating System**: Windows, macOS, or Linux

### Additional Tools
- **Excel**: Microsoft Excel, LibreOffice Calc, or compatible spreadsheet viewer
- **PDF Reader**: For viewing extracted expense reports (optional)

## Dependencies

### External Libraries
| Library        | Version  | Purpose |
|----------------|----------|---------|
| **pandas**     | ≥ 1.3.0  | Data manipulation, analysis, and transformation |
| **matplotlib** | ≥ 3.3.0  | Data visualization and plotting |
| **seaborn**    | ≥ 0.11.0 | Statistical data visualization |
| **openpyxl**   | ≥ 3.0.0  | Reading/writing Excel files (.xlsx format) |
| **PyPDF2**     | ≥ 3.0.0  | Reading/writing Pdf files|

### Built-in Libraries (No Installation Required)
- **time**: Time-related functions and utilities
- **os**: Operating system interfaces and file path operations
- **tkinter**: GUI toolkit for user interfaces

### Local Modules
- **app**: Application orchestration (Controller) — `ExpenseTrackerApp`
- **services**: Business logic (Model) — normalization, financial analysis, alerts, forecasting
- **domain**: Typed contracts used by services — enums (`TransactionType`, `AlertStatus`) and validators
- **ui**: Tkinter windows (View)
- **scripts.process_pdf**: Module for PDF processing and generation
- **scripts.process_txt**: Module for text file parsing and processing

## Installation

### Step 1: Verify Python Installation
```bash
python --version
# or 
python3 --version
```

### Step 2: Clone/Setup Project
```bash
cd expense-tracker-excel
```

### Step 3: Install Dependencies
Using pip:
```bash
pip install -r requirements.txt
```

### Step 4: Verify Installation
```bash
python -c "import pandas, matplotlib, seaborn, openpyxl; print('All dependencies installed successfully!')"
```

## Project Structure

```
expense-tracker-excel/
├── main.py                # Entry point
├── app/
│   └── app.py             # ExpenseTrackerApp (Controller)
├── services/               # Business logic (Model)
│   ├── data_loader.py
│   ├── normalization_service.py
│   ├── financial_service.py
│   ├── alert_service.py
│   └── forecast_service.py
├── domain/                 # Typed contracts (Model)
│   ├── enums.py
│   ├── models.py
│   └── validators.py
├── ui/                      # Tkinter windows (View)
│   ├── main_window.py
│   ├── dashboard_window.py
│   ├── styles.py
│   └── widgets.py
├── data/
│   └── pdf/              # PDF (usually Mercado Pago) export directory 
│       └── Silvana/      # User-specific expense data
├── scripts/
│   ├── process_excel.py  # Excel file processing
│   ├── process_pdf.py    # PDF generation/processing
│   ├── process_txt.py    # Text file processing
│   └── generate_sample_expenses.py  # Sample data generator
├── legacy/
│   └── process_expenses.py  # Pre-refactor monolith, kept for historical reference only
├── tests/
│   └── test_services.py
├── docs/
│   └── requirements.md   # This file
└── README.md            # Project overview
```

## Scripts Overview

### `main.py`
- **Purpose**: Entry point for the active application (MVC: `app/` Controller → `services/`+`domain/` Model → `ui/` View)
- **Usage**: `python main.py`

### `process_excel.py`
- **Purpose**: Handle Excel file operations and transformations
- **Features**: Read, write, format Excel files
- **Usage**: `python scripts/process_excel.py`

### `process_pdf.py`
- **Purpose**: Generate or process PDF reports from expense data
- **Output**: PDF files in `data/pdf/` directory
- **Usage**: `python scripts/process_pdf.py`

### `process_txt.py`
- **Purpose**: Parse and process text-based expense data
- **Input**: TXT files from mobile downloads
- **Usage**: `python scripts/process_txt.py`

### `generate_sample_expenses.py`
- **Purpose**: Generate sample expense data for testing
- **Usage**: `python scripts/generate_sample_expenses.py`

## Usage

### Basic Workflow

1. **Prepare Your Data**
   - Ensure expense data is in the correct format (see [Data Format](#data-format))
   - Place Excel files in the project directory

2. **Run the Application**
   ```bash
   python main.py
   ```

3. **Review Results**
   - Check generated reports and statistics
   - Exports are saved to appropriate directories (Excel, PDF, etc.)

### Processing Mobile Exports
```bash
python scripts/process_txt.py
# Processes .txt files from mobile downloads
```

## Data Format

### Excel File Format
The `expenses.xlsx` file should contain the following columns:

| Column       | Type       | Description                   | Example |
|--------------|------------|-------------------------------|---------|
| **Date**     | YYYY-MM-DD | Transaction date              | 2024-01-15 |
| **Category** | Text       | Expense category              | Food, Transport, Utilities |
| **Amount**   | Decimal    | Expense amount                | 50.00 |
| **Notes**    | Text       | Additional details (optional) | Grocery store |

### Required Format
- Header row with column names
- One expense per row
- Consistent date format
- Numeric amounts (no currency symbols)

### Example Data
```
Date,Category,Amount,Notes
2024-01-15,Food,50.00,Grocery store
2024-01-15,Transport,12.50,Gas
2024-01-16,Utilities,45.00,Electricity bill
```

## Troubleshooting

### Common Issues

**"ModuleNotFoundError: No module named 'pandas'"**
- Solution: Run `pip install pandas openpyxl`

**"File not found" error**
- Solution: Ensure the Excel file exists in the correct directory
- Check file path and permissions

**Encoding issues with text files**
- Solution: Ensure text files are UTF-8 encoded
- Use `process_txt.py` with proper encoding detection

## Next Steps
- Review the main [README.md](../README.md) for project overview
- Check individual script files for detailed documentation
- Run `generate_sample_expenses.py` to create test data